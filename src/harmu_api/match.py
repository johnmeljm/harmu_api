"""对局状态机：回合推进、动作提交与结算触发。"""

from __future__ import annotations

from .models import (
    Action,
    ActionType,
    ConflictError,
    InvalidActionError,
    MatchStatus,
    PlayerState,
    RoundResult,
)
from .rules import ACTION_NAMES, check_preconditions, get_action_def
from .settlement import settle_round


class Match:
    def __init__(self, match_id: str, players: list[PlayerState]):
        if len(players) != 2:
            raise ValueError("当前规则仅支持 2 名玩家")
        self.match_id = match_id
        self.players: dict[str, PlayerState] = {p.player_id: p for p in players}
        self.round_number = 1
        self.status = MatchStatus.IN_PROGRESS
        self.winner: str | None = None
        self.pending: dict[str, Action] = {}
        self.history: list[RoundResult] = []

    def submit_action(
        self,
        player_id: str,
        action_type: ActionType,
        target_id: str | None = None,
    ) -> RoundResult | None:
        """提交本回合动作；双方都提交后自动结算并返回结果，否则返回 None。"""
        if self.status is MatchStatus.ENDED:
            raise ConflictError("对局已结束，无法提交动作")
        if player_id not in self.players:
            raise InvalidActionError(f"玩家不存在：{player_id}")
        player = self.players[player_id]
        if not player.alive:
            raise ConflictError(f"玩家 {player_id} 已死亡，无法行动")
        if player_id in self.pending:
            raise ConflictError(f"玩家 {player_id} 本回合已提交过动作")

        action_def = get_action_def(action_type)
        if action_def.needs_target:
            if target_id is None:
                raise InvalidActionError(
                    f"攻击类动作「{ACTION_NAMES[action_type]}」必须指定目标玩家"
                )
            if target_id == player_id:
                raise InvalidActionError("不能以自己为攻击目标")
            if target_id not in self.players:
                raise InvalidActionError(f"目标玩家不存在：{target_id}")
        elif target_id is not None:
            raise InvalidActionError(
                f"动作「{ACTION_NAMES[action_type]}」不支持指定目标"
            )

        check_preconditions(player.resources, action_type)
        self.pending[player_id] = Action(action_type, target_id)
        if len(self.pending) == len(self.players):
            return self._settle()
        return None

    def _settle(self) -> RoundResult:
        result = settle_round(self.round_number, self.players, dict(self.pending))
        self.pending.clear()
        self.history.append(result)
        self.status = result.match_status
        self.winner = result.winner
        if result.match_status is MatchStatus.IN_PROGRESS:
            self.round_number += 1
        return result

    def view(self) -> dict:
        return {
            "match_id": self.match_id,
            "round_number": self.round_number,
            "status": self.status.value,
            "winner": self.winner,
            "players": {
                pid: {
                    "player_id": pid,
                    "name": p.name,
                    "alive": p.alive,
                    "resources": p.resources.to_dict(),
                }
                for pid, p in self.players.items()
            },
            "submitted": list(self.pending.keys()),
        }
