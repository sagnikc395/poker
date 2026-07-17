"""Tests for the agent package — parsing, state tracking, director logic."""

import random

from agent import Action, GameDirector, GameState, PlayerInfo, ReplayLog, ReplayStep
from agent.harness import _classify_action, _default_tools, _parse_bet
from agent.tools import get_game_context, set_state
from poker.game import BetRequest, TexasHoldem
from poker.player import Player

# ── Helpers ──────────────────────────────────────────────────────────


class FakeHarness:
    """Duck-typed harness that returns a fixed bet — no smolagents involved."""

    def __init__(self, name: str, fixed_bet: int = 0):
        self.name = name
        self.style = "TAG"
        self.fixed_bet = fixed_bet

    def decide(self, state: GameState) -> int:
        return self.fixed_bet


def make_bet(player: Player, pot: int = 0, to_call: int = 0, max_bet: int = 100) -> BetRequest:
    return BetRequest(
        player=player,
        pot=pot,
        committed=0,
        to_call=to_call,
        max_bet=max_bet,
    )


H2 = [FakeHarness("A"), FakeHarness("B")]


# ── _parse_bet ───────────────────────────────────────────────────────


class TestParseBet:
    def test_fold_check(self):
        s = GameState(to_call=10, max_bet=100)
        assert _parse_bet(0, s) == 0
        assert _parse_bet("fold", s) == 0
        assert _parse_bet("check", s) == 0
        assert _parse_bet("0", s) == 0

    def test_call(self):
        s = GameState(to_call=10, max_bet=100)
        assert _parse_bet("call", s) == 10
        assert _parse_bet("I call", s) == 10
        assert _parse_bet(10, s) == 10
        assert _parse_bet("10", s) == 10

    def test_raise(self):
        s = GameState(to_call=10, max_bet=100)
        assert _parse_bet("raise to 40", s) == 40
        assert _parse_bet("raise 40", s) == 40
        assert _parse_bet(50, s) == 50

    def test_all_in(self):
        s = GameState(to_call=10, max_bet=100)
        assert _parse_bet("all in", s) == 100
        assert _parse_bet("all-in", s) == 100
        assert _parse_bet("I go all in", s) == 100

    def test_clamping(self):
        s = GameState(to_call=10, max_bet=50)
        assert _parse_bet(150, s) == 50
        assert _parse_bet(-5, s) == 0

    def test_none(self):
        assert _parse_bet(None, GameState()) == 0


# ── _classify_action ─────────────────────────────────────────────────


class TestClassifyAction:
    def test_fold(self):
        assert _classify_action(0, 10) == "fold"

    def test_check(self):
        assert _classify_action(0, 0) == "check"

    def test_call(self):
        assert _classify_action(10, 10) == "call"
        assert _classify_action(5, 10) == "call"

    def test_raise(self):
        assert _classify_action(20, 10) == "raise"
        assert _classify_action(10, 0) == "raise"


# ── GameState / tools ────────────────────────────────────────────────


class TestGameStateAndTools:
    def test_game_context_formatting(self):
        state = GameState(
            hand_number=1,
            street="pre-flop",
            pot=3,
            to_call=2,
            max_bet=100,
            hero_name="Hero",
            hero_cards=["As", "Kh"],
            hero_chips=98,
            hero_position=2,
            num_players=3,
            players=[
                PlayerInfo("Alice", 100, bet=1),
                PlayerInfo("Bob", 100, bet=2),
                PlayerInfo("Hero", 98, bet=0),
            ],
        )
        set_state(state)
        ctx = get_game_context()
        assert "Hand #1" in ctx
        assert "As Kh" in ctx
        assert "Alice" in ctx
        assert "Bob" in ctx


# ── GameDirector: message parsing ────────────────────────────────────


class TestDirectorMessageParsing:
    def test_preflop_resets_state(self):
        d = GameDirector(H2, ["A", "B"])
        d._hand_number = 5
        d._street = "river"
        d._community = ["As", "Ks"]
        d._bets = {"A": 10, "B": 20}
        d._folds = {"A": True}
        d._player_cards = {"A": ["Ah", "Kh"]}
        d._action_history = [Action("A", "call", 10, "pre-flop")]

        d.message("Pre-flop:")
        assert d._hand_number == 6
        assert d._street == "pre-flop"
        assert d._community == []
        assert d._bets == {"A": 0, "B": 0}
        assert d._folds == {"A": False, "B": False}
        assert d._player_cards == {}

    def test_blind_message(self):
        d = GameDirector(H2, ["A", "B"])
        d.message("Pre-flop:")
        d.message("[A] Pot: 0. Blind: 1/99")
        assert d._bets["A"] == 1

    def test_hole_cards_message(self):
        d = GameDirector(H2, ["A", "B"])
        d.message("Pre-flop:")
        d.message("[A] As Kh")
        assert d._player_cards == {"A": ["As", "Kh"]}

    def test_community_cards(self):
        d = GameDirector(H2, ["A", "B"])
        d.message("Pre-flop:")
        d.message("Flop: As Kd Qh")
        assert d._street == "flop"
        assert d._community == ["As", "Kd", "Qh"]

        d.message("Turn: 2c")
        assert d._community == ["As", "Kd", "Qh", "2c"]

        d.message("River: 3s")
        assert d._community == ["As", "Kd", "Qh", "2c", "3s"]

    def test_showdown_chips_update(self):
        d = GameDirector(H2, ["A", "B"], buy_in=100)
        d._chips = {"A": 50, "B": 150}
        d.message("[A] ... Chips: 80")
        assert d._chips["A"] == 80

    def test_divider_is_noop(self):
        d = GameDirector(H2, ["A", "B"])
        d.divider()
        d.divider(heavy=True)


# ── GameDirector: request_bet ────────────────────────────────────────


class TestDirectorRequestBet:
    def test_routes_to_correct_agent(self):
        h = FakeHarness("Alice", fixed_bet=10)
        d = GameDirector([h, FakeHarness("Bob")], ["Alice", "Bob"])
        d.message("Pre-flop:")
        d.message("[Alice] As Kh")
        d.message("[Bob] 7d 2c")

        bet = d.request_bet(make_bet(Player("Alice", 100, cards=["As", "Kh"]), pot=3, to_call=2))
        assert bet == 10

    def test_records_replay_step(self):
        d = GameDirector(H2, ["A", "B"])
        d.message("Pre-flop:")
        d.request_bet(make_bet(Player("A", 100, cards=["As", "Kh"]), to_call=2))
        assert d.replay.total_steps == 1
        assert d.replay.steps[0].player == "A"

    def test_fold_updates_internal_state(self):
        h = FakeHarness("A", fixed_bet=0)
        d = GameDirector([h, FakeHarness("B")], ["A", "B"])
        d.message("Pre-flop:")
        d.request_bet(make_bet(Player("A", 100, cards=["As", "Kh"]), to_call=2))
        assert d._folds["A"] is True

    def test_call_does_not_mark_fold(self):
        h = FakeHarness("A", fixed_bet=2)
        d = GameDirector([h, FakeHarness("B")], ["A", "B"])
        d.message("Pre-flop:")
        d.request_bet(make_bet(Player("A", 100, cards=["As", "Kh"]), to_call=2))
        assert d._folds["A"] is False

    def test_invalid_bet_falls_back_to_zero(self):
        h = FakeHarness("A", fixed_bet=999)
        d = GameDirector([h, FakeHarness("B")], ["A", "B"])
        d.message("Pre-flop:")
        bet = d.request_bet(make_bet(Player("A", 100, cards=["As", "Kh"]), to_call=2, max_bet=5))
        assert bet == 0

    def test_build_state_includes_all_players(self):
        h = FakeHarness("A")
        d = GameDirector([h, FakeHarness("B"), FakeHarness("C")], ["A", "B", "C"])
        d.message("Pre-flop:")
        d.message("[A] As Kh")
        d.message("[B] 7d 2c")
        d.message("[C] 3s 4s")
        d.request_bet(make_bet(Player("A", 100, cards=["As", "Kh"]), pot=3, to_call=2))
        assert d.replay.steps[0].state.num_players == 3
        assert len(d.replay.steps[0].state.players) == 3

    def test_raises_for_unknown_player(self):
        import pytest

        h = FakeHarness("A")
        d = GameDirector([h, FakeHarness("B")], ["A", "B"])
        d.message("Pre-flop:")
        with pytest.raises(RuntimeError, match="No agent configured for C"):
            d.request_bet(make_bet(Player("C", 100, cards=["As", "Kh"])))


# ── ReplayLog ────────────────────────────────────────────────────────


class TestReplayLog:
    def test_record_and_step(self):
        log = ReplayLog()
        log.record(ReplayStep(1, "pre-flop", "A", "call", 10))
        log.record(ReplayStep(1, "flop", "B", "raise", 20))
        assert log.total_steps == 2

        assert log.step_forward() is not None
        assert log.step_forward() is not None
        assert log.step_forward() is None

    def test_step_back(self):
        log = ReplayLog()
        log.record(ReplayStep(1, "pre-flop", "A", "call", 10))
        log.record(ReplayStep(1, "flop", "B", "raise", 20))
        log.step_forward()
        log.step_forward()
        assert log.step_back() is not None

    def test_summary(self):
        log = ReplayLog()
        log.record(ReplayStep(1, "pre-flop", "A", "call", 10))
        log.record(ReplayStep(1, "flop", "B", "raise", 20))
        lines = log.summary()
        assert len(lines) == 2
        assert "call" in lines[0]
        assert "raise" in lines[1]


# ── Full game integration ────────────────────────────────────────────


class TestFullGame:
    def test_two_fake_harnesses_produce_winner(self):
        h1 = FakeHarness("TAGbot", fixed_bet=0)
        h2 = FakeHarness("LAGbot", fixed_bet=2)
        director = GameDirector([h1, h2], ["TAGbot", "LAGbot"], buy_in=100)
        players = [Player("TAGbot", 100), Player("LAGbot", 100)]
        game = TexasHoldem(players, ui=director, big_blind=2, rng=random.Random(42))
        winner = game.play()
        assert winner.chips > 0
        assert director.replay.total_steps > 0


# ── Default tools list ───────────────────────────────────────────────


class TestDefaultTools:
    def test_default_tools_are_callable(self):
        tools = _default_tools()
        assert len(tools) == 6
        for t in tools:
            assert callable(t)
