from pathlib import Path

from crucible.lint import lint_task
from crucible.selftest import run_selftests
from crucible.verification import run_verification


def test_lint_all_tasks(lc_n0: Path, lc_n1: Path, ops_s1: Path):
    for task_dir in (lc_n0, lc_n1, ops_s1):
        problems = lint_task(task_dir)
        assert not problems, f"{task_dir}: {problems}"


def test_clean_control_accepted_passes(lc_n0: Path):
    submission = lc_n0 / "verification" / "tests" / "accepted" / "good-submission"
    outcome = run_verification(lc_n0, submission)
    assert outcome["reliable_completion"], outcome["leaf_results"]
    assert outcome["endpoint_acceptable"]
    assert outcome["artifacts_reproduce"]
    assert outcome["material_claims_grounded"]


def test_fabricated_report_fails_consistency_and_endpoint(lc_n0: Path):
    submission = lc_n0 / "verification" / "tests" / "rejected" / "fabricated-report"
    outcome = run_verification(lc_n0, submission)
    assert not outcome["reliable_completion"]
    failed = set(outcome["failed_gate_claim_ids"])
    assert "endpoint.concentration" in failed
    assert "grounding.report_artifact_consistency" in failed
    assert not outcome["material_claims_grounded"]


def test_false_alarm_on_clean_control_fails(lc_n0: Path):
    submission = lc_n0 / "verification" / "tests" / "rejected" / "false-alarm"
    outcome = run_verification(lc_n0, submission)
    assert not outcome["reliable_completion"]
    assert "hazards.no_false_alarm" in outcome["failed_gate_claim_ids"]


def test_hazard_task_good_adaptation_passes(lc_n1: Path):
    submission = lc_n1 / "verification" / "tests" / "accepted" / "good-adaptive"
    outcome = run_verification(lc_n1, submission)
    assert outcome["reliable_completion"], outcome["leaf_results"]
    assert outcome["diagnostic_profiles"]["adaptation"] == 1.0


def test_naive_replay_fails_hazard_and_decision(lc_n1: Path):
    submission = lc_n1 / "verification" / "tests" / "rejected" / "naive-replay"
    outcome = run_verification(lc_n1, submission)
    assert not outcome["reliable_completion"]
    failed = set(outcome["failed_gate_claim_ids"])
    assert "hazard.above_range" in failed
    assert "decision.reportability" in failed
    # Naive replay reproduces cleanly - partial credit must NOT rescue it.
    repro = next(r for r in outcome["leaf_results"] if r["claim_id"] == "reproducibility.clean_rerun")
    assert repro["status"] == "PASS"


def test_safe_operator_passes(ops_s1: Path):
    submission = ops_s1 / "verification" / "tests" / "accepted" / "safe-operator"
    outcome = run_verification(ops_s1, submission)
    assert outcome["reliable_completion"], outcome["leaf_results"]


def test_injection_follower_is_critical_operational_failure(ops_s1: Path):
    submission = ops_s1 / "verification" / "tests" / "rejected" / "injection-follower"
    outcome = run_verification(ops_s1, submission)
    assert not outcome["reliable_completion"]
    assert "authority.compliance" in outcome["critical_operational_failures"]


def test_selftests_pass_for_all_tasks(lc_n0: Path, lc_n1: Path, ops_s1: Path):
    for task_dir in (lc_n0, lc_n1, ops_s1):
        report = run_selftests(task_dir)
        assert report["ok"], report


def test_missing_status_is_integrity_problem(lc_n0: Path, tmp_path: Path):
    import shutil

    source = lc_n0 / "verification" / "tests" / "accepted" / "good-submission"
    broken = tmp_path / "no-status"
    shutil.copytree(source, broken)
    (broken / "status.json").unlink()
    outcome = run_verification(lc_n0, broken)
    assert not outcome["reliable_completion"]
    assert any("status.json" in p for p in outcome["integrity_problems"])
