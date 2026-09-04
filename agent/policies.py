"""Participant policies used by the game director.

The engine asks for a bet amount. Policies hide whether that amount came from
an LLM, a human UI, a rules-based baseline, or an experiment harness.
"""

from collections.abc import Callable
from typing import Protocol

from .game_state import GameState


class DecisionPolicy(Protocol):
    def decide(self, state: GameState) -> int: ...


class HumanPolicy:
    """Adapt a state-aware callback (CLI, web, or desktop UI) to a policy."""

    def __init__(self, callback: Callable[[GameState], int]) -> None:
        self.callback = callback

    def decide(self, state: GameState) -> int:
        return self.callback(state)


class CallbackPolicy:
    """Small adapter useful for scripted policies and backtests."""

    def __init__(self, callback: Callable[[GameState], int]) -> None:
        self.callback = callback

    def decide(self, state: GameState) -> int:
        return self.callback(state)
