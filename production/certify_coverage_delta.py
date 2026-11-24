#!/usr/bin/env python3
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parent
ACCEPTED = ("engine=gpu-exact-block-v3", "engine=cpu-gpu-two-v1",
            "engine=cpu-gpu-three-v1", "engine=depth3-block-v3", "engine=depth4-block-v3")
WITHDRAWN = ("engine=cpu-gpu-pair-candidate-v1", "engine=cpu-gpu-triple-candidate-v1",
             "engine=cpu-gpu-quad-candidate-v1", "engine=gpu-exact-wide")


def load(name):
    return json.loads((ROOT / name).read_text())


def sha256(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def tail(name):
    path = ROOT / name
    with path.open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(max(0, size - 65536))
        data = stream.read().decode(errors="replace")
    return data if "result=" in data or size <= 65536 else path.read_text()


def uncovered(name):
    return {tuple(map(int, line.split()[1:])) for line in (ROOT / name).read_text().splitlines()
            if line.startswith("uncovered_parent ")}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--r", type=int, required=True)
    parser.add_argument("--stage", type=int, required=True)
    parser.add_argument("--previous-stage", type=int, required=True)
    parser.add_argument("--previous-count", type=int, required=True)
    parser.add_argument("--continuous", required=True)
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()
    r = args.r
    stage = args.stage
    records = [json.loads(line) for line in (ROOT / args.continuous).read_text().splitlines() if line]
    selected = [record for record in records if record["stage"] == stage]
    assert len(selected) == 1 and selected[0]["valid"]
    record = selected[0]
    snapshot_name = record["snapshot"]
    snapshot = load(snapshot_name)
    assert snapshot["valid"] and sha256(snapshot_name) == record["snapshot_sha256"]
    assert snapshot["S5_bounds"] == [87, 89] and not snapshot["found87"] and not snapshot["found88"]
    assert record["uncovered"] == snapshot["strict_uncovered_parents_current"]
    assert record["by_r"] == snapshot["uncovered_by_r"]
    assert sha256(snapshot["coverage"]) == snapshot["coverage_sha256"]
    audit = load(snapshot["audit_report"])
    assert not audit["violations"] and not audit["positive_logs"]["86"] and not audit["positive_logs"]["87"]
    assert not audit["no_engine_log_names"]["86"] and not audit["no_engine_log_names"]["87"]
    current_count = record["by_r"][str(r)]
    assert args.previous_count >= current_count
    mapping = load(snapshot["verified_owner_mapping"])
    layer_verified = sum(load(name)["accepted_negatives"] for name in mapping.values() if load(name)["r"] == r)
    suffix = "_recheck" if args.verify_existing else ""
    coverage_name = f"logs/r{r}_scoped_coverage_safe{stage}{suffix}.log"
    coverage_path = ROOT / coverage_name
    assert not coverage_path.exists()
    env = dict(os.environ, VERIFIED_SAFE_OWNERS=json.dumps(mapping),
               COVERAGE_APPROVED_CACHE="", COVERAGE_DETAIL_R=str(r), COVERAGE_ONLY_R=str(r))
    env.pop("COVERAGE_APPROVED_CACHE_OUT", None)
    env.pop("VERIFIED_SAFE_OWNERS_BASE", None)
    with coverage_path.open("x") as stream:
        result = subprocess.run(["nice", "-n", "10", "python3", "coverage87_distinct_v1.py"],
                                cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
    text = coverage_path.read_text()
    assert result.returncode == (1 if current_count else 0)
    assert "coverage cache:" not in text and "representations found: []" in text
    assert f"uncovered {current_count}" in text
    assert f"verified_safe_logs: {layer_verified}" in text
    assert sum(line.startswith("uncovered_parent ") for line in text.splitlines()) == current_count
    previous_name = f"logs/r{r}_scoped_coverage_safe{args.previous_stage}.log"
    before = uncovered(previous_name)
    after = uncovered(coverage_name)
    assert len(before) == args.previous_count and len(after) == current_count and after < before
    closed = sorted(before - after)
    assert closed and len(closed) == args.previous_count - current_count
    index = {}
    for owner, report_name in mapping.items():
        report = load(report_name)
        assert report["valid"] and str(report["owner"]) == owner and not report["representations"]
        assert report["accepted_negatives"] == len(report["records"])
        pending = set(map(tuple, report["pending_coordinates"]))
        for item in report["records"]:
            coordinate = tuple(item["coordinate"])
            assert coordinate not in pending and coordinate[0] == report["r"]
            assert coordinate not in index
            index[coordinate] = item, owner, report_name
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    certificates = []
    summaries = []
    for parent in closed:
        rr, x, y = parent
        assert rr == r
        coordinates = [(r, x, y, z) for z in range(y + 1, 87 - r + 4)]
        evidence = []
        for coordinate in coordinates:
            item, owner, report_name = index[coordinate]
            name = item["log"]
            assert name == f"logs/fixed87_depth3/r{r}_x{x}_y{y}_z{coordinate[3]}.log"
            text = tail(name)
            assert sha256(name) == item["log_sha256"]
            assert "result=no" in text and "result=yes" not in text and "MULTISLOT " not in text
            assert any(tag in text for tag in ACCEPTED) and not any(tag in text for tag in WITHDRAWN)
            evidence.append({"coordinate": coordinate, "log": name, "log_sha256": item["log_sha256"],
                             "owner": owner, "owner_report": report_name})
        certificate_name = f"logs/r{r}_x{x}_y{y}_closure_safe{stage}.json"
        certificate = {"valid": True,
                       "scope": f"r{r}-only no-cache coverage difference and reconstruction linked to safe{stage}",
                       "parent": [r, x, y], "parent_closed": True, "closure_mode": "depth3_complete",
                       "previous_scope_stage": args.previous_stage, "previous_scoped_log": previous_name,
                       "previous_scoped_sha256": sha256(previous_name),
                       "previous_layer_uncovered_parents": args.previous_count,
                       "current_scoped_log": coverage_name, "current_scoped_sha256": sha256(coverage_name),
                       "current_layer_uncovered_parents": current_count, "coverage_cache_used": False,
                       "global_snapshot": snapshot_name, "global_snapshot_sha256": record["snapshot_sha256"],
                       "global_uncovered_parents": record["uncovered"], "verified_owner_logs": record["verified"],
                       "S5_bounds": [87, 89], "representations_found": [], "global_87_exclusion_complete": False,
                       "new_search_workers_started": False, "production_changed": False,
                       "closure_observed_by_stage": stage, "first_closure_stage_claimed": False,
                       "created_at": now, "records": evidence}
        if args.verify_existing:
            existing = load(certificate_name)
            assert existing["valid"] and existing["parent_closed"]
            assert existing["parent"] == [r, x, y]
            assert existing["records"] == json.loads(json.dumps(evidence))
            for key in ("previous_scope_stage", "previous_scoped_sha256", "previous_layer_uncovered_parents",
                        "current_layer_uncovered_parents", "global_snapshot",
                        "global_snapshot_sha256", "global_uncovered_parents", "verified_owner_logs"):
                assert existing[key] == certificate[key], (key, existing[key], certificate[key])
        else:
            assert not (ROOT / certificate_name).exists()
            certificates.append((certificate_name, certificate))
        summaries.append({"parent": [r, x, y], "mode": "depth3_complete", "certificate": certificate_name,
                          "accepted_coordinate_count": len(evidence), "z_values": [c[3] for c in coordinates]})
    summary_name = f"logs/r{r}_new_closures_safe{stage}_summary.json"
    summary = {"valid": True, "stage": stage, "previous_stage": args.previous_stage,
               "previous_layer_uncovered_parents": args.previous_count,
               "current_layer_uncovered_parents": current_count, "closed_parents": summaries,
               "closed_parent_count": len(closed),
               "accepted_coordinate_count": sum(item["accepted_coordinate_count"] for item in summaries),
               "scoped_coverage_log": coverage_name, "scoped_coverage_sha256": sha256(coverage_name),
               "global_snapshot": snapshot_name, "global_snapshot_sha256": record["snapshot_sha256"],
               "global_uncovered_parents": record["uncovered"], "verified_owner_logs": record["verified"],
               "S5_bounds": [87, 89], "global_87_exclusion_complete": False,
               "new_search_workers_started": False, "production_changed": False, "created_at": now}
    if args.verify_existing:
        existing = load(summary_name)
        assert existing["valid"] and existing["closed_parent_count"] == len(closed)
        assert existing["closed_parents"] == summaries
        assert existing["accepted_coordinate_count"] == summary["accepted_coordinate_count"]
    else:
        assert not (ROOT / summary_name).exists()
        certificates.append((summary_name, summary))
        for name, data in certificates:
            (ROOT / name).write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({"valid": True, "r": r, "stage": stage, "previous_stage": args.previous_stage,
                      "previous_count": args.previous_count, "current_count": current_count,
                      "closed_parents": closed, "accepted_coordinate_count": summary["accepted_coordinate_count"],
                      "coverage": coverage_name, "coverage_sha256": sha256(coverage_name),
                      "summary": summary_name, "verified_existing": args.verify_existing}, indent=2))


if __name__ == "__main__":
    main()
