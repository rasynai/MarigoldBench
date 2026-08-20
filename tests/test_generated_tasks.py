"""Sampled regression checks over the generated 1.0 task population."""
import json
import random
from pathlib import Path

from crucible.lint import lint_task
from crucible.schemas import validate_file
from crucible.selftest import run_selftests


def _index(repo_root: Path) -> list[dict]:
    return json.loads(
        (repo_root / "registry" / "generated_task_index.json").read_text(encoding="utf-8"))


def test_population_counts(repo_root: Path):
    index = _index(repo_root)
    assert len({r["template_id"] for r in index}) == 30
    assert len(index) >= 100
    splits = {r["split"] for r in index}
    assert splits == {"development", "hidden_test", "sealed"}
    assert len({r["archetype"] for r in index}) == 10


def test_sampled_instances_fully_valid(repo_root: Path):
    index = _index(repo_root)
    rng = random.Random(2026)
    for row in rng.sample(index, 6):
        inst = repo_root / row["path"]
        assert not validate_file("task-instance", inst / "instance.yaml"), row["path"]
        assert not validate_file("verification-manifest",
                                 inst / "verification" / "manifest.json"), row["path"]
        assert not lint_task(inst), row["path"]
        report = run_selftests(inst)
        assert report["ok"], (row["path"], report)


def test_condition_symmetry_no_card_leak(repo_root: Path):
    """Clean and hazard instances of a template share an identical card."""
    index = _index(repo_root)
    by_template: dict[str, dict[str, Path]] = {}
    for row in index:
        by_template.setdefault(row["template_id"], {})[row["condition"]] = (
            repo_root / row["path"])
    checked = 0
    for template_id, conds in by_template.items():
        if "N0" in conds and "N1" in conds:
            c0 = (conds["N0"] / "task_card" / "card.md").read_text(encoding="utf-8")
            c1 = (conds["N1"] / "task_card" / "card.md").read_text(encoding="utf-8")
            assert c0 == c1, f"card asymmetry leaks the condition in {template_id}"
            checked += 1
    assert checked >= 20
