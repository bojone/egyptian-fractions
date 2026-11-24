#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json
import os

root = Path(__file__).resolve().parent
logs = root / "logs"
specification = json.loads(os.environ.get("VERIFIED_SAFE_OWNERS", "{}"))
if os.environ.get("VERIFIED_SAFE_OWNERS_BASE"):
    merged = json.loads((root / os.environ["VERIFIED_SAFE_OWNERS_BASE"]).read_text())
    merged.update(specification)
    specification = merged
approved = {}
reviewed = set()
coverage_program_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
cache_name = os.environ.get("COVERAGE_APPROVED_CACHE")
cache_output_name = os.environ.get("COVERAGE_APPROVED_CACHE_OUT")
cache = {"version": 1, "coverage_program_sha256": coverage_program_sha256, "reports": {}}
if cache_name:
    cache = json.loads((root / cache_name).read_text())
    assert cache["version"] == 1 and cache["coverage_program_sha256"] == coverage_program_sha256
cache_output = {"version": 1, "coverage_program_sha256": coverage_program_sha256, "reports": {}}
cache_hits = 0
cache_misses = 0
claims_by_r = {}
coverage_only_r = int(os.environ.get("COVERAGE_ONLY_R", "0"))
assert coverage_only_r == 0 or 4 <= coverage_only_r <= 17
if coverage_only_r:
    print(f"scoped coverage only: r={coverage_only_r}; not a global coverage total", flush=True)
for owner_id, report_name in specification.items():
    report = json.loads((root / report_name).read_text())
    assert report["valid"] and str(report["owner"]) == str(owner_id)
    if coverage_only_r and report["r"] != coverage_only_r:
        continue
    if report.get("engine_kind") == "removed_fourth_gpu_v1":
        expected_candidate = "347dfcb97d22f56007968d1349d0ef1a2184e4383728be3a7cbb449d50ad8212"
        assert report["complete"] and report["r"] >= 4
        assert report["server"] == "fixed_removed_fourth_gpu"
        assert report["server_sha256"] == expected_candidate
        assert report["product_source_sha256"] == "93b4a9552f12838b54454d4ee280a4d0ebd82eb81e968d9daedbac9b19aa744e"
        assert hashlib.sha256((root / report["server"]).read_bytes()).hexdigest() == expected_candidate
        assert hashlib.sha256((root / "symdiff_removed_fourth_lower_bound.cpp").read_bytes()).hexdigest() == report["product_source_sha256"]
        regression = json.loads((root / report["engine_regression"]).read_text())
        assert regression["valid"] and regression["cases"] == 12 and regression["positives"] > 0
        assert regression["candidate_sha256"] == expected_candidate
        z = report["coordinate"][3]
        parts = sorted(report["parts"], key=lambda part: part["fourth_min"])
        previous = z
        for part in parts:
            assert part["fourth_min"] == previous + 1 and part["fourth_min"] <= part["fourth_max"] <= 77
            previous = part["fourth_max"]
            assert part["sha256"] == expected_candidate and part["server_returncode"] == 0
            assert part["returncode"] == 1 and part["pid"] > 0 and part["start_time_ticks"] > 0
            assert hashlib.sha256((root / part["log"]).read_bytes()).hexdigest() == part["log_sha256"]
            text = (root / part["log"]).read_text()
            assert "result=no" in text and "result=yes" not in text
            assert f"JOB_END {part['index']} code=1" in text
        assert previous == 87 - report["r"] + 4
        source = json.loads((root / report["source"]).read_text())
        assert source["valid_launch"] and source["r"] == report["r"]
        assert source["workers"] == len(source["services"]) >= 1
        assert report["original_services"] == source["services"]
        assert report["original_superseded_states"] == ["T"] * (source["workers"] + 1)
        for service in source["services"]:
            stat = Path(f"/proc/{service['pid']}/stat").read_text().split()
            assert int(stat[21]) == service["start_time_ticks"] and stat[2][0] == "T"
            assert hashlib.sha256(Path(f"/proc/{service['pid']}/exe").read_bytes()).hexdigest() == service["sha256"]
        driver = report["original_driver"]
        assert driver["pid"] == source["owner"]
        stat = Path(f"/proc/{driver['pid']}/stat").read_text().split()
        assert int(stat[21]) == driver["start_time_ticks"] and stat[2][0] == "T"
        if report.get("original_prepaused"):
            prior = json.loads((root / report["prepaused_evidence"]).read_text())
            assert prior["valid"] and prior["complete"] and prior["source"] == report["source"]
            assert prior["original_services"] == source["services"]
            assert prior["original_driver"] == driver
            assert prior["original_superseded_states"] == report["original_superseded_states"]
        assert (root / report["claim"] / "owner").read_text().startswith(f"pid={report['owner']} ")
        assert report["claim_original_owner"].startswith(f"pid={source['owner']} ")
        donor_source = json.loads((root / report["donor_source"]).read_text())
        assert donor_source["valid_launch"] and len(report["donors"]) == 1
        assert report["donors"] == [donor_source["services"][report.get("donor_index", 0)]]
        assert len(report["donor_resumed_states"]) == 1
        donor = report["donors"][0]
        assert report["donor_resumed_states"][0][0] in ("R", "S", "D")
        process = Path(f"/proc/{donor['pid']}")
        if process.exists():
            stat = (process / "stat").read_text().split()
            assert int(stat[21]) == donor["start_time_ticks"] and stat[2][0] in ("R", "S", "D")
            assert hashlib.sha256((process / "exe").read_bytes()).hexdigest() == donor["sha256"]
        assert report["scheduler_after"]["total_nonpaused"] <= 288
        assert not report["scheduler_after"]["duplicate_active_coordinates"] and not report["scheduler_after"]["found87"]
    elif report.get("engine_kind") in ("split_first_gpu_safe_nested_v1", "split_first_gpu_safe_grouped_v1"):
        expected_candidate = "56b53bc59da17559bb7cd4194a653c505c5bd5998bd1591e748ae0f1ac92ebdc"
        assert report["complete"] and report["r"] == 4
        assert report["server"] == "fixed_split_first_gpu_safe"
        assert report["server_sha256"] == expected_candidate
        assert report["product_source_sha256"] == "0b96a324f0d7ff397a32dea784abf051e3f2130e1725fad80a182be69fb61671"
        assert hashlib.sha256((root / report["server"]).read_bytes()).hexdigest() == expected_candidate
        assert hashlib.sha256((root / "symdiff_split_first_lower_bound.cpp").read_bytes()).hexdigest() == report["product_source_sha256"]
        regression = json.loads((root / report["candidate_regression"]).read_text())
        assert regression["valid"] and regression["cases"] == 54 and regression["positives"] == 4
        assert regression["mismatches"] == 0 and regression["candidate_sha256"] == expected_candidate
        assert regression["source_sha256"] == report["product_source_sha256"]
        initial = json.loads((root / "logs/split_first_gpu_safe_initial.json").read_text())
        assert initial["valid"] and initial["binary_sha256"] == expected_candidate
        base = json.loads((root / report["base_report"]).read_text())
        assert not base["valid"] and not base.get("complete")
        assert base["owner"] == report["claim_replaced_owner"]
        assert base["coordinate"] == report["coordinate"]
        external = report.get("external_alternative")
        if external is None:
            assert base["server"] == report["server"] and base["server_sha256"] == expected_candidate
            assert base["engine_kind"] == "split_first_gpu_safe_all_v1"
        else:
            assert base["server"] == "fixed_split_first_server"
            assert base["server_sha256"] == "9655e2aab189d53c5325cd9a553ee9a0e83a88304ff21446a52184ee8ba9c579"
            assert base["engine_kind"] == "split_first_intervals_v1"
        assert report.get("outer_server_sha256", base["server_sha256"]) == base["server_sha256"]
        assert base["source"] == report["source"]
        index = report["replacement_index"]
        original = report["original_part"]
        if external is None:
            assert original == base["parts"][index]
        else:
            old = report["base_original_part"]
            assert old == base["parts"][index] == external["original_part"]
            for key in ("index", "first_min", "first_max", "log"):
                assert original[key] == old[key]
            assert original["pid"] == external["candidate_pid"]
            assert original["start_time_ticks"] == external["candidate_start_time_ticks"]
            old_stat = Path(f"/proc/{old['pid']}/stat").read_text().split()
            assert int(old_stat[21]) == old["start_time_ticks"] and old_stat[2][0] == "T"
            assert hashlib.sha256(Path(f"/proc/{old['pid']}/exe").read_bytes()).hexdigest() == old["sha256"]
            assert external["controller"] == base["owner"] and external["candidate_sha256"] == expected_candidate
            assert hashlib.sha256((root / external["original_partial_log"]).read_bytes()).hexdigest() == external["original_partial_log_sha256"]
            watchdog = report["external_watchdog"]
            assert watchdog["valid"] and watchdog["controller_paused"]
            assert watchdog["controller"] != external["controller"] and watchdog["candidate"] == original["pid"]
            controller_stat = Path(f"/proc/{watchdog['controller']}/stat").read_text().split()
            assert int(controller_stat[21]) == watchdog["controller_start_time_ticks"] and controller_stat[2][0] == "T"
            assert report["external_alternative_states"] == {"controller": "T", "original_cpu_part": "T"}
        original_stat = Path(f"/proc/{original['pid']}/stat").read_text().split()
        assert int(original_stat[21]) == original["start_time_ticks"] and original_stat[2][0] == "T"
        assert hashlib.sha256(Path(f"/proc/{original['pid']}/exe").read_bytes()).hexdigest() == expected_candidate
        assert original["index"] == index and "returncode" not in original
        assert hashlib.sha256((root / report["original_partial_log"]).read_bytes()).hexdigest() == report["original_partial_log_sha256"]
        partial = (root / report["original_partial_log"]).read_text()
        assert "result=no" not in partial and "result=yes" not in partial
        completed = {part["index"]: part for part in report["completed_outer_parts"]}
        assert set(completed) == set(range(len(base["parts"]))) - {index}
        previous = 87
        for i, old in enumerate(base["parts"]):
            part = original if i == index else completed[i]
            if i != index:
                assert part == old
                assert part["sha256"] == report.get("outer_server_sha256", expected_candidate) and part["server_returncode"] == 0
                assert part["returncode"] == 1 and part["pid"] > 0 and part["start_time_ticks"] > 0
                assert hashlib.sha256((root / part["log"]).read_bytes()).hexdigest() == part["log_sha256"]
                text = (root / part["log"]).read_text()
                assert "result=no" in text and "result=yes" not in text
                assert f"JOB_END {i} code=1" in text
            assert part["first_min"] == previous + 1 and part["first_min"] <= part["first_max"]
            previous = part["first_max"]
        assert previous == (1 << 64) - 1
        partition = report["contiguous_partition"]
        assert partition["first_min_inclusive"] == original["first_min"]
        assert partition["last_max_inclusive"] == original["first_max"]
        grouped = report["engine_kind"] == "split_first_gpu_safe_grouped_v1"
        if grouped:
            parts = sorted(report["reused_parts"] + report["singleton_parts"],
                           key=lambda part: part["first_min"])
            assert partition["intervals"] == [[part["first_min"], part["first_max"]] for part in parts]
            assert report["completed_denominators"] == report["coverage_denominator_count"] == original["first_max"] - original["first_min"] + 1
            assert report["completed_singletons"] == report["singleton_count"] == len(parts)
            assert 1 <= report["group_size"] <= 8192
            previous = original["first_min"] - 1
            for part in parts:
                assert part["first_min"] == previous + 1 and part["first_min"] <= part["first_max"]
                previous = part["first_max"]
            assert previous == original["first_max"]
        else:
            assert partition["intervals"] == [[a, a] for a in range(original["first_min"], original["first_max"] + 1)]
            parts = report["singleton_parts"]
            assert len(parts) == original["first_max"] - original["first_min"] + 1
        for part in parts:
            i = part["index"]
            if not grouped:
                assert i == parts.index(part) and part["first_min"] == part["first_max"] == original["first_min"] + i
            assert part["sha256"] == expected_candidate and part["server_returncode"] == 0
            assert part["returncode"] == 1 and part["pid"] > 0 and part["start_time_ticks"] > 0
            assert hashlib.sha256((root / part["log"]).read_bytes()).hexdigest() == part["log_sha256"]
            text = (root / part["log"]).read_text()
            assert "result=no" in text and "result=yes" not in text
            assert f"JOB_END {i} code=1" in text
        source = json.loads((root / report["source"]).read_text())
        assert source["valid_launch"] and source["r"] == 4
        assert report["original_services"] == source["services"] == base["original_services"]
        assert report["original_driver"] == base["original_driver"]
        assert report["original_superseded_states"] == ["T"] * (source["workers"] + 1)
        for service in source["services"]:
            stat = Path(f"/proc/{service['pid']}/stat").read_text().split()
            assert int(stat[21]) == service["start_time_ticks"] and stat[2][0] == "T"
            assert hashlib.sha256(Path(f"/proc/{service['pid']}/exe").read_bytes()).hexdigest() == service["sha256"]
        driver = report["original_driver"]
        assert driver["pid"] == source["owner"]
        stat = Path(f"/proc/{driver['pid']}/stat").read_text().split()
        assert int(stat[21]) == driver["start_time_ticks"] and stat[2][0] == "T"
        assert report["original_prepaused"] == base.get("original_prepaused", False)
        if report["original_prepaused"]:
            assert report["prepaused_evidence"] == base["prepaused_evidence"]
            prior = json.loads((root / report["prepaused_evidence"]).read_text())
            assert prior["valid"] and prior["complete"] and prior["original_services"] == source["services"]
        assert (root / report["claim"] / "owner").read_text().startswith(f"pid={report['owner']} ")
        assert report["claim_original_owner"].startswith(f"pid={source['owner']} ")
        termination = report["base_after_termination"]
        assert not termination["valid"] and not termination["complete"]
        assert termination["original_part_state"] == termination["base_controller_state"] == "T"
        assert termination["original_superseded_states"] == report["original_superseded_states"]
        controller = report["base_controller"]
        assert controller["pid"] == base["owner"]
        controller_stat = Path(f"/proc/{controller['pid']}/stat").read_text().split()
        assert int(controller_stat[21]) == controller["start_time_ticks"] and controller_stat[2][0] == "T"
        assert len(termination["base_donor_resumed_states"]) == len(report["base_donors"]) == 4
        assert report["base_donors"] == base["donors"]
        assert report["base_donor_source"] == base["donor_source"]
        assert report["base_donor_indices"] == base["donor_indices"]
        if report["base_donor_source"] == "proc":
            for donor in report["base_donors"]:
                assert donor["args"][1:3] == ["5", "87"]
                assert tuple(map(int, donor["args"][3:7])) != tuple(report["coordinate"])
        else:
            base_donor_source = json.loads((root / report["base_donor_source"]).read_text())
            assert base_donor_source["valid_launch"]
            assert report["base_donors"] == [base_donor_source["services"][i] for i in report["base_donor_indices"]]
        for donor, state in zip(report["base_donors"], termination["base_donor_resumed_states"]):
            stat = Path(f"/proc/{donor['pid']}/stat").read_text().split()
            assert int(stat[21]) == donor["start_time_ticks"] and stat[2][0] in ("R", "S", "D") and state[0] in ("R", "S", "D")
            assert hashlib.sha256(Path(f"/proc/{donor['pid']}/exe").read_bytes()).hexdigest() == donor["sha256"]
        donor_source = json.loads((root / report["donor_source"]).read_text())
        assert donor_source["valid_launch"]
        assert report["donors"] == [donor_source["services"][i] for i in report["donor_indices"]]
        assert len(report["donor_resumed_states"]) == 4
        for donor, state in zip(report["donors"], report["donor_resumed_states"]):
            stat = Path(f"/proc/{donor['pid']}/stat").read_text().split()
            assert int(stat[21]) == donor["start_time_ticks"] and stat[2][0] in ("R", "S", "D") and state[0] in ("R", "S", "D")
            assert hashlib.sha256(Path(f"/proc/{donor['pid']}/exe").read_bytes()).hexdigest() == donor["sha256"]
    elif report.get("engine_kind") in ("split_first_intervals_v1", "split_first_gpu_safe_v1", "split_first_gpu_safe_all_v1"):
        assert report["complete"] and report["r"] == 4 and report["workers"] == 4
        assert report["server"] in ("fixed_split_first_server", "fixed_split_first_gpu_safe")
        if report["engine_kind"] == "split_first_gpu_safe_all_v1":
            assert report["server"] == "fixed_split_first_gpu_safe"
            assert report["server_sha256"] == "56b53bc59da17559bb7cd4194a653c505c5bd5998bd1591e748ae0f1ac92ebdc"
        else:
            assert report["server"] == "fixed_split_first_server"
            assert report["server_sha256"] == "9655e2aab189d53c5325cd9a553ee9a0e83a88304ff21446a52184ee8ba9c579"
        assert report["product_source_sha256"] == "0b96a324f0d7ff397a32dea784abf051e3f2130e1725fad80a182be69fb61671"
        partition = report["contiguous_partition"]
        assert partition["first_min_inclusive"] == 88
        assert partition["last_max_inclusive"] == (1 << 64) - 1
        intervals = partition["intervals"]
        assert len(intervals) == report["part_count"] == len(report["parts"]) > 4
        for index, (part, interval) in enumerate(zip(report["parts"], intervals)):
            assert part["index"] == index and part["returncode"] == 1
            assert part["server_returncode"] == 0
            if ((report["engine_kind"] == "split_first_gpu_safe_v1" and index == 6) or
                    report["engine_kind"] == "split_first_gpu_safe_all_v1"):
                assert part["sha256"] == "56b53bc59da17559bb7cd4194a653c505c5bd5998bd1591e748ae0f1ac92ebdc"
            else:
                assert part["sha256"] == report["server_sha256"]
            assert part["pid"] > 0 and part["start_time_ticks"] > 0
            assert [part["first_min"], part["first_max"]] == interval
            assert part["first_min"] <= part["first_max"]
            if index + 1 < len(intervals):
                assert intervals[index + 1][0] == part["first_max"] + 1
            else:
                assert part["first_max"] == (1 << 64) - 1
            assert hashlib.sha256((root / part["log"]).read_bytes()).hexdigest() == part["log_sha256"]
            text = (root / part["log"]).read_text()
            assert "result=no" in text and "result=yes" not in text
            assert f"JOB_END {index} code=1" in text
        if report["engine_kind"] == "split_first_gpu_safe_all_v1":
            expected_candidate = "56b53bc59da17559bb7cd4194a653c505c5bd5998bd1591e748ae0f1ac92ebdc"
            assert hashlib.sha256((root / report["server"]).read_bytes()).hexdigest() == expected_candidate
            regression = json.loads((root / report["candidate_regression"]).read_text())
            assert regression["valid"] and regression["cases"] == 54 and regression["positives"] == 4
            assert regression["mismatches"] == 0 and regression["candidate_sha256"] == expected_candidate
            assert regression["source_sha256"] == report["product_source_sha256"]
            initial = json.loads((root / "logs/split_first_gpu_safe_initial.json").read_text())
            assert initial["valid"] and initial["binary_sha256"] == expected_candidate
        if report["engine_kind"] == "split_first_gpu_safe_v1":
            base = json.loads((root / report["base_report"]).read_text())
            assert base["valid"] and base["complete"]
            assert len(report["alternative_parts"]) == 1
            alternative = report["alternative_parts"][0]
            assert alternative["index"] == 6 and alternative["server"] == "fixed_split_first_gpu_safe"
            expected_candidate = "56b53bc59da17559bb7cd4194a653c505c5bd5998bd1591e748ae0f1ac92ebdc"
            assert alternative["server_sha256"] == expected_candidate
            assert hashlib.sha256((root / alternative["server"]).read_bytes()).hexdigest() == expected_candidate
            regression = json.loads((root / alternative["regression"]).read_text())
            assert regression["valid"] and regression["cases"] == 54 and regression["positives"] == 4
            assert regression["mismatches"] == 0 and regression["candidate_sha256"] == expected_candidate
            assert regression["source_sha256"] == report["product_source_sha256"]
            initial = json.loads((root / alternative["initial_validation"]).read_text())
            assert initial["valid"] and initial["binary_sha256"] == expected_candidate
            assert alternative["part"] == report["parts"][6]
            assert alternative["original_part"]["sha256"] == report["server_sha256"]
            assert alternative["original_part"]["log_sha256"] == report["parts"][6]["log_sha256"]
            assert hashlib.sha256((root / alternative["original_partial_log"]).read_bytes()).hexdigest() == alternative["original_partial_log_sha256"]
            for index, part in enumerate(report["parts"]):
                if index != 6:
                    assert part == base["parts"][index]
            assert base["parts"][6]["server_returncode"] == -15
            assert base["parts"][6]["log_sha256"] == report["parts"][6]["log_sha256"]
            termination = report["alternative_original_termination"]
            assert termination["pid"] == alternative["original_part"]["pid"]
            assert termination["start_time_ticks"] == alternative["original_part"]["start_time_ticks"]
            assert termination["sha256"] == report["server_sha256"]
            assert termination["returncode"] == -15
        source = json.loads((root / report["source"]).read_text())
        assert source["valid_launch"] and source["r"] == 4 and source["workers"] >= 1
        assert report["original_services"] == source["services"]
        assert report["original_superseded_states"] == ["T"] * (source["workers"] + 1)
        if report.get("original_prepaused"):
            prior = json.loads((root / report["prepaused_evidence"]).read_text())
            assert prior["valid"] and prior["complete"] and prior["source"] == report["source"]
            assert prior["original_services"] == report["original_services"]
            assert prior["original_superseded_states"] == ["T"] * (source["workers"] + 1)
            assert prior["original_driver"] == report["original_driver"]
        for original in source["services"]:
            process = Path(f"/proc/{original['pid']}")
            stat = (process / "stat").read_text().split()
            assert int(stat[21]) == original["start_time_ticks"] and stat[2][0] == "T"
            assert hashlib.sha256((process / "exe").read_bytes()).hexdigest() == original["sha256"]
        driver = report["original_driver"]
        assert driver["pid"] == source["owner"]
        stat = Path(f"/proc/{driver['pid']}/stat").read_text().split()
        assert int(stat[21]) == driver["start_time_ticks"] and stat[2][0] == "T"
        owner = root / report["claim"] / "owner"
        assert owner.read_text().startswith(f"pid={report['owner']} ")
        assert report["claim_original_owner"].startswith(f"pid={source['owner']} ")
        assert report["donor_paused"]
        if report["donor_source"] == "proc":
            assert report["donor_indices"] == []
            for donor in report["donors"]:
                assert Path(donor["args"][0]).name in {"fixed_exact", "fixed_lower_bound", "fixed_server_product_max"}
                assert donor["args"][1:3] == ["5", "87"]
                assert tuple(map(int, donor["args"][3:7])) != tuple(report["coordinate"])
        else:
            donor_source = json.loads((root / report["donor_source"]).read_text())
            assert donor_source["valid_launch"] and donor_source["r"] != 4
            assert report["donors"] == [donor_source["services"][index] for index in report["donor_indices"]]
        assert len(report["donors"]) == len(report["donor_resumed_states"]) == 4
        for donor, state in zip(report["donors"], report["donor_resumed_states"]):
            process = Path(f"/proc/{donor['pid']}")
            stat = (process / "stat").read_text().split()
            assert int(stat[21]) == donor["start_time_ticks"] and stat[2][0] in ("R", "S", "D")
            assert hashlib.sha256((process / "exe").read_bytes()).hexdigest() == donor["sha256"]
            assert state[0] in ("R", "S", "D")
    elif report.get("engine_kind") == "split_nested_v3":
        assert report["complete"] and report["part_count"] == report["workers"] + 6 == 10
        assert report["server"] == "fixed_split_third_server"
        assert report["server_sha256"] == "256778535abf2d02216772210b6a55b178d55787795f4dd79451b640249f45b3"
        assert report["product_source_sha256"] == "c5837a7a1ba2f94cd16076c36f5e2d1f9f7aaa4c9ea92df16ec3af8f33274423"
        maximum = (1 << 64) - 1
        expected = [
            (88, 88, 89, 89, 90, 90), (88, 88, 89, 89, 91, 91),
            (88, 88, 89, 89, 92, 92), (88, 88, 89, 89, 93, maximum),
            (88, 88, 90, 90, None, None), (88, 88, 91, 91, None, None),
            (88, 88, 92, maximum, None, None), (89, 89, None, None, None, None),
            (90, 90, None, None, None, None), (91, maximum, None, None, None, None),
        ]
        assert report["nested_partition"] == {
            "first_min_inclusive": 88, "last_max_inclusive": maximum,
            "groups": [
                {"first_min": 88, "first_max": 88, "second_groups": [
                    {"second_min": 89, "second_max": 89,
                     "third_intervals": [[90, 90], [91, 91], [92, 92], [93, maximum]]},
                    {"second_min": 90, "second_max": 90, "third_intervals": None},
                    {"second_min": 91, "second_max": 91, "third_intervals": None},
                    {"second_min": 92, "second_max": maximum, "third_intervals": None},
                ]},
                {"first_min": 89, "first_max": 89, "second_groups": None},
                {"first_min": 90, "first_max": 90, "second_groups": None},
                {"first_min": 91, "first_max": maximum, "second_groups": None},
            ],
        }
        assert len(report["parts"]) == len(expected)
        for index, (part, ranges) in enumerate(zip(report["parts"], expected)):
            assert part["index"] == index and part["returncode"] == 1
            assert part["server_returncode"] == 0 and part["sha256"] == report["server_sha256"]
            assert part["pid"] > 0 and part["start_time_ticks"] > 0
            assert [part["first_min"], part["first_max"], part["second_min"], part["second_max"],
                    part["third_min"], part["third_max"]] == list(ranges)
            assert hashlib.sha256((root / part["log"]).read_bytes()).hexdigest() == part["log_sha256"]
            text = (root / part["log"]).read_text()
            assert "result=no" in text and "result=yes" not in text
            assert f"JOB_END {index} code=1" in text
        assert all(state in ("R", "S", "D") for state in report["original_resumed_states"])
    elif report.get("engine_kind") == "split_nested_v2":
        assert report["complete"] and report["part_count"] == report["workers"] + 3 == 7
        assert report["server"] == "fixed_split_second_server"
        assert report["server_sha256"] == "4b3ae6fd6cc0f7089772bf4f57cdedf5b48e2da1a46b5387ce2ac7d7146e1f28"
        assert report["product_source_sha256"] == "dc34033d0e3306b4d8d7be00b58a486cefeb3c779522e879a4291c4e0d4daac1"
        maximum = (1 << 64) - 1
        expected = [
            (88, 88, 89, 89), (88, 88, 90, 90),
            (88, 88, 91, 91), (88, 88, 92, maximum),
            (89, 89, None, None), (90, 90, None, None),
            (91, maximum, None, None),
        ]
        assert report["nested_partition"] == {
            "first_min_inclusive": 88, "last_max_inclusive": maximum,
            "groups": [
                {"first_min": 88, "first_max": 88,
                 "second_intervals": [[89, 89], [90, 90], [91, 91], [92, maximum]]},
                {"first_min": 89, "first_max": 89, "second_intervals": None},
                {"first_min": 90, "first_max": 90, "second_intervals": None},
                {"first_min": 91, "first_max": maximum, "second_intervals": None},
            ],
        }
        assert len(report["parts"]) == len(expected)
        for index, (part, ranges) in enumerate(zip(report["parts"], expected)):
            assert part["index"] == index and part["returncode"] == 1
            assert part["server_returncode"] == 0 and part["sha256"] == report["server_sha256"]
            assert part["pid"] > 0 and part["start_time_ticks"] > 0
            assert [part["first_min"], part["first_max"],
                    part["second_min"], part["second_max"]] == list(ranges)
            assert hashlib.sha256((root / part["log"]).read_bytes()).hexdigest() == part["log_sha256"]
            text = (root / part["log"]).read_text()
            assert "result=no" in text and "result=yes" not in text
            assert f"JOB_END {index} code=1" in text
        assert all(state in ("R", "S", "D") for state in report["original_resumed_states"])
    elif report.get("engine_kind") == "split_first_v1":
        assert report["complete"]
        assert report["server_sha256"] == "9655e2aab189d53c5325cd9a553ee9a0e83a88304ff21446a52184ee8ba9c579"
        assert report["product_source_sha256"] == "0b96a324f0d7ff397a32dea784abf051e3f2130e1725fad80a182be69fb61671"
        partition = report["contiguous_partition"]
        assert partition["first_min_inclusive"] == 88
        assert partition["last_max_inclusive"] == (1 << 64) - 1
        assert len(report["parts"]) == len(partition["intervals"]) == 4
        for index, part in enumerate(report["parts"]):
            assert part["returncode"] == 1 and part["sha256"] == report["server_sha256"]
            assert [part["first_min"], part["first_max"]] == partition["intervals"][index]
            assert hashlib.sha256((root / part["log"]).read_bytes()).hexdigest() == part["log_sha256"]
            text = (root / part["log"]).read_text()
            assert "result=no" in text and "result=yes" not in text
            if index:
                assert part["first_min"] == report["parts"][index - 1]["first_max"] + 1
            else:
                assert part["first_min"] == 88
        assert report["parts"][-1]["first_max"] == (1 << 64) - 1
        assert all(state in ("R", "S", "held_with_pending_signal") for state in report["original_resumed_states"])
        for held in report.get("held_originals", []):
            assert held["state"] == "T" and held["pending_signal"] == "SIGUSR1"
    elif report.get("engine_kind") == "quad_lower_bound_v1":
        expected = "af86cb888c16bf24fc83c58fdce97bd1bd11e2ced0e62ceb8bb1267600c7e963"
        assert report["server"] == "fixed_server_pair_quad"
        assert report["server_sha256"] == expected
        assert report["product_source_sha256"] == "1c841a162733dfa091d0e18e96bc7a8c16ab52eb01a9f869817a1e3980039f65"
        assert hashlib.sha256((root / report["server"]).read_bytes()).hexdigest() == expected
        assert hashlib.sha256((root / "symdiff_pair_quad.cpp").read_bytes()).hexdigest() == report["product_source_sha256"]
        regression = json.loads((root / report["engine_regression"]).read_text())
        assert regression["valid"] and regression["constructed_checked"] == 15000
        assert regression["partition_count"] == 15 and regression["candidate_source_sha256"] == report["product_source_sha256"]
        assert regression["server_sha256"] == expected
        assert hashlib.sha256((root / regression["log"]).read_bytes()).hexdigest() == regression["log_sha256"]
        trace = json.loads((root / regression["trace_check"]).read_text())
        assert trace["valid"] and trace["pruned_candidates_checked"] >= 1
        assert trace["source_sha256"] == report["product_source_sha256"]
        assert hashlib.sha256((root / "logs/quad_r12_trace.log").read_bytes()).hexdigest() == trace["trace_log_sha256"]
        recursive = json.loads((root / regression["recursion_regression"]).read_text())
        assert recursive["valid"] and recursive["all_three_engines_find_representation"]
        assert recursive["representation"] == [9, 10, 12, 15]
        smoke = json.loads((root / regression["server_smoke"]).read_text())
        assert smoke["valid"] and smoke["server_sha256"] == expected
        assert smoke["source_sha256"] == report["product_source_sha256"]
        crosscheck = json.loads((root / regression["r12_crosscheck"]).read_text())
        assert crosscheck["valid"] and crosscheck["complete"] and crosscheck["original_result_no"]
        assert crosscheck["coordinate"] == [12, 46, 74, 78] and crosscheck["xnodes_match"]
        assert crosscheck["candidate_server_sha256"] == expected
        assert crosscheck["original_server_sha256"] == "9a80b9ebbb5ea9e7d1473089941b85cedae8e97ea7330a5078e3b3e2e9267d12"
        for name in ("candidate_log", "original_log"):
            assert hashlib.sha256((root / crosscheck[name]).read_bytes()).hexdigest() == crosscheck[name + "_sha256"]
            data = (root / crosscheck[name]).read_text()
            assert "result=no" in data and "result=yes" not in data
        assert not report["no_prime_power_pigeonhole"]
    elif report.get("engine_kind") == "triple_lower_bound_v1":
        expected = "9a80b9ebbb5ea9e7d1473089941b85cedae8e97ea7330a5078e3b3e2e9267d12"
        assert report["server"] == "fixed_server_pair_triple"
        assert report["server_sha256"] == expected
        assert report["product_source_sha256"] == "ec33c5ba56a6cdbc916a54e4b3323bce956b7708217fd727355938898a6cdb13"
        assert hashlib.sha256((root / report["server"]).read_bytes()).hexdigest() == expected
        assert hashlib.sha256((root / "symdiff_pair_triple.cpp").read_bytes()).hexdigest() == report["product_source_sha256"]
        regression = json.loads((root / report["engine_regression"]).read_text())
        assert regression["valid"] and regression["constructed_checked"] == 7770 and not regression["failures"]
        assert regression["server_sha256"] == expected
        assert regression["candidate_source_sha256"] == report["product_source_sha256"]
        smoke = json.loads((root / regression["server_smoke"]).read_text())
        assert smoke["valid"] and smoke["server_sha256"] == expected
        assert smoke["source_sha256"] == report["product_source_sha256"]
        benchmark = json.loads((root / regression["real_r13_benchmark"]).read_text())
        assert benchmark["valid"] and benchmark["xnodes"] == 286 and benchmark["speedup_over_pair"] > 1
        assert benchmark["candidate_sha256"] == regression["direct_candidate_sha256"]
        crosscheck = json.loads((root / regression["first_negative_crosscheck"]).read_text())
        assert crosscheck["valid"] and crosscheck["original_result_no"] and crosscheck["complete"]
        assert crosscheck["coordinate"] == [13, 63, 70, 75]
        assert crosscheck["candidate_server_sha256"] == expected
        assert crosscheck["original_source_sha256"] == "82209289071a7a743da5b7f3bae0d30635e96ad51ed53476841c6e93b1579948"
        for name in ("candidate_log", "original_log"):
            assert hashlib.sha256((root / crosscheck[name]).read_bytes()).hexdigest() == crosscheck[name + "_sha256"]
            text = (root / crosscheck[name]).read_text()
            assert "result=no" in text and "result=yes" not in text
        assert not report["no_prime_power_pigeonhole"]
    elif report.get("engine_kind") == "pair_lower_bound_v1":
        expected = "012e3171015f9d37972cbc4579d7bf9d27c23413123d42715714c520eb4b28c9"
        assert report["server"] == "fixed_server_pair_candidate"
        assert report["server_sha256"] == expected
        assert report["product_source_sha256"] == "82209289071a7a743da5b7f3bae0d30635e96ad51ed53476841c6e93b1579948"
        assert hashlib.sha256((root / report["server"]).read_bytes()).hexdigest() == expected
        assert hashlib.sha256((root / "symdiff_pair_candidate.cpp").read_bytes()).hexdigest() == report["product_source_sha256"]
        regression = json.loads((root / report["engine_regression"]).read_text())
        assert regression["valid"] and regression["cases"] == 4298 and regression["positives"] == 1653
        assert not regression["failures"] and regression["candidate_sha256"] == expected
        assert regression["source_sha256"] == report["product_source_sha256"]
        smoke = json.loads((root / regression["server_smoke"]).read_text())
        assert smoke["valid"] and smoke["server_sha256"] == expected
        assert smoke["source_sha256"] == report["product_source_sha256"]
        benchmark = json.loads((root / regression["real_r13_benchmark"]).read_text())
        assert benchmark["valid"] and benchmark["xnodes_match"] and benchmark["speedup"] > 1
        assert benchmark["candidate_sha256"] == regression["direct_candidate_sha256"]
        assert not report["no_prime_power_pigeonhole"]
        crosscheck = json.loads((root / regression["first_negative_crosscheck"]).read_text())
        assert crosscheck["valid"] and crosscheck["original_result_no"] and crosscheck["complete"]
        assert crosscheck["candidate_log"] == "logs/fixed87_depth3/r13_x63_y72_z76.log"
        assert hashlib.sha256((root / crosscheck["candidate_log"]).read_bytes()).hexdigest() == crosscheck["candidate_log_sha256"]
        expected_ranges = [
            (88, 88, 89, 89, 90, 90), (88, 88, 89, 89, 91, 91),
            (88, 88, 89, 89, 92, 92), (88, 88, 89, 89, 93, (1 << 64) - 1),
            (88, 88, 90, 90, None, None), (88, 88, 91, 91, None, None),
            (88, 88, 92, (1 << 64) - 1, None, None), (89, 89, None, None, None, None),
            (90, 90, None, None, None, None), (91, (1 << 64) - 1, None, None, None, None),
        ]
        assert len(crosscheck["parts"]) == len(expected_ranges)
        for index, (part, ranges) in enumerate(zip(crosscheck["parts"], expected_ranges)):
            assert part["index"] == index and part["returncode"] == 1 and part["server_returncode"] == 0
            assert [part["first_min"], part["first_max"], part["second_min"], part["second_max"],
                    part["third_min"], part["third_max"]] == list(ranges)
            assert hashlib.sha256((root / part["log"]).read_bytes()).hexdigest() == part["log_sha256"]
            part_text = (root / part["log"]).read_text()
            assert "result=no" in part_text and "result=yes" not in part_text
            assert f"JOB_END {index} code=1" in part_text
    elif report.get("engine_kind") == "split_first_gpu_safe_tail_resume_v1":
        from audit_r4_tail import audit_report as audit_tail_report
        audit_tail_report(report)
    elif report.get("engine_kind") == "distinct_companion_v1":
        assert report["server"] == "fixed_server_product_distinct"
        assert report["server_sha256"] == "7d324ca4a267bfdf0de9b182092145dbc2d9c5a515383c4a45c15f81ebd58e28"
        assert report["product_source_sha256"] == "2c64d6c671bf5acbb369f8172a98da287bc49d270f87587dcede0262ecd28be2"
        assert hashlib.sha256((root / report["server"]).read_bytes()).hexdigest() == report["server_sha256"]
        assert hashlib.sha256((root / "symdiff_product_fast.cpp").read_bytes()).hexdigest() == report["product_source_sha256"]
        regression = json.loads((root / report["engine_regression"]).read_text())
        assert regression["valid"] and regression["candidate_sha256"] == report["server_sha256"]
        assert regression["source_sha256"] == report["product_source_sha256"]
        assert regression["cases"] == 22680 and regression["positives"] == 7081
        assert regression["mismatches"] == 0 and regression["constructed_cases"] == 4400
        assert regression["constructed_mismatches"] == 0 and regression["combinatorial_cases"] == 300
        smoke = json.loads((root / regression["server_smoke"]).read_text())
        assert smoke["valid"] and smoke["server_sha256"] == report["server_sha256"]
        assert smoke["source_sha256"] == report["product_source_sha256"]
        assert not report["no_prime_power_pigeonhole"]
    elif report.get("engine_kind") == "corrected_product_max_v1":
        assert report["server_sha256"] == "c74221cc7274d0f7bf6f446d943c7dd94e1ec4fb85df647cd3b58f1018e53ead"
        assert report["product_source_sha256"] == "7cadd3069e1173dfa931e3b28717110cd091cf4f0d9efc22ec73e96bdee269eb"
    else:
        assert report["server_sha256"] == "fdbac4890b8d2a3af43b4162fa57afc93353b493d227a7ab836bce64f0ee7c31"
        assert report["no_prime_power_pigeonhole"]
    assert json.loads((root / report["engine_regression"]).read_text())["valid"]
    r = report["r"]
    directory = root / f"claims87_r{r}_adaptive_v1"
    try:
        directory_mtime = directory.stat().st_mtime_ns
    except FileNotFoundError:
        directory_mtime = None
    if r not in claims_by_r or claims_by_r[r][0] != directory_mtime:
        by_owner = {}
        for owner in directory.glob("*/owner"):
            try:
                data = owner.read_text()
            except FileNotFoundError:
                continue
            token = data.split(" ", 1)[0]
            if token.startswith("pid=") and len(token) > 4 and data.startswith(token + " "):
                by_owner.setdefault(token[4:], []).append(
                    f"logs/fixed87_depth3/{owner.parent.name}.log")
        claims_by_r[r] = (directory_mtime, by_owner)
    reviewed.update(claims_by_r[r][1].get(str(owner_id), []))
    report_sha256 = hashlib.sha256((root / report_name).read_bytes()).hexdigest()
    cached_report = cache["reports"].get(report_name)
    if not cached_report or cached_report["owner"] != str(owner_id):
        prior_versions = [candidate for candidate in cache["reports"].values()
                          if candidate["owner"] == str(owner_id)]
        cached_report = max(prior_versions, key=lambda candidate: len(candidate["records"])) if prior_versions else None
    cache_hit = cached_report and cached_report["owner"] == str(owner_id)
    cached_records = {item["log"]: item for item in cached_report["records"]} if cache_hit else {}
    cached_output_records = []
    for item in report["records"]:
        assert item["coordinate"][0] == r
        r_item, x, y, z = item["coordinate"]
        name = item["log"]
        assert name == f"logs/fixed87_depth3/r{r_item}_x{x}_y{y}_z{z}.log"
        stat = (root / name).stat()
        fingerprint = {"device": stat.st_dev, "inode": stat.st_ino, "size": stat.st_size,
                       "mtime_ns": stat.st_mtime_ns, "ctime_ns": stat.st_ctime_ns}
        if cache_hit and name in cached_records and cached_records[name]["log_sha256"] == item["log_sha256"] and cached_records[name]["fingerprint"] == fingerprint:
            cache_hits += 1
        else:
            assert hashlib.sha256((root / name).read_bytes()).hexdigest() == item["log_sha256"]
            cache_misses += 1
        approved[name] = item["log_sha256"]
        cached_output_records.append({**item, "fingerprint": fingerprint})
    cache_output["reports"][report_name] = {"owner": str(owner_id), "report_sha256": report_sha256,
                                             "records": cached_output_records}
    assert len(approved) >= report["accepted_negatives"]

if cache_output_name:
    cache_output["cached_file_identity_checks"] = cache_hits
    cache_output["full_hash_checks"] = cache_misses
    cache_output["scope_r"] = coverage_only_r or None
    cache_output["note"] = "Reuse is per record, including prior report versions of the same owner: unchanged log digest and device/inode/size/mtime/ctime are required. Report hashes are recorded for provenance. Omit COVERAGE_APPROVED_CACHE for a full content-hash audit."
    output = root / cache_output_name
    assert not output.exists()
    output.write_text(json.dumps(cache_output, indent=2) + "\n")
    print(f"coverage cache: file-identity hits {cache_hits}; full content hashes {cache_misses}")


def text(path):
    try:
        with path.open("rb") as stream:
            size = os.fstat(stream.fileno()).st_size
            if size <= 65536:
                return stream.read().decode("utf-8")
            stream.seek(size - 65536)
            data = stream.read().decode("utf-8", errors="replace")
    except FileNotFoundError:
        return ""
    return data if "result=" in data else path.read_text()


def completed(data, r, trusted_pair=False):
    if "result=yes" in data:
        return True
    if "result=no" not in data:
        return False
    if ("engine=cpu-gpu-pair-candidate-v1" in data or "engine=cpu-gpu-triple-candidate-v1" in data
            or "engine=cpu-gpu-quad-candidate-v1" in data):
        return False
    if r >= 5 and "engine=" in data:
        return ("engine=gpu-exact-block-v3" in data or
                "engine=cpu-gpu-two-v1" in data or
                "engine=cpu-gpu-three-v1" in data or
                "engine=depth3-block-v3" in data or
                "engine=depth4-block-v3" in data)
    return True


found = []
missing = 0
main = text(logs / "n5_k87_r1_3.log")
for r in range(1, 4) if not coverage_only_r else ():
    lines = [line for line in main.splitlines() if line.startswith(f"r={r} xnodes=")]
    if lines and all("result=no" in line for line in lines):
        print(f"r={r}: complete")
    else:
        missing += 1

for r in range(4, 20) if not coverage_only_r else (coverage_only_r,):
    complete = text(logs / f"n5_k87_r{r}_parallel.log")
    if "result=yes" in complete:
        found.append((r,))
        continue
    if completed(complete, r):
        print(f"r={r}: complete")
        continue
    roots = pairs = expected = uncovered = 0
    for x in range(17, 87 - r + 2):
        root_data = text(logs / "root87" / f"r{r}_x{x}.log")
        if "result=yes" in root_data:
            found.append((r, x))
        if completed(root_data, r):
            roots += 1
            continue
        for y in range(x + 1, 87 - r + 3):
            expected += 1
            pair_data = text(logs / "fixed87" / f"r{r}_x{x}_y{y}.log")
            if "result=yes" in pair_data:
                found.append((r, x, y))
            if completed(pair_data, r):
                pairs += 1
                continue
            depth3 = []
            for z in range(y + 1, 87 - r + 4):
                name = f"r{r}_x{x}_y{y}_z{z}.log"
                data = text(logs / "fixed87_depth3" / name)
                relative = f"logs/fixed87_depth3/{name}"
                trusted_pair = False
                if relative in reviewed:
                    if relative not in approved:
                        assert "result=yes" not in data, relative
                        data = ""
                    else:
                        assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == approved[relative]
                        trusted_pair = True
                depth3.append((data, trusted_pair))
                if "result=yes" in data:
                    found.append((r, x, y, z))
            if depth3 and all(completed(data, r, trusted_pair) for data, trusted_pair in depth3):
                pairs += 1
            else:
                uncovered += 1
                if os.environ.get("COVERAGE_DETAIL_R") == str(r):
                    print("uncovered_parent", r, x, y)
    missing += uncovered
    print(f"r={r}: root exclusions {roots}/{87-r+1-16}; secondary exclusions {pairs}/{expected}; uncovered {uncovered}")
print(f"verified_safe_logs: {len(approved)}")
print(f"unverified_safe_owner_logs: {len(reviewed-approved.keys())}")
print(f"representations found: {found}")
print(f"uncovered branches: {missing}")
raise SystemExit(bool(missing) and not found)
