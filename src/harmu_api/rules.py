"""动作定义表：分类、前置条件、消耗与产出。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .models import (
    ActionCategory,
    ActionType,
    InvalidActionError,
    PreconditionFailedError,
    RESOURCE_NAMES,
    ResourcePack,
)

ACTION_NAMES: dict[ActionType, str] = {
    ActionType.EARN_MONEY: "赚钱",
    ActionType.BUY_KNIFE: "买刀",
    ActionType.BUY_GUNPOWDER: "买火药",
    ActionType.CRAFT_BOMB: "制作炸弹",
    ActionType.CRAFT_REFLECT_SHIELD: "制作反弹盾",
    ActionType.USE_KNIFE: "使用刀",
    ActionType.USE_DOUBLE_KNIFE: "使用双刀",
    ActionType.USE_BOMB: "使用炸弹",
    ActionType.USE_NORMAL_SHIELD: "使用普通盾",
    ActionType.USE_REFLECT_SHIELD: "使用反弹盾",
}


@dataclass(frozen=True)
class ActionDef:
    action: ActionType
    category: ActionCategory
    requirement: Mapping[str, int]
    cost: Mapping[str, int]
    gain: Mapping[str, int]

    @property
    def needs_target(self) -> bool:
        return self.category is ActionCategory.ATTACK


ACTION_DEFS: dict[ActionType, ActionDef] = {
    ActionType.EARN_MONEY: ActionDef(
        ActionType.EARN_MONEY, ActionCategory.PRODUCTION, {}, {}, {"money": 1}
    ),
    ActionType.BUY_KNIFE: ActionDef(
        ActionType.BUY_KNIFE, ActionCategory.PRODUCTION, {"money": 1}, {"money": 1}, {"knives": 1}
    ),
    ActionType.BUY_GUNPOWDER: ActionDef(
        ActionType.BUY_GUNPOWDER, ActionCategory.PRODUCTION, {"money": 2}, {"money": 2}, {"gunpowder": 1}
    ),
    ActionType.CRAFT_BOMB: ActionDef(
        ActionType.CRAFT_BOMB, ActionCategory.PRODUCTION, {"gunpowder": 1}, {"gunpowder": 1}, {"bombs": 1}
    ),
    ActionType.CRAFT_REFLECT_SHIELD: ActionDef(
        ActionType.CRAFT_REFLECT_SHIELD, ActionCategory.PRODUCTION, {}, {}, {"reflect_shields": 1}
    ),
    ActionType.USE_KNIFE: ActionDef(
        ActionType.USE_KNIFE, ActionCategory.ATTACK, {"knives": 1}, {"knives": 1}, {}
    ),
    ActionType.USE_DOUBLE_KNIFE: ActionDef(
        ActionType.USE_DOUBLE_KNIFE, ActionCategory.ATTACK, {"knives": 2}, {"knives": 2}, {}
    ),
    ActionType.USE_BOMB: ActionDef(
        ActionType.USE_BOMB, ActionCategory.ATTACK, {"bombs": 1}, {"bombs": 1}, {}
    ),
    ActionType.USE_NORMAL_SHIELD: ActionDef(
        ActionType.USE_NORMAL_SHIELD, ActionCategory.DEFENSE, {}, {}, {}
    ),
    ActionType.USE_REFLECT_SHIELD: ActionDef(
        ActionType.USE_REFLECT_SHIELD, ActionCategory.DEFENSE, {"reflect_shields": 1}, {"reflect_shields": 1}, {}
    ),
}


def get_action_def(action_type: ActionType) -> ActionDef:
    try:
        return ACTION_DEFS[action_type]
    except KeyError:
        raise InvalidActionError(f"未知动作：{action_type}") from None


def check_preconditions(resources: ResourcePack, action_type: ActionType) -> None:
    action_def = get_action_def(action_type)
    missing = [
        (res, need, getattr(resources, res))
        for res, need in action_def.requirement.items()
        if getattr(resources, res) < need
    ]
    if missing:
        parts = "、".join(
            f"{RESOURCE_NAMES[res]}>={need}（当前 {cur}）" for res, need, cur in missing
        )
        raise PreconditionFailedError(
            f"动作「{ACTION_NAMES[action_type]}」前置条件不满足：需要 {parts}"
        )


def apply_action_effects(resources: ResourcePack, action_type: ActionType) -> dict[str, int]:
    """扣除消耗并增加产出，返回资源变化量（不涉及生命值）。"""
    check_preconditions(resources, action_type)
    action_def = ACTION_DEFS[action_type]
    changes: dict[str, int] = {}
    for res, amount in action_def.cost.items():
        setattr(resources, res, getattr(resources, res) - amount)
        changes[res] = changes.get(res, 0) - amount
    for res, amount in action_def.gain.items():
        setattr(resources, res, getattr(resources, res) + amount)
        changes[res] = changes.get(res, 0) + amount
    return changes
