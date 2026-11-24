#!/usr/bin/env python3
from fractions import Fraction
from pathlib import Path
import datetime
import hashlib
import json
import os
import random
import subprocess
import time

ROOT = Path(__file__).resolve().parent
source = json.loads((ROOT / "logs/construct89_emath.json").read_text())
initial = tuple(source["denominators"])
assert source["valid"] and len(initial) == len(set(initial)) == 89
assert sum((Fraction(1, a) for a in initial), Fraction()) == 5
seed = int(os.environ.get("WALK_SEED", "20261116"))
seconds = int(os.environ.get("WALK_SECONDS", "600"))
max_steps = int(os.environ.get("WALK_MAX_STEPS", "100000"))
rng = random.Random(seed)
started = time.monotonic()
seen = {initial}
unique89 = {initial}
best = initial
steps = 0
accepted_splits = 0
accepted_merges = 0
found = None
checkpoint_path = ROOT / "logs/search88_walk_candidates.jsonl"
checkpoint_path.write_text("")


def split_options(values):
    a = rng.choice(values)
    if a <= 256:
        candidates = [b for b in range(1, a + 1) if (a * a) % b == 0]
    else:
        candidates = [1] + [b for b in range(2, min(a, 64) + 1) if (a * a) % b == 0]
    rng.shuffle(candidates)
    for b in candidates:
        u = a + b
        v = a * u // b
        if u == v or u in values or v in values or v.bit_length() > 512:
            continue
        assert Fraction(1, a) == Fraction(1, u) + Fraction(1, v)
        return tuple(sorted((set(values) - {a}) | {u, v}))
    return None


def merge_options(values):
    pairs = []
    for i, u in enumerate(values):
        for v in values[i + 1:]:
            if v % u:
                continue
            ratio = v // u
            if u % (ratio + 1):
                continue
            a = ratio * u // (ratio + 1)
            remaining = set(values) - {u, v}
            if a <= 0 or a in remaining:
                continue
            assert Fraction(1, u) + Fraction(1, v) == Fraction(1, a)
            candidate = tuple(sorted(remaining | {a}))
            if candidate not in seen:
                pairs.append(candidate)
    rng.shuffle(pairs)
    return pairs


assert split_options([2]) == (3, 6)
assert merge_options([3, 6]) == [(2,)]
assert merge_options([2, 3, 6]) == []
current = initial
last_new89 = 0
while steps < max_steps and time.monotonic() - started < seconds and found is None:
    steps += 1
    split = split_options(list(current))
    if split is None:
        current = initial
        continue
    accepted_splits += 1
    candidates = merge_options(list(split))
    if candidates:
        current = candidates[0]
        accepted_merges += 1
    else:
        current = split
    assert len(current) == len(set(current))
    assert sum((Fraction(1, a) for a in current), Fraction()) == 5
    seen.add(current)
    if len(current) < len(best):
        best = current
    if len(current) == 89 and current not in unique89:
        unique89.add(current)
        last_new89 = steps
        with checkpoint_path.open("a") as output:
            output.write(json.dumps({"step": steps, "denominators": list(current)}) + "\n")
    if len(current) <= 88:
        assert sum((Fraction(1, a) for a in current), Fraction()) == 5
        check = subprocess.run(["python3", "verify.py", "5", *map(str, current)],
                               text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert check.returncode == 0, check.stdout
        found = {"values": list(current), "verify": check.stdout}
        (ROOT / "logs/found88.log").write_text("5 88 : " + " ".join(map(str, current)) + "\n")
        break
    if len(current) > 91 or steps - last_new89 > 200:
        current = initial
        last_new89 = steps
    if steps % 1000 == 0:
        print(json.dumps({"steps": steps, "best_terms": len(best), "unique89": len(unique89),
                          "seen": len(seen), "seconds": time.monotonic() - started}), flush=True)
    if len(unique89) >= 10000 or len(seen) >= 250000:
        break

report = {"valid": True, "scope": "Bounded heuristic split/merge walk; non-exhaustive and not a nonexistence proof",
          "seed": seed, "steps": steps, "seconds": time.monotonic() - started,
          "source_sha256": hashlib.sha256((ROOT / "logs/construct89_emath.json").read_bytes()).hexdigest(),
          "unique89": len(unique89), "seen_states": len(seen), "best_terms": len(best),
          "accepted_splits": accepted_splits, "accepted_merges": accepted_merges,
          "found": found, "checkpoint": str(checkpoint_path.relative_to(ROOT)),
          "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
(ROOT / "logs/search88_walk_summary.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2), flush=True)
