#!/usr/bin/env python3
from collections import Counter
from pathlib import Path
import argparse
import datetime
import json
import os

CONFIGURED = {
    340726: 16,
    342430: 107,
    352016: 32,
    206273: 28,
    213177: 34,
    209304: 24,
    213675: 17,
    213499: 15,
    328155: 16,
    332405: 16,
    351932: 16,
    283865: 8,
    348145: 8,
    348000: 6,
}
ORDINARY_BINARIES = {"fixed_hybrid_three_cached_b200", "fixed_exact", "fixed_87_first_added_test", "fixed_lower_bound"}


def snapshot():
    ordinary = []
    servers = []
    children = Counter()
    candidates = {}
    for directory in Path("/proc").iterdir():
        if not directory.name.isdigit():
            continue
        try:
            stat = (directory / "stat").read_text().split()
            command = [part.decode() for part in (directory / "cmdline").read_bytes().split(b"\0") if part]
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        if not command:
            continue
        name = os.path.basename(command[0])
        running = stat[2][0] != "T"
        item = {
            "pid": int(directory.name),
            "ppid": int(stat[3]),
            "state": stat[2],
            "start": stat[21],
        }
        if len(command) >= 7 and name in ORDINARY_BINARIES and command[1:3] in (["5", "86"], ["5", "87"]):
            item["coordinate"] = list(map(int, command[1:7]))
            item["full_coordinate"] = list(map(int, command[1:]))
            item["claim_coordinate"] = list(item["full_coordinate"])
            if name in {"fixed_87_first_added_test", "fixed_lower_bound"}:
                try:
                    fields = (directory / "environ").read_bytes().split(b"\0")
                    environment = {key.decode(): value.decode()
                                   for field in fields if field.startswith(b"FIRST_ADDED")
                                   for key, value in [field.split(b"=", 1)]}
                    lower = int(environment.get("FIRST_ADDED_MIN", environment.get("FIRST_ADDED", "0")))
                    upper = int(environment.get("FIRST_ADDED_MAX", environment.get("FIRST_ADDED", "0")))
                    item["first_added_range"] = [lower, upper]
                except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError):
                    item["first_added_range"] = ["unavailable"]
                item["claim_coordinate"] += item["first_added_range"]
            ordinary.append(item)
            if running:
                children[item["ppid"]] += 1
        if len(command) >= 3 and (name.startswith("fixed_server_") or name in {
                "fixed_multislot_server", "fixed_multislot_trace_server",
                "fixed_multislot_trace_cpu_server", "fixed_split_first_server",
                "fixed_split_first_gpu_safe", "fixed_split_second_server", "fixed_split_third_server"}):
            item["n_k"] = command[1:3]
            servers.append(item)
    for pid in CONFIGURED:
        try:
            stat = Path(f"/proc/{pid}/stat").read_text().split()
            command = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode()
        except FileNotFoundError:
            candidates[pid] = {"state": "gone"}
            continue
        candidates[pid] = {
            "state": stat[2],
            "start": stat[21],
            "cmd": command,
            "active_children": children[pid],
        }
    active = [item for item in ordinary if item["state"][0] != "T"]
    running_servers = [item for item in servers if item["state"][0] != "T"]
    total = len(active) + len(running_servers)
    eligibility = {}
    for pid, item in candidates.items():
        if item["state"] != "T":
            continue
        waiting = CONFIGURED[pid] - item["active_children"]
        eligibility[str(pid)] = {
            "worst_new": waiting,
            "after_worst": total + waiting,
            "threshold_eligible": total <= 260 and total + waiting <= 280,
        }
    return {
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_nonpaused": total,
        "ordinary_active": len(active),
        "servers": len(running_servers),
        "by_target_r": dict(Counter(f"{item['coordinate'][1]}_r{item['coordinate'][2]}" for item in active)),
        "stopped_ordinary": len(ordinary) - len(active),
        "stopped_servers": len(servers) - len(running_servers),
        "active_coordinates": [item["coordinate"] for item in active],
        "active_full_coordinates": [item["full_coordinate"] for item in active],
        "active_first_added_ranges": {str(item["pid"]): item["first_added_range"]
                                      for item in active if "first_added_range" in item},
        "duplicate_active_coordinates": [list(coord) for coord, count in Counter(
            tuple(item["claim_coordinate"]) for item in active).items() if count > 1],
        "candidates": candidates,
        "eligibility": eligibility,
        "found86": Path("logs/found86.log").exists(),
        "found87": Path("logs/found87.log").exists(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    report = snapshot()
    text = json.dumps(report, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text)
        print(json.dumps({key: value for key, value in report.items() if key != "active_coordinates"}, indent=2))
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
