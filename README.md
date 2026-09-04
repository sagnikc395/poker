# Poker

A no-limit Texas Hold 'em engine with an LLM agent harness, built for human-vs-LLM play and
quantitative strategy research.

The engine knows nothing about *who* is acting. It asks "here is a legal bet request, what do
you do?" and any participant — a person clicking in the GUI, an LLM agent, or a scripted
baseline — answers with a single integer. That one seam is what lets the same hand run through
a GUI, an agent-vs-agent match, or a replay harness without changing the rules code.

Hand evaluation is powered by [pokerkit](https://github.com/sagnikc395/pokerkit).

## Install

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

## Play (GUI)

```bash
uv run python main.py                              # 2 players, 100 chips each
uv run python main.py -n 4 --buy-in 200 --seed 42  # 4 players, reproducible deck
```

| Flag | Default | Meaning |
|---|---|---|
| `-n`, `--players` | `2` | Number of seats (2–9) |
| `-b`, `--buy-in` | `100` | Starting chips per player |
| `--big-blind` | `2` | Big blind size (small blind is half) |
| `--seed` | *(random)* | Seed the deck for a reproducible session |
| `--names` | `Player 1…N` | Custom player names |

The game runs hands until one player holds every chip.

## Play with LLM agents

`GameDirector` implements the same `GameUI` protocol the GUI does, so you hand it to the engine
in place of a UI. It routes each bet request to the right seat and records every decision.

```python
from agent import GameDirector, create_harnesses
from poker import Player, TexasHoldem
from smolagents import InferenceClientModel

names = ["Alice", "Bob"]
model = InferenceClientModel(model_id="Qwen/Qwen2.5-Coder-7B-Instruct")
agents = create_harnesses(names, model, style_map={"Alice": "TAG", "Bob": "LAG"})

director = GameDirector(agents, names, buy_in=100, research_seed=42)
winner = TexasHoldem([Player(n, 100) for n in names], ui=director).play()
```

Available play styles (`style_map`): `TAG`, `LAG`, `CallingStation`, `Random`, `Nit`.
Each agent gets tools for hand rank, Monte Carlo equity, pot odds, position, pre-flop hand
class, and game context.

### Mixed human + agent tables

Seat a person at an otherwise agent-filled table by naming their seat and passing a UI for it:

```python
director = GameDirector(
    agents,                       # one harness per LLM seat
    player_names=["You", "Bob"],
    human_players=["You"],        # must be a subset of player_names
    human_ui=gui,                 # any GameUI — e.g. the Flet app
    observer_ui=gui,              # optional: mirror director messages into that UI
    research_seed=42,
    equity_simulations=1024,
)
```

## Research output

Every decision becomes a `ReplayStep`: the observation the actor saw, the action it chose, and
diagnostics (equity, pot odds, equity edge, latency, raw model output, errors).

```python
from agent import summarize, to_json

report = summarize(director.replay)          # per-player action counts, mean latency, errors
with open("replay.json", "w") as f:
    f.write(to_json(director.replay))        # full row-level artifact
```

`director.replay.steps` is the row-level dataset — treat each row as one
observation/action sample in a partially observed sequential decision problem.

## How one decision flows

```text
deal → build private information set → estimate equity/odds → choose action
     → validate action → record state/action/latency → replay and compare
```

1. The engine creates a legal `BetRequest` (pot, amount to call, maximum raise).
2. `GameDirector` builds a seat-specific `GameState` — public cards, stacks, bets, recent
   actions, and **only that actor's** hole cards.
3. An LLM seat may call its tools; a human seat is routed to `human_ui`.
4. The answer is parsed into one integer and validated against the request.
5. A `ReplayStep` records the observation, action, and diagnostics.

## Betting convention

A bet is a single integer:

- `0` — check when nothing is owed, fold when facing a bet.
- *call amount* — call.
- anything above the call amount, up to `max_valid_bet` — raise.

LLM output is parsed and clamped at the engine boundary, so a malformed or illegal response
degrades to a fold rather than corrupting the hand. An agent that raises an exception folds and
the error is recorded in that step's metrics.

## Project layout

| Module | Purpose |
|---|---|
| `poker/game.py` | UI-agnostic dealing, betting, and showdown engine |
| `poker/evaluation.py` | Pokerkit-backed hand evaluation |
| `poker/equity.py` | Reproducible Monte Carlo equity estimation |
| `poker/cards.py`, `poker/ranges.py`, `poker/player.py` | Deck, pre-flop rankings, player state |
| `agent/harness.py` | LLM adapter (`AgentHarness`) and mixed-game `GameDirector` |
| `agent/policies.py` | Human and scripted participant adapters |
| `agent/game_state.py` | Private-information-set and action schemas |
| `agent/tools.py`, `agent/prompts.py` | Agent tools and per-style system prompts |
| `agent/replay.py` | Step-through replay records |
| `agent/analytics.py` | Research summaries and JSON export |
| `ui/app.py` | Flet human interface |
| `tests/` | Engine, equity, evaluation, and agent tests |

## Development

```bash
uv run pytest        # engine, equity, evaluation, and agent tests
uv run ruff check .
uv run ruff format .
```

Agent tests use duck-typed fake harnesses, so the suite runs without any model calls.

## Notes on running experiments

- Equity simulations take a per-decision seed for reproducibility. Raise `equity_simulations`
  for evaluation runs; lower it for interactive play.
- Hole cards are filtered per decision — an agent never sees another participant's private cards.
- A single hand is illustrative, not evidence. For real comparisons run many independent deck
  seeds and record the model ID, prompt version, and bankroll rules alongside the replay.

Further reading: [`docs/RESEARCH.md`](docs/RESEARCH.md).

## License

MIT
