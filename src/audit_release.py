#!/usr/bin/env python3
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = {"4": 14, "5": 155, "6": 338, "7": 386, "8": 658,
            "9": 574, "10": 436, "11": 314, "12": 207, "13": 27,
            "14": 0, "15": 0, "16": 0, "17": 0}
ACCEPTED = {"gpu-exact-block-v3", "cpu-gpu-two-v1", "cpu-gpu-three-v1",
            "depth3-block-v3", "depth4-block-v3"}


def sha(name):
    return sha256((ROOT / name).read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text())


def uncovered(name):
    return {tuple(map(int, line.split()[1:])) for line in (ROOT / name).read_text().splitlines()
            if line.startswith("uncovered_parent ")}


def check(name, condition):
    if not condition:
        raise AssertionError(name)


def harmonic_bound(n, k):
    h = [Fraction()] * (2 * k + 2)
    for a in range(1, len(h)):
        h[a] = h[a - 1] + Fraction(1, a)
    prefix = 0
    for a in range(1, k + 1):
        if h[k + 1] - Fraction(1, a) < n:
            prefix = a
        else:
            break
    delta = h[k] - n
    removed = Fraction()
    for r in range(1, k - prefix + 1):
        removed += Fraction(1, k - r + 1)
        if removed > delta + h[k + r] - h[k]:
            return prefix, r - 1
    return prefix, k - prefix


def main():
    for n, k, prefix, rmax in ((3, 12, 5, 3), (4, 31, 17, 5), (4, 32, 11, 7),
                               (5, 83, 71, 3), (5, 84, 38, 9), (5, 85, 26, 13),
                               (5, 86, 20, 16), (5, 87, 16, 19)):
        check("harmonic bound", harmonic_bound(n, k) == (prefix, rmax))
    three = list(range(1, 11)) + [15, 230, 57960]
    four = list(range(1, 29)) + [30, 34, 100, 11934, 14536368]
    for n, values, count in ((3, three, 13), (4, four, 33)):
        check("distinct small representation", len(values) == len(set(values)) == count)
        check("exact small sum", sum((Fraction(1, a) for a in values), Fraction()) == n)
    print("PASS: exact harmonic bounds and the 13-term/33-term representations")

    construction = load("logs/construct89_emath.json")
    base = list(range(1, 61))
    base += [a for a in range(61, 81) if any(a % d == 0 for d in range(2, a))]
    base += [81, 84, 88, 90, 92, 96, 98, 99, 100]
    base.remove(96)
    tail = [82, 162, 76368, 1821627808, 323912070702990, 1848221296482496]
    denominators = base + tail
    check("89-term definition", sorted(denominators) == construction["denominators"])
    check("89 distinct terms", len(denominators) == len(set(denominators)) == 89)
    check("89-term exact sum", sum((Fraction(1, a) for a in denominators), Fraction()) == 5)
    print("PASS: the explicit 89-term representation sums to 5")

    for name in ("logs/coverage85_cpu_only.log", "logs/r9_depth4_complete_coverage86.log"):
        text = (ROOT / name).read_text()
        check(name + " zero uncovered", "uncovered branches: 0" in text)
        check(name + " no representation", "representations found: []" in text)
    audit86 = (ROOT / "logs/r9_depth4_complete_audit.log").read_text()
    check("86 final child audit", '"accepted_children": 118' in audit86)
    check("86 final parent audit", '"verified_closed_parents": 9' in audit86)
    check("86 final audit valid", '"all_parents_verified": true' in audit86)
    print("PASS: archived complete 85/86-term coverage and final 86-term audit")

    audit = load("logs/independent_safe31700_audit.json")
    snapshot = load(audit["snapshot"])
    check("safe stage", audit["stage"] == 31700)
    check("safe full hash", audit["full_content_hash_audit"] and not audit["coverage_cache_used"])
    check("safe no reused coverage", not audit["independent_coverage_reused_after_completed_run"])
    check("safe verified logs", audit["verified_safe_logs"] == audit["unique_verified_log_paths"] == 276997)
    check("safe counts", audit["by_r"] == snapshot["uncovered_by_r"] == EXPECTED)
    check("safe total", audit["uncovered"] == snapshot["strict_uncovered_parents_current"] == sum(EXPECTED.values()) == 3109)
    check("safe bounds", snapshot["S5_bounds"] == [87, 89])
    check("safe unfinished", not snapshot["global_87_exclusion_complete"])
    check("safe no representations", not snapshot["found87"] and not snapshot["found88"] and not audit["representations_found"])
    check("safe snapshot digest", sha(audit["snapshot"]) == audit["snapshot_sha256"])
    check("safe coverage digest", sha(audit["independent_coverage"]) == audit["independent_coverage_sha256"])
    check("safe production coverage digest", sha(snapshot["coverage"]) == snapshot["coverage_sha256"])
    check("safe no stale conclusions", snapshot["valid"] and audit["valid"])
    print("PASS: safe31700 independent audit, snapshot, bounds, counts and digests")

    latest = load("logs/independent_safe31990_audit.json")
    latest_snapshot = load(latest["snapshot"])
    latest_expected = dict(EXPECTED, **{"9": 573, "10": 434, "11": 310, "12": 206})
    check("latest stage", latest["stage"] == 31990)
    check("latest full hash", latest["full_content_hash_audit"] and not latest["coverage_cache_used"])
    check("latest no reused coverage", not latest["independent_coverage_reused_after_completed_run"])
    check("latest verified logs", latest["verified_safe_logs"] == latest["unique_verified_log_paths"] == 277076)
    check("latest counts", latest["by_r"] == latest_snapshot["uncovered_by_r"] == latest_expected)
    check("latest total", latest["uncovered"] == latest_snapshot["strict_uncovered_parents_current"] == sum(latest_expected.values()) == 3101)
    check("latest snapshot digest", sha(latest["snapshot"]) == latest["snapshot_sha256"])
    check("latest coverage digest", sha(latest["independent_coverage"]) == latest["independent_coverage_sha256"])
    check("latest unfinished", not latest["global_87_exclusion_complete"] and not latest["representations_found"])
    check("latest no representations", latest_snapshot["valid"] and not latest_snapshot["found87"] and not latest_snapshot["found88"])

    campaign = load("logs/campaign_summary.json")
    check("campaign latest checkpoint", campaign["latest_independent_checkpoint"]["stage"] == 31990)
    check("campaign latest counts", campaign["latest_independent_checkpoint"]["verified_safe_logs"] == 277076 and campaign["latest_independent_checkpoint"]["uncovered"] == 3101)
    check("campaign audit window", campaign["continuous_audit_window"]["additional_verified_logs"] == 241 and campaign["continuous_audit_window"]["parent_reduction"] == 17)
    check("campaign no total time", not campaign["time_accounting"]["total_cpu_hours_known"] and not campaign["time_accounting"]["total_gpu_hours_known"])
    check("campaign no percentage", not campaign["time_accounting"]["meaningful_global_percentage_known"] and not campaign["time_accounting"]["completion_estimate_available"])
    check("campaign stage not seconds", not campaign["time_accounting"]["stage_numbers_are_seconds"] and not campaign["time_accounting"]["remaining_parents_are_candidate_counts"])
    check("campaign long r4 log", "seconds=168442 result=no" in (ROOT / "logs/fixed87_depth3/r4_x77_y79_z85.log").read_text())
    check("campaign long r10 log", "seconds=43997 result=no" in (ROOT / "logs/fixed86_depth3/r10_x67_y69_z70.log").read_text())
    print("PASS: safe31990 independent audit and campaign time accounting")

    inventory = load("logs/uncovered_parents_safe31700.json")
    parents = [tuple(x) for x in inventory["uncovered_parents"]]
    check("inventory count", inventory["uncovered_count"] == len(parents) == len(set(parents)) == 3109)
    check("inventory ordering", parents == sorted(parents))
    check("inventory scope", inventory["scope"].endswith("not a negative certificate"))
    check("inventory counts", inventory["by_r"] == EXPECTED)
    check("inventory unfinished", not inventory["global_87_exclusion_complete"] and not inventory["representations_found"])
    for record in inventory["coverage_sources"]:
        rows = uncovered(record["coverage"])
        check("source hash", sha(record["coverage"]) == record["sha256"])
        check("source count", len(rows) == record["count"] == EXPECTED[str(record["r"])])
        check("source coordinates", rows == {x for x in parents if x[0] == record["r"]})
    check("inventory audit link", inventory["independent_coverage_sha256"] == audit["independent_coverage_sha256"])
    print("PASS: all 3109 unique uncovered parents and all ten scoped source files")

    history = load("logs/two_tail_history_safe31700_validation.json")
    check("history counts 86", history["counts"]["86"]["negative_logs"] == 236879)
    check("history counts 87", history["counts"]["87"]["negative_logs"] == 397278)
    check("history depth4 counts", history["depth4_counts"]["86"]["negative_logs"] == 206 and history["depth4_counts"]["87"]["negative_logs"] == 97)
    check("history no violations", not history["violations"])
    check("history no positives", not any(history["positive_logs"].values()) and not any(history["depth4_positive_logs"].values()))
    check("history restored", history["static_input_restored"] and history["static_history_preserved"] and history["history_atomic_write"])
    check("history digest", history["sha256"] == "ce48b523f25d7c73d99d940666e58725b45a95c885945c071602d0bc91811362")
    check("history r4 unfinished", len(history["r4_status"]["modular_pending_coordinates"]) == 4 and not history["r4_status"]["negative_certificate_created"])
    summary = load("logs/history_safe31700_summary.json")
    check("history summary counts", summary["counts"] == history["counts"] and summary["depth4_counts"] == history["depth4_counts"])
    check("history summary digest", summary["audit_sha256"] == history["sha256"])
    print("PASS: safe31700 historical audit summary and preserved-input validation")

    certificate = load("logs/r11_x51_y75_closure_safe31700.json")
    records = certificate["records"]
    check("closure coordinates", [x["coordinate"] for x in records] == [[11, 51, 75, z] for z in range(76, 80)])
    check("closure scope", certificate["parent_closed"] and not certificate["coverage_cache_used"])
    for record in records:
        text = (ROOT / record["log"]).read_text()
        check("closure log digest", sha(record["log"]) == record["log_sha256"])
        check("closure negative", "result=no" in text and "result=yes" not in text and "MULTISLOT " not in text)
        engines = [line.split("=", 1)[1].strip() for line in text.splitlines() if line.startswith("engine=")]
        check("closure engine", len(engines) == 1 and engines[0] in ACCEPTED)
    before = uncovered(certificate["previous_scoped_log"])
    after = uncovered(certificate["current_scoped_log"])
    recheck = uncovered("logs/r11_scoped_coverage_safe31700_recheck.log")
    check("closure before count", len(before) == 315)
    check("closure after count", len(after) == len(recheck) == 314)
    check("closure set relation", after < before and before - after == {(11, 51, 75)})
    check("closure recheck set", after == recheck)
    check("closure digests", sha(certificate["current_scoped_log"]) == certificate["current_scoped_sha256"])
    check("closure snapshot digest", sha(certificate["global_snapshot"]) == certificate["global_snapshot_sha256"])
    check("closure still partial", not certificate["global_87_exclusion_complete"] and not certificate["representations_found"])
    print("PASS: the four-log r11 closure, negative evidence and before/after parent sets")

    latest_inventory = load("logs/uncovered_parents_safe31990.json")
    latest_parents = [tuple(x) for x in latest_inventory["uncovered_parents"]]
    check("latest inventory count", latest_inventory["uncovered_count"] == len(latest_parents) == len(set(latest_parents)) == 3101)
    check("latest inventory ordering", latest_parents == sorted(latest_parents))
    check("latest inventory scope", latest_inventory["scope"].endswith("not a negative certificate"))
    check("latest inventory counts", latest_inventory["by_r"] == latest_expected)
    check("latest inventory unfinished", not latest_inventory["global_87_exclusion_complete"] and not latest_inventory["representations_found"])
    for record in latest_inventory["coverage_sources"]:
        rows = uncovered(record["coverage"])
        check("latest source hash", sha(record["coverage"]) == record["sha256"])
        check("latest source count", len(rows) == record["count"] == latest_expected[str(record["r"])])
        check("latest source coordinates", rows == {x for x in latest_parents if x[0] == record["r"]})
    check("latest inventory audit link", latest_inventory["independent_coverage_sha256"] == latest["independent_coverage_sha256"])
    print("PASS: all 3101 unique uncovered parents at safe31990 and all ten scoped sources")

    later_closures = [
        (11, 52, 54, 31780, 314, 313, 3108),
        (11, 51, 71, 31880, 313, 312, 3107),
        (11, 51, 73, 31910, 312, 311, 3106),
        (9, 45, 61, 31940, 574, 573, 3105),
        (11, 51, 74, 31970, 311, 310, 3103),
        (10, 64, 75, 31970, 436, 435, 3103),
        (10, 46, 59, 31980, 435, 434, 3102),
        (12, 57, 73, 31990, 207, 206, 3101),
    ]
    for r, x, y, stage, previous_count, current_count, global_count in later_closures:
        name = f"logs/r{r}_x{x}_y{y}_closure_safe{stage}.json"
        certificate = load(name)
        parent = [r, x, y]
        check("later closure valid", certificate["valid"] and certificate["parent_closed"])
        check("later closure parent", certificate["parent"] == parent)
        check("later closure baseline", certificate["previous_layer_uncovered_parents"] == previous_count)
        before = uncovered(certificate["previous_scoped_log"])
        after = uncovered(certificate["current_scoped_log"])
        check("later closure before count", len(before) == previous_count)
        check("later closure after count", len(after) == current_count == certificate["current_layer_uncovered_parents"])
        check("later closure set relation", after < before and before - after == {tuple(parent)})
        check("later closure global count", certificate["global_uncovered_parents"] == global_count)
        check("later closure unfinished", not certificate["global_87_exclusion_complete"] and not certificate["representations_found"])
        records = certificate["records"]
        check("later closure z range", [item["coordinate"] for item in records] == [[r, x, y, z] for z in range(y + 1, 87 - r + 4)])
        for item in records:
            text = (ROOT / item["log"]).read_text()
            check("later closure log hash", sha(item["log"]) == item["log_sha256"])
            check("later closure negative", "result=no" in text and "result=yes" not in text and "MULTISLOT " not in text)
            engines = [line.split("=", 1)[1].strip() for line in text.splitlines() if line.startswith("engine=")]
            check("later closure engine", len(engines) == 1 and engines[0] in ACCEPTED)
        recheck = load(f"logs/r{r}_closures_safe{stage}_recheck.json")
        check("later recheck valid", recheck["valid"] and recheck["verified_existing"])
        check("later recheck parent", recheck["closed_parents"] == [parent])
        check("later recheck count", recheck["accepted_coordinate_count"] == len(records))
        check("later recheck sets", uncovered(recheck["coverage"]) == after)
        check("later original coverage hash", sha(certificate["current_scoped_log"]) == certificate["current_scoped_sha256"])
        check("later recheck coverage hash", sha(recheck["coverage"]) == recheck["coverage_sha256"])
    print("PASS: all eight closures from safe31780 through safe31990 with 94 original negative logs")

    fallback = load("logs/two_tail_forced_fallback_summary.json")
    check("forced fallback positive", fallback["positive"]["a"] == 28 and fallback["positive"]["b"] == 52 and fallback["positive"]["exact_rational_verified"])
    check("forced fallback certificate", fallback["positive"]["certificate"] == "1/28+1/52=5/91")
    check("forced fallback negative", fallback["negative"]["result"] == "NO exact (exhaustive CPU fallback)")
    check("forced fallback scope", fallback["curated_paths_replaced_with_original_hashes"] and not fallback["original_files_modified"])
    ratio_host = (ROOT / "logs/three_pair_ratio_host_test.log").read_text()
    ratio_regression = (ROOT / "logs/three_pair_ratio_regression.log").read_text()
    check("ratio host regression", "wide_cases=20736 failures=0" in ratio_host and "lost_solutions=0" in ratio_host)
    check("ratio GPU regression", "tasks=2404 positives=655 negatives=1749 fallbacks=0" in ratio_regression and "ALL THREE-PAIR-LIFT REGRESSIONS PASSED" in ratio_regression)
    print("PASS: curated forced-fallback and three-pair regression evidence")

    local_names = ("search88_v89_six_complete_audit", "search88_v90_five_complete_audit",
                   "search88_swap89_full5_complete_audit", "construct88_tail60_complete_audit",
                   "audit89_pair_triple_merges", "search88_three_to_two_complete_audit",
                   "search88_three_to_two_reconciliation", "search88_split_merge_neighbors",
                   "search88_two_split_neighbors", "search88_sequential_split_neighbors",
                   "search88_base_pair_swaps", "search88_base_pair_swaps_independent",
                   "search88_pair90_full6_complete_audit", "search88_pair90_next_valid2_audit",
                   "search88_pair90_69_75_audit", "search88_pair90_1_2_audit", "search88_pair90_3_4_audit")
    for name in local_names:
        local = load("logs/" + name + ".json")
        check("local family valid: " + name, local["valid"])
        check("local only: " + name, not local["global_88_nonexistence_claimed"])
        check("local no representations: " + name, not local.get("representations", []))
        check("local no found88: " + name, not local.get("found88", False))
        check("local no found87: " + name, not local.get("found87", False))
    merges = load("logs/merge89_independent_recheck.json")
    check("merge counts", merges["checked_pairs"] == 3916 and merges["checked_triples"] == 113564)
    check("merge duplicates", merges["pair_duplicates_rejected"] == 58 and merges["triple_duplicates_rejected"] == 214)
    check("merge no valid representation", not merges["valid_88_merges"] and not merges["valid_87_merges"])
    check("merge source digest", merges["source_sha256"] == sha("logs/construct89_emath.json"))
    base_pairs = load("logs/base_pairs89_independent_recheck.json")
    check("base pair counts", base_pairs["checked_base_pairs"] == base_pairs["two_denominator_solutions"] == base_pairs["solutions_returning_to_original"] == 3403)
    check("base pair no new state", base_pairs["unique_new_89_states"] == 0 and not base_pairs["representations_88"])
    check("base pair source digest", base_pairs["source_sha256"] == sha("logs/construct89_emath.json"))
    source_rechecks = load("logs/construct88_source_rechecks.json")
    check("source reruns valid", source_rechecks["valid"] and source_rechecks["all_reports_complete_local_only"])
    check("source reruns no global claim", not source_rechecks["global_88_nonexistence_claimed"] and not source_rechecks["representations_found"])
    check("source rerun family count", len(source_rechecks["checks"]) == 5)
    for entry in source_rechecks["checks"]:
        check("source rerun valid entry", entry["valid"] and entry["expected_fields"])
        check("source rerun report exists", (ROOT / entry["report"]).is_file())
    print("PASS: all named local 88-term families and independent merge/base-pair rechecks")
    print("PASS: five fresh-workspace construction source reruns")

    model_terms = ("b" + "200", "h" + "200", "a" + "100", "h" + "100", "r" + "tx", "xe" + "on", "ep" + "yc")
    path_terms = ("sujian" + "lin", "moon" + "fs")
    forbidden = re.compile(r"(?i)\b(?:" + "|".join(model_terms + path_terms) + r")\b|/(?:home|data|mnt)/")
    for path in ROOT.rglob("*"):
        if path == Path(__file__) or path.is_symlink() or not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() in {".md", ".json", ".py", ".cpp", ".cu", ".hpp", ".log", ".txt", ".cff"} or path.name in {"Makefile", "requirements.txt"}:
            check("hardware/path redaction: " + str(path.relative_to(ROOT)), not forbidden.search(path.read_text(errors="replace")))
    print("PASS: no specific hardware models or personal machine paths in the curated release")
    print("RELEASE_AUDIT_OK")


if __name__ == "__main__":
    main()
