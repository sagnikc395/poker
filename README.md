# Poker Research Lab

An experiment-ready Texas Hold'em environment for human-vs-LLM play and quantitative strategy research. The engine is independent of the UI and participant policies, so the same hand can run through a GUI, an LLM, a scripted baseline, or a replay harness. Hand evaluation is powered by [pokerkit](https://github.com/sagnikc395/pokerkit).

```text
deal → build private information set → estimate equity/odds → choose action
     → validate action → record state/action/latency → replay and compare
```

## Quick start

```bash
python main.py
python main.py -n 4 --buy-in 200 --seed 42
```

For a mixed game, construct an `AgentHarness` for the LLM seat, list the human seat in `human_players`, and pass the existing GUI (or another `GameUI`) as `human_ui`. Set `observer_ui` to show director messages in that UI. `director.replay.steps` is the row-level dataset; `agent.summarize(replay)` provides action frequencies, mean latency, and error counts, while `agent.to_json(replay)` exports a replay artifact.

## Structure

| Module | Purpose |
|---|---|
| `poker/game.py` | UI-agnostic dealing, betting, and showdown engine |
| `poker/evaluation.py` | Pokerkit-backed hand evaluation |
| `poker/equity.py` | Reproducible Monte Carlo equity estimation |
| `agent/harness.py` | LLM adapter and mixed-game director |
| `agent/policies.py` | Human and scripted participant adapters |
| `agent/game_state.py` | Private-information-set and action schemas |
| `agent/replay.py` | Step-through replay records |
| `agent/analytics.py` | Research summaries and JSON export |
| `ui/app.py` | Flet human interface |
| `tests/` | Engine, equity, evaluation, and agent tests |

## Design notes

- `0` means check when no chips are required and fold when facing a bet.
- LLM outputs are parsed and clamped at the engine boundary.
- Equity simulations accept a per-decision seed for reproducible experiments; increase `equity_simulations` for evaluation and lower it for interactive use.
- Hole cards are filtered per decision: an LLM sees its own cards and public information, never another participant's private cards.
- A single hand is illustrative. For meaningful comparisons, run many independent deck seeds and retain model ID, prompt version, and bankroll rules.

## License

MIT
