"""Texas Hold 'em game engine.

The engine is UI-agnostic: it drives dealing, betting rounds, and showdowns,
and delegates all presentation and input to a :class:`GameUI` implementation.

Known limitation carried over from the original implementation: side pots are
not modeled, and a split pot discards the indivisible remainder.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Protocol

from .cards import DECK
from .evaluation import best_hand, category
from .player import Player

STREETS = (("Flop", 3), ("Turn", 1), ("River", 1))


@dataclass(frozen=True)
class BetRequest:
    """Everything a UI needs to ask a player for a bet."""

    player: Player
    pot: int
    committed: int  # chips this player already put in during this street
    to_call: int
    max_bet: int  # betting beyond this cannot be matched by any opponent

    @property
    def call_amount(self) -> int:
        """Chips actually needed to call (capped by the player's stack)."""
        return min(self.to_call, self.player.chips)

    @property
    def max_valid_bet(self) -> int:
        return min(self.max_bet, self.player.chips)

    def is_valid(self, bet: int) -> bool:
        """A bet is a fold/check (0), a call, or a raise up to ``max_valid_bet``."""
        if bet == 0 or bet == self.call_amount:
            return True
        return self.to_call < bet <= self.max_valid_bet


class GameUI(Protocol):
    def message(self, text: str) -> None: ...

    def divider(self, heavy: bool = False) -> None: ...

    def request_bet(self, request: BetRequest) -> int: ...


class TexasHoldem:
    """A hot-seat no-limit Texas Hold 'em game for 2-9 players."""

    def __init__(
        self,
        players: list[Player],
        ui: GameUI,
        big_blind: int = 2,
        rng: random.Random | None = None,
    ) -> None:
        if not 1 < len(players) < 10:
            raise ValueError("need 2 to 9 players")
        self.players = list(players)
        self.ui = ui
        self.big_blind = big_blind
        self.rng = rng or random.Random()
        self.hand_number = 1
        self.pot = 0
        self.bets: list[int] = []
        self.folds: list[bool] = []
        self.community: list[str] = []

    def play(self) -> Player:
        """Play hands until one player holds all the chips; return the winner."""
        while True:
            self.players = [p for p in self.players if p.chips > 0]
            if len(self.players) < 2:
                break
            self._play_hand()
            self.hand_number += 1
            self.players.append(self.players.pop(0))  # move the button
        winner = self.players[0]
        self.ui.divider()
        self.ui.message(f"Game over. [{winner.name}] wins with {winner.chips} chips.")
        return winner

    def _play_hand(self) -> None:
        deck = list(DECK)
        self.rng.shuffle(deck)
        n = len(self.players)
        self.pot = 0
        self.bets = [0] * n
        self.folds = [False] * n
        self.community = []

        for player in self.players:
            player.cards = [deck.pop(), deck.pop()]

        self.ui.message("Pre-flop:")
        for player in self.players:
            self.ui.message(f"[{player.name}] {' '.join(player.cards)}")

        if contested := self._betting_round(blind=True):
            for street, n_cards in STREETS:
                dealt = [deck.pop() for _ in range(n_cards)]
                self.community += dealt
                self.ui.message(f"{street}: {' '.join(dealt)}")
                if not (contested := self._betting_round()):
                    break

        self._showdown(contested)

    def _betting_round(self, blind: bool = False) -> bool:
        """Run one betting street. Return False when only one player remains."""
        n = len(self.players)
        self.ui.divider()
        n_round = 0
        all_in = [False] * n
        while not (all(all_in) or self.folds.count(False) == 1):
            for i in range(n):
                if self.folds[i]:
                    continue
                bet = self._bet(i, n_round, blind)
                self.bets[i] += bet
                self.players[i].chips -= bet
            if self.folds.count(False) == 1:
                break
            n_round += 1
            open_bets = [
                bet
                for bet, player, folded, was_all_in in zip(self.bets, self.players, self.folds, all_in)
                if not (folded or was_all_in or not (bet or player.chips))
            ]
            all_in = [p.chips == 0 for p in self.players]
            if len(set(open_bets)) < 2:  # everyone still in has matched
                break

        self.pot += sum(self.bets)
        self.bets = [0] * n
        self.ui.divider(heavy=True)
        return self.folds.count(False) > 1

    def _bet(self, position: int, n_round: int, blind: bool) -> int:
        player = self.players[position]
        opponents_chips = sum(
            p.chips for i, p in enumerate(self.players) if not self.folds[i] and i != position
        )
        to_call = max(self.bets) - self.bets[position]
        if not player.chips or not (to_call + opponents_chips):
            return 0
        if n_round == 0 and blind and position < 2:
            bet = min((position + 1) * self.big_blind // 2, player.chips)
            self.ui.message(f"[{player.name}] Pot: 0. Blind: {bet}/{player.chips - bet}")
            return bet
        if n_round == 0 or (n_round == 1 and blind and position < 2) or to_call > 0:
            return self._prompt(position, to_call)
        return 0

    def _prompt(self, position: int, to_call: int) -> int:
        player = self.players[position]
        others = [
            i for i in range(len(self.players)) if not self.folds[i] and i != position
        ]
        biggest = max(others, key=lambda i: self.players[i].chips)
        max_bet = self.bets[biggest] - self.bets[position] + self.players[biggest].chips
        request = BetRequest(
            player=player,
            pot=self.pot,
            committed=self.bets[position],
            to_call=to_call,
            max_bet=max_bet,
        )
        bet = self.ui.request_bet(request)
        if not request.is_valid(bet):
            raise ValueError(f"UI returned invalid bet {bet} for {request}")
        if bet == 0 and to_call > 0:
            self.folds[position] = True
        return bet

    def _showdown(self, contested: bool) -> None:
        self.ui.message(f"Results of hand {self.hand_number}:")
        if contested and len(self.community) == 5:
            results = [best_hand(p.cards + self.community) for p in self.players]
            best = max(
                value for (value, _), folded in zip(results, self.folds) if not folded
            )
            winners = [
                i
                for i, (value, _) in enumerate(results)
                if not self.folds[i] and value == best
            ]
            share = self.pot // len(winners)
            for i, player in enumerate(self.players):
                value, hand = results[i]
                if self.folds[i]:
                    mark = " -"
                elif i in winners:
                    player.chips += share
                    mark = " ★"
                else:
                    mark = ""
                self.ui.message(
                    f"[{player.name}] Hand: {' '.join(hand)} ({category(value).label}). "
                    f"Chips: {player.chips}{mark}"
                )
        else:
            for i, player in enumerate(self.players):
                if not self.folds[i]:
                    player.chips += self.pot
                mark = " -" if self.folds[i] else " ★"
                self.ui.message(f"[{player.name}] Chips: {player.chips}{mark}")
        self.ui.divider(heavy=True)
