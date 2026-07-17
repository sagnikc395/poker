
## poker

A Texas Hold 'em game for macOS with a tkinter GUI. Hand evaluation driven by [pokerkit](https://github.com/sagnikc395/pokerkit).

### Quick Start

```
uv run main.py
```

Or with options:

```
python main.py -n 4 --buy-in 200 --seed 42
```

### Structure

| Module | Purpose |
|---|---|
| `main.py` | Entry point — runs `python main.py` |
| `poker/game.py` | UI-agnostic game engine (dealing, betting, showdown) |
| `poker/evaluation.py` | Hand evaluation via pokerkit `StandardHighHand` |
| `poker/equity.py` | Monte Carlo equity estimation against ranged opponents |
| `poker/ranges.py` | Pre-flop hand rankings (169 classes → 1326 combos) |
| `poker/cards.py` | Card primitives (ranks, suits, 52-card deck) |
| `poker/player.py` | Player dataclass |
| `poker/gui.py` | Tkinter GUI with card display, action buttons, and game log |
| `tests/` | Pytest suite (21 tests, hand evaluation + equity + game engine) |

### License

MIT
