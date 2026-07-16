"""Monte Carlo equity estimation against ranged opponents."""

import random
from collections.abc import Sequence

from .cards import DECK, is_card
from .evaluation import evaluate
from .ranges import PREFLOP_HANDS


def simulate_equity(
    pocket: Sequence[str],
    community: Sequence[str] = (),
    n_players: int = 2,
    *,
    n_simulations: int = 1024,
    ranges: Sequence[float] | None = None,
    rng: random.Random | None = None,
) -> tuple[float, float]:
    """Estimate ``(win_probability, tie_probability)`` for a pocket pair of cards.

    Each opponent is dealt a hand drawn uniformly from the top fraction of
    pre-flop hands given by ``ranges`` (1.0 = any two cards). ``community``
    may hold 0 or 3-5 known board cards; the rest are sampled.
    """
    pocket = list(pocket)
    community = list(community)
    seen = pocket + community

    if len(pocket) != 2 or len(community) not in (0, 3, 4, 5):
        raise ValueError("expected 2 pocket cards and 0 or 3-5 community cards")
    if len(set(seen)) != len(seen) or not all(is_card(card) for card in seen):
        raise ValueError("invalid or duplicate cards")
    if not 1 < n_players < 10:
        raise ValueError("n_players must be between 2 and 9")
    if ranges is None:
        ranges = [1.0] * (n_players - 1)
    if len(ranges) != n_players - 1:
        raise ValueError("ranges must have one entry per opponent")

    rng = rng or random.Random()
    unseen = [card for card in DECK if card not in seen]
    n_board = 5 - len(community)
    cutoffs = [max(1, int(len(PREFLOP_HANDS) * fraction)) for fraction in ranges]

    wins = ties = 0
    for _ in range(n_simulations):
        board = rng.sample(unseen, n_board)
        available = set(unseen).difference(board)
        full_board = community + board
        my_value = evaluate(pocket + full_board)
        best_opponent: tuple[int, ...] | None = None
        for cutoff in cutoffs:
            candidates = [
                hand
                for hand in PREFLOP_HANDS[:cutoff]
                if hand[0] in available and hand[1] in available
            ]
            hand = rng.choice(candidates)
            available.difference_update(hand)
            value = evaluate([*hand, *full_board])
            if best_opponent is None or value > best_opponent:
                best_opponent = value
        wins += my_value > best_opponent
        ties += my_value == best_opponent

    return wins / n_simulations, ties / n_simulations
