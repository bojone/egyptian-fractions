#!/usr/bin/env python3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
logs = root / "logs"
marker = "GPU candidate method failed; used exhaustive CPU fallback"
forbidden = [marker, "two_tail_divisors failure", "two-tail solver failed", "Traceback"]
old_source = root / "two_tail_divisors_pre_complete.py"
old_text = old_source.read_text()
assert "q_divisor_solve(p, q, previous, cap=None, full=True)" in old_text
assert old_text.index("q_divisor_solve(p, q, previous, cap=None, full=True)") < old_text.index(marker)
assert "if process.returncode == 0:" in old_text
assert marker not in (root / "two_tail.py").read_text()
assert "count < 0 or count > 65536 or len(lines) != count + 1" in (root / "two_tail.py").read_text()

old_direct = [
    "fixed_hybrid_three_cached_pre_divisors",
    "fixed_hybrid_three_factored_b200",
    "fixed_hybrid_three_b200",
    "fixed_hybrid_b200_benchmark",
    "fixed_hybrid_b200",
    "fixed_exact_pre_divisors",
]
helper_binaries = [
    "fixed_hybrid_three_cached_pre_tail_bsearch",
    "fixed_hybrid_three_cached_b200",
    "fixed_hybrid_three_cached_pre_ratio",
    "fixed_hybrid_three_cached_pre_coarse",
    "fixed_hybrid_three_cached_pre_three_pair",
    "fixed_hybrid_three_cached_cpu_quad",
    "fixed_hybrid_three_cached_pre_cpu_quadratic",
    "fixed_hybrid_three_cached_pre_pair_divisor",
    "fixed_hybrid_three_gcdfilter_b200",
    "fixed_hybrid_three_adaptive_b200",
    "fixed_exact_pre_tail_bsearch",
    "fixed_exact",
    "fixed_exact_pre_ratio",
    "fixed_exact_pre_three_pair",
    "fixed_exact_pre_pair_divisor",
]
binary_evidence = {}
for name in old_direct + helper_binaries + ["fixed_verified"]:
    data = (root / name).read_bytes()
    helper = b"two_tail_divisors.py" in data
    direct = b"two_tail.py" in data
    if name in old_direct:
        assert direct and not helper, name
    elif name in helper_binaries:
        assert helper and not direct, name
    else:
        assert not helper and not direct, name
    binary_evidence[name] = {
        "sha256": hashlib.sha256(data).hexdigest(),
        "calls_two_tail_divisors": helper,
        "calls_complete_gpu_solver_directly": direct,
    }

report = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "All k=86 and k=87 depth3 and split-depth4 logs at this snapshot; production may add more, so rerun at the final coverage audit.",
    "marker": marker,
    "binary_evidence": binary_evidence,
    "old_source": old_source.name,
    "old_source_sha256": hashlib.sha256(old_source.read_bytes()).hexdigest(),
    "old_gpu_solver": "two_tail.py",
    "old_gpu_solver_sha256": hashlib.sha256((root / "two_tail.py").read_bytes()).hexdigest(),
    "counts": {},
    "violations": [],
    "positive_logs": {},
}
for k in (86, 87):
    engines = Counter()
    negatives = 0
    positives = []
    for path in (logs / f"fixed{k}_depth3").glob("*.log"):
        text = path.read_text(errors="replace")
        if "result=yes" in text:
            positives.append(path.name)
        if "result=no" not in text:
            continue
        negatives += 1
        for item in forbidden:
            if item in text:
                report["violations"].append({"log": str(path.relative_to(root)), "marker": item})
        engine_lines = [line for line in text.splitlines() if line.startswith("engine=")]
        engines[engine_lines[-1] if engine_lines else "none"] += 1
    report["counts"][str(k)] = {"negative_logs": negatives, "engines": dict(engines)}
    report["positive_logs"][str(k)] = positives
    depth4_engines = Counter()
    depth4_negatives = 0
    depth4_positives = []
    depth4_directory = logs / f"fixed{k}_depth4"
    for path in depth4_directory.glob("*.log") if depth4_directory.exists() else []:
        text = path.read_text(errors="replace")
        if "result=yes" in text:
            depth4_positives.append(path.name)
        if "result=no" not in text:
            continue
        depth4_negatives += 1
        for item in forbidden:
            if item in text:
                report["violations"].append({"log": str(path.relative_to(root)), "marker": item})
        engine_lines = [line for line in text.splitlines() if line.startswith("engine=")]
        depth4_engines[engine_lines[-1] if engine_lines else "none"] += 1
    report.setdefault("depth4_counts", {})[str(k)] = {
        "negative_logs": depth4_negatives, "engines": dict(depth4_engines)}
    report.setdefault("depth4_positive_logs", {})[str(k)] = depth4_positives
report["conclusion"] = (
    "No accepted negative log at this snapshot contains the mandatory marker preceding the defective "
    "full=True fallback or another solver-error marker. The defect was reachable only after two_tail.py "
    "returned nonzero. Old-direct binaries do not contain the defective helper at all; two_tail.py checks "
    "candidate-buffer truncation instead of silently accepting it. This excludes that specific historical "
    "defect from the accepted negative evidence. It does not replace the separate coverage proof."
)
assert not report["violations"], report["violations"][:10]
path = logs / "two_tail_history_static_audit.json"
temporary = path.with_suffix(path.suffix + ".tmp")
temporary.write_text(json.dumps(report, indent=2) + "\n")
temporary.replace(path)
print(json.dumps({"counts": report["counts"], "depth4_counts": report["depth4_counts"],
                  "violations": report["violations"], "positive_logs": report["positive_logs"],
                  "depth4_positive_logs": report["depth4_positive_logs"], "output": str(path)}, indent=2))
