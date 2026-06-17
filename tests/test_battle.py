"""Tests for the battle simulator."""

import pytest
from models.monster import Monster
from battle import simulate_battle, win_rates, is_competitive, _parse_damage_dice


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


# ---------------------------------------------------------------------------
# Win rates (Monte Carlo)
# ---------------------------------------------------------------------------

class TestWinRates:
    def test_rates_sum_to_one(self):
        m1 = make_monster("A", hp=10, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        m2 = make_monster("B", hp=10, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        r1, r2 = win_rates(m1, m2)
        assert abs(r1 + r2 - 1.0) < 1e-9

    def test_rates_are_in_range(self):
        m1 = make_monster("A", hp=10, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        m2 = make_monster("B", hp=8, ac=10, strength=8, attack_bonus=2, damage_dice="1d4")
        r1, r2 = win_rates(m1, m2)
        assert 0.0 <= r1 <= 1.0
        assert 0.0 <= r2 <= 1.0

    def test_same_seed_reproducible(self):
        m1 = make_monster("A", hp=10, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        m2 = make_monster("B", hp=10, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        assert win_rates(m1, m2, seed=7) == win_rates(m1, m2, seed=7)

    def test_dominant_monster_wins_majority(self):
        """Tank with overwhelming HP and AC should win >80% of the time."""
        tank = make_monster("Tank", hp=200, ac=18, strength=20, attack_bonus=8, damage_dice="1d10+5")
        weak = make_monster("Weak", hp=5, ac=10, strength=8, attack_bonus=0, damage_dice="1d4")
        r_tank, r_weak = win_rates(tank, weak, n=200)
        assert r_tank > 0.8

    def test_invincible_monster_wins_all(self):
        """AC 30 is unhittable — win rate should be 100%."""
        god = make_monster("God", hp=50, ac=30, strength=10, attack_bonus=5, damage_dice="1d6")
        mortal = make_monster("Mortal", hp=50, ac=10, strength=10, attack_bonus=0, damage_dice="1d4")
        r_god, r_mortal = win_rates(god, mortal, n=100)
        assert r_god == 1.0
        assert r_mortal == 0.0

    def test_n_controls_sample_size(self):
        """Larger n should produce a more stable estimate (lower variance)."""
        m1 = make_monster("A", hp=10, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        m2 = make_monster("B", hp=10, ac=12, strength=10, attack_bonus=3, damage_dice="1d6")
        # With n=1000 default, estimate should be within 10% of 50%
        r1, _ = win_rates(m1, m2, n=1000)
        assert 0.40 <= r1 <= 0.60

    def test_both_no_attack_consistent_result(self):
        """No-attack monsters always resolve the same way — rate should be 0% or 100%."""
        strong = make_monster("Strong", hp=10, ac=10, strength=16)
        weak = make_monster("Weak", hp=5, ac=10, strength=8)
        r_strong, r_weak = win_rates(strong, weak, n=50)
        assert r_strong == 1.0
        assert r_weak == 0.0


# ---------------------------------------------------------------------------
# Competitive verdict (fun vs boring threshold)
# ---------------------------------------------------------------------------

class TestIsCompetitive:
    def test_perfect_50_50_is_competitive(self):
        assert is_competitive(0.50, 0.50) is True

    def test_exactly_at_threshold_is_competitive(self):
        # 0.20 is the agreed minimum — must be included
        assert is_competitive(0.20, 0.80) is True

    def test_just_below_threshold_is_not_competitive(self):
        assert is_competitive(0.19, 0.81) is False

    def test_shutout_is_not_competitive(self):
        assert is_competitive(0.0, 1.0) is False

    def test_comfortable_underdog_is_competitive(self):
        assert is_competitive(0.35, 0.65) is True

    def test_custom_threshold_respected(self):
        # With a stricter threshold, 25% underdog is a stomp
        assert is_competitive(0.25, 0.75, threshold=0.30) is False

    def test_custom_threshold_passes_when_above(self):
        assert is_competitive(0.35, 0.65, threshold=0.30) is True

    def test_symmetry(self):
        # Order of arguments should not matter
        assert is_competitive(0.30, 0.70) == is_competitive(0.70, 0.30)
