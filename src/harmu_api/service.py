"""对局服务：创建、查询、提交动作（内存存储）。"""

from __future__ import annotations

import threading
from dataclasses import replace
from itertools import count

from .match import Match
from .models import InvalidActionError, MatchNotFoundError, PlayerState, ResourcePack

DEFAULT_PLAYERS: tuple[tuple[str, str], ...] = (("p1", "玩家1"), ("p2", "玩家2"))


class MatchService:
    def __init__(self) -> None:
        self._matches: dict[str, Match] = {}
        self._lock = threading.RLock()
        self._seq = count(1)

    def create_match(
        self,
        player_specs: list[tuple[str, str]] | None = None,
        initial_resources: ResourcePack | None = None,
    ) -> Match:
        specs = list(player_specs or DEFAULT_PLAYERS)
        if len(specs) != 2:
            raise InvalidActionError("对局必须恰好有 2 名玩家")
        if len({pid for pid, _ in specs}) != 2:
            raise InvalidActionError("玩家 ID 不能重复")
        initial = initial_resources or ResourcePack()
        with self._lock:
            match_id = f"m{next(self._seq)}"
            players = [PlayerState(pid, name, replace(initial)) for pid, name in specs]
            match = Match(match_id, players)
            self._matches[match_id] = match
            return match

    def get_match(self, match_id: str) -> Match:
        with self._lock:
            match = self._matches.get(match_id)
        if match is None:
            raise MatchNotFoundError(f"对局不存在：{match_id}")
        return match

    def list_matches(self) -> list[dict]:
        with self._lock:
            return [m.view() for m in self._matches.values()]

    def submit_action(
        self,
        match_id: str,
        player_id: str,
        action_type,
        target_id: str | None = None,
    ) -> dict:
        with self._lock:
            match = self.get_match(match_id)
            result = match.submit_action(player_id, action_type, target_id)
            if result is None:
                return {"status": "waiting_opponent", "match": match.view()}
            return {
                "status": "settled",
                "round": result.to_dict(),
                "match": match.view(),
            }

    def get_match_view(self, match_id: str) -> dict:
        with self._lock:
            return self.get_match(match_id).view()

    def match_history(self, match_id: str) -> list[dict]:
        with self._lock:
            match = self.get_match(match_id)
            return [r.to_dict() for r in match.history]
