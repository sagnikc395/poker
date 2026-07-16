"""Texas Hold 'em: hand evaluation, equity simulation, and a game engine."""

from .cards import DECK, RANKS, SUITS, card_key, is_card
from .equity import simulate_equity
from .evaluation import HandCategory, HandValue, best_hand, category, evaluate, evaluate_five
from .game import BetRequest, GameUI, TexasHoldem
from .gui import PokerGUI
from .player import Player
from .ranges import PREFLOP_HANDS, PREFLOP_RANKING

__version__ = "1.0.0"

__all__ = [
    "DECK",
    "PREFLOP_HANDS",
    "PREFLOP_RANKING",
    "RANKS",
    "SUITS",
    "BetRequest",
    "GameUI",
    "HandCategory",
    "HandValue",
    "Player",
    "PokerGUI",
    "TexasHoldem",
    "best_hand",
    "card_key",
    "category",
    "evaluate",
    "evaluate_five",
    "is_card",
    "simulate_equity",
]
