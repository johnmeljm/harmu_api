"""回合结算引擎。

结算顺序：
1. 生产类动作：只改变自身资源；
2. 防御类动作：普通盾无消耗，反弹盾数量-1；
3. 攻击类动作：先扣除武器消耗，再依据目标本回合的防御动作结算伤害；
4. 死亡判定：生命值 <= 0 即死亡；
5. 对局结果：仅一人存活判胜，双方同时死亡判平局。
"""

from __future__ import annotations

from enum import Enum

from .models import (
    Action,
    ActionCategory,
    ActionType,
    MatchStatus,
    PlayerState,
    RESOURCE_NAMES,
    RoundResult,
)
from .rules import ACTION_NAMES, apply_action_effects, get_action_def

WEAPON_NAMES: dict[ActionType, str] = {
    ActionType.USE_KNIFE: "刀",
    ActionType.USE_DOUBLE_KNIFE: "双刀",
    ActionType.USE_BOMB: "炸弹",
}


class AttackOutcome(str, Enum):
    HIT = "hit"
    BLOCKED = "blocked"
    PIERCED = "pierced"
    REFLECTED = "reflected"


def resolve_attack(weapon: ActionType, target_defense: ActionType | None) -> AttackOutcome:
    """攻击与防御交互表：
    - 刀：无防御→命中；普通盾→被挡下（回合结束）；反弹盾→反弹，攻击者受伤
    - 双刀：无防御或普通盾→命中（穿透普通盾）；反弹盾→反弹，攻击者受伤
    - 炸弹：无防御或普通盾→命中（穿透普通盾）；反弹盾→被挡下，双方无伤
    """
    if target_defense is None:
        return AttackOutcome.HIT
    if target_defense is ActionType.USE_NORMAL_SHIELD:
        if weapon is ActionType.USE_KNIFE:
            return AttackOutcome.BLOCKED
        return AttackOutcome.PIERCED
    if weapon is ActionType.USE_BOMB:
        return AttackOutcome.BLOCKED
    return AttackOutcome.REFLECTED


def _defense_type_of(action: Action | None) -> ActionType | None:
    if action is not None and get_action_def(action.type).category is ActionCategory.DEFENSE:
        return action.type
    return None


def _fmt_changes(changes: dict[str, int]) -> str:
    return "，".join(f"{RESOURCE_NAMES[res]}{delta:+d}" for res, delta in changes.items())


def _outcome_detail(
    pid: str,
    target_id: str,
    weapon: ActionType,
    outcome: AttackOutcome,
    defense: ActionType | None,
) -> str:
    weapon_name = WEAPON_NAMES[weapon]
    if outcome is AttackOutcome.HIT:
        return f"{pid} 对 {target_id} 使用{weapon_name}，{target_id} 生命值-1"
    if outcome is AttackOutcome.PIERCED:
        return f"{pid} 对 {target_id} 使用{weapon_name}，普通盾无法抵挡，{target_id} 生命值-1"
    if outcome is AttackOutcome.BLOCKED:
        if defense is ActionType.USE_NORMAL_SHIELD:
            return (
                f"{target_id} 使用普通盾挡下了 {pid} 的{weapon_name}，"
                f"双方生命值不变，回合结束"
            )
        return f"{target_id} 使用反弹盾挡下了 {pid} 的{weapon_name}，双方生命值不变"
    return (
        f"{target_id} 使用反弹盾反弹了 {pid} 的{weapon_name}，"
        f"{pid} 生命值-1，{target_id} 生命值不变"
    )


def settle_round(
    round_number: int,
    players: dict[str, PlayerState],
    actions: dict[str, Action],
) -> RoundResult:
    events: list[dict] = []

    # 1) 生产类动作
    for pid, player in players.items():
        action = actions.get(pid)
        if action is None:
            continue
        if get_action_def(action.type).category is not ActionCategory.PRODUCTION:
            continue
        changes = apply_action_effects(player.resources, action.type)
        events.append({
            "type": "production",
            "player": pid,
            "action": action.type.value,
            "changes": changes,
            "detail": f"{pid} 执行「{ACTION_NAMES[action.type]}」：{_fmt_changes(changes)}",
        })

    # 2) 防御类动作
    for pid, player in players.items():
        action = actions.get(pid)
        if action is None:
            continue
        if get_action_def(action.type).category is not ActionCategory.DEFENSE:
            continue
        changes = apply_action_effects(player.resources, action.type)
        if action.type is ActionType.USE_NORMAL_SHIELD:
            detail = f"{pid} 使用普通盾（数量不限，无消耗）"
        else:
            detail = f"{pid} 使用反弹盾：反弹盾数量-1"
        events.append({
            "type": "defense",
            "player": pid,
            "action": action.type.value,
            "changes": changes,
            "detail": detail,
        })

    # 3) 攻击类动作：扣除武器 + 依据目标防御结算伤害
    for pid, player in players.items():
        action = actions.get(pid)
        if action is None:
            continue
        if get_action_def(action.type).category is not ActionCategory.ATTACK:
            continue
        target = players[action.target_id]
        changes = apply_action_effects(player.resources, action.type)
        defense = _defense_type_of(actions.get(action.target_id))
        outcome = resolve_attack(action.type, defense)
        damage_to = None
        if outcome in (AttackOutcome.HIT, AttackOutcome.PIERCED):
            target.resources.hp -= 1
            damage_to = target.player_id
        elif outcome is AttackOutcome.REFLECTED:
            player.resources.hp -= 1
            damage_to = pid
        events.append({
            "type": "attack",
            "player": pid,
            "target": action.target_id,
            "action": action.type.value,
            "outcome": outcome.value,
            "damage_to": damage_to,
            "changes": changes,
            "detail": _outcome_detail(pid, action.target_id, action.type, outcome, defense),
        })

    # 4) 死亡判定
    deaths: list[str] = []
    for pid, player in players.items():
        if player.alive and player.resources.hp <= 0:
            player.alive = False
            deaths.append(pid)
            events.append({
                "type": "death",
                "player": pid,
                "detail": f"{pid} 受到伤害，生命值降为 0，死亡",
            })

    # 5) 对局结果
    survivors = [pid for pid, p in players.items() if p.alive]
    if not deaths:
        match_status, winner = MatchStatus.IN_PROGRESS, None
    elif not survivors:
        match_status, winner = MatchStatus.ENDED, "draw"
        events.append({
            "type": "match_end",
            "winner": winner,
            "detail": "双方同时死亡，平局",
        })
    else:
        match_status, winner = MatchStatus.ENDED, survivors[0]
        events.append({
            "type": "match_end",
            "winner": winner,
            "detail": f"对局结束，{winner} 获胜",
        })

    return RoundResult(
        round_number=round_number,
        actions={
            pid: {"action": action.type.value, "target_id": action.target_id}
            for pid, action in actions.items()
        },
        events=events,
        players={
            pid: {"alive": p.alive, "resources": p.resources.to_dict()}
            for pid, p in players.items()
        },
        deaths=deaths,
        match_status=match_status,
        winner=winner,
    )
