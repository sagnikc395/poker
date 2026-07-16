"""Player state."""

from dataclasses import dataclass, field


@dataclass
class Player:
    name: str
    chips: int
    cards: list[str] = field(default_factory=list)
