import pytest

from harmu_api.models import ActionType, ConflictError, InvalidActionError, MatchStatus
from harmu_api.rules import ACTION_DEFS, get_action_def


class TestSubmissionValidation:
    def test_first_submit_waits_for_opponent(self, make_match):
        m = make_match()
        assert m.submit_action("p1", ActionType.EARN_MONEY) is None
        assert m.view()["submitted"] == ["p1"]
        assert m.round_number == 1

    def test_double_submit_rejected(self, make_match):
        m = make_match()
        m.submit_action("p1", ActionType.EARN_MONEY)
        with pytest.raises(ConflictError, match="已提交"):
            m.submit_action("p1", ActionType.EARN_MONEY)

    def test_unknown_player_rejected(self, make_match):
        m = make_match()
        with pytest.raises(InvalidActionError, match="玩家不存在"):
            m.submit_action("p3", ActionType.EARN_MONEY)

    def test_attack_requires_target(self, make_match):
        m = make_match({"knives": 1}, {})
        with pytest.raises(InvalidActionError, match="必须指定目标"):
            m.submit_action("p1", ActionType.USE_KNIFE, None)

    def test_attack_self_rejected(self, make_match):
        m = make_match({"knives": 1}, {})
        with pytest.raises(InvalidActionError, match="不能以自己"):
            m.submit_action("p1", ActionType.USE_KNIFE, "p1")

    def test_attack_unknown_target_rejected(self, make_match):
        m = make_match({"knives": 1}, {})
        with pytest.raises(InvalidActionError, match="目标玩家不存在"):
            m.submit_action("p1", ActionType.USE_KNIFE, "p9")

    def test_non_attack_with_target_rejected(self, make_match):
        m = make_match()
        with pytest.raises(InvalidActionError, match="不支持指定目标"):
            m.submit_action("p1", ActionType.EARN_MONEY, "p2")

    def test_actions_rejected_after_match_end(self, make_match, play_round):
        m = make_match({"knives": 1}, {})
        play_round(m, ActionType.USE_KNIFE, ActionType.EARN_MONEY)
        with pytest.raises(ConflictError, match="对局已结束"):
            m.submit_action("p2", ActionType.EARN_MONEY)

    def test_insufficient_resources_rejected_at_submission(self, make_match):
        m = make_match()
        with pytest.raises(Exception, match="前置条件不满足"):
            m.submit_action("p1", ActionType.USE_KNIFE, "p2")
        assert m.view()["submitted"] == []


class TestFullGames:
    def test_knife_rush_game(self, make_match, play_round):
        m = make_match()
        play_round(m, ActionType.EARN_MONEY, ActionType.EARN_MONEY)
        play_round(m, ActionType.BUY_KNIFE, ActionType.EARN_MONEY)
        r = play_round(m, ActionType.USE_KNIFE, ActionType.EARN_MONEY)
        assert r.winner == "p1"
        assert m.status is MatchStatus.ENDED
        assert m.round_number == 3

    def test_reflect_shield_counter_game(self, make_match, play_round):
        m = make_match()
        play_round(m, ActionType.EARN_MONEY, ActionType.CRAFT_REFLECT_SHIELD)
        play_round(m, ActionType.BUY_KNIFE, ActionType.EARN_MONEY)
        r = play_round(m, ActionType.USE_KNIFE, ActionType.USE_REFLECT_SHIELD)
        assert r.winner == "p2"
        assert m.status is MatchStatus.ENDED

    def test_bomb_pierce_game(self, make_match, play_round):
        m = make_match()
        play_round(m, ActionType.EARN_MONEY, ActionType.USE_NORMAL_SHIELD)
        play_round(m, ActionType.EARN_MONEY, ActionType.USE_NORMAL_SHIELD)
        play_round(m, ActionType.BUY_GUNPOWDER, ActionType.USE_NORMAL_SHIELD)
        play_round(m, ActionType.CRAFT_BOMB, ActionType.USE_NORMAL_SHIELD)
        r = play_round(m, ActionType.USE_BOMB, ActionType.USE_NORMAL_SHIELD)
        assert r.winner == "p1"
        assert m.players["p1"].resources.money == 0
        assert m.players["p1"].resources.gunpowder == 0
        assert m.players["p1"].resources.bombs == 0

    def test_mutual_attack_draw(self, make_match, play_round):
        m = make_match({"knives": 1}, {"knives": 1})
        r = play_round(m, ActionType.USE_KNIFE, ActionType.USE_KNIFE)
        assert r.winner == "draw"
        assert m.status is MatchStatus.ENDED
        assert m.winner == "draw"


class TestRoundAccounting:
    def test_round_number_and_history_advance(self, make_match, play_round):
        m = make_match()
        play_round(m, ActionType.EARN_MONEY, ActionType.EARN_MONEY)
        play_round(m, ActionType.EARN_MONEY, ActionType.USE_NORMAL_SHIELD)
        assert m.round_number == 3
        assert [r.round_number for r in m.history] == [1, 2]
        assert m.view()["status"] == "in_progress"

    def test_round_number_frozen_on_end(self, make_match, play_round):
        m = make_match({"knives": 1}, {})
        play_round(m, ActionType.USE_KNIFE, ActionType.EARN_MONEY)
        assert m.round_number == 1
        assert m.view()["status"] == "ended"
        assert m.view()["winner"] == "p1"


class TestActionCoverage:
    def test_every_action_is_playable_in_a_match(self, make_match):
        resources = {
            "money": 99,
            "knives": 2,
            "gunpowder": 1,
            "bombs": 1,
            "reflect_shields": 1,
        }
        for action in ACTION_DEFS:
            m = make_match(resources, resources)
            target = "p2" if get_action_def(action).needs_target else None
            assert m.submit_action("p1", action, target) is None
            assert m.submit_action("p2", action, "p1" if target else None) is not None
