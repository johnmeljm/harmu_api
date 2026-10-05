from harmu_api.models import ActionType, MatchStatus
from harmu_api.settlement import AttackOutcome


def attack_event(result) -> dict:
    return next(e for e in result.events if e["type"] == "attack")


class TestKnife:
    def test_hits_undefended_target(self, make_match, play_round):
        m = make_match({"knives": 1}, {})
        r = play_round(m, ActionType.USE_KNIFE, ActionType.EARN_MONEY)
        assert attack_event(r)["outcome"] == AttackOutcome.HIT.value
        assert attack_event(r)["damage_to"] == "p2"
        assert r.deaths == ["p2"]
        assert r.winner == "p1"
        assert r.match_status is MatchStatus.ENDED
        assert m.players["p1"].resources.knives == 0
        assert m.players["p2"].resources.hp == 0
        assert not m.players["p2"].alive

    def test_blocked_by_normal_shield(self, make_match, play_round):
        m = make_match({"knives": 1}, {})
        r = play_round(m, ActionType.USE_KNIFE, ActionType.USE_NORMAL_SHIELD)
        assert attack_event(r)["outcome"] == AttackOutcome.BLOCKED.value
        assert attack_event(r)["damage_to"] is None
        assert r.deaths == []
        assert r.winner is None
        assert r.match_status is MatchStatus.IN_PROGRESS
        assert m.players["p1"].resources.knives == 0
        assert m.players["p1"].resources.hp == 1
        assert m.players["p2"].resources.hp == 1
        assert m.round_number == 2

    def test_reflected_by_reflect_shield(self, make_match, play_round):
        m = make_match({"knives": 1}, {"reflect_shields": 1})
        r = play_round(m, ActionType.USE_KNIFE, ActionType.USE_REFLECT_SHIELD)
        assert attack_event(r)["outcome"] == AttackOutcome.REFLECTED.value
        assert attack_event(r)["damage_to"] == "p1"
        assert r.deaths == ["p1"]
        assert r.winner == "p2"
        assert m.players["p1"].resources.knives == 0
        assert m.players["p1"].resources.hp == 0
        assert m.players["p2"].resources.hp == 1
        assert m.players["p2"].resources.reflect_shields == 0


class TestDoubleKnife:
    def test_hits_undefended_target(self, make_match, play_round):
        m = make_match({"knives": 2}, {})
        r = play_round(m, ActionType.USE_DOUBLE_KNIFE, ActionType.EARN_MONEY)
        assert attack_event(r)["outcome"] == AttackOutcome.HIT.value
        assert r.deaths == ["p2"]
        assert r.winner == "p1"
        assert m.players["p1"].resources.knives == 0

    def test_pierces_normal_shield(self, make_match, play_round):
        m = make_match({"knives": 2}, {})
        r = play_round(m, ActionType.USE_DOUBLE_KNIFE, ActionType.USE_NORMAL_SHIELD)
        assert attack_event(r)["outcome"] == AttackOutcome.PIERCED.value
        assert attack_event(r)["damage_to"] == "p2"
        assert r.deaths == ["p2"]
        assert r.winner == "p1"
        assert m.players["p1"].resources.knives == 0
        assert m.players["p2"].resources.hp == 0

    def test_reflected_by_reflect_shield(self, make_match, play_round):
        m = make_match({"knives": 2}, {"reflect_shields": 1})
        r = play_round(m, ActionType.USE_DOUBLE_KNIFE, ActionType.USE_REFLECT_SHIELD)
        assert attack_event(r)["outcome"] == AttackOutcome.REFLECTED.value
        assert attack_event(r)["damage_to"] == "p1"
        assert r.deaths == ["p1"]
        assert r.winner == "p2"
        assert m.players["p1"].resources.knives == 0
        assert m.players["p1"].resources.hp == 0
        assert m.players["p2"].resources.hp == 1
        assert m.players["p2"].resources.reflect_shields == 0


class TestBomb:
    def test_hits_undefended_target(self, make_match, play_round):
        m = make_match({"bombs": 1}, {})
        r = play_round(m, ActionType.USE_BOMB, ActionType.EARN_MONEY)
        assert attack_event(r)["outcome"] == AttackOutcome.HIT.value
        assert r.deaths == ["p2"]
        assert r.winner == "p1"
        assert m.players["p1"].resources.bombs == 0

    def test_pierces_normal_shield(self, make_match, play_round):
        m = make_match({"bombs": 1}, {})
        r = play_round(m, ActionType.USE_BOMB, ActionType.USE_NORMAL_SHIELD)
        assert attack_event(r)["outcome"] == AttackOutcome.PIERCED.value
        assert attack_event(r)["damage_to"] == "p2"
        assert r.deaths == ["p2"]
        assert r.winner == "p1"
        assert m.players["p1"].resources.bombs == 0

    def test_blocked_by_reflect_shield(self, make_match, play_round):
        m = make_match({"bombs": 1}, {"reflect_shields": 1})
        r = play_round(m, ActionType.USE_BOMB, ActionType.USE_REFLECT_SHIELD)
        assert attack_event(r)["outcome"] == AttackOutcome.BLOCKED.value
        assert attack_event(r)["damage_to"] is None
        assert r.deaths == []
        assert r.winner is None
        assert r.match_status is MatchStatus.IN_PROGRESS
        assert m.players["p1"].resources.bombs == 0
        assert m.players["p1"].resources.hp == 1
        assert m.players["p2"].resources.hp == 1
        assert m.players["p2"].resources.reflect_shields == 0


class TestMutualAttacks:
    def test_mutual_knife_is_draw(self, make_match, play_round):
        m = make_match({"knives": 1}, {"knives": 1})
        r = play_round(m, ActionType.USE_KNIFE, ActionType.USE_KNIFE)
        assert set(r.deaths) == {"p1", "p2"}
        assert r.winner == "draw"
        assert r.match_status is MatchStatus.ENDED

    def test_knife_vs_bomb_both_die(self, make_match, play_round):
        m = make_match({"knives": 1}, {"bombs": 1})
        r = play_round(m, ActionType.USE_KNIFE, ActionType.USE_BOMB)
        assert set(r.deaths) == {"p1", "p2"}
        assert r.winner == "draw"


class TestDefenseEconomy:
    def test_reflect_shield_consumed_even_without_attack(self, make_match, play_round):
        m = make_match({}, {"reflect_shields": 1})
        r = play_round(m, ActionType.EARN_MONEY, ActionType.USE_REFLECT_SHIELD)
        assert r.deaths == []
        assert m.players["p2"].resources.reflect_shields == 0

    def test_normal_shield_costs_nothing(self, make_match, play_round):
        m = make_match({}, {})
        play_round(m, ActionType.USE_NORMAL_SHIELD, ActionType.USE_NORMAL_SHIELD)
        assert m.players["p1"].resources == m.players["p2"].resources
        assert m.players["p1"].resources.money == 0


class TestProductionDuringSettlement:
    def test_production_applied_before_death(self, make_match, play_round):
        m = make_match({"knives": 1}, {"money": 1})
        r = play_round(m, ActionType.USE_KNIFE, ActionType.BUY_KNIFE)
        assert r.deaths == ["p2"]
        assert m.players["p2"].resources.knives == 1
        assert m.players["p2"].resources.money == 0

    def test_both_players_produce(self, make_match, play_round):
        m = make_match({}, {})
        r = play_round(m, ActionType.EARN_MONEY, ActionType.EARN_MONEY)
        assert r.deaths == []
        assert m.players["p1"].resources.money == 1
        assert m.players["p2"].resources.money == 1
        assert m.round_number == 2
        assert len(m.history) == 1

    def test_round_result_records_actions(self, make_match, play_round):
        m = make_match({"knives": 1}, {})
        r = play_round(m, ActionType.USE_KNIFE, ActionType.USE_NORMAL_SHIELD)
        assert r.actions["p1"] == {"action": "use_knife", "target_id": "p2"}
        assert r.actions["p2"] == {"action": "use_normal_shield", "target_id": None}
