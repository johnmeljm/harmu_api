"""核心数据模型：动作、资源、玩家、回合结果与规则异常。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ActionCategory(str, Enum):
    PRODUCTION = "production"
    ATTACK = "attack"
    DEFENSE = "defense"


class ActionType(str, Enum):
    EARN_MONEY = "earn_money"
    BUY_KNIFE = "buy_knife"
    BUY_GUNPOWDER = "buy_gunpowder"
    CRAFT_BOMB = "craft_bomb"
    CRAFT_REFLECT_SHIELD = "craft_reflect_shield"
    USE_KNIFE = "use_knife"
    USE_DOUBLE_KNIFE = "use_double_knife"
    USE_BOMB = "use_bomb"
    USE_NORMAL_SHIELD = "use_normal_shield"
    USE_REFLECT_SHIELD = "use_reflect_shield"


RESOURCE_NAMES: dict[str, str] = {
    "hp": "生命值",
    "money": "钱",
    "knives": "刀",
    "gunpowder": "火药",
    "bombs": "炸弹",
    "reflect_shields": "反弹盾",
}


@dataclass
class ResourcePack:
    hp: int = 1
    money: int = 0
    knives: int = 0
    gunpowder: int = 0
    bombs: int = 0
    reflect_shields: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "hp": self.hp,
            "money": self.money,
            "knives": self.knives,
            "gunpowder": self.gunpowder,
            "bombs": self.bombs,
            "reflect_shields": self.reflect_shields,
        }


@dataclass(frozen=True)
class Action:
    type: ActionType
    target_id: str | None = None


@dataclass
class PlayerState:
    player_id: str
    name: str
    resources: ResourcePack = field(default_factory=ResourcePack)
    alive: bool = True


class MatchStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    ENDED = "ended"


@dataclass
class RoundResult:
    round_number: int
    actions: dict[str, dict]
    events: list[dict]
    players: dict[str, dict]
    deaths: list[str]
    match_status: MatchStatus
    winner: str | None

    def to_dict(self) -> dict:
        return {
            "round_number": self.round_number,
            "actions": self.actions,
            "events": self.events,
            "players": self.players,
            "deaths": self.deaths,
            "match_status": self.match_status.value,
            "winner": self.winner,
        }


class GameError(Exception):
    status_code = 400


class MatchNotFoundError(GameError):
    status_code = 404


class InvalidActionError(GameError):
    status_code = 400


class ConflictError(GameError):
    status_code = 409


class PreconditionFailedError(GameError):
    status_code = 422
