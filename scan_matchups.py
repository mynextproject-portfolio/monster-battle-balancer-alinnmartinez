#!/usr/bin/env python3
"""Scan all monster pairs and identify fun (competitive) matchups.

Follows the three-lever strategy from APPROACH.md:
  1. Cache monster data to disk to avoid repeated API calls.
  2. Pre-filter pairs where at least one side can never deal damage.
  3. Two-phase simulation: 50-trial pilot, full 200-trial run only for
     pairs that look close in the pilot.

Output: fun_pairs.csv sorted by balance score (closest to 50/50 first).
"""

import csv
import itertools
import json
import os

import requests
from dotenv import load_dotenv

from models.monster import Monster
from battle import win_rates, is_competitive

load_dotenv()
BASE_URL = os.getenv("DND_API_BASE_URL")
IMAGE_BASE_URL = os.getenv("DND_API_IMAGE_BASE_URL")

CACHE_FILE = "monster_cache.json"
OUTPUT_FILE = "fun_pairs.csv"

# Two-phase simulation settings
PILOT_N = 50
PILOT_CUTOFF = 0.08  # underdog rate below this in pilot → likely stomp, skip
FULL_N = 200
SEED = 0


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict) -> None:
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def _fetch_raw(index: str, cache: dict) -> dict | None:
    """Return raw API data for a monster, reading from cache when available."""
    if index in cache:
        return cache[index]
    try:
        resp = requests.get(f"{BASE_URL}/monsters/{index}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        data["full_image_url"] = f"{IMAGE_BASE_URL}{data['image']}" if data.get("image") else None
        cache[index] = data
        return data
    except Exception as e:
        print(f"  Warning: could not fetch {index}: {e}")
        return None


# ---------------------------------------------------------------------------
# Monster loading
# ---------------------------------------------------------------------------

def load_monsters() -> list[Monster]:
    """Fetch all monsters from the API, caching raw data to disk.

    On first call this hits the network for every monster. Subsequent calls
    read from monster_cache.json and are essentially instantaneous.
    """
    resp = requests.get(f"{BASE_URL}/monsters", timeout=10)
    resp.raise_for_status()
    entries = resp.json().get("results", [])

    cache = _load_cache()
    monsters = []
    total = len(entries)

    for i, entry in enumerate(entries):
        data = _fetch_raw(entry["index"], cache)
        if data is None:
            continue
        try:
            monsters.append(Monster(data))
        except ValueError:
            pass  # skip monsters that are missing required fields

        # Persist periodically so progress survives interruptions
        if (i + 1) % 50 == 0 or (i + 1) == total:
            _save_cache(cache)
            print(f"  {i + 1}/{total} monsters loaded...")

    return monsters


# ---------------------------------------------------------------------------
# Pre-filter
# ---------------------------------------------------------------------------

def can_deal_damage(attacker: Monster, defender: Monster) -> bool:
    """Return True if the attacker can ever land a hit on the defender.

    A monster with no attack action deals no damage. A monster whose best
    possible roll (natural 20 + bonus) still falls short of the defender's
    AC also deals no damage — the fight will never progress.
    """
    if attacker.attack is None:
        return False
    return (20 + attacker.attack.to_hit_bonus) >= defender.ac


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def scan_fun_pairs(monsters: list[Monster]) -> list[dict]:
    """Evaluate all unique pairs and return the fun (competitive) matchups.

    Uses the two-phase approach: 50-trial pilot to discard obvious stomps,
    200-trial full run for pairs that survive. Reuses win_rates and
    is_competitive from battle.py — no combat logic here.
    """
    pairs = list(itertools.combinations(monsters, 2))
    print(f"{len(pairs):,} pairs to evaluate.")

    fun = []
    counts = {"pre_filtered": 0, "pilot_dropped": 0, "fully_evaluated": 0}

    for i, (m1, m2) in enumerate(pairs):
        # Pre-filter: skip pairs where either side can never deal damage
        if not can_deal_damage(m1, m2) or not can_deal_damage(m2, m1):
            counts["pre_filtered"] += 1
            continue

        # Pilot: 50 sims — drop clear stomps before running the full batch
        r1, r2 = win_rates(m1, m2, n=PILOT_N, seed=SEED)
        if min(r1, r2) < PILOT_CUTOFF:
            counts["pilot_dropped"] += 1
            continue

        # Full run: 200 sims
        r1, r2 = win_rates(m1, m2, n=FULL_N, seed=SEED)
        counts["fully_evaluated"] += 1

        if is_competitive(r1, r2):
            fun.append({
                "monster1": m1.name,
                "monster2": m2.name,
                "m1_win_pct": round(r1 * 100, 1),
                "m2_win_pct": round(r2 * 100, 1),
                "balance": round(min(r1, r2) * 100, 1),
            })

        if (i + 1) % 2000 == 0:
            print(f"  {i + 1:,}/{len(pairs):,} pairs done — {len(fun)} fun matchups so far...")

    fun.sort(key=lambda x: x["balance"], reverse=True)

    print(f"\n  Pre-filtered (one side can't deal damage): {counts['pre_filtered']:,}")
    print(f"  Dropped by pilot:                           {counts['pilot_dropped']:,}")
    print(f"  Fully evaluated:                            {counts['fully_evaluated']:,}")
    print(f"  Fun matchups found:                         {len(fun)}")
    return fun


def write_csv(fun: list[dict], path: str = OUTPUT_FILE) -> None:
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["monster1", "monster2", "m1_win_pct", "m2_win_pct", "balance"]
        )
        writer.writeheader()
        writer.writerows(fun)
    print(f"Saved {len(fun)} rows to {path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Loading monsters...")
    monsters = load_monsters()
    print(f"Loaded {len(monsters)} valid monsters.\n")

    fun = scan_fun_pairs(monsters)
    write_csv(fun)
