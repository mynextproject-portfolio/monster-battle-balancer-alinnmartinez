import random
import re
from typing import Optional

from models.monster import Monster


def _parse_damage_dice(damage_dice: str) -> tuple[int, int, int]:
    """Return (count, sides, modifier) from a dice string like '2d10+8'."""
    match = re.match(r"(\d+)d(\d+)([+-]\d+)?", damage_dice.strip())
    if not match:
        return (1, 4, 0)
    count = int(match.group(1))
    sides = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    return count, sides, modifier


def _roll_damage(damage_dice: str, rng: random.Random) -> int:
    count, sides, modifier = _parse_damage_dice(damage_dice)
    total = sum(rng.randint(1, sides) for _ in range(count)) + modifier
    return max(1, total)


def simulate_battle(monster1: Monster, monster2: Monster, seed=None) -> Monster:
    """Simulate a turn-based fight between two monsters and return the winner.

    Each round the monsters alternate attacking. The attacker rolls d20 plus
    their to-hit bonus against the defender's AC. On a hit, damage is rolled
    and subtracted from the defender's current HP. The first monster whose HP
    drops to 0 or below loses.

    Monsters with no attack skip their damage step but can still be killed.
    If neither monster can attack (both lack attack actions) the fight ends
    immediately using HP as a tiebreaker, with strength as a secondary
    tiebreaker and monster1 as the final fallback.

    Args:
        monster1: First combatant (attacks first each round).
        monster2: Second combatant.
        seed: RNG seed for reproducibility. Same seed always produces the same
              outcome. Pass None for a non-reproducible battle.

    Returns:
        The winning Monster object (always one of the two inputs).
    """
    rng = random.Random(seed)

    hps = [monster1.hp, monster2.hp]
    combatants = [monster1, monster2]

    # Fast path: neither monster can deal damage — compare stats directly.
    if monster1.attack is None and monster2.attack is None:
        return _stat_winner(monster1, monster2)

    MAX_ROUNDS = 10_000
    for _ in range(MAX_ROUNDS):
        for attacker_idx in range(2):
            defender_idx = 1 - attacker_idx
            attacker = combatants[attacker_idx]
            defender = combatants[defender_idx]

            if attacker.attack is not None:
                roll = rng.randint(1, 20) + attacker.attack.to_hit_bonus
                if roll >= defender.ac:
                    hps[defender_idx] -= _roll_damage(attacker.attack.damage_dice, rng)
                    if hps[defender_idx] <= 0:
                        return attacker

    # Fallback if nobody dropped to 0 (e.g. one side can't attack and the
    # attacker keeps missing for 10 000 rounds — pathologically unlikely but
    # we must not loop forever).
    if hps[0] > hps[1]:
        return monster1
    if hps[1] > hps[0]:
        return monster2
    return _stat_winner(monster1, monster2)


def _stat_winner(monster1: Monster, monster2: Monster) -> Monster:
    """Break a tie using HP then strength, defaulting to monster1."""
    if monster1.hp > monster2.hp:
        return monster1
    if monster2.hp > monster1.hp:
        return monster2
    if monster1.strength >= monster2.strength:
        return monster1
    return monster2
