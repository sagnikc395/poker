# Human-vs-LLM research guide

## What happens during a decision

1. The engine creates a legal `BetRequest` with the pot, call amount, and maximum raise.
2. `GameDirector` builds a player-specific `GameState`: public cards, stack/bet information, recent actions, and only the actor's hole cards.
3. An LLM harness can call hand rank, pot odds, position, and Monte Carlo equity tools. A human seat is routed to the configured UI.
4. The result becomes one integer and is checked against the legal request.
5. A `ReplayStep` stores the observation, action, and diagnostics.

## Quantitative framing

This is a partially observed sequential decision problem. Each replay row can be treated as an observation/action sample. Useful features include street, position, stack-to-pot ratio, call amount, pot odds, equity estimate, action history, and selected action. Compare policies using fixed deck and equity seeds, then report action frequencies, latency, error rate, chip change, and performance over many hands.

Model latency and raw output are diagnostics, not information available to the player. Human steps therefore have no model metrics rather than silently imputing them.

```python
from agent import summarize, to_json

report = summarize(director.replay)
with open("replay.json", "w") as f:
    f.write(to_json(director.replay))
```
