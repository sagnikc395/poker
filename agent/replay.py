from dataclasses import dataclass, field

from .game_state import GameState


@dataclass
class ReplayStep:
    hand_number: int
    street: str
    player: str
    action_type: str
    amount: int
    state: GameState | None = None


@dataclass
class ReplayLog:
    steps: list[ReplayStep] = field(default_factory=list)
    _index: int = -1

    def record(self, step: ReplayStep) -> None:
        self.steps.append(step)

    def reset(self) -> None:
        self._index = -1

    def step_forward(self) -> ReplayStep | None:
        if self._index + 1 >= len(self.steps):
            return None
        self._index += 1
        return self.steps[self._index]

    def step_back(self) -> ReplayStep | None:
        if self._index <= 0:
            return None
        self._index -= 1
        return self.steps[self._index]

    def current(self) -> ReplayStep | None:
        if 0 <= self._index < len(self.steps):
            return self.steps[self._index]
        return None

    def summary(self) -> list[str]:
        lines = []
        for s in self.steps:
            amt = f" {s.amount}" if s.amount else ""
            lines.append(f"#{s.hand_number} {s.street:>9} | {s.player}: {s.action_type}{amt}")
        return lines

    @property
    def total_steps(self) -> int:
        return len(self.steps)
