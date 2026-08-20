"""Build the CRUCIBLE 2.0 open-ended population: author -> validate -> review
-> repair -> materialize, parallel across templates, restartable per template.

CLI:
    python -m crucible.taskgen2.build [--only OE-...] [--workers 6]
Artifacts:
    tasks_open/<template>/template.json           (sections + provenance)
    tasks_open/<template>/instances/<cond>-s<n>/  (prompt.md, artifacts/, truth2/)
    tasks_open_sealed/...                         (sealed instances, gitignored)
    registry/open_task_index.json
Generation logs (every author/review verdict): runs/taskgen2_log/<template>.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ..paths import find_repo_root
from .author import author_template, review_template
from .plan import CONDITIONS, template_plan
from .validate import TemplateInvalid, render_rubric, validate_template

TRUTH_MARKER = "CRUCIBLE-TRUTH-ZONE-DO-NOT-DISTRIBUTE"
SEEDS = [11, 12, 13]          # 3 seeds x 3 conditions = 9 instances / template
SEALED_SEED = 13              # every template's third seed goes to the sealed tree
DEV_TEMPLATE_COUNT = 6        # first N templates contribute their (C0, seed 11)
                              # instance to the public development split


def _w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def render_instance_dirs(repo: Path, slot: dict, sections: dict, payloads: dict) -> list[dict]:
    rows = []
    template_id = slot["template_id"]
    for seed, per_cond in payloads.items():
        for condition in CONDITIONS:
            payload = per_cond[condition]
            sealed = (seed == SEALED_SEED)
            root = repo / ("tasks_open_sealed" if sealed else "tasks_open")
            inst = root / template_id / "instances" / f"{condition}-s{seed}"
            _w(inst / "prompt.md", payload["prompt"])
            for name, content in payload["artifacts"].items():
                safe = name.replace("..", "_").lstrip("/\\")
                _w(inst / "artifacts" / safe, content)
            truth = payload["truth"]
            rendered_rubric = render_rubric(sections["RUBRIC"], truth, condition)
            _w(inst / "truth2" / "truth.json",
               f"// {TRUTH_MARKER}\n" + json.dumps(truth, indent=2, default=str))
            _w(inst / "truth2" / "rubric.json",
               f"// {TRUTH_MARKER}\n" + json.dumps(rendered_rubric, indent=2))
            _w(inst / "truth2" / "reference_answer.md",
               f"<!-- {TRUTH_MARKER} -->\n" + payload["reference_answer"])
            _w(inst / "truth2" / "weak_answer.md",
               f"<!-- {TRUTH_MARKER} -->\n" + payload["weak_answer"])
            _w(inst / "answer_schema.json", json.dumps(sections["ANSWER_SCHEMA"], indent=2))
            if sealed:
                split = "sealed"
            elif (slot["n_index"] <= DEV_TEMPLATE_COUNT
                  and condition == "C0" and seed == SEEDS[0]):
                split = "development"
            else:
                split = "hidden_test"
            rows.append({
                "template_id": template_id, "area": slot["area"],
                "workflow": slot["workflow"], "condition": condition,
                "instance": f"{condition}-s{seed}", "split": split,
                "path": str(inst.relative_to(repo)).replace("\\", "/"),
                "author_family": slot["author_family"],
            })
    return rows


def build_one(repo: Path, slot: dict) -> dict:
    template_id = slot["template_id"]
    log_path = repo / "runs" / "taskgen2_log" / f"{template_id}.json"
    done_marker = repo / "tasks_open" / template_id / "template.json"
    if done_marker.exists():
        return {"template_id": template_id, "status": "already_built"}
    log: dict = {"template_id": template_id, "slot": slot, "rounds": []}
    feedback = None
    for attempt in range(3):
        entry: dict = {"attempt": attempt}
        try:
            sections = author_template(slot, feedback)
            payloads = validate_template(sections, SEEDS)
        except (TemplateInvalid, ValueError, RuntimeError) as exc:
            entry["structural_error"] = str(exc)[:500]
            log["rounds"].append(entry)
            feedback = f"Structural validation failed: {str(exc)[:500]}"
            continue
        rendered_bits = []
        for condition in CONDITIONS:
            payload = payloads[SEEDS[0]][condition]
            rendered_bits.append(
                f"## Condition {condition}\n### Prompt\n{payload['prompt']}\n"
                f"### Artifacts\n" + "\n".join(
                    f"--- {n} ---\n{c[:2500]}" for n, c in payload["artifacts"].items())
                + f"\n### Hidden truth\n{json.dumps(payload['truth'], default=str)[:2000]}\n"
                f"### Rendered rubric\n"
                + json.dumps(render_rubric(sections['RUBRIC'], payload['truth'], condition))[:3500]
                + f"\n### Reference answer\n{payload['reference_answer'][:2500]}\n"
                f"### Weak answer\n{payload['weak_answer'][:1800]}\n")
        try:
            verdict = review_template(slot, "\n".join(rendered_bits))
        except Exception as exc:  # noqa: BLE001 - review infra failure: retry round
            entry["review_error"] = str(exc)[:300]
            log["rounds"].append(entry)
            feedback = None
            continue
        entry["review"] = verdict
        log["rounds"].append(entry)
        if verdict.get("approve"):
            rows = render_instance_dirs(repo, slot, sections, payloads)
            _w(repo / "tasks_open" / template_id / "template.json", json.dumps({
                "template_id": template_id, "slot": slot,
                "title": sections["TITLE"], "design_notes_marker": TRUTH_MARKER,
                "design_notes": sections["DESIGN_NOTES"],
                "generator_py": sections["GENERATOR"],
                "rubric": sections["RUBRIC"], "answer_schema": sections["ANSWER_SCHEMA"],
                "review": verdict, "authored": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }, indent=2))
            log["status"] = "built"
            _w(log_path, json.dumps(log, indent=2))
            return {"template_id": template_id, "status": "built", "rows": rows}
        feedback = "\n".join(verdict.get("problems", []) + verdict.get("required_fixes", []))[:3000]
    log["status"] = "failed"
    _w(log_path, json.dumps(log, indent=2))
    return {"template_id": template_id, "status": "failed"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default=None)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args(argv)
    repo = find_repo_root()
    plan = template_plan()
    for i, slot in enumerate(plan, 1):
        slot["n_index"] = i
    if args.only:
        plan = [s for s in plan if s["template_id"] == args.only]
    all_rows: list[dict] = []
    statuses: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(build_one, repo, slot): slot["template_id"] for slot in plan}
        for future in as_completed(futures):
            result = future.result()
            statuses[result["template_id"]] = result["status"]
            all_rows.extend(result.get("rows", []))
            print(json.dumps({k: result[k] for k in ("template_id", "status")}), flush=True)
    index_path = repo / "registry" / "open_task_index.json"
    existing = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    known = {(r["template_id"], r["instance"]) for r in existing}
    merged = existing + [r for r in all_rows if (r["template_id"], r["instance"]) not in known]
    _w(index_path, json.dumps(merged, indent=2))
    print(json.dumps({"built": sum(1 for s in statuses.values() if s == "built"),
                      "already": sum(1 for s in statuses.values() if s == "already_built"),
                      "failed": sum(1 for s in statuses.values() if s == "failed"),
                      "instances_indexed": len(merged)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
