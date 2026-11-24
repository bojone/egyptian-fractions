#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import subprocess
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=int, required=True)
    parser.add_argument("--baseline-validation", required=True)
    parser.add_argument("--static-backup", required=True)
    parser.add_argument("--continuous", required=True)
    parser.add_argument("--controller-pid", type=int, required=True)
    parser.add_argument("--wait-seconds", type=int, default=3600)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    stage = args.stage
    root = Path(__file__).resolve().parent
    os.chdir(root)
    sha = lambda data: hashlib.sha256(data).hexdigest()
    file_sha = lambda path: sha(Path(path).read_bytes())

    def atomic(path, data):
        temporary = Path(str(path) + ".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, path)

    def record_at(target):
        for line in Path(args.continuous).read_text().splitlines():
            row = json.loads(line)
            if row["stage"] == target:
                return row
        return None

    static = Path("logs/two_tail_history_static_audit.json")
    backup = Path(f"logs/two_tail_history_pre_safe{stage}_audit.json")
    archive = Path(f"logs/two_tail_history_safe{stage}_audit.json")
    validation = Path(f"logs/two_tail_history_safe{stage}_validation.json")
    driver = Path(f"logs/two_tail_history_safe{stage}_scan.log")
    for path in (backup, archive, validation, driver):
        assert not path.exists(), path
    baseline_path = Path(args.baseline_validation)
    baseline = json.loads(baseline_path.read_text())
    assert baseline["valid"] and baseline["static_input_restored"]
    assert file_sha(baseline["report"]) == baseline["sha256"]
    original = static.read_bytes()
    assert original == Path(args.static_backup).read_bytes()
    assert sha(original) == baseline["fixed_static_input_sha256"]
    assert "continue_safe_cycles.py" in Path(
        f"/proc/{args.controller_pid}/cmdline").read_bytes().decode()
    preflight = {
        "valid": True,
        "stage": stage,
        "baseline": str(baseline_path),
        "static_sha256": sha(original),
        "script_sha256": file_sha(__file__),
    }
    if args.dry_run:
        print(json.dumps(preflight, indent=2))
        return
    atomic(backup, original)
    assert backup.read_bytes() == original
    print("static_input_saved", sha(original), "comparison_report", baseline["report"], flush=True)
    row = None
    try:
        deadline = time.monotonic() + args.wait_seconds
        while (row := record_at(stage)) is None:
            assert time.monotonic() < deadline, "stage wait timeout"
            assert Path(f"/proc/{args.controller_pid}").exists(), "controller exited"
            time.sleep(2)
        assert row["valid"] and file_sha(row["snapshot"]) == row["snapshot_sha256"]
        with driver.open("x") as output:
            run = subprocess.run(["python3", "audit_two_tail_history.py"],
                                 stdout=output, stderr=subprocess.STDOUT)
        assert run.returncode == 0, run.returncode
        scanned = static.read_bytes()
        assert scanned != original, "scan did not replace fixed static input"
        report = json.loads(scanned)
        atomic(archive, scanned)
        print("scan_archived", sha(scanned), json.dumps(report["counts"]), flush=True)
    finally:
        atomic(static, original)
        assert static.read_bytes() == backup.read_bytes() == original
    assert archive.read_bytes() == scanned
    assert not report["violations"]
    for group in ("positive_logs", "depth4_positive_logs"):
        for k in ("86", "87"):
            assert not report[group][k], (group, k, report[group][k])
    for group in ("counts", "depth4_counts"):
        for k in ("86", "87"):
            assert report[group][k]["negative_logs"] >= baseline[group][k]["negative_logs"]
    modular = []
    for r, x, y, z in ((4, 73, 84, 85), (4, 76, 81, 84),
                       (4, 76, 82, 83), (4, 76, 83, 84)):
        path = Path(f"logs/fixed87_depth3/r{r}_x{x}_y{y}_z{z}.log")
        text = path.read_text() if path.exists() else ""
        assert "result=no" not in text and "result=yes" not in text
        modular.append({"coordinate": [r, x, y, z], "log_exists": path.exists(),
                        "terminal_negative": False})
    paused = [800653, 800717, 800656, 800657, 800720]
    services = [976104, 976105, 976106, 976107, 976108]

    def state(pid):
        return Path(f"/proc/{pid}/stat").read_text().split(") ", 1)[1].split()

    paused_states = {pid: state(pid) for pid in paused}
    service_states = {pid: state(pid) for pid in services}
    assert all(value[0] == "T" for value in paused_states.values()), paused_states
    assert all(value[0] not in ("T", "Z") for value in service_states.values()), service_states
    r4 = {
        "valid": True,
        "stage": stage,
        "scope": "liveness and pending-state preservation only; no coverage claim",
        "owner": 976096,
        "services": [{"pid": pid, "state": service_states[pid][0],
                      "cpu_ticks": int(service_states[pid][11])} for pid in services],
        "all_five_services_live": True,
        "modular_pending_coordinates": modular,
        "paused_controllers_and_workers": [
            {"pid": pid, "state": paused_states[pid][0], "signal_sent": False}
            for pid in paused],
        "negative_certificate_created": False,
        "coverage_accepted": False,
        "representations_found": [],
    }
    atomic(Path(f"logs/r4_liveness_safe{stage}.json"),
           (json.dumps(r4, indent=2) + "\n").encode())
    changes = {}
    for k in ("86", "87"):
        old = baseline["counts"][k]["engines"]
        new = report["counts"][k]["engines"]
        for key in set(old) | set(new):
            difference = new.get(key, 0) - old.get(key, 0)
            if difference:
                changes[key] = changes.get(key, 0) + difference
    output = {
        "valid": True,
        "scheduled_stage": stage,
        "stage_seen_before_scan": stage,
        "snapshot": row["snapshot"],
        "snapshot_sha256": row["snapshot_sha256"],
        "report": str(archive),
        "sha256": sha(scanned),
        "static_history_preserved": True,
        "history_atomic_write": True,
        "static_input_restored": True,
        "scan_report_archived_before_restore": True,
        "comparison_baseline": baseline["report"],
        "comparison_baseline_sha256": baseline["sha256"],
        "fixed_static_input_sha256": sha(original),
        "script_sha256": preflight["script_sha256"],
        "engine_label_changes_do_not_add_coverage": True,
        "driver_log": str(driver),
        "driver_returncode": run.returncode,
        "counts": report["counts"],
        "depth4_counts": report["depth4_counts"],
        "violations": report["violations"],
        "positive_logs": report["positive_logs"],
        "depth4_positive_logs": report["depth4_positive_logs"],
        "history_timestamp": report["timestamp_utc"],
        "r4_status": r4,
        f"engine_label_changes_from_safe{baseline['scheduled_stage']}": changes,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic(validation, (json.dumps(output, indent=2) + "\n").encode())
    print(json.dumps(output, indent=2), flush=True)


if __name__ == "__main__":
    main()
