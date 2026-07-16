"""Poker hand evaluation backed by pokerkit."""

from enum import IntEnum
from itertools import combinations

from pokerkit import Card, Label, Rank, StandardHighHand, Suit

_RANK = {
    "2": Rank.DEUCE,
    "3": Rank.TREY,
    "4": Rank.FOUR,
    "5": Rank.FIVE,
    "6": Rank.SIX,
    "7": Rank.SEVEN,
    "8": Rank.EIGHT,
    "9": Rank.NINE,
    "T": Rank.TEN,
    "J": Rank.JACK,
    "Q": Rank.QUEEN,
    "K": Rank.KING,
    "A": Rank.ACE,
}
_SUIT = {"s": Suit.SPADE, "h": Suit.HEART, "d": Suit.DIAMOND, "c": Suit.CLUB}
_LABEL = {
    Label.HIGH_CARD: 0,
    Label.ONE_PAIR: 1,
    Label.TWO_PAIR: 2,
    Label.THREE_OF_A_KIND: 3,
    Label.STRAIGHT: 4,
    Label.FLUSH: 5,
    Label.FULL_HOUSE: 6,
    Label.FOUR_OF_A_KIND: 7,
    Label.STRAIGHT_FLUSH: 8,
}

HandValue = StandardHighHand


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


def _cards(cards):
    return [Card(_RANK[c[0]], _SUIT[c[1]]) for c in cards]


def evaluate_five(hand):
    """Evaluate exactly five cards into a comparable hand value."""
    return StandardHighHand(_cards(hand))


def evaluate(cards):
    """Evaluate the best 5-card hand from 5 to 7 cards."""
    c = _cards(cards)
    return max(StandardHighHand(combo) for combo in combinations(c, 5))


def best_hand(cards):
    """Return ``(value, best_five_cards)`` for 5 to 7 cards."""
    c = _cards(cards)
    best = max(combinations(c, 5), key=StandardHighHand)
    return StandardHighHand(best), [repr(card) for card in best]


def category(value: HandValue) -> HandCategory:
    """Extract the :class:`HandCategory` from an evaluated hand value."""
    return HandCategory(_LABEL[value.entry.label])
