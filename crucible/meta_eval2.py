"""Judge qualification for CRUCIBLE 2.0 (gold-set meta-evaluation).

Humanless analog of HealthBench's physician meta-eval, disclosed as such:
for a sample of instances we hold answers with KNOWN intended outcomes -
the generator's reference (strong) and weak answers, plus a programmatic
mutation of the reference with its machine-readable block stripped. Each
candidate judge family grades all of them; we gate on:
  - mean judged score: reference >= 0.80, weak <= 0.50,
  - anchors on the stripped mutation = all unmet (deterministic sanity),
  - per-criterion inter-judge agreement (Cohen's kappa) >= 0.60.
Failing the gate blocks the campaign (adjust judge protocol, re-run).
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

from .judge2 import judge_submission2
from .paths import find_repo_root


def _strip_json_block(text: str) -> str:
    return re.sub(r"```json\s*.*?```", "", text, flags=re.S)


def _kappa(pairs: list[tuple[bool, bool]]) -> float | None:
    if len(pairs) < 10:
        return None
    n = len(pairs)
    po = sum(1 for a, b in pairs if a == b) / n
    pa_yes = sum(1 for a, _ in pairs if a) / n
    pb_yes = sum(1 for _, b in pairs if b) / n
    pe = pa_yes * pb_yes + (1 - pa_yes) * (1 - pb_yes)
    return (po - pe) / (1 - pe) if pe < 1 else None


def run_meta_eval(sample_size: int = 24, out_name: str = "meta_eval2.json") -> dict:
    repo = find_repo_root()
    index = json.loads((repo / "registry" / "open_task_index.json").read_text(encoding="utf-8"))
    by_template: dict = {}
    for row in index:
        if row["condition"] in ("C0", "H1") and row["split"] != "sealed":
            by_template.setdefault(row["template_id"], []).append(row)
    rng = random.Random(2026)
    chosen = [rng.choice(rows) for _, rows in sorted(by_template.items())]
    rng.shuffle(chosen)
    chosen = chosen[:sample_size]

    report: dict = {"instances": [], "judges": {}}
    agreement_pairs: list[tuple[bool, bool]] = []
    stats = {"anthropic": {"ref": [], "weak": []}, "openai": {"ref": [], "weak": []}}
    anchor_violations = 0
    for row in chosen:
        inst = repo / row["path"]
        reference = re.sub(r"^<!--.*?-->\n", "",
                           (inst / "truth2" / "reference_answer.md").read_text(encoding="utf-8"))
        weak = re.sub(r"^<!--.*?-->\n", "",
                      (inst / "truth2" / "weak_answer.md").read_text(encoding="utf-8"))
        mutated = _strip_json_block(reference)
        per_judge: dict = {}
        for judge in ("anthropic", "openai"):
            ref_out = judge_submission2(inst, reference, judge)
            weak_out = judge_submission2(inst, weak, judge)
            stats[judge]["ref"].append(ref_out["score"])
            stats[judge]["weak"].append(weak_out["score"])
            per_judge[judge] = {"ref": ref_out, "weak": weak_out}
        mut_out = judge_submission2(inst, mutated, "anthropic")
        anchors_met = [v for v in mut_out["verdicts"]
                       if v["mode"] == "deterministic" and v["met"]]
        anchor_violations += len(anchors_met)
        for v_a in per_judge["anthropic"]["ref"]["verdicts"]:
            if v_a["mode"] != "judged":
                continue
            v_b = next((v for v in per_judge["openai"]["ref"]["verdicts"]
                        if v["id"] == v_a["id"]), None)
            if v_b:
                agreement_pairs.append((v_a["met"], v_b["met"]))
        for v_a in per_judge["anthropic"]["weak"]["verdicts"]:
            if v_a["mode"] != "judged":
                continue
            v_b = next((v for v in per_judge["openai"]["weak"]["verdicts"]
                        if v["id"] == v_a["id"]), None)
            if v_b:
                agreement_pairs.append((v_a["met"], v_b["met"]))
        report["instances"].append({
            "path": row["path"],
            "scores": {j: {"ref": per_judge[j]["ref"]["score"],
                           "weak": per_judge[j]["weak"]["score"]}
                       for j in per_judge}})

    kappa = _kappa(agreement_pairs)
    for judge in stats:
        ref_scores, weak_scores = stats[judge]["ref"], stats[judge]["weak"]
        report["judges"][judge] = {
            "mean_ref": round(sum(ref_scores) / len(ref_scores), 3) if ref_scores else None,
            "mean_weak": round(sum(weak_scores) / len(weak_scores), 3) if weak_scores else None,
        }
    report["inter_judge_kappa_on_judged_criteria"] = round(kappa, 3) if kappa is not None else None
    report["n_agreement_pairs"] = len(agreement_pairs)
    report["stripped_block_anchor_violations"] = anchor_violations
    gate = all(report["judges"][j]["mean_ref"] is not None
               and report["judges"][j]["mean_ref"] >= 0.80
               and report["judges"][j]["mean_weak"] <= 0.50 for j in report["judges"]) \
        and anchor_violations == 0 and (kappa is None or kappa >= 0.60)
    report["gate_passed"] = gate
    out = repo / "runs" / "release-2.0.0" / out_name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps({k: v for k, v in run_meta_eval().items()
                      if k != "instances"}, indent=2))
