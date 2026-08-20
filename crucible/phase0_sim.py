"""Phase 0 job analysis with SIMULATED participants (guide section 8).

We have no access to human scientists, so the critical-incident interviews are
conducted with LLM personas from two providers, and coded into the guide's
task ontology by a separate coder model. Every artifact is stamped
MODEL-SIMULATED: this establishes the machinery and produces provisional
weights, and its outputs must be replaced by real interviews before any
naturalistic-representativeness claim is made (see LIMITATIONS.md).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .llm import ModelClient

PERSONAS = [
    ("openai", "an analytical chemist running an LC-MS/HPLC lab in a mid-size pharma QC department"),
    ("anthropic", "an academic natural-products chemist who does NMR structure elucidation weekly"),
    ("openai", "a computational chemist supporting a medicinal chemistry team (docking, QSAR, conformers)"),
    ("anthropic", "a laboratory informatics manager responsible for data integrity and instrument software"),
]

INTERVIEW_SYSTEM = """You are role-playing a specific working scientist in a
critical-incident interview about your ACTUAL day-to-day work. Give concrete,
mundane, realistic incidents - not idealized or dramatic ones. Real work is
full of format problems, ambiguous requests, and boring verification."""

INTERVIEW_PROMPT = """You are: {persona}.

Describe, as JSON, four concrete recent work incidents:
{{"incidents": [{{
   "title": "...",
   "initial_request": "the exact-ish wording of how the task arrived",
   "what_happened": "3-5 sentences, concrete",
   "files_and_tools": [...],
   "time_spent_hours": <number>,
   "error_consequence": "what a wrong result would have cost",
   "would_delegate_to_ai": true/false,
   "why_or_why_not": "...",
   "workflow_stage_guess": "one of: request_interpretation, literature, data_acquisition,
      qc_preprocessing, method_selection, computation, validation_controls,
      interpretation_uncertainty, packaging_provenance, decision, monitoring_recovery"
}}]}}
Include at least one incident where a plausible result was later found wrong,
and one where the correct outcome was a negative/null/'cannot report' result.
"""

CODER_SYSTEM = """You are a qualitative-research coder applying a fixed taxonomy
to interview incidents. Code conservatively; use 'other' only if truly nothing
fits."""

STAGES = [
    "request_interpretation", "literature", "data_acquisition", "qc_preprocessing",
    "method_selection", "computation", "validation_controls",
    "interpretation_uncertainty", "packaging_provenance", "decision",
    "monitoring_recovery", "other",
]


def run(repo_root: Path) -> dict:
    phase0_dir = repo_root / "phase0"
    phase0_dir.mkdir(exist_ok=True)

    incidents = []
    for provider, persona in PERSONAS:
        client = ModelClient(provider, purpose="phase0-interview", effort="low")
        reply = client.ask_json(INTERVIEW_SYSTEM, INTERVIEW_PROMPT.format(persona=persona))
        for incident in reply.get("incidents", []):
            incident["persona"] = persona
            incident["source_model_provider"] = provider
            incidents.append(incident)

    with (phase0_dir / "incidents_simulated.jsonl").open("w", encoding="utf-8") as fh:
        for incident in incidents:
            fh.write(json.dumps(incident) + "\n")

    # Independent coding pass by the OTHER provider family than the narrator.
    coded = []
    for incident in incidents:
        coder_provider = "anthropic" if incident["source_model_provider"] == "openai" else "openai"
        coder = ModelClient(coder_provider, purpose="phase0-coding", effort="low")
        code = coder.ask_json(
            CODER_SYSTEM,
            "Taxonomy stages: " + ", ".join(STAGES) + "\n\nIncident:\n"
            + json.dumps({k: incident[k] for k in ("title", "what_happened", "initial_request")})
            + '\n\nRespond JSON: {"stage": "...", "consequence": "low"|"medium"|"high",'
            ' "automation_appropriate": true/false}',
        )
        coded.append({**incident, "coded": code})

    stage_counts: dict[str, int] = {}
    for incident in coded:
        stage = incident.get("coded", {}).get("stage", "other")
        if stage not in STAGES:
            stage = "other"
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    total = sum(stage_counts.values()) or 1
    weights = {stage: round(count / total, 3) for stage, count in sorted(stage_counts.items())}

    agreement = sum(
        1
        for incident in coded
        if incident.get("workflow_stage_guess") == incident.get("coded", {}).get("stage")
    )
    synthesis = {
        "status": "MODEL-SIMULATED (guide 8: replace with real interviews before any representativeness claim)",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "personas": [p for _, p in PERSONAS],
        "n_incidents": len(coded),
        "naturalistic_stage_weights_provisional": weights,
        "narrator_coder_stage_agreement": f"{agreement}/{len(coded)}",
        "other_rate": stage_counts.get("other", 0) / total,
        "notes": [
            "Narrator and coder are always different model families (independent coding analog).",
            "Weights are provisional policy inputs, not naturalistic evidence.",
        ],
    }
    (phase0_dir / "interview_synthesis.json").write_text(json.dumps(synthesis, indent=2), encoding="utf-8")
    (phase0_dir / "naturalistic_weights_provisional.json").write_text(
        json.dumps(weights, indent=2), encoding="utf-8"
    )
    with (phase0_dir / "incidents_coded.jsonl").open("w", encoding="utf-8") as fh:
        for incident in coded:
            fh.write(json.dumps(incident) + "\n")
    return synthesis
