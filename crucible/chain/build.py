"""Build the CRUCIBLE-CHAIN population: author -> validate -> hostile review
-> repair -> materialize. Parallel across templates, restartable per template.

CLI:
    python -m crucible.chain.build [--only OEC-...] [--workers 6] [--attempts 3]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ..paths import find_repo_root
from .author import author_chain, render_for_review, review_chain
from .plan import template_plan
from .sandbox2 import GeneratorRejected
from .spec import CONDITIONS, ChainInvalid, answer_key
from .validate import guessability_probe, validate_chain_template

TRUTH_MARKER = "CRUCIBLE-TRUTH-ZONE-DO-NOT-DISTRIBUTE"
# 6 seeds x 3 conditions = 18 instances per template. Extra seeds cost no
# model calls - the generator is deterministic - and every additional seed is
# another instance an adversary cannot have seen, so this is the cheapest
# contamination resistance available.
SEEDS = [11, 12, 13, 14, 15, 16]
SEALED_SEEDS = {14, 16}       # never published in any form
DEV_SEEDS = {11}              # public development split (truth published)


def _w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _split_for(seed: int) -> str:
    if seed in SEALED_SEEDS:
        return "sealed"
    if seed in DEV_SEEDS:
        return "development"
    return "hidden_test"


def materialize(repo: Path, slot: dict, sections: dict, payloads: dict) -> list[dict]:
    rows = []
    template_id = slot["template_id"]
    for seed, per_condition in payloads.items():
        for condition in CONDITIONS:
            payload = per_condition[condition]
            split = _split_for(seed)
            root = repo / ("tasks_chain_sealed" if split == "sealed" else "tasks_chain")
            inst = root / template_id / "instances" / f"{condition}-s{seed}"
            _w(inst / "prompt.md", payload["prompt"])
            for name, content in payload["artifacts"].items():
                safe = name.replace("..", "_").lstrip("/\\")
                _w(inst / "artifacts" / safe, content)
            key = answer_key(payload)
            _w(inst / "truth_chain" / "key.json",
               f"// {TRUTH_MARKER}\n" + json.dumps(key, indent=2, default=str))
            _w(inst / "truth_chain" / "reference_answer.md",
               f"<!-- {TRUTH_MARKER} -->\n" + payload["reference_answer"])
            _w(inst / "truth_chain" / "weak_answer.md",
               f"<!-- {TRUTH_MARKER} -->\n" + payload["weak_answer"])
            rows.append({
                "template_id": template_id, "area": slot["area"],
                "workflow": slot["workflow"], "condition": condition,
                "seed": seed, "instance": f"{condition}-s{seed}", "split": split,
                "path": str(inst.relative_to(repo)).replace("\\", "/"),
                "author_family": slot["author_family"],
                "n_stages": len(key["stages"]),
            })
    return rows


def build_one(repo: Path, slot: dict, attempts: int) -> dict:
    template_id = slot["template_id"]
    done_marker = repo / "tasks_chain" / template_id / "template.json"
    if done_marker.exists():
        return {"template_id": template_id, "status": "already_built"}
    log: dict = {"template_id": template_id, "slot": slot, "rounds": []}
    feedback = None
    for attempt in range(attempts):
        entry: dict = {"attempt": attempt}
        try:
            sections = author_chain(slot, feedback)
            payloads = validate_chain_template(sections["GENERATOR"], SEEDS,
                                               determinism_reps=1)
        except (ChainInvalid, GeneratorRejected, ValueError, RuntimeError) as exc:
            entry["gate_failure"] = str(exc)[:900]
            log["rounds"].append(entry)
            feedback = (f"Automatic validity gates REJECTED the template:\n{str(exc)[:900]}\n"
                        "Fix that specific problem. Your generator must import cleanly,"
                        " run under `python -I` with stdlib only, and recompute every"
                        " value in code - never hardcode a number the generator should"
                        " derive, and never write a decoy that is implausible.")
            continue
        try:
            verdict = review_chain(slot, render_for_review(payloads, SEEDS[0], sections))
        except Exception as exc:  # noqa: BLE001 - review infra hiccup: retry round
            entry["review_error"] = str(exc)[:300]
            log["rounds"].append(entry)
            continue
        entry["review"] = verdict
        entry["guessability"] = guessability_probe(payloads[SEEDS[0]]["C0"])["n_suspicious"]
        log["rounds"].append(entry)
        # An approval that arrives WITH required fixes is not an approval:
        # five of eight 3.0.0 templates shipped `approve: true` alongside a
        # non-empty required_fixes list documenting the exact giveaways that
        # later saturated the campaign (hardening spec section 0, root cause
        # 2). Fixes demanded means another round, full stop.
        if verdict.get("approve") and verdict.get("key_correctness_verified") \
                and not verdict.get("required_fixes"):
            rows = materialize(repo, slot, sections, payloads)
            _w(repo / "tasks_chain" / template_id / "template.json", json.dumps({
                "template_id": template_id, "slot": slot,
                "title": sections["TITLE"], "design_notes": sections["DESIGN_NOTES"],
                "generator_py": sections["GENERATOR"],
                "review": verdict,
                "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }, indent=2))
            log["status"] = "built"
            _w(repo / "runs" / "chain_build_log" / f"{template_id}.json",
               json.dumps(log, indent=2, default=str))
            return {"template_id": template_id, "status": "built", "rows": rows}
        feedback = ("A hostile reviewer REJECTED the template. Fix every point:\n"
                    + "\n".join(verdict.get("problems", [])
                                + verdict.get("required_fixes", []))[:2500])
    log["status"] = "failed"
    _w(repo / "runs" / "chain_build_log" / f"{template_id}.json",
       json.dumps(log, indent=2, default=str))
    return {"template_id": template_id, "status": "failed"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default=None)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--attempts", type=int, default=3)
    args = parser.parse_args(argv)
    repo = find_repo_root()
    plan = template_plan()
    if args.only:
        plan = [s for s in plan if s["template_id"] == args.only]

    all_rows: list[dict] = []
    statuses: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(build_one, repo, slot, args.attempts): slot["template_id"]
                   for slot in plan}
        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                result = {"template_id": futures[future], "status": f"crash: {str(exc)[:200]}"}
            statuses[result["template_id"]] = result["status"]
            all_rows.extend(result.get("rows", []))
            print(json.dumps({"template_id": result["template_id"],
                              "status": result["status"]}), flush=True)

    index_path = repo / "registry" / "chain_task_index.json"
    existing = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    known = {(r["template_id"], r["instance"]) for r in existing}
    merged = existing + [r for r in all_rows if (r["template_id"], r["instance"]) not in known]
    _w(index_path, json.dumps(merged, indent=2))
    summary = {
        "built": sum(1 for s in statuses.values() if s == "built"),
        "already_built": sum(1 for s in statuses.values() if s == "already_built"),
        "failed": sum(1 for s in statuses.values() if s == "failed"),
        "instances_indexed": len(merged),
    }
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
