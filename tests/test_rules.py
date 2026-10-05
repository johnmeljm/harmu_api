import pytest

from harmu_api.models import (
    ActionCategory,
    ActionType,
    PreconditionFailedError,
    ResourcePack,
)
from harmu_api.rules import apply_action_effects, check_preconditions, get_action_def


def pack(**kwargs) -> ResourcePack:
    return ResourcePack(**kwargs)


class TestActionCategories:
    @pytest.mark.parametrize(
        "action",
        [
            ActionType.EARN_MONEY,
            ActionType.BUY_KNIFE,
            ActionType.BUY_GUNPOWDER,
            ActionType.CRAFT_BOMB,
            ActionType.CRAFT_REFLECT_SHIELD,
        ],
    )
    def test_production_actions(self, action):
        assert get_action_def(action).category is ActionCategory.PRODUCTION
        assert not get_action_def(action).needs_target

    @pytest.mark.parametrize(
        "action",
        [ActionType.USE_KNIFE, ActionType.USE_DOUBLE_KNIFE, ActionType.USE_BOMB],
    )
    def test_attack_actions_need_target(self, action):
        assert get_action_def(action).category is ActionCategory.ATTACK
        assert get_action_def(action).needs_target

    @pytest.mark.parametrize(
        "action",
        [ActionType.USE_NORMAL_SHIELD, ActionType.USE_REFLECT_SHIELD],
    )
    def test_defense_actions(self, action):
        assert get_action_def(action).category is ActionCategory.DEFENSE
        assert not get_action_def(action).needs_target


class TestProductionEffects:
    def test_earn_money(self):
        r = pack()
        changes = apply_action_effects(r, ActionType.EARN_MONEY)
        assert (r.money, r.knives) == (1, 0)
        assert changes == {"money": 1}

    def test_buy_knife(self):
        r = pack(money=1)
        changes = apply_action_effects(r, ActionType.BUY_KNIFE)
        assert (r.money, r.knives) == (0, 1)
        assert changes == {"money": -1, "knives": 1}

    def test_buy_gunpowder(self):
        r = pack(money=2)
        apply_action_effects(r, ActionType.BUY_GUNPOWDER)
        assert (r.money, r.gunpowder) == (0, 1)

    def test_craft_bomb(self):
        r = pack(gunpowder=1)
        apply_action_effects(r, ActionType.CRAFT_BOMB)
        assert (r.gunpowder, r.bombs) == (0, 1)

    def test_craft_reflect_shield_is_free(self):
        r = pack()
        apply_action_effects(r, ActionType.CRAFT_REFLECT_SHIELD)
        assert r.reflect_shields == 1
        assert r.money == 0

    def test_normal_shield_has_no_cost(self):
        r = pack()
        changes = apply_action_effects(r, ActionType.USE_NORMAL_SHIELD)
        assert changes == {}
        assert r == ResourcePack()


class TestPreconditions:
    @pytest.mark.parametrize(
        "action,resources",
        [
            (ActionType.BUY_KNIFE, {}),
            (ActionType.BUY_GUNPOWDER, {"money": 1}),
            (ActionType.CRAFT_BOMB, {}),
            (ActionType.USE_KNIFE, {}),
            (ActionType.USE_DOUBLE_KNIFE, {"knives": 1}),
            (ActionType.USE_BOMB, {}),
            (ActionType.USE_REFLECT_SHIELD, {}),
        ],
    )
    def test_insufficient_resources(self, action, resources):
        with pytest.raises(PreconditionFailedError):
            check_preconditions(pack(**resources), action)

    def test_normal_shield_always_usable(self):
        check_preconditions(pack(), ActionType.USE_NORMAL_SHIELD)

    def test_error_message_mentions_resource(self):
        with pytest.raises(PreconditionFailedError, match="钱"):
            check_preconditions(pack(), ActionType.BUY_KNIFE)
