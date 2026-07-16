import random

import pytest

from poker import simulate_equity
from poker.ranges import PREFLOP_HANDS, PREFLOP_RANKING


def test_ranges_expand_to_all_combinations():
    assert len(PREFLOP_RANKING) == 169
    assert len(PREFLOP_HANDS) == 1326
    assert len(set(map(frozenset, PREFLOP_HANDS))) == 1326


def test_aces_are_favored_heads_up():
    win, tie = simulate_equity(["As", "Ah"], n_players=2, n_simulations=300,
                               rng=random.Random(1))
    assert win > 0.7
    assert 0 <= tie < 0.1


def test_board_cards_are_respected():
    # quads on the flop is nearly unbeatable
    win, tie = simulate_equity(["As", "Ah"], ["Ac", "Ad", "2s"], n_players=2,
                               n_simulations=200, rng=random.Random(2))
    assert win + tie == 1.0


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        simulate_equity(["As", "As"])  # duplicate
    with pytest.raises(ValueError):
        simulate_equity(["As", "Xx"])  # not a card
    with pytest.raises(ValueError):
        simulate_equity(["As", "Ah"], n_players=1)
    with pytest.raises(ValueError):
        simulate_equity(["As", "Ah"], ["2s", "3s"])  # 2 board cards is invalid
