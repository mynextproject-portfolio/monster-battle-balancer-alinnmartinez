# Finding Every Fun Matchup — Approach

## The scale problem

The D&D API has **334 monsters**. Every unique pair is `334 × 333 / 2 = 55,611` matchups. Running 1,000 simulations per pair (our current default) means **55.6 million `simulate_battle` calls**. At 100 simulations per pair it's still 5.6 million. Naive brute force is too slow, and the API fetch alone — one HTTP request per monster — would take several minutes just to load the data.

Two costs compound: **network** (fetching monster data) and **CPU** (running simulations). The approach below separates them and attacks each one.

---

## Lever 1 — Cache monster data

Every `get_monster_details` call is an HTTP round-trip. Fetching 334 monsters sequentially at ~300 ms each takes ~100 seconds. We only need to do that once.

**Plan:** on first run, fetch all monster details and write them to a local JSON file (e.g. `monster_cache.json`). On subsequent runs, load from disk. Cache invalidation can be manual (delete the file to refresh). This turns a 100-second network cost into a sub-second disk read for every run after the first.

---

## Lever 2 — Pre-filter before simulating

Many pairs can be ruled out as stomps before running a single simulation, using cheap checks on the raw stats we already have:

- **No attack vs. attacker** — a monster with no attack action can never deal damage; it loses 100% of the time against any monster that can hit it. No sim needed.
- **Can't hit** — if `max(d20) + attacker.to_hit_bonus < defender.ac` (i.e. `20 + bonus < ac`), the attacker literally cannot land a blow. Instant 0% win rate.
- **Extreme HP gap as a proxy** — if one monster has, say, 10× the HP of the other and a comparable attack, early-exit as a likely blowout and only confirm with a small sample.

Conservatively, no-attack filtering alone may eliminate 20–30% of pairs. The "can't hit" check is O(1) per pair and can cut more. The fewer pairs that reach simulation, the faster the full run.

---

## Lever 3 — Right-size simulations with early stopping

Not every pair needs 1,000 simulations to get a stable answer.

**Two-phase approach:**

1. **Pilot phase** — run 50 simulations per pair. If the underdog win rate is below ~8% (well below our 20% threshold), the result is already clear: it's a blowout. Skip the full run.
2. **Full phase** — for pairs where the pilot looks competitive (underdog ≥ 8%), run the remaining sims up to a total of 200. That is enough for the standard error on a 50/50 fight to be ~3.5%, well within useful precision for our display.

We don't need 1,000 sims per pair to decide fun vs. boring — 200 is plenty for a stable verdict. 1,000 is appropriate for the *single* matchup the user is looking at on the battle screen; it is overkill for a bulk scan.

**Rough estimate after all three levers:**

| Stage | Pairs remaining | Sims each | Total sim calls |
|---|---|---|---|
| All pairs | 55,611 | — | — |
| After pre-filter | ~40,000 | — | — |
| Pilot phase (50 sims) | 40,000 | 50 | 2,000,000 |
| Survive pilot (est. 30%) | ~12,000 | 150 more | 1,800,000 |
| **Total** | | | **~3.8 million** |

`simulate_battle` is pure Python with no I/O. At roughly 50 µs per call, 3.8 million calls ≈ **3 minutes**. That is a one-time offline job, not a per-user request.

---

## Scoping the monster set

As an alternative to filtering pairs, we could scope the monster set itself — e.g. only monsters that have a valid attack action and HP > 0. That alone would shrink the roster and square-root the pair count. We can decide this based on how many no-attack monsters actually exist in the API once the cache is built.

---

## Output

The job produces a single JSON file at the repo root: **`fun_matchups.json`**.

Each entry:

```json
{
  "monster1": "goblin",
  "monster2": "kobold",
  "m1_rate": 0.47,
  "m2_rate": 0.53,
  "balance": 0.47
}
```

`balance` = `min(m1_rate, m2_rate)` — the underdog's win rate, our single measure of tension. The file is sorted descending by `balance` so the closest fights come first.

The scanner itself will live in a new script (e.g. `scan_matchups.py`) that can be run from the command line independently of the app.

---

## What we are not doing yet

- Parallelism: possible speedup with `concurrent.futures` if 3 minutes proves too slow in practice, but not needed upfront.
- Database: flat JSON is sufficient for the output size we expect (a few thousand fun matchups).
- Live in-app scanning: the scan is an offline job. The app reads the results; it does not run the scan itself.
