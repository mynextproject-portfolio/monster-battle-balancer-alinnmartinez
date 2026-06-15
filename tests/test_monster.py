"""
Tests for the Monster model class.

These tests cover:
- Fail-fast validation (required fields)
- Raw attribute access (hp, ac, strength, name, image_url)
- Attack parsing (to-hit bonus and damage dice)
- String representations
"""

import pytest
from models.monster import Monster, Attack


class TestMonsterInitialization:
    """Test Monster initialization and validation."""

    def test_successful_initialization_with_valid_data(self):
        """Test that a Monster can be created with all required fields."""
        data = {
            "index": "goblin",
            "name": "Goblin",
            "hit_points": 7,
            "armor_class": [{"value": 15}],
            "strength": 8,
            "full_image_url": "https://example.com/goblin.png"
        }

        monster = Monster(data)

        assert monster.index == "goblin"
        assert monster.name == "Goblin"
        assert monster.hp == 7
        assert monster.ac == 15
        assert monster.strength == 8
        assert monster.image_url == "https://example.com/goblin.png"

    def test_initialization_with_defaults(self):
        """Test that optional fields use sensible defaults."""
        data = {
            "name": "Test Monster",
            "hit_points": 50,
            "armor_class": [{"value": 12}],
            "strength": 10,
            # No index or image_url
        }

        monster = Monster(data)

        assert monster.index == ""
        assert monster.image_url is None


class TestMonsterValidation:
    """Test fail-fast validation for required fields."""

    def test_missing_hit_points_raises_error(self):
        """Test that missing hit_points raises ValueError immediately."""
        data = {
            "name": "Invalid Monster",
            # Missing hit_points
            "armor_class": [{"value": 12}],
            "strength": 10,
        }

        with pytest.raises(ValueError, match="missing required 'hit_points'"):
            Monster(data)

    def test_missing_armor_class_raises_error(self):
        """Test that missing armor_class raises ValueError immediately."""
        data = {
            "name": "Invalid Monster",
            "hit_points": 50,
            # Missing armor_class
            "strength": 10,
        }

        with pytest.raises(ValueError, match="missing required 'armor_class'"):
            Monster(data)

    def test_missing_strength_raises_error(self):
        """Test that missing strength raises ValueError immediately."""
        data = {
            "name": "Invalid Monster",
            "hit_points": 50,
            "armor_class": [{"value": 12}],
            # Missing strength
        }

        with pytest.raises(ValueError, match="missing required 'strength'"):
            Monster(data)


class TestStringRepresentations:
    """Test __str__ and __repr__ methods."""

    def test_str_returns_name(self):
        """Test that str(monster) returns the monster name."""
        data = {
            "name": "Ancient Dragon",
            "hit_points": 500,
            "armor_class": [{"value": 22}],
            "strength": 27,
        }

        monster = Monster(data)

        assert str(monster) == "Ancient Dragon"

    def test_repr_shows_key_attributes(self):
        """Test that repr(monster) shows name, hp, and ac."""
        data = {
            "name": "Goblin",
            "hit_points": 7,
            "armor_class": [{"value": 15}],
            "strength": 8,
        }

        monster = Monster(data)

        assert repr(monster) == "Monster(name='Goblin', hp=7, ac=15)"


class TestAttackParsing:
    """Test attack parsing from monster actions."""

    def test_monster_with_attack_parses_correctly(self):
        """Test that a monster with a simple attack is parsed."""
        data = {
            "name": "Goblin",
            "hit_points": 7,
            "armor_class": [{"value": 15}],
            "strength": 8,
            "actions": [
                {
                    "name": "Scimitar",
                    "attack_bonus": 4,
                    "damage": [
                        {
                            "damage_dice": "1d6+2",
                            "damage_type": {"name": "Slashing"}
                        }
                    ]
                }
            ]
        }

        monster = Monster(data)

        assert monster.attack is not None
        assert monster.attack.to_hit_bonus == 4
        assert monster.attack.damage_dice == "1d6+2"

    def test_monster_with_no_actions_has_no_attack(self):
        """Test that a monster with no actions has no attack."""
        data = {
            "name": "Commoner",
            "hit_points": 3,
            "armor_class": [{"value": 10}],
            "strength": 10,
            # No actions field
        }

        monster = Monster(data)

        assert monster.attack is None

    def test_monster_with_empty_actions_has_no_attack(self):
        """Test that a monster with empty actions has no attack."""
        data = {
            "name": "Commoner",
            "hit_points": 3,
            "armor_class": [{"value": 10}],
            "strength": 10,
            "actions": []
        }

        monster = Monster(data)

        assert monster.attack is None

    def test_multiattack_is_skipped(self):
        """Test that Multiattack action is skipped, using next real attack."""
        data = {
            "name": "Ancient Red Dragon",
            "hit_points": 546,
            "armor_class": [{"value": 22}],
            "strength": 27,
            "actions": [
                {
                    "name": "Multiattack",
                    "desc": "The dragon can use its Frightful Presence...",
                    # No attack_bonus or damage - this is not an attack
                    "damage": []
                },
                {
                    "name": "Bite",
                    "attack_bonus": 17,
                    "damage": [
                        {
                            "damage_dice": "2d10+10",
                            "damage_type": {"name": "Piercing"}
                        }
                    ]
                }
            ]
        }

        monster = Monster(data)

        # Should skip Multiattack and use Bite
        assert monster.attack is not None
        assert monster.attack.to_hit_bonus == 17
        assert monster.attack.damage_dice == "2d10+10"

    def test_first_attack_is_used_when_multiple_exist(self):
        """Test that the first actual attack is used when multiple attacks exist."""
        data = {
            "name": "Test Monster",
            "hit_points": 50,
            "armor_class": [{"value": 15}],
            "strength": 16,
            "actions": [
                {
                    "name": "Sword",
                    "attack_bonus": 6,
                    "damage": [
                        {"damage_dice": "1d8+3", "damage_type": {"name": "Slashing"}}
                    ]
                },
                {
                    "name": "Bow",
                    "attack_bonus": 5,
                    "damage": [
                        {"damage_dice": "1d6+2", "damage_type": {"name": "Piercing"}}
                    ]
                }
            ]
        }

        monster = Monster(data)

        # Should use the first attack (Sword)
        assert monster.attack.to_hit_bonus == 6
        assert monster.attack.damage_dice == "1d8+3"

    def test_attack_with_multiple_damage_types(self):
        """Test that attack with multiple damage types uses the first one."""
        data = {
            "name": "Fire Dragon",
            "hit_points": 200,
            "armor_class": [{"value": 19}],
            "strength": 22,
            "actions": [
                {
                    "name": "Bite",
                    "attack_bonus": 12,
                    "damage": [
                        {
                            "damage_dice": "2d10+8",
                            "damage_type": {"name": "Piercing"}
                        },
                        {
                            "damage_dice": "3d6",
                            "damage_type": {"name": "Fire"}
                        }
                    ]
                }
            ]
        }

        monster = Monster(data)

        # Should use first damage (piercing)
        assert monster.attack.to_hit_bonus == 12
        assert monster.attack.damage_dice == "2d10+8"

    def test_attack_with_zero_bonus(self):
        """Test that attacks with 0 to-hit bonus are handled correctly."""
        data = {
            "name": "Weak Monster",
            "hit_points": 10,
            "armor_class": [{"value": 10}],
            "strength": 3,
            "actions": [
                {
                    "name": "Fist",
                    "attack_bonus": 0,
                    "damage": [
                        {"damage_dice": "1d4", "damage_type": {"name": "Bludgeoning"}}
                    ]
                }
            ]
        }

        monster = Monster(data)

        assert monster.attack is not None
        assert monster.attack.to_hit_bonus == 0
        assert monster.attack.damage_dice == "1d4"

    def test_attack_with_negative_bonus(self):
        """Test that attacks with negative to-hit bonus are handled correctly."""
        data = {
            "name": "Very Weak Monster",
            "hit_points": 5,
            "armor_class": [{"value": 8}],
            "strength": 2,
            "actions": [
                {
                    "name": "Fist",
                    "attack_bonus": -2,
                    "damage": [
                        {"damage_dice": "1d3", "damage_type": {"name": "Bludgeoning"}}
                    ]
                }
            ]
        }

        monster = Monster(data)

        assert monster.attack is not None
        assert monster.attack.to_hit_bonus == -2
        assert monster.attack.damage_dice == "1d3"

    def test_action_without_damage_is_not_used_as_attack(self):
        """Test that actions without damage data are not used as attacks."""
        data = {
            "name": "Wizard",
            "hit_points": 40,
            "armor_class": [{"value": 12}],
            "strength": 10,
            "actions": [
                {
                    "name": "Spellcasting",
                    "desc": "The wizard knows various spells...",
                    # Has attack_bonus but no damage
                    "attack_bonus": 5,
                    "damage": []
                },
                {
                    "name": "Dagger",
                    "attack_bonus": 3,
                    "damage": [
                        {"damage_dice": "1d4+1", "damage_type": {"name": "Piercing"}}
                    ]
                }
            ]
        }

        monster = Monster(data)

        # Should skip Spellcasting and use Dagger
        assert monster.attack.to_hit_bonus == 3
        assert monster.attack.damage_dice == "1d4+1"


class TestAttackClass:
    """Test the Attack class."""

    def test_attack_initialization(self):
        """Test that Attack can be initialized with to-hit and damage."""
        attack = Attack(to_hit_bonus=4, damage_dice="1d6+2")

        assert attack.to_hit_bonus == 4
        assert attack.damage_dice == "1d6+2"

    def test_attack_str_representation(self):
        """Test the string representation of Attack."""
        attack = Attack(to_hit_bonus=4, damage_dice="1d6+2")

        assert str(attack) == "+4 to hit, 1d6+2 damage"

    def test_attack_repr_representation(self):
        """Test the repr representation of Attack."""
        attack = Attack(to_hit_bonus=4, damage_dice="1d6+2")

        assert repr(attack) == "Attack(to_hit=+4, damage=1d6+2)"

    def test_attack_repr_with_negative_bonus(self):
        """Test the repr representation with negative bonus."""
        attack = Attack(to_hit_bonus=-2, damage_dice="1d4")

        assert repr(attack) == "Attack(to_hit=-2, damage=1d4)"


class TestMonsterExistingBehavior:
    """Test that existing Monster behavior is unchanged."""

    def test_successful_initialization_with_valid_data(self):
        """Test that a Monster can be created with all required fields."""
        data = {
            "index": "goblin",
            "name": "Goblin",
            "hit_points": 7,
            "armor_class": [{"value": 15}],
            "strength": 8,
            "full_image_url": "https://example.com/goblin.png"
        }

        monster = Monster(data)

        assert monster.index == "goblin"
        assert monster.name == "Goblin"
        assert monster.hp == 7
        assert monster.ac == 15
        assert monster.strength == 8
        assert monster.image_url == "https://example.com/goblin.png"

    def test_initialization_with_defaults(self):
        """Test that optional fields use sensible defaults."""
        data = {
            "name": "Test Monster",
            "hit_points": 50,
            "armor_class": [{"value": 12}],
            "strength": 10,
            # No index or image_url
        }

        monster = Monster(data)

        assert monster.index == ""
        assert monster.image_url is None

    def test_repr_shows_key_attributes_without_attack(self):
        """Test that repr without attack still works."""
        data = {
            "name": "Commoner",
            "hit_points": 3,
            "armor_class": [{"value": 10}],
            "strength": 10,
            "actions": []
        }

        monster = Monster(data)

        assert repr(monster) == "Monster(name='Commoner', hp=3, ac=10)"
