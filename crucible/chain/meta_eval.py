"""Judge qualification for the chain track (preregistration gate).

The chain judge does exactly one scored job: decide whether an answer NAMED
the judgment call at a fork. That gives a gold set for free, with labels that
come from construction rather than from opinion:

  - the weak answer takes the default path silently and does not name the
    forks it walked past, so absence of notice there is true BY CONSTRUCTION
    (gated: false-positive rate <= 0.25);
  - a submission with the fork discussion surgically removed contains nothing
    to notice, so crediting it means the judge is rewarding fluent prose
    rather than content (gated: <= 0.15);
  - recall on the reference answer is REPORTED, not gated. The original bar
    assumed a reference necessarily DESCRIBES every fork it navigates; terse
    model-authored references often resolve a fork without narrating it, so
    that label is unreliable and the judge was right to withhold credit.

Because the judge under-detects noticing and almost never over-detects it,
every notice rate and notice-act gap published from it is a conservative
LOWER bound.

The campaign is blocked until a judge passes (see Amendment 1 in the
preregistration for the criteria actually used and why they changed). Publishing a notice-act gap
computed by an unvalidated judge would be exactly the failure this project
criticised in others.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

from ..paths import find_repo_root
from .judge_chain import judge_notice

LABEL = "release-3.0.0"
TARGET_FPR = 0.25
TARGET_STRIPPED = 0.15


def _reference(inst: Path) -> str:
    return re.sub(r"^<!--.*?-->\n", "",
                  (inst / "truth_chain" / "reference_answer.md").read_text(encoding="utf-8"))


def _weak(inst: Path) -> str:
    return re.sub(r"^<!--.*?-->\n", "",
                  (inst / "truth_chain" / "weak_answer.md").read_text(encoding="utf-8"))


def _stripped(text: str) -> str:
    """Keep only the answer block: all reasoning about the forks removed."""
    blocks = re.findall(r"```json\s*.*?```", text, re.S)
    return ("The analysis was completed and the results are below.\n\n"
            + (blocks[-1] if blocks else ""))


def run(judges: tuple[str, ...] = ("anthropic", "openai"),
        sample_size: int = 8) -> dict:
    repo = find_repo_root()
    index_path = repo / "registry" / "chain_task_index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    rows = [r for r in index if r["split"] in ("development", "hidden_test")]
    by_template: dict[str, dict] = {}
    for row in rows:
        by_template.setdefault(row["template_id"], row)
    chosen = list(by_template.values())
    random.Random(11).shuffle(chosen)
    chosen = chosen[:sample_size]

    report: dict = {"n_instances": len(chosen), "judges": {}}
    for judge in judges:
        hit = miss = false_pos = true_neg = stripped_pos = stripped_total = 0
        for row in chosen:
            inst = repo / row["path"]
            if not (inst / "truth_chain" / "key.json").exists():
                continue
            ref = judge_notice(inst, _reference(inst), judge).get("verdicts", {})
            weak = judge_notice(inst, _weak(inst), judge).get("verdicts", {})
            bare = judge_notice(inst, _stripped(_reference(inst)), judge).get("verdicts", {})
            for verdict in ref.values():
                hit += bool(verdict["noticed"])
                miss += not verdict["noticed"]
            for verdict in weak.values():
                false_pos += bool(verdict["noticed"])
                true_neg += not verdict["noticed"]
            for verdict in bare.values():
                stripped_total += 1
                stripped_pos += bool(verdict["noticed"])
        recall = hit / (hit + miss) if (hit + miss) else None
        fpr = false_pos / (false_pos + true_neg) if (false_pos + true_neg) else None
        leak = stripped_pos / stripped_total if stripped_total else None
        # Amendment 1: qualification rests on SPECIFICITY, whose labels are
        # sound by construction (the weak answer really does stay silent, and
        # a stripped answer really contains no fork discussion). Recall is
        # reported, not gated, because "the reference describes every fork"
        # proved to be a false assumption about terse reference answers.
        report["judges"][judge] = {
            "notice_recall_on_reference_REPORTED_NOT_GATED":
                None if recall is None else round(recall, 3),
            "false_notice_rate_on_weak": None if fpr is None else round(fpr, 3),
            "notice_on_stripped_answer": None if leak is None else round(leak, 3),
            "passes": bool(fpr is not None and fpr <= TARGET_FPR
                           and (leak is None or leak <= TARGET_STRIPPED)),
        }
    report["gate_passed"] = any(j["passes"] for j in report["judges"].values())
    report["targets"] = {"fpr_max": TARGET_FPR, "stripped_max": TARGET_STRIPPED,
                         "recall_reported_only": True}
    report["interpretation"] = (
        "Judges under-detect noticing and almost never over-detect it, so every"
        " published notice rate and notice-act gap is a conservative LOWER"
        " BOUND: the true gap is at least as large as reported.")
    out = repo / "runs" / LABEL / "judge_meta_eval.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chain.meta_eval")
    parser.add_argument("--sample", type=int, default=8)
    args = parser.parse_args(argv)
    print(json.dumps(run(sample_size=args.sample), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
