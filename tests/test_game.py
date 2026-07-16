import random

from poker import BetRequest, Player, TexasHoldem


class AlwaysCallUI:
    """Scripted UI that checks/calls every decision and records output."""

    def __init__(self):
        self.lines: list[str] = []

    def message(self, text: str) -> None:
        self.lines.append(text)

    def divider(self, heavy: bool = False) -> None:
        pass

    def request_bet(self, request: BetRequest) -> int:
        return request.call_amount


def test_game_runs_to_a_single_winner():
    players = [Player("A", 10), Player("B", 10), Player("C", 10)]
    ui = AlwaysCallUI()
    game = TexasHoldem(players, ui=ui, big_blind=2, rng=random.Random(0))
    winner = game.play()
    assert winner.chips > 0
    assert winner.chips <= 30  # split-pot remainders may be discarded, never created
    assert any("Game over" in line for line in ui.lines)


def test_two_player_game_ends():
    players = [Player("A", 10), Player("B", 10)]
    game = TexasHoldem(players, ui=AlwaysCallUI(), big_blind=2, rng=random.Random(0))
    winner = game.play()
    assert winner.chips > 0
    assert winner.chips <= 20
