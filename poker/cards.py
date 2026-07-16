"""Card primitives: ranks, suits, and the standard 52-card deck.

A card is a 2-character string: rank + suit, e.g. ``"As"`` (ace of spades).
"""

from __future__ import annotations

RANKS = "23456789TJQKA"
SUITS = "shcd"

RANK_VALUE = {rank: value for value, rank in enumerate(RANKS, start=2)}
SUIT_VALUE = {suit: value for value, suit in enumerate(SUITS)}

DECK: tuple[str, ...] = tuple(rank + suit for rank in RANKS for suit in SUITS)


def is_card(card: str) -> bool:
    """Return whether ``card`` is a valid 2-character card string."""
    return len(card) == 2 and card[0] in RANK_VALUE and card[1] in SUIT_VALUE


def card_key(card: str) -> tuple[int, int]:
    """Sort key ordering cards by rank, then suit."""
    return RANK_VALUE[card[0]], SUIT_VALUE[card[1]]
