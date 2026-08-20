from pathlib import Path

import pytest

from crucible.audit import AuditLog
from crucible.registry import PIPELINE, TaskRegistry, TransitionError, allowed_transitions


@pytest.fixture
def registry(tmp_path: Path, repo_root: Path, monkeypatch):
    # Point the registry at a temp dir but keep schema resolution at the repo.
    monkeypatch.setattr("crucible.registry.registry_dir", lambda root=None: tmp_path)
    return TaskRegistry(root=repo_root)


def test_add_and_walk_full_pipeline(registry, repo_root: Path):
    template = repo_root / "tasks_public" / "CHEM-LC-CAL-001" / "template.yaml"
    entry = registry.add_task(template, actor="tester")
    assert entry["status"] == "NOMINATED"
    for status in PIPELINE[1:]:
        entry = registry.transition("CHEM-LC-CAL-001", status, actor="tester", reason="gate passed")
    assert entry["status"] == "FROZEN"
    assert len(entry["history"]) == len(PIPELINE) - 1


def test_no_gate_skipping(registry, repo_root: Path):
    template = repo_root / "tasks_public" / "OPS-AUTH-001" / "template.yaml"
    registry.add_task(template, actor="tester")
    with pytest.raises(TransitionError):
        registry.transition("OPS-AUTH-001", "ADMITTED", actor="tester", reason="skip attempt")


def test_transition_requires_owner_and_reason(registry, repo_root: Path):
    template = repo_root / "tasks_public" / "CHEM-LC-CAL-001" / "template.yaml"
    registry.add_task(template, actor="tester")
    with pytest.raises(TransitionError):
        registry.transition("CHEM-LC-CAL-001", "TRIAGED", actor="", reason="x")
    with pytest.raises(TransitionError):
        registry.transition("CHEM-LC-CAL-001", "TRIAGED", actor="tester", reason="  ")


def test_terminal_statuses(registry, repo_root: Path):
    template = repo_root / "tasks_public" / "CHEM-LC-CAL-001" / "template.yaml"
    registry.add_task(template, actor="tester")
    registry.transition("CHEM-LC-CAL-001", "REJECTED", actor="editor", reason="no real decision")
    assert allowed_transitions("REJECTED") == set()
    with pytest.raises(TransitionError):
        registry.transition("CHEM-LC-CAL-001", "TRIAGED", actor="editor", reason="resurrect")


def test_audit_chain_detects_tampering(registry, repo_root: Path):
    template = repo_root / "tasks_public" / "CHEM-LC-CAL-001" / "template.yaml"
    registry.add_task(template, actor="tester")
    registry.transition("CHEM-LC-CAL-001", "TRIAGED", actor="tester", reason="triage done")
    ok, problems = registry.audit.verify_chain()
    assert ok, problems
    # Tamper with the log and confirm detection.
    text = registry.audit.path.read_text(encoding="utf-8")
    tampered = text.replace("triage done", "totally legit")
    registry.audit.path.write_text(tampered, encoding="utf-8")
    ok, problems = AuditLog(registry.audit.path).verify_chain()
    assert not ok and problems
