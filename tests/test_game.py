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


def test_folding_awards_pot_to_last_player():
    class FoldToFirstUI(AlwaysCallUI):
        def request_bet(self, request: BetRequest) -> int:
            return 0  # check when free, fold when facing a bet

    players = [Player("A", 10), Player("B", 10)]
    game = TexasHoldem(players, ui=FoldToFirstUI(), big_blind=2, rng=random.Random(0))
    winner = game.play()
    # blinds get posted every hand and the small blind folds to the big blind
    assert winner.chips == 20
