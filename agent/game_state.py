from dataclasses import dataclass, field


@dataclass
class PlayerInfo:
    name: str
    chips: int
    folded: bool = False
    bet: int = 0


@dataclass
class Action:
    player: str
    action_type: str
    amount: int = 0
    street: str = ""


@dataclass
class GameState:
    hand_number: int = 0
    street: str = "pre-flop"
    pot: int = 0
    to_call: int = 0
    min_raise: int = 0
    max_bet: int = 0
    hero_name: str = ""
    hero_cards: list[str] = field(default_factory=list)
    hero_chips: int = 0
    hero_position: int = 0
    num_players: int = 0
    community_cards: list[str] = field(default_factory=list)
    players: list[PlayerInfo] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
