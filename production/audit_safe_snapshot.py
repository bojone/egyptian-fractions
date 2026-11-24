#!/usr/bin/env python3
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parent
ACCEPTED = ("engine=gpu-exact-block-v3", "engine=cpu-gpu-two-v1",
            "engine=cpu-gpu-three-v1", "engine=depth3-block-v3", "engine=depth4-block-v3")
WITHDRAWN = ("engine=cpu-gpu-pair-candidate-v1", "engine=cpu-gpu-triple-candidate-v1",
             "engine=cpu-gpu-quad-candidate-v1", "engine=gpu-exact-wide")


def load(name):
    return json.loads((ROOT / name).read_text())


def digest(name):
    return hashlib.sha256((ROOT / name).read_bytes()).hexdigest()


def tail(name):
    with (ROOT / name).open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(max(0, size - 65536))
        return stream.read().decode(errors="replace")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", type=int)
    parser.add_argument("--continuous", default="logs/safe_continuous_8340_9990.jsonl")
    args = parser.parse_args()
    records = [json.loads(line) for line in (ROOT / args.continuous).read_text().splitlines() if line]
    selected = [record for record in records if record["stage"] == args.stage]
    assert len(selected) == 1 and selected[0]["valid"]
    record = selected[0]
    snapshot_name = record["snapshot"]
    snapshot = load(snapshot_name)
    assert snapshot["valid"] and not snapshot["global_87_exclusion_complete"]
    assert snapshot["S5_bounds"] == [87, 89] and not snapshot["found87"] and not snapshot["found88"]
    assert digest(snapshot_name) == record["snapshot_sha256"]
    assert snapshot["strict_uncovered_parents_current"] == record["uncovered"]
    assert snapshot["uncovered_by_r"] == record["by_r"]
    assert sum(record["by_r"].values()) == record["uncovered"]
    assert snapshot["coverage"] == f"logs/goal87_safe{args.stage}.log"
    assert digest(snapshot["coverage"]) == snapshot["coverage_sha256"]
    assert digest(snapshot["audit_report"]) == snapshot["audit_report_sha256"]
    assert digest(snapshot["coverage_cache"]) == snapshot["coverage_cache_sha256"]
    audit = load(snapshot["audit_report"])
    assert not audit["violations"] and not audit["positive_logs"]["86"] and not audit["positive_logs"]["87"]
    assert audit["no_engine_log_names"] == {"86": [], "87": []}
    assert audit["counts"]["87"]["new_negative_logs"] == record["new_negative_logs"]
    assert audit["counts"]["86"]["new_negative_logs"] == 0
    mapping_name = snapshot["verified_owner_mapping"]
    mapping = load(mapping_name)
    assert mapping_name == f"logs/safe{args.stage}_verified_safe_owners.json"
    for owner in ("834989", "835248", "834298", "831073"):
        report = load(mapping[owner])
        assert report["valid"] and str(report["owner"]) == owner
        assert report["engine_kind"] == "corrected_product_max_v1"
    approved = {}
    accepted = 0
    report_summaries = {}
    for owner, report_name in mapping.items():
        report = load(report_name)
        assert report["valid"] and str(report["owner"]) == owner and not report["representations"]
        assert report["accepted_negatives"] == len(report["records"])
        assert digest(report["server"]) == report["server_sha256"]
        assert load(report["engine_regression"])["valid"]
        assert len(report["pending_coordinates"]) == len(set(map(tuple, report["pending_coordinates"])))
        pending = set(map(tuple, report["pending_coordinates"]))
        for item in report["records"]:
            coordinate = tuple(item["coordinate"])
            r, x, y, z = coordinate
            assert coordinate not in pending and r == report["r"]
            name = f"logs/fixed87_depth3/r{r}_x{x}_y{y}_z{z}.log"
            assert item["log"] == name
            sha256 = digest(name)
            assert sha256 == item["log_sha256"]
            text = tail(name)
            assert "result=no" in text and "result=yes" not in text and "MULTISLOT " not in text
            assert any(tag in text for tag in ACCEPTED), coordinate
            assert not any(tag in text for tag in WITHDRAWN), coordinate
            if name in approved:
                assert approved[name] == sha256
            approved[name] = sha256
            accepted += 1
        report_summaries[owner] = {"r": report["r"], "accepted": len(report["records"]),
                                   "pending": len(pending), "report": report_name}
    assert accepted == snapshot["verified_owner_logs"] == record["verified"]
    assert len(approved) == accepted
    coverage_log = f"logs/independent_safe{args.stage}_coverage.log"
    reuse_coverage = os.environ.get("REUSE_INDEPENDENT_COVERAGE") == "1"
    if reuse_coverage:
        result = subprocess.CompletedProcess([], 1 if record["uncovered"] else 0)
    else:
        assert not (ROOT / coverage_log).exists()
        env = dict(os.environ, VERIFIED_SAFE_OWNERS=json.dumps(mapping),
                   COVERAGE_APPROVED_CACHE="", COVERAGE_DETAIL_R="")
        env.pop("COVERAGE_APPROVED_CACHE_OUT", None)
        env.pop("COVERAGE_ONLY_R", None)
        env.pop("VERIFIED_SAFE_OWNERS_BASE", None)
        with (ROOT / coverage_log).open("x") as stream:
            result = subprocess.run(["python3", "coverage87_distinct_v1.py"], cwd=ROOT,
                                    env=env, stdout=stream, stderr=subprocess.STDOUT)
    text = (ROOT / coverage_log).read_text()
    assert result.returncode == (1 if record["uncovered"] else 0), result.returncode
    assert "coverage cache:" not in text and "representations found: []" in text
    assert f"verified_safe_logs: {accepted}" in text
    assert f"uncovered branches: {record['uncovered']}" in text
    match = re.search(r"^unverified_safe_owner_logs: (\d+)$", text, re.M)
    assert match
    independent_unverified = int(match.group(1))
    assert independent_unverified >= record["unverified_excluded"]
    by_r = {}
    for line in text.splitlines():
        match = re.fullmatch(r"r=(\d+): root exclusions (\d+)/(\d+); secondary exclusions (\d+)/(\d+); uncovered (\d+)", line)
        if match:
            by_r[match.group(1)] = int(match.group(6))
    assert all(by_r.get(str(r), 0) == count for r, count in record["by_r"].items())
    out = {"valid": True, "stage": args.stage, "uncovered": record["uncovered"],
           "by_r": record["by_r"], "snapshot": snapshot_name,
           "snapshot_sha256": record["snapshot_sha256"], "verified_safe_logs": accepted,
           "unique_verified_log_paths": len(approved),
           "snapshot_unverified_safe_owner_logs": record["unverified_excluded"],
           "unverified_safe_owner_logs_at_independent_coverage": independent_unverified,
           "new_negative_logs": record["new_negative_logs"], "owners": report_summaries,
           "full_content_hash_audit": True, "coverage_cache_used": False,
           "independent_coverage_reused_after_completed_run": reuse_coverage,
           "independent_coverage": coverage_log, "independent_coverage_sha256": digest(coverage_log),
           "representations_found": [], "global_87_exclusion_complete": False,
           "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    output = ROOT / f"logs/independent_safe{args.stage}_audit.json"
    assert not output.exists()
    output.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({key: value for key, value in out.items() if key != "owners"}, indent=2))


if __name__ == "__main__":
    main()
