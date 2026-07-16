"""Terminal front end for the game engine."""

from __future__ import annotations

import argparse
import random

from .game import BetRequest, TexasHoldem
from .player import Player

COLORS = (
    "\033[91m", "\033[92m", "\033[93m", "\033[94m", "\033[95m",
    "\033[96m", "\033[31m", "\033[32m", "\033[34m",
)
DARKGRAY = "\033[90m"
RESET = "\033[0m"


class TerminalUI:
    def message(self, text: str) -> None:
        print(text)

    def divider(self, heavy: bool = False) -> None:
        print(DARKGRAY + ("#" if heavy else "·") * 80 + RESET)

    def request_bet(self, request: BetRequest) -> int:
        call = request.call_amount
        call_label = "all-in" if request.to_call >= request.player.chips else str(request.to_call)
        prompt = (
            f"[{request.player.name}] Pot: {request.pot}. "
            f"Chips: {request.committed}/{request.player.chips}. "
            f"Enter bet ({call_label} to call, 0 to {'fold' if request.to_call else 'check'}): "
        )
        while True:
            try:
                raw = input(prompt)
            except (KeyboardInterrupt, EOFError):
                print("\nGood bye")
                raise SystemExit(0) from None
            try:
                bet = int(raw)
            except ValueError:
                print(f"{DARKGRAY}  not a number{RESET}")
                continue
            if request.is_valid(bet):
                return bet
            if request.max_valid_bet <= call:
                print(f"{DARKGRAY}  enter 0 to fold or {call} to call{RESET}")
            else:
                print(
                    f"{DARKGRAY}  enter 0, {call} to call, "
                    f"or raise up to {request.max_valid_bet}{RESET}"
                )


def _ask_n_players() -> int:
    while True:
        try:
            n = int(input("Enter number of players (2-9): "))
        except (KeyboardInterrupt, EOFError):
            print("\nGood bye")
            raise SystemExit(0) from None
        except ValueError:
            continue
        if 1 < n < 10:
            return n


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="poker", description="Hot-seat no-limit Texas Hold 'em in the terminal."
    )
    parser.add_argument("-n", "--players", type=int, help="number of players (2-9)")
    parser.add_argument("-b", "--buy-in", type=int, default=100, help="starting chips (default: 100)")
    parser.add_argument("--big-blind", type=int, default=2, help="big blind size (default: 2)")
    parser.add_argument("--seed", type=int, help="random seed for reproducible deals")
    parser.add_argument(
        "--names", nargs="+", metavar="NAME", help="player names (must match --players)"
    )
    args = parser.parse_args()

    n_players = args.players if args.players is not None else _ask_n_players()
    if not 1 < n_players < 10:
        parser.error("--players must be between 2 and 9")

    names = args.names or [f"Player {i + 1}" for i in range(n_players)]
    if len(names) != n_players:
        parser.error("--names must provide exactly one name per player")

    players = [
        Player(name=f"{COLORS[i % len(COLORS)]}{name}{RESET}", chips=args.buy_in)
        for i, name in enumerate(names)
    ]
    game = TexasHoldem(
        players, ui=TerminalUI(), big_blind=args.big_blind, rng=random.Random(args.seed)
    )
    game.play()


if __name__ == "__main__":
    main()
