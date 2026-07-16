"""Tkinter GUI for Texas Hold 'em."""

import contextlib
import tkinter as tk

SUIT = {"s": "\u2660", "h": "\u2665", "d": "\u2666", "c": "\u2663"}
COLOR = {"s": "black", "h": "red", "d": "red", "c": "black"}
GREEN = "#1a5c2a"
LGREEN = "#2d8a4e"


def _card(card, **kw):
    if card is None:
        return tk.Label(
            text="  ", width=3, bg="white", relief=tk.RAISED, font=("Courier", 16, "bold"), **kw
        )
    r, s = card[0], card[1]
    return tk.Label(
        text=f"{r}{SUIT[s]}",
        width=3,
        bg="white",
        fg=COLOR[s],
        relief=tk.RAISED,
        font=("Courier", 16, "bold"),
        **kw,
    )


class PokerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Texas Hold 'em")
        self.root.configure(bg=GREEN)
        self.bet_result = None
        self.req = None
        self.closed = False
        self.pw = []
        self._build()

    def _build(self):
        tk.Label(
            self.root, text="Texas Hold 'em", bg=GREEN, fg="white", font=("Arial", 18, "bold")
        ).pack(pady=(10, 0))
        self.pa = tk.Frame(self.root, bg=GREEN)
        self.pa.pack(fill=tk.X, padx=10, pady=5)

        cf = tk.Frame(self.root, bg=GREEN)
        cf.pack(pady=5)
        tk.Label(cf, text="Board:", bg=GREEN, fg="white", font=("Arial", 12)).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        self.cl = []
        for _ in range(5):
            lbl = _card(None, master=cf)
            lbl.pack(side=tk.LEFT, padx=2)
            self.cl.append(lbl)

        self.pot = tk.Label(
            self.root, text="Pot: 0", bg=GREEN, fg="white", font=("Arial", 14, "bold")
        )
        self.pot.pack(pady=3)

        self.hand_label = tk.Label(
            self.root, text="", bg=GREEN, fg="#ffd700", font=("Arial", 14, "bold")
        )
        self.hand_label.pack(pady=2)

        af = tk.Frame(self.root, bg=GREEN)
        af.pack(pady=5)
        self.cc = tk.Button(af, text="Check", command=self._cc, font=("Arial", 11), padx=15, pady=5)
        self.cc.pack(side=tk.LEFT, padx=3)
        self.rv = tk.IntVar()
        self.rs = tk.Scale(
            af,
            from_=2,
            to=100,
            orient=tk.HORIZONTAL,
            length=140,
            variable=self.rv,
            bg=GREEN,
            fg="white",
            highlightbackground=GREEN,
            troughcolor=LGREEN,
        )
        self.rs.pack(side=tk.LEFT, padx=3)
        self.rb = tk.Button(
            af, text="Raise", command=self._raise_bet, font=("Arial", 11), padx=15, pady=5
        )
        self.rb.pack(side=tk.LEFT, padx=3)
        self.fb = tk.Button(
            af, text="Fold", command=self._fold, font=("Arial", 11), padx=15, pady=5
        )
        self.fb.pack(side=tk.LEFT, padx=3)

        lf = tk.Frame(self.root)
        lf.pack(padx=10, pady=(5, 10), fill=tk.BOTH, expand=True)
        self.log = tk.Text(
            lf,
            height=12,
            width=80,
            font=("Courier", 9),
            state=tk.DISABLED,
            bg="#f5f5dc",
            wrap=tk.WORD,
        )
        sb = tk.Scrollbar(lf, command=self.log.yview)
        self.log.config(yscrollcommand=sb.set)
        self.log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def set_players(self, players):
        for p in players:
            f = tk.Frame(self.pa, bg=GREEN)
            f.pack(fill=tk.X, pady=1)
            n = tk.Label(
                f, text=p.name, bg=GREEN, fg="white", font=("Arial", 11, "bold"), anchor=tk.W
            )
            n.pack(side=tk.LEFT, padx=5)
            c = tk.Label(f, text=f"Chips: {p.chips}", bg=GREEN, fg="white", font=("Arial", 11))
            c.pack(side=tk.LEFT, padx=10)
            ls = []
            for _ in range(2):
                lbl = _card(None, master=f)
                lbl.pack(side=tk.LEFT, padx=2)
                ls.append(lbl)
            self.pw.append({"f": f, "n": n, "c": c, "ls": ls, "p": p})

    def _close(self):
        self.closed = True
        if self.bet_result is not None:
            self.bet_result.set(-1)

    def message(self, text):
        if self.closed:
            return
        if text == "Pre-flop:":
            for lbl in self.cl:
                lbl.config(text="  ", fg="black")
            for w in self.pw:
                for lbl in w["ls"]:
                    lbl.config(text="  ", fg="black")
            self.hand_label.config(text="")
        for prefix, off in [("Flop: ", 0), ("Turn: ", 3), ("River: ", 4)]:
            if text.startswith(prefix):
                cards = text[len(prefix) :].split()
                for i, card in enumerate(cards):
                    idx = off + i
                    if idx < len(self.cl):
                        r, s = card[0], card[1]
                        self.cl[idx].config(text=f"{r}{SUIT[s]}", fg=COLOR[s])
        if text.endswith(" \u2605"):
            name_end = text.index("] ")
            rest = text[name_end + 2 :]
            colon = rest.index(":")
            hand_type = rest[:colon]
            self.hand_label.config(text=hand_type)
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def divider(self, heavy=False):
        if self.closed:
            return
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, ("#" if heavy else "\u00b7") * 80 + "\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)

    def request_bet(self, req):
        if self.closed:
            raise SystemExit(0)
        self.req = req
        self.bet_result = tk.IntVar()
        for w in self.pw:
            p = w["p"]
            active = p is req.player
            w["f"].config(relief=tk.RAISED if active else tk.FLAT, bg=LGREEN if active else GREEN)
            for lbl in (w["n"], w["c"]):
                lbl.config(bg=LGREEN if active else GREEN)
            w["c"].config(text=f"Chips: {p.chips}")
            for j, lbl in enumerate(w["ls"]):
                if active and j < len(p.cards):
                    r, s = p.cards[j][0], p.cards[j][1]
                    lbl.config(text=f"{r}{SUIT[s]}", fg=COLOR[s])
                elif not active:
                    lbl.config(text="  ", fg="black")
        call = req.call_amount
        vmax = req.max_valid_bet
        self.cc.config(text="Check" if call == 0 else f"Call {call}", state=tk.NORMAL)
        self.fb.config(state=tk.DISABLED if call == 0 else tk.NORMAL)
        if vmax > call:
            self.rs.config(from_=call + 1, to=vmax)
            self.rv.set(min(call + 2, vmax))
            self.rb.config(state=tk.NORMAL)
        else:
            self.rb.config(state=tk.DISABLED)
        self.pot.config(text=f"Pot: {req.pot}")
        self.root.wait_variable(self.bet_result)
        bet = self.bet_result.get()
        if bet == -1:
            raise SystemExit(0)
        return bet

    def _cc(self):
        if self.req is not None:
            self.bet_result.set(self.req.call_amount)

    def _raise_bet(self):
        if self.req is not None:
            amt = self.rv.get()
            if self.req.is_valid(amt):
                self.bet_result.set(amt)

    def _fold(self):
        self.bet_result.set(0)


def main():
    import argparse
    import random

    from .game import TexasHoldem
    from .player import Player

    parser = argparse.ArgumentParser(description="Texas Hold 'em")
    parser.add_argument("-n", "--players", type=int, default=2, help="number of players (2-9)")
    parser.add_argument("-b", "--buy-in", type=int, default=100, help="starting chips per player")
    parser.add_argument("--big-blind", type=int, default=2)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--names", nargs="+", help="player names")
    args = parser.parse_args()
    n = args.players
    if not 1 < n < 10:
        parser.error("players must be between 2 and 9")
    names = args.names or [f"Player {i + 1}" for i in range(n)]
    if len(names) != n:
        parser.error("number of --names must match --players")
    players = [Player(name, args.buy_in) for name in names]
    gui = PokerGUI()
    gui.set_players(players)
    game = TexasHoldem(players, ui=gui, big_blind=args.big_blind, rng=random.Random(args.seed))
    gui.root.after(100, lambda: _play(gui, game))
    gui.root.mainloop()


def _play(gui, game):
    with contextlib.suppress(SystemExit):
        game.play()
