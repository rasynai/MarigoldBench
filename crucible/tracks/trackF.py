"""Track F analog: randomized SIMULATED scientist-uplift crossover.

We have no human scientists (see LIMITATIONS.md), so the guide's Track F is
run as a methods rehearsal with LLM stand-ins:

- "scientist" = a junior-analyst persona (low effort, no verification gate);
- treatment  = access to a co-scientist (the OTHER provider) that supplies a
  method plan before the scientist works;
- crossover  = 2 participants x 2 matched task forms, counterbalanced so each
  participant does one aided and one unaided task, and each form is seen once
  per condition (guide 14.7);
- outcome    = blinded grading: the deterministic verification pipeline plus
  the reliable-completion gate. Graders (code) never see the condition.

Permitted claim: a treatment-effect ESTIMATE for simulated personas under this
protocol. Prohibited: any claim about real scientists.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ..agent import CONTRACT, _bundle_text, _write_submission
from ..llm import ModelClient
from ..packaging import build_agent_bundle
from ..verification import run_verification

JUNIOR_SYSTEM = """You are a junior analyst, one year into your first laboratory
job. You are careful but not experienced. Complete the delegated work item to
the best of your ability, honestly, using only the supplied files."""

ASSISTANT_SYSTEM = """You are an experienced co-scientist assisting a junior
analyst. Given the work item, write a concise method plan: the right analysis
steps, the validity checks that matter, and the pitfalls to avoid. Do NOT
compute or state final numeric answers - guide the method only."""

# Latin-square assignment: participant x (form, condition).
ASSIGNMENT = [
    {"participant": "openai", "form": "N0-s101", "condition": "alone"},
    {"participant": "openai", "form": "N0-s103", "condition": "assisted"},
    {"participant": "anthropic", "form": "N0-s101", "condition": "assisted"},
    {"participant": "anthropic", "form": "N0-s103", "condition": "alone"},
]


def _assistant_plan(task_dir: Path, assistant_provider: str) -> str:
    with tempfile.TemporaryDirectory(prefix="crucible-tf-") as tmp:
        bundle = Path(tmp) / "bundle"
        build_agent_bundle(task_dir, bundle)
        prompt = _bundle_text(bundle) + "\n\nWrite the method plan for the junior analyst."
    client = ModelClient(assistant_provider, purpose="trackF-assistant")
    return client.ask(ASSISTANT_SYSTEM, prompt, max_tokens=4000)


def _participant_attempt(task_dir: Path, out_dir: Path, provider: str, advice: str | None) -> dict:
    with tempfile.TemporaryDirectory(prefix="crucible-tf-") as tmp:
        bundle = Path(tmp) / "bundle"
        build_agent_bundle(task_dir, bundle)
        prompt = "Complete the following scientific work item.\n\n" + _bundle_text(bundle)
    if advice:
        prompt += "\n\n===== METHOD PLAN FROM YOUR CO-SCIENTIST =====\n" + advice
    prompt += "\n\n" + CONTRACT
    client = ModelClient(provider, purpose="trackF-participant", effort="low", max_tokens=24000)
    reply = client.ask_json(JUNIOR_SYSTEM, prompt)
    _write_submission(reply.get("files", {}), out_dir)
    return run_verification(task_dir, out_dir)


def run(out_dir: Path, instances_root: Path) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for cell in ASSIGNMENT:
        task_dir = instances_root / cell["form"]
        assistant = None
        if cell["condition"] == "assisted":
            assistant_provider = "anthropic" if cell["participant"] == "openai" else "openai"
            assistant = _assistant_plan(task_dir, assistant_provider)
        sub_dir = out_dir / f"{cell['participant']}-{cell['form']}-{cell['condition']}"
        outcome = _participant_attempt(task_dir, sub_dir, cell["participant"], assistant)
        results.append(
            {
                **cell,
                "reliable_completion": outcome["reliable_completion"],
                "failed_gate_claim_ids": outcome["failed_gate_claim_ids"],
                "diagnostic_profiles": outcome["diagnostic_profiles"],
            }
        )

    aided = [r["reliable_completion"] for r in results if r["condition"] == "assisted"]
    alone = [r["reliable_completion"] for r in results if r["condition"] == "alone"]
    ate = (sum(aided) / len(aided)) - (sum(alone) / len(alone)) if aided and alone else None
    report = {
        "design": "2 simulated participants x 2 matched forms, counterbalanced crossover",
        "primary_estimand": "ITT effect of co-scientist access on reliable completion (SIMULATED personas)",
        "results": results,
        "ate_estimate": ate,
        "n_caveat": "n=4 cells; a feasibility rehearsal of the protocol, not a powered study",
        "prohibited_claim": "no inference to real human scientists",
    }
    (out_dir / "trackF_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
