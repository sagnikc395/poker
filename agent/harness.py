import logging
import re
from collections.abc import Sequence

from smolagents import CodeAgent

from poker.game import BetRequest

from . import tools
from .game_state import Action, GameState, PlayerInfo
from .prompts import BASE_SYSTEM_PROMPT, STYLE_INSTRUCTIONS
from .replay import ReplayLog, ReplayStep

logger = logging.getLogger(__name__)

DEFAULT_MAX_STEPS = 8


class AgentHarness:
    """Wraps a smolagents CodeAgent with poker-specific state management."""

    def __init__(
        self,
        name: str,
        model,
        style: str = "TAG",
        tools_list: Sequence | None = None,
        max_steps: int = DEFAULT_MAX_STEPS,
    ) -> None:
        self.name = name
        self.style = style
        instructions = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS["TAG"])
        system_prompt = BASE_SYSTEM_PROMPT.format(
            style=style.lower(), style_description=instructions
        )
        self.agent = CodeAgent(
            tools=list(tools_list) if tools_list else [],
            model=model,
            instructions=system_prompt,
            max_steps=max_steps,
        )

    def decide(self, state: GameState) -> int:
        """Build a task prompt and run the agent to get a bet decision."""
        tools.set_state(state)
        task = _build_task(state)
        try:
            result = self.agent.run(task, reset=True)
            return _parse_bet(result, state)
        except Exception:
            logger.exception("Agent %s failed, folding", self.name)
            return 0

    @classmethod
    def from_model_id(
        cls,
        name: str,
        model_id: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
        style: str = "TAG",
        tools_list: Sequence | None = None,
        max_steps: int = DEFAULT_MAX_STEPS,
    ) -> "AgentHarness":
        from smolagents import InferenceClientModel

        model = InferenceClientModel(model_id=model_id)
        return cls(name, model, style, tools_list, max_steps)


def _build_task(state: GameState) -> str:
    lines = [
        f"It's your turn to act. Hand #{state.hand_number} - {state.street.upper()}",
        f"Your cards: {' '.join(state.hero_cards)}",
        f"Your chips: {state.hero_chips}",
        f"Pot: {state.pot}",
    ]
    if state.community_cards:
        lines.append(f"Board: {' '.join(state.community_cards)}")
    lines.append("")
    if state.to_call == 0:
        lines.append(
            "No one has bet yet. You can CHECK (return 0) or BET (return a value up to max_bet)."
        )
    else:
        lines.append(
            f"To call: {state.to_call}. 0=FOLD, {state.to_call}=CALL, "
            f"{state.to_call + 1}-{state.max_bet}=RAISE."
        )
    lines.append("")
    lines.append("Use the available tools to analyze the situation, then return your bet amount.")
    return "\n".join(lines)


def _parse_bet(result, state: GameState) -> int:
    if result is None:
        return 0
    if isinstance(result, int | float):
        bet = int(result)
    elif isinstance(result, str):
        s = result.strip().lower()
        if s in ("fold", "check", "0"):
            return 0
        if "all in" in s or "all-in" in s:
            return state.max_bet
        if "call" in s and "raise" not in s:
            return state.to_call
        nums = re.findall(r"\d+", s)
        bet = int(nums[0]) if nums else 0
    else:
        bet = 0
    if bet < 0:
        return 0
    if state.to_call > 0 and bet < state.to_call and bet > 0:
        return state.to_call
    if bet > state.max_bet:
        return state.max_bet
    return bet


class GameDirector:
    """Implements GameUI to orchestrate multiple agents playing against each other.

    Parses engine messages to track game state, routes request_bet calls to the
    appropriate agent, and records all actions for replay.
    """

    def __init__(
        self,
        agents: list[AgentHarness],
        player_names: list[str],
        buy_in: int = 100,
    ) -> None:
        if len(agents) > len(player_names):
            raise ValueError("More agents than players")
        if len(agents) < 2:
            raise ValueError("Need at least 2 agents")

        self.agents = list(agents)
        self.replay = ReplayLog()
        self._player_names = list(player_names)
        self._agent_map = {a.name: a for a in agents}
        self._hand_number = 0
        self._street = "pre-flop"
        self._community: list[str] = []
        self._chips: dict[str, int] = {p: buy_in for p in player_names}
        self._bets: dict[str, int] = {}
        self._folds: dict[str, bool] = {}
        self._action_history: list[Action] = []
        self._player_cards: dict[str, list[str]] = {}

    def set_player_cards(self, player_cards: dict[str, list[str]]) -> None:
        self._player_cards.update(player_cards)

    def set_community(self, cards: list[str]) -> None:
        self._community = list(cards)

    # ── GameUI Protocol ──────────────────────────────────────────────

    def message(self, text: str) -> None:
        if text == "Pre-flop:":
            self._hand_number += 1
            self._street = "pre-flop"
            self._community.clear()
            self._bets = {p: 0 for p in self._player_names}
            self._folds = {p: False for p in self._player_names}
            self._player_cards.clear()
            self._action_history.clear()
            return

        if m := re.match(r"^\[(.+?)\] (.*)$", text):
            name, rest = m.group(1), m.group(2)
            if bm := re.search(r"Blind: (\d+)", rest):
                bet = int(bm.group(1))
                self._bets[name] = self._bets.get(name, 0) + bet
                self._action_history.append(Action(name, "blind", bet, self._street))
            elif cm := re.search(r"Chips: (\d+)", rest):
                self._chips[name] = int(cm.group(1))
            else:
                cards = rest.strip().split()
                if cards and all(len(c) == 2 for c in cards):
                    self._player_cards[name] = cards
            return

        if text.startswith("Flop:"):
            self._street = "flop"
            self._community = text.split(":", 1)[1].strip().split()
        elif text.startswith("Turn:"):
            self._street = "turn"
            self._community.append(text.split(":", 1)[1].strip())
        elif text.startswith("River:"):
            self._street = "river"
            self._community.append(text.split(":", 1)[1].strip())

    def divider(self, heavy: bool = False) -> None:
        pass

    def request_bet(self, request: BetRequest) -> int:
        agent = self._agent_map.get(request.player.name)
        if agent is None:
            raise RuntimeError(f"No agent configured for {request.player.name}")

        state = self._build_state(agent.name, request)
        bet = agent.decide(state)

        if not request.is_valid(bet):
            bet = 0

        if bet == 0 and request.to_call > 0:
            self._folds[request.player.name] = True

        action_type = _classify_action(bet, request.to_call)
        self._action_history.append(Action(request.player.name, action_type, bet, self._street))

        self.replay.record(
            ReplayStep(
                hand_number=self._hand_number,
                street=self._street,
                player=request.player.name,
                action_type=action_type,
                amount=bet,
                state=state,
            )
        )

        return bet

    # ── Internal ─────────────────────────────────────────────────────

    def _build_state(self, hero_name: str, request: BetRequest) -> GameState:
        return GameState(
            hand_number=self._hand_number,
            street=self._street,
            pot=request.pot,
            to_call=request.to_call,
            max_bet=request.max_valid_bet,
            hero_name=hero_name,
            hero_cards=list(request.player.cards),
            hero_chips=request.player.chips,
            hero_position=self._player_names.index(hero_name),
            num_players=len(self._player_names),
            community_cards=list(self._community),
            players=[
                PlayerInfo(
                    name=p,
                    chips=self._chips.get(p, 0),
                    folded=self._folds.get(p, False),
                    bet=self._bets.get(p, 0),
                )
                for p in self._player_names
            ],
            actions=list(self._action_history),
        )


def _classify_action(bet: int, to_call: int) -> str:
    if bet == 0:
        return "fold" if to_call > 0 else "check"
    if bet == to_call or (to_call > 0 and bet <= to_call):
        return "call"
    return "raise"


def create_harnesses(
    names: list[str],
    model,
    style_map: dict[str, str] | None = None,
    tools_list: Sequence | None = None,
    max_steps: int = DEFAULT_MAX_STEPS,
) -> list[AgentHarness]:
    """Create one AgentHarness per name, optionally with per-name styles."""

    tl = list(tools_list) if tools_list else _default_tools()
    style_map = style_map or {}
    return [AgentHarness(name, model, style_map.get(name, "TAG"), tl, max_steps) for name in names]


def _default_tools():
    return [
        tools.get_hand_rank,
        tools.calculate_equity,
        tools.get_pot_odds,
        tools.get_position,
        tools.get_preflop_class,
        tools.get_game_context,
    ]
