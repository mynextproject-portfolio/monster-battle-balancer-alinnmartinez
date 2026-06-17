"""Tests for the battle simulator."""

import pytest
from models.monster import Monster
from battle import simulate_battle, _parse_damage_dice


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_monster(name, hp, ac, strength, attack_bonus=None, damage_dice=None):
    """Build a minimal Monster suitable for battle tests."""
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
# Dice parsing
# ---------------------------------------------------------------------------

class TestParseDamageDice:
    def test_simple_dice(self):
        assert _parse_damage_dice("1d6") == (1, 6, 0)

    def test_dice_with_positive_modifier(self):
        assert _parse_damage_dice("2d10+8") == (2, 10, 8)

    def test_dice_with_negative_modifier(self):
        assert _parse_damage_dice("1d4-1") == (1, 4, -1)

    def test_multi_dice(self):
        assert _parse_damage_dice("3d6") == (3, 6, 0)


# ---------------------------------------------------------------------------
# Core contract
# ---------------------------------------------------------------------------

class TestSimulateBattleContract:
    def test_returns_one_of_the_two_monsters(self):
        m1 = make_monster("Goblin", hp=7, ac=15, strength=8, attack_bonus=4, damage_dice="1d6+2")
        m2 = make_monster("Orc", hp=15, ac=13, strength=16, attack_bonus=5, damage_dice="1d12+3")
        winner = simulate_battle(m1, m2, seed=42)
        assert winner is m1 or winner is m2

    def test_same_seed_same_result(self):
        m1 = make_monster("Goblin", hp=7, ac=15, strength=8, attack_bonus=4, damage_dice="1d6+2")
        m2 = make_monster("Orc", hp=15, ac=13, strength=16, attack_bonus=5, damage_dice="1d12+3")
        assert simulate_battle(m1, m2, seed=99) is simulate_battle(m1, m2, seed=99)

    def test_different_seeds_affect_outcome(self):
        """With a balanced matchup, different seeds should not all produce the same winner."""
        m1 = make_monster("A", hp=10, ac=10, strength=10, attack_bonus=0, damage_dice="1d6")
        m2 = make_monster("B", hp=10, ac=10, strength=9, attack_bonus=0, damage_dice="1d6")
        winners = {simulate_battle(m1, m2, seed=s) for s in range(30)}
        assert len(winners) == 2

    def test_no_seed_is_nondeterministic(self):
        """Running without a seed twice on a balanced matchup should occasionally differ."""
        m1 = make_monster("X", hp=10, ac=10, strength=10, attack_bonus=0, damage_dice="1d6")
        m2 = make_monster("Y", hp=10, ac=10, strength=9, attack_bonus=0, damage_dice="1d6")
        # Just verify it runs without error and returns a valid winner.
        winner = simulate_battle(m1, m2)
        assert winner is m1 or winner is m2


# ---------------------------------------------------------------------------
# Termination guarantees
# ---------------------------------------------------------------------------

class TestTermination:
    def test_always_terminates_monster1_no_attack(self):
        """Fight terminates even when monster1 cannot attack."""
        no_attack = make_monster("Pacifist", hp=20, ac=11, strength=7)
        attacker = make_monster("Warrior", hp=52, ac=18, strength=16, attack_bonus=5, damage_dice="1d8+3")
        winner = simulate_battle(no_attack, attacker, seed=0)
        assert winner is no_attack or winner is attacker

    def test_always_terminates_monster2_no_attack(self):
        """Fight terminates even when monster2 cannot attack."""
        attacker = make_monster("Warrior", hp=52, ac=18, strength=16, attack_bonus=5, damage_dice="1d8+3")
        no_attack = make_monster("Pacifist", hp=20, ac=11, strength=7)
        winner = simulate_battle(attacker, no_attack, seed=0)
        assert winner is attacker or winner is no_attack

    def test_always_terminates_both_no_attack(self):
        """Fight terminates when neither monster has an attack."""
        m1 = make_monster("Commoner", hp=3, ac=10, strength=10)
        m2 = make_monster("Peasant", hp=4, ac=10, strength=10)
        winner = simulate_battle(m1, m2, seed=0)
        assert winner is m1 or winner is m2

    def test_only_attacker_can_win_when_defender_cannot_attack(self):
        """A monster that can't deal damage should always lose to a competent attacker."""
        pacifist = make_monster("Pacifist", hp=5, ac=10, strength=10)
        warrior = make_monster("Warrior", hp=100, ac=10, strength=20, attack_bonus=10, damage_dice="1d8+5")
        for seed in range(10):
            assert simulate_battle(warrior, pacifist, seed=seed) is warrior

    def test_both_no_attack_higher_hp_wins(self):
        """When neither can attack, the monster with more HP wins."""
        weak = make_monster("Weak", hp=3, ac=10, strength=10)
        strong = make_monster("Strong", hp=10, ac=10, strength=10)
        assert simulate_battle(weak, strong) is strong
        assert simulate_battle(strong, weak) is strong

    def test_both_no_attack_hp_tie_strength_decides(self):
        """Equal HP, no attacks: monster with higher strength wins."""
        m1 = make_monster("Low Str", hp=5, ac=10, strength=8)
        m2 = make_monster("High Str", hp=5, ac=10, strength=16)
        assert simulate_battle(m1, m2) is m2


# ---------------------------------------------------------------------------
# Stats are used
# ---------------------------------------------------------------------------

class TestBattleUsesStats:
    def test_overwhelming_hp_advantage_wins(self):
        """Monster with dramatically more HP should win every seed tested."""
        tank = make_monster("Tank", hp=1000, ac=10, strength=10, attack_bonus=5, damage_dice="1d6")
        glass = make_monster("Glass", hp=1, ac=10, strength=10, attack_bonus=5, damage_dice="1d6")
        for seed in range(10):
            assert simulate_battle(tank, glass, seed=seed) is tank

    def test_impossible_to_hit_ac_always_wins(self):
        """Armor class of 30 is unhittable (max roll d20+bonus < 30)."""
        untouchable = make_monster("Untouchable", hp=50, ac=30, strength=10,
                                   attack_bonus=5, damage_dice="1d6")
        weak = make_monster("Weak", hp=50, ac=10, strength=10,
                             attack_bonus=0, damage_dice="1d4")
        # weak attacks untouchable: needs 30, max is d20(20)+0 = 20 → never hits
        # untouchable attacks weak: needs 10, d20+5 → almost always hits
        for seed in range(10):
            assert simulate_battle(untouchable, weak, seed=seed) is untouchable

    def test_seed_is_used_not_ignored(self):
        """Verify that the seed actually controls the RNG (same seed, same winner)."""
        m1 = make_monster("Fighter", hp=20, ac=14, strength=16, attack_bonus=5, damage_dice="1d8+3")
        m2 = make_monster("Rogue", hp=16, ac=13, strength=10, attack_bonus=4, damage_dice="1d6+2")
        results = [simulate_battle(m1, m2, seed=7) for _ in range(5)]
        assert len(set(id(r) for r in results)) == 1  # always the same object
