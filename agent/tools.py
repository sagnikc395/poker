import random

from smolagents import tool

from poker.cards import RANKS
from poker.equity import simulate_equity
from poker.evaluation import category, evaluate
from poker.ranges import PREFLOP_RANKING

from .game_state import GameState

_current_state: GameState | None = None


def set_state(state: GameState | None) -> None:
    global _current_state
    _current_state = state


def _get_preflop_class(cards: list[str]) -> str | None:
    if len(cards) != 2:
        return None
    r1, s1 = cards[0][0], cards[0][1]
    r2, s2 = cards[1][0], cards[1][1]
    sorted_ranks = sorted([r1, r2], key=lambda r: RANKS.index(r), reverse=True)
    if r1 == r2:
        cls = sorted_ranks[0] + sorted_ranks[1]
    elif s1 == s2:
        cls = sorted_ranks[0] + sorted_ranks[1] + "s"
    else:
        cls = sorted_ranks[0] + sorted_ranks[1] + "o"
    return cls if cls in PREFLOP_RANKING else None


def _position_label(pos: int, n: int) -> str:
    if n == 2:
        return "dealer (button)" if pos == 1 else "small blind"
    if pos == 0:
        return "small blind"
    if pos == 1:
        return "big blind"
    if pos == n - 1:
        return "dealer (button)"
    if n <= 4:
        return "late"
    return "early" if pos <= 3 else "middle"


@tool
def get_hand_rank() -> str:
    """Evaluate your current hand strength.

    Pre-flop returns the hand class (e.g. 'AK suited', 'pocket aces').
    Post-flop returns the best 5-card hand category (e.g. 'top pair', 'flush', 'two pair').

    Returns:
        A string describing your hand strength.
    """
    state = _current_state
    if not state or not state.hero_cards:
        return "unknown"

    if not state.community_cards:
        pfc = _get_preflop_class(state.hero_cards)
        if pfc:
            return f"pre-flop: {pfc}"
        return f"pre-flop: {' '.join(state.hero_cards)}"

    all_cards = state.hero_cards + state.community_cards
    cat = category(evaluate(all_cards))
    return f"post-flop: {cat.label}"


@tool
def calculate_equity(num_opponents: int = 0) -> float:
    """Runs a Monte Carlo simulation to estimate your equity (win + tie probability).

    Call this to get a statistically accurate estimate of your chance of winning.

    Args:
        num_opponents: Number of active opponents (0 = auto-detect from game state).

    Returns:
        Your win probability as a float between 0.0 and 1.0.
    """
    state = _current_state
    if not state or not state.hero_cards:
        return 0.0

    if num_opponents < 1:
        num_opponents = max(1, sum(1 for p in state.players if not p.folded) - 1)

    win_prob, tie_prob = simulate_equity(
        pocket=state.hero_cards,
        community=state.community_cards,
        n_players=num_opponents + 1,
        n_simulations=1024,
        rng=random.Random(),
    )
    return win_prob + tie_prob


@tool
def get_pot_odds() -> float:
    """Calculate the pot odds as a decimal ratio.

    Pot odds = (amount to call) / (pot + amount to call).
    Lower values mean you're getting better odds to call.
    A value of 0.0 means there is nothing to call.

    Returns:
        Pot odds ratio between 0.0 and 1.0.
    """
    state = _current_state
    if not state or state.to_call == 0:
        return 0.0
    return state.to_call / (state.pot + state.to_call)


@tool
def get_position() -> str:
    """Determine your position at the table relative to the dealer.

    Returns:
        One of: 'small blind', 'big blind', 'early', 'middle', 'late', 'dealer (button)'.
    """
    state = _current_state
    if not state:
        return "unknown"
    return _position_label(state.hero_position, state.num_players)


@tool
def get_preflop_class() -> str:
    """Get the pre-flop classification of your hole cards.

    Returns a standard 169-class label like 'AA', 'AKs', 'KQo', '76s'.
    Useful for assessing starting hand strength.

    Returns:
        The pre-flop hand class string, or 'unknown'.
    """
    state = _current_state
    if not state or not state.hero_cards:
        return "unknown"
    pfc = _get_preflop_class(state.hero_cards)
    return pfc or "unknown"


@tool
def get_game_context() -> str:
    """Get a complete formatted summary of the current game state.

    Includes hand number, street, pot, your cards, position, community cards,
    chip counts for all players, and recent actions.
    Call this first to understand the full situation.

    Returns:
        A multi-line string with the full game context.
    """
    state = _current_state
    if not state:
        return "No game state available."

    lines = [
        f"Hand #{state.hand_number} - {state.street.upper()}",
        f"Pot: {state.pot} | To call: {state.to_call}",
        f"Your cards: {' '.join(state.hero_cards)}",
        f"Your chips: {state.hero_chips}",
        f"Position: {_position_label(state.hero_position, state.num_players)}",
    ]

    if state.community_cards:
        lines.append(f"Board: {' '.join(state.community_cards)}")

    lines.append("")
    lines.append("Players:")
    for p in state.players:
        tag = " (YOU)" if p.name == state.hero_name else ""
        status = "FOLDED" if p.folded else "ACTIVE"
        lines.append(f"  {p.name}{tag} - {p.chips} chips, {status}, bet {p.bet}")

    if state.actions:
        lines.append("")
        lines.append("Recent actions:")
        for a in state.actions[-8:]:
            amt = f" {a.amount}" if a.amount else ""
            lines.append(f"  {a.player}: {a.action_type}{amt}")

    return "\n".join(lines)
