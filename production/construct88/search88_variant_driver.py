#!/usr/bin/env python3
from fractions import Fraction
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import signal
import subprocess
import time

from scheduler_snapshot import snapshot

ROOT = Path(__file__).resolve().parent
MODES = (("v90-5", 0, 2), ("v90-5", 1, 2), ("v89-6", 0, 2), ("v89-6", 1, 2))
STATUS = ROOT / "logs/search88_variant_status.json"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(report):
    temporary = STATUS.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, indent=2) + "\n")
    os.replace(temporary, STATUS)


def base_values(version):
    values = set(range(1, 61))
    values |= {a for a in range(61, 81)
               if any(a % d == 0 for d in range(2, int(a ** 0.5) + 1))}
    values |= {81, 84, 88, 90, 92, 96, 98, 99, 100}
    if version == 89:
        values.remove(96)
    return values


def verify(path):
    text = path.read_text()
    metadata = re.findall(r"base_version=(\d+) removed_base=(\d+) target=(\d+)", text)
    tails = re.findall(r"tail_denominators=([0-9,]+)", text)
    if not metadata or not tails or "result=yes" not in text:
        raise RuntimeError(f"missing successful variant metadata in {path}")
    version, removed, target = map(int, metadata[-1])
    tail = list(map(int, tails[-1].split(",")))
    base = base_values(version)
    base.discard(removed)
    values = sorted(base | set(tail))
    if len(values) != 88 or len(set(values)) != 88:
        raise RuntimeError(f"wrong representation size at {path}: {len(values)}")
    if sum((Fraction(1, a) for a in values), Fraction()) != 5:
        raise RuntimeError(f"wrong rational sum at {path}")
    check = subprocess.run(["python3", str(ROOT / "verify.py"), "5", *map(str, values)],
                           text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if check.returncode:
        raise RuntimeError(f"verify.py rejected {path}: {check.stdout}")
    output = f"5 88 : {' '.join(map(str, values))}\n{check.stdout}"
    (ROOT / "logs/found88.log").write_text(output)
    return {
        "base_version": version, "removed_base": removed, "tail": tail,
        "denominators": values, "terms": 88, "sum": 5,
        "verification": check.stdout, "certificate": "logs/found88.log",
        "source_log": str(path.relative_to(ROOT)),
    }


def stop(processes):
    for process in processes:
        if process.poll() is None:
            process.terminate()
    deadline = time.monotonic() + 10
    for process in processes:
        try:
            process.wait(timeout=max(0.1, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


def main():
    if STATUS.exists() or (ROOT / "logs/found88.log").exists():
        raise RuntimeError("variant search output already exists")
    current = snapshot()
    if current["total_nonpaused"] + len(MODES) > 288:
        raise RuntimeError(f"insufficient slots: {current['total_nonpaused']}")
    if current["duplicate_active_coordinates"] or current["found87"]:
        raise RuntimeError("unsafe production state")
    self_test = (ROOT / "logs/search88_factor_six_self_test_variants.log").read_text()
    if "known_six_term_divisors_verified=6" not in self_test or "result=yes" not in self_test:
        raise RuntimeError("six-term self-test has not passed")
    report = {
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "running", "modes": MODES,
        "source_sha256": sha256(ROOT / "search88_factor_tail.cpp"),
        "binary_sha256": sha256(ROOT / "search88_factor_tail"),
        "driver_sha256": sha256(ROOT / "search88_variant_driver.py"),
        "active_production_before": current["total_nonpaused"],
        "constructor_workers": len(MODES),
        "local_search_only": True,
        "global_nonexistence_claimed": False,
        "found": None,
    }
    save(report)
    processes = []
    streams = []
    try:
        for mode, start, step in MODES:
            log = ROOT / f"logs/search88_{mode}_part{start}.log"
            stream = log.open("x")
            streams.append(stream)
            process = subprocess.Popen(
                ["nice", "-n", "3", str(ROOT / "search88_factor_tail"), mode, str(start), str(step)],
                cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
            processes.append((process, log))
        report["pids"] = [process.pid for process, _ in processes]
        save(report)
        pending = {process for process, _ in processes}
        returncodes = {}
        while pending:
            for process, log in processes:
                if process not in pending or process.poll() is None:
                    continue
                code = process.returncode
                returncodes[process.pid] = code
                pending.remove(process)
                if code == 0:
                    found = verify(log)
                    stop(pending)
                    for other in pending:
                        returncodes[other.pid] = "terminated_after_verified_find"
                    pending.clear()
                    report["found"] = found
                    report["status"] = "found_verified"
                    report["returncodes"] = returncodes
                    save(report)
                    print(json.dumps(report["found"], indent=2), flush=True)
                    return 0
                if code != 1:
                    raise RuntimeError(f"variant worker failed pid={process.pid} code={code}")
            if pending:
                time.sleep(0.5)
        report["status"] = "completed_without_representation"
        report["returncodes"] = returncodes
        report["note"] = "Only the enumerated base-and-factor-tail families are exhausted; no global 88-term nonexistence claim."
        save(report)
        print(json.dumps(report, indent=2), flush=True)
        return 1
    except Exception as error:
        stop([process for process, _ in processes])
        report["status"] = "failed"
        report["error"] = f"{type(error).__name__}: {error}"
        save(report)
        raise
    finally:
        for stream in streams:
            stream.close()


if __name__ == "__main__":
    raise SystemExit(main())
