from typing import Dict, Any, Optional


class Attack:
    """Represents a single attack action from a monster.
    
    Contains the attack's to-hit bonus and damage dice.
    """

    def __init__(self, to_hit_bonus: int, damage_dice: str):
        """Initialize an Attack.

        Args:
            to_hit_bonus: The bonus added to attack rolls (e.g., +4)
            damage_dice: The damage dice notation (e.g., "1d6+2")
        """
        self.to_hit_bonus = to_hit_bonus
        self.damage_dice = damage_dice

    def __repr__(self) -> str:
        return f"Attack(to_hit={self.to_hit_bonus:+d}, damage={self.damage_dice})"

    def __str__(self) -> str:
        return f"{self.to_hit_bonus:+d} to hit, {self.damage_dice} damage"


class Monster:
    """Represents a D&D monster with its raw display attributes.

    This class validates required fields during initialization so that
    invalid API data fails fast with a clear error message.
    """

    def __init__(self, data: Dict[str, Any]):
        """Initialize a Monster from API response data.

        Validates required fields immediately (fail-fast error handling).

        Args:
            data: Dictionary containing monster data from the API

        Raises:
            ValueError: If required fields are missing or invalid
        """
        self._data = data

        # Basic attributes (with defaults)
        self.index = data.get("index", "")
        self.name = data.get("name", "Unknown")
        self.image_url = data.get("full_image_url")

        # Validate and extract required fields (fail fast)
        self._validate_and_extract_required_fields()

    def _validate_and_extract_required_fields(self) -> None:
        """Validate and extract required fields from API data.

        Raises:
            ValueError: If any required field is missing or invalid
        """
        # Hit points (required)
        if "hit_points" not in self._data:
            raise ValueError(f"Monster '{self.name}' missing required 'hit_points' data")
        self._hp = self._data["hit_points"]

        # Armor class (required)
        armor_class = self._data.get("armor_class", [])
        if not armor_class or len(armor_class) == 0:
            raise ValueError(f"Monster '{self.name}' missing required 'armor_class' data")
        ac_value = armor_class[0].get("value")
        if ac_value is None:
            raise ValueError(f"Monster '{self.name}' has invalid 'armor_class' structure")
        self._ac = ac_value

        # Strength (required)
        if "strength" not in self._data:
            raise ValueError(f"Monster '{self.name}' missing required 'strength' data")
        self._strength = self._data["strength"]

        # Attack (optional - parse from actions)
        self._attack: Optional[Attack] = self._parse_attack()

    def _parse_attack(self) -> Optional[Attack]:
        """Parse the first actual attack from the monster's actions.
        
        Skips non-attack actions like Multiattack and special abilities.
        Returns None if no attack is found.

        Returns:
            Attack object with to_hit_bonus and damage_dice, or None
        """
        actions = self._data.get("actions", [])
        
        for action in actions:
            # Skip non-attack actions
            if action.get("name", "").lower() == "multiattack":
                continue
            
            # Check if this action has attack_bonus and damage (indicates it's an attack)
            attack_bonus = action.get("attack_bonus")
            damage = action.get("damage", [])
            
            # A valid attack should have both to-hit bonus and damage
            if attack_bonus is not None and damage:
                # Extract the first damage dice
                first_damage = damage[0] if damage else None
                if first_damage:
                    damage_dice = first_damage.get("damage_dice", "")
                    if damage_dice:
                        return Attack(attack_bonus, damage_dice)
        
        return None

    # Properties - lightweight accessors returning the validated values

    @property
    def hp(self) -> int:
        """Return the monster's hit points."""
        return self._hp

    @property
    def ac(self) -> int:
        """Return the monster's armor class (Defense)."""
        return self._ac

    @property
    def strength(self) -> int:
        """Return the monster's Strength score."""
        return self._strength

    @property
    def attack(self) -> Optional[Attack]:
        """Return the monster's primary attack, or None if no attack found.
        
        Parses the first actual attack from the monster's actions,
        skipping non-attack actions like Multiattack.
        """
        return self._attack

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        attack_str = f", attack={self.attack}" if self.attack else ""
        return f"Monster(name='{self.name}', hp={self.hp}, ac={self.ac}{attack_str})"
