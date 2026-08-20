from pathlib import Path

from crucible.schemas import load_record, validate_file, validate_record


def test_templates_validate(repo_root: Path):
    for template in (repo_root / "tasks_public").glob("*/template.yaml"):
        errors = validate_file("task-template", template)
        assert not errors, f"{template}: {errors}"


def test_instances_validate(repo_root: Path):
    instance_files = list((repo_root / "tasks_public").glob("*/instances/*/instance.yaml"))
    assert instance_files, "no instance records found"
    for instance in instance_files:
        errors = validate_file("task-instance", instance)
        assert not errors, f"{instance}: {errors}"


def test_manifests_validate(repo_root: Path):
    manifests = list((repo_root / "tasks_public").glob("*/instances/*/verification/manifest.json"))
    assert manifests, "no verification manifests found"
    for manifest in manifests:
        errors = validate_file("verification-manifest", manifest)
        assert not errors, f"{manifest}: {errors}"


def test_system_card_validates(repo_root: Path):
    card = repo_root / "examples" / "system_card_reference_agent.yaml"
    assert not validate_file("system-card", card)


def test_invalid_record_fails_for_the_right_reason(repo_root: Path):
    record = load_record(repo_root / "tasks_public" / "CHEM-LC-CAL-001" / "template.yaml")
    record["instances"]["generator"]["max_primary_instances_per_release"] = 50  # cap is 3
    errors = validate_record("task-template", record)
    assert errors and any("max_primary_instances_per_release" in e for e in errors)


def test_submission_claims_validate(repo_root: Path):
    claims_files = list((repo_root / "tasks_public").glob("*/instances/*/verification/tests/*/*/claims.json"))
    assert claims_files
    for path in claims_files:
        errors = validate_file("claims", path)
        assert not errors, f"{path}: {errors}"
