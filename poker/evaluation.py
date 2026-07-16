"""Poker hand evaluation.

Hands evaluate to a flat tuple ``(category, *tiebreakers)`` where ``category``
is a :class:`HandCategory`. Tuples compare lexicographically, so a higher
tuple is a stronger hand. This replaces the old precomputed 50MB lookup
table with direct evaluation.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from enum import IntEnum
from itertools import combinations

from .cards import RANK_VALUE, card_key

HandValue = tuple[int, ...]


class HandCategory(IntEnum):
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8

    @property
    def label(self) -> str:
        return self.name.replace("_", " ").lower()


def evaluate_five(hand: Sequence[str]) -> HandValue:
    """Evaluate exactly five cards into a comparable ``(category, *ranks)`` tuple."""
    ranks = sorted((RANK_VALUE[card[0]] for card in hand), reverse=True)
    is_flush = len({card[1] for card in hand}) == 1

    if len(set(ranks)) == 5:  # no pairs: straight, flush, or high card
        if ranks[0] - ranks[4] == 4:
            straight_high = ranks[0]
        elif ranks == [14, 5, 4, 3, 2]:  # the wheel: ace plays low
            straight_high = 5
        else:
            straight_high = 0
        if straight_high:
            category = HandCategory.STRAIGHT_FLUSH if is_flush else HandCategory.STRAIGHT
            return (category, straight_high)
        if is_flush:
            return (HandCategory.FLUSH, *ranks)
        return (HandCategory.HIGH_CARD, *ranks)

    # group ranks by multiplicity, highest count first, then highest rank
    groups = sorted(Counter(ranks).items(), key=lambda item: (item[1], item[0]), reverse=True)
    shape = tuple(count for _, count in groups)
    order = tuple(rank for rank, _ in groups)

    if shape[0] == 4:
        return (HandCategory.FOUR_OF_A_KIND, *order)
    if shape == (3, 2):
        return (HandCategory.FULL_HOUSE, *order)
    if shape[0] == 3:
        return (HandCategory.THREE_OF_A_KIND, *order)
    if shape[:2] == (2, 2):
        return (HandCategory.TWO_PAIR, *order)
    return (HandCategory.ONE_PAIR, *order)


def evaluate(cards: Iterable[str]) -> HandValue:
    """Evaluate the best 5-card hand from 5 to 7 cards."""
    cards = tuple(cards)
    if len(cards) == 5:
        return evaluate_five(cards)
    return max(evaluate_five(combo) for combo in combinations(cards, 5))


def best_hand(cards: Iterable[str]) -> tuple[HandValue, list[str]]:
    """Return ``(value, best_five_cards)`` for 5 to 7 cards."""
    best = max(combinations(tuple(cards), 5), key=evaluate_five)
    return evaluate_five(best), sorted(best, key=card_key, reverse=True)


def category(value: HandValue) -> HandCategory:
    """Extract the :class:`HandCategory` from an evaluated hand value."""
    return HandCategory(value[0])
