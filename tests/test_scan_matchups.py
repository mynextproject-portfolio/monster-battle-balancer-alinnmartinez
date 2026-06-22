"""Tests for the scan_matchups module.

These tests exercise can_deal_damage (the pre-filter) and scan_fun_pairs
using small in-memory Monster sets — no API calls, no CSV I/O.
"""

import pytest
from models.monster import Monster
from scan_matchups import can_deal_damage, scan_fun_pairs


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_monster(name, hp, ac, strength, attack_bonus=None, damage_dice=None):
    data = {
        "name": name,
        "hit_points": hp,
        "armor_class": [{"value": ac}],
        "strength": strength,
    }
    if attack_bonus is not None and damage_dice is not None:
        data["actions"] = [{
            "name": "Attack",
            "attack_bonus": attack_bonus,
            "damage": [{"damage_dice": damage_dice, "damage_type": {"name": "Slashing"}}],
        }]
    return Monster(data)


# ---------------------------------------------------------------------------
# can_deal_damage
# ---------------------------------------------------------------------------

class TestCanDealDamage:
    def test_no_attack_returns_false(self):
        pacifist = make_monster("Pacifist", hp=10, ac=10, strength=10)
        target = make_monster("Target", hp=10, ac=10, strength=10)
        assert can_deal_damage(pacifist, target) is False

    def test_attack_that_reaches_ac_returns_true(self):
        fighter = make_monster("Fighter", hp=10, ac=10, strength=10, attack_bonus=5, damage_dice="1d6")
        target = make_monster("Target", hp=10, ac=15, strength=10)  # 20+5=25 >= 15
        assert can_deal_damage(fighter, target) is True

    def test_attack_that_cannot_reach_ac_returns_false(self):
        weakling = make_monster("Weakling", hp=10, ac=10, strength=10, attack_bonus=-5, damage_dice="1d4")
        armored = make_monster("Armored", hp=10, ac=20, strength=10)  # 20-5=15 < 20
        assert can_deal_damage(weakling, armored) is False

    def test_natural_20_exactly_reaches_ac(self):
        lucky = make_monster("Lucky", hp=10, ac=10, strength=10, attack_bonus=0, damage_dice="1d6")
        target = make_monster("Target", hp=10, ac=20, strength=10)  # 20+0=20 >= 20
        assert can_deal_damage(lucky, target) is True

    def test_one_above_max_roll_returns_false(self):
        unlucky = make_monster("Unlucky", hp=10, ac=10, strength=10, attack_bonus=0, damage_dice="1d6")
        fortress = make_monster("Fortress", hp=10, ac=21, strength=10)  # 20+0=20 < 21
        assert can_deal_damage(unlucky, fortress) is False


# ---------------------------------------------------------------------------
# scan_fun_pairs
# ---------------------------------------------------------------------------

class TestScanFunPairs:
    def test_balanced_pair_is_included(self):
        """Two identical monsters should produce a competitive matchup."""
        m1 = make_monster("A", hp=20, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        m2 = make_monster("B", hp=20, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        results = scan_fun_pairs([m1, m2])
        assert len(results) == 1
        assert {results[0]["monster1"], results[0]["monster2"]} == {"A", "B"}

    def test_one_sided_pair_is_excluded(self):
        """Pair where one side can never deal damage is pre-filtered out."""
        warrior = make_monster("Warrior", hp=50, ac=10, strength=10, attack_bonus=5, damage_dice="1d8")
        pacifist = make_monster("Pacifist", hp=50, ac=10, strength=10)
        assert scan_fun_pairs([warrior, pacifist]) == []

    def test_pair_where_one_cannot_hit_is_excluded(self):
        """Pair where one attacker can never reach the defender's AC is excluded."""
        god = make_monster("God", hp=50, ac=30, strength=10, attack_bonus=5, damage_dice="1d6")
        mortal = make_monster("Mortal", hp=50, ac=10, strength=10, attack_bonus=0, damage_dice="1d4")
        # mortal needs 30 to hit god, max is 20+0=20 → can't deal damage
        assert scan_fun_pairs([god, mortal]) == []

    def test_results_sorted_by_balance_descending(self):
        """Results should come out closest-to-50/50 first."""
        m1 = make_monster("A", hp=20, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        m2 = make_monster("B", hp=20, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        m3 = make_monster("C", hp=20, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        results = scan_fun_pairs([m1, m2, m3])
        balances = [r["balance"] for r in results]
        assert balances == sorted(balances, reverse=True)

    def test_result_row_has_required_fields(self):
        m1 = make_monster("A", hp=20, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        m2 = make_monster("B", hp=20, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        results = scan_fun_pairs([m1, m2])
        assert len(results) == 1
        row = results[0]
        for field in ("monster1", "monster2", "m1_win_pct", "m2_win_pct", "balance"):
            assert field in row

    def test_win_pcts_sum_to_100(self):
        m1 = make_monster("A", hp=20, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        m2 = make_monster("B", hp=20, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        results = scan_fun_pairs([m1, m2])
        for row in results:
            assert abs(row["m1_win_pct"] + row["m2_win_pct"] - 100.0) < 0.2

    def test_empty_monster_list_returns_empty(self):
        assert scan_fun_pairs([]) == []

    def test_single_monster_returns_empty(self):
        m = make_monster("Lonely", hp=10, ac=10, strength=10, attack_bonus=0, damage_dice="1d6")
        assert scan_fun_pairs([m]) == []
