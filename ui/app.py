"""Flet GUI for Texas Hold 'em."""

import contextlib
import threading

import flet as ft

from poker.game import BetRequest
from poker.player import Player

SUIT_SYMBOL = {"s": "\u2660", "h": "\u2665", "d": "\u2666", "c": "\u2663"}
GREEN = "#1a5c2a"
LGREEN = "#2d8a4e"


def _card_widget(card: str | None) -> ft.Container:
    if card is None:
        return ft.Container(
            width=48,
            height=64,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=ft.BorderRadius.all(6),
        )
    r, s = card[0], card[1]
    fg = ft.Colors.RED if s in "hd" else ft.Colors.BLACK
    return ft.Container(
        width=48,
        height=64,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.GREY_300),
        border_radius=ft.BorderRadius.all(6),
        alignment=ft.Alignment.CENTER,
        content=ft.Text(
            f"{r}{SUIT_SYMBOL[s]}",
            color=fg,
            size=20,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        ),
    )


def _card_back() -> ft.Container:
    return ft.Container(
        width=48,
        height=64,
        bgcolor="#1a3a6b",
        border=ft.Border.all(1, ft.Colors.BLUE_900),
        border_radius=ft.BorderRadius.all(6),
        alignment=ft.Alignment.CENTER,
        content=ft.Text("\u2660", color=ft.Colors.WHITE24, size=20),
    )


class FletGUI:
    def __init__(self, page: ft.Page):
        self.page = page
        self._bet_event = threading.Event()
        self._bet_result = 0
        self._current_request: BetRequest | None = None
        self._player_widgets: list[dict] = []
        self._board_cards: list[ft.Container] = []
        self.closed = False

        page.title = "Texas Hold 'em"
        page.bgcolor = GREEN
        page.padding = 20
        page.scroll = ft.ScrollMode.AUTO

        self._build()

    def _build(self):
        title = ft.Text(
            "Texas Hold 'em",
            size=26,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        )

        self._players_row = ft.Row(
            wrap=True,
            spacing=12,
            run_spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self._board_row = ft.Row(
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        for _ in range(5):
            c = _card_widget(None)
            self._board_cards.append(c)
            self._board_row.controls.append(c)

        self._pot_text = ft.Text(
            "Pot: 0",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        )

        self._hand_text = ft.Text(
            "",
            size=16,
            color="#ffd700",
        )

        self._check_call_btn = ft.Button(
            content=ft.Text("Check"),
            on_click=self._on_check_call,
            disabled=True,
        )
        self._fold_btn = ft.Button(
            content=ft.Text("Fold"),
            on_click=self._on_fold,
            disabled=True,
        )
        self._raise_slider = ft.Slider(
            min=2,
            max=100,
            value=4,
            divisions=98,
            label="${value}",
            width=200,
        )
        self._raise_btn = ft.Button(
            content=ft.Text("Raise"),
            on_click=self._on_raise,
            disabled=True,
        )

        action_row = ft.Row(
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                self._check_call_btn,
                self._raise_slider,
                self._raise_btn,
                self._fold_btn,
            ],
        )

        self._log_col = ft.Column(spacing=1, scroll=ft.ScrollMode.ALWAYS, height=220)
        log_box = ft.Container(
            content=self._log_col,
            bgcolor="#1e1e1e",
            border_radius=ft.BorderRadius.all(6),
            padding=10,
            border=ft.Border.all(1, ft.Colors.GREY_400),
        )

        body = ft.Column(
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                title,
                ft.Divider(height=1, color=ft.Colors.WHITE24),
                self._players_row,
                ft.Text("Board:", size=13, color=ft.Colors.WHITE70),
                self._board_row,
                self._pot_text,
                self._hand_text,
                ft.Divider(height=1, color=ft.Colors.WHITE24),
                action_row,
                log_box,
            ],
        )

        self.page.add(ft.SafeArea(content=body))

    def set_players(self, players: list[Player]):
        for p in players:
            name = ft.Text(p.name, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
            chips = ft.Text(f"Chips: {p.chips}", size=13, color=ft.Colors.WHITE)
            card_w = _card_back()
            card_w2 = _card_back()
            cards_row = ft.Row(spacing=4, controls=[card_w, card_w2])
            col = ft.Column(
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[name, chips, cards_row],
            )
            container = ft.Container(
                content=col,
                padding=10,
                border_radius=ft.BorderRadius.all(8),
                bgcolor=LGREEN,
            )
            self._player_widgets.append(
                {
                    "container": container,
                    "name": name,
                    "chips": chips,
                    "cards_row": cards_row,
                    "cards": [card_w, card_w2],
                    "player": p,
                }
            )
            self._players_row.controls.append(container)

    def _log(self, text: str):
        t = ft.Text(text, size=11, font_family="monospace", selectable=True, color=ft.Colors.WHITE)
        self._log_col.controls.append(t)
        self._log_col.scroll_to(offset=-1, duration=0)

    def message(self, text: str):
        if self.closed:
            return
        if text == "Pre-flop:":
            for c in self._board_cards:
                c.content = None
                c.bgcolor = ft.Colors.WHITE
            for pw in self._player_widgets:
                pw["cards"][0].content = None
                pw["cards"][0].bgcolor = "#1a3a6b"
                pw["cards"][1].content = None
                pw["cards"][1].bgcolor = "#1a3a6b"
            self._hand_text.value = ""
        for prefix, off in [("Flop: ", 0), ("Turn: ", 3), ("River: ", 4)]:
            if text.startswith(prefix):
                cards = text[len(prefix) :].split()
                for i, card in enumerate(cards):
                    idx = off + i
                    if idx < len(self._board_cards):
                        r, s = card[0], card[1]
                        fg = ft.Colors.RED if s in "hd" else ft.Colors.BLACK
                        self._board_cards[idx].content = ft.Text(
                            f"{r}{SUIT_SYMBOL[s]}",
                            color=fg,
                            size=20,
                            weight=ft.FontWeight.BOLD,
                        )
        if text.endswith(" \u2605"):
            name_end = text.index("] ")
            rest = text[name_end + 2 :]
            colon = rest.index(":")
            self._hand_text.value = rest[:colon]
        self._log(text)
        self.page.update()

    def divider(self, heavy: bool = False):
        if self.closed:
            return
        self._log("#" * 80 if heavy else "\u00b7" * 80)
        self.page.update()

    def request_bet(self, req: BetRequest) -> int:
        if self.closed:
            raise SystemExit(0)
        self._current_request = req

        for pw in self._player_widgets:
            p = pw["player"]
            active = p is req.player
            pw["container"].bgcolor = LGREEN if active else GREEN
            pw["chips"].value = f"Chips: {p.chips}"
            for j, card_w in enumerate(pw["cards"]):
                if active and j < len(p.cards):
                    r, s = p.cards[j][0], p.cards[j][1]
                    fg = ft.Colors.RED if s in "hd" else ft.Colors.BLACK
                    card_w.content = ft.Text(
                        f"{r}{SUIT_SYMBOL[s]}",
                        color=fg,
                        size=20,
                        weight=ft.FontWeight.BOLD,
                    )
                    card_w.bgcolor = ft.Colors.WHITE
                elif not active:
                    card_w.content = None
                    card_w.bgcolor = "#1a3a6b"

        call = req.call_amount
        self._check_call_btn.content = ft.Text("Check" if call == 0 else f"Call {call}")
        self._check_call_btn.disabled = False
        self._fold_btn.disabled = call == 0

        vmax = req.max_valid_bet
        if vmax > call:
            self._raise_slider.min = call + 1
            self._raise_slider.max = vmax
            self._raise_slider.value = min(call + 2, vmax)
            self._raise_btn.disabled = False
        else:
            self._raise_btn.disabled = True

        self._pot_text.value = f"Pot: {req.pot}"
        self.page.update()

        self._bet_event.wait()
        self._bet_event.clear()
        return self._bet_result

    def _on_check_call(self, e):
        if self._current_request is not None:
            self._bet_result = self._current_request.call_amount
            self._bet_event.set()

    def _on_raise(self, e):
        if self._current_request is not None:
            amt = int(self._raise_slider.value)
            if self._current_request.is_valid(amt):
                self._bet_result = amt
                self._bet_event.set()

    def _on_fold(self, e):
        self._bet_result = 0
        self._bet_event.set()


def _play(gui: FletGUI, game):
    with contextlib.suppress(SystemExit):
        game.play()


def main():
    import argparse
    import random

    from poker.game import TexasHoldem

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

    def _start(page: ft.Page):
        players = [Player(name, args.buy_in) for name in names]
        gui = FletGUI(page)
        gui.set_players(players)
        game = TexasHoldem(
            players,
            ui=gui,
            big_blind=args.big_blind,
            rng=random.Random(args.seed) if args.seed else None,
        )
        threading.Thread(target=_play, args=(gui, game), daemon=True).start()

    ft.run(_start)


if __name__ == "__main__":
    main()
