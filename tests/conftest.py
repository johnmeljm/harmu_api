import pytest

from harmu_api.match import Match
from harmu_api.models import ActionType, PlayerState, ResourcePack
from harmu_api.rules import get_action_def


@pytest.fixture
def make_match():
    def _make(p1_resources: dict | None = None, p2_resources: dict | None = None) -> Match:
        return Match(
            "m-test",
            [
                PlayerState("p1", "玩家1", ResourcePack(**(p1_resources or {}))),
                PlayerState("p2", "玩家2", ResourcePack(**(p2_resources or {}))),
            ],
        )

    return _make


@pytest.fixture
def play_round(make_match):
    def _play(
        match: Match,
        p1_action: ActionType,
        p2_action: ActionType,
        p1_target: str | None = None,
        p2_target: str | None = None,
    ):
        t1 = p1_target or ("p2" if get_action_def(p1_action).needs_target else None)
        t2 = p2_target or ("p1" if get_action_def(p2_action).needs_target else None)
        assert match.submit_action("p1", p1_action, t1) is None
        return match.submit_action("p2", p2_action, t2)

    return _play


def attack_event(result) -> dict:
    return next(e for e in result.events if e["type"] == "attack")
