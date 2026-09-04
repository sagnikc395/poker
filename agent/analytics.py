"""Research-friendly summaries for replay logs."""

import json
from collections import Counter
from dataclasses import asdict

from .replay import ReplayLog


def summarize(log: ReplayLog) -> dict:
    """Return compact decision statistics suitable for a backtest report."""
    by_player: dict[str, dict] = {}
    for step in log.steps:
        row = by_player.setdefault(
            step.player,
            {"decisions": 0, "actions": Counter(), "latency_ms": [], "errors": 0},
        )
        row["decisions"] += 1
        row["actions"][step.action_type] += 1
        if step.metrics and step.metrics.latency_ms is not None:
            row["latency_ms"].append(step.metrics.latency_ms)
        if step.metrics and step.metrics.error:
            row["errors"] += 1

    for row in by_player.values():
        row["actions"] = dict(row["actions"])
        latencies = row.pop("latency_ms")
        row["mean_latency_ms"] = sum(latencies) / len(latencies) if latencies else None
    return {"total_decisions": log.total_steps, "players": by_player}


def to_json(log: ReplayLog, *, indent: int = 2) -> str:
    """Serialize a replay without leaking implementation-specific objects."""
    payload = {
        "steps": [
            {
                **asdict(step),
                "metrics": asdict(step.metrics) if step.metrics else None,
            }
            for step in log.steps
        ],
        "summary": summarize(log),
    }
    return json.dumps(payload, indent=indent, default=str)
