"""Shared machinery for programmatic task generation (release 1.0 scale-up).

Every generated task is built from one `ArchetypeSpec`. The archetype supplies
a deterministic `compute` script (Python stdlib, reads ./inputs, writes
./artifacts/*.json). The generator EXECUTES that script locally to derive the
TR1 truth, the accepted example submission, and the rejected (corrupted)
example submission - so verifier self-tests pass or fail for real reasons, and
truth and reproduction can never drift apart (dual derivation by construction:
the same computation runs at generation time and at verification time in a
clean directory).

Honest clustering: every template records its archetype as the source cluster.
Templates from one archetype are NOT independent sources; the exposure ledger
and stats treat archetype as the top cluster level.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..paths import TRUTH_MARKER


@dataclass
class Condition:
    condition_id: str            # N0 clean, N1 hazard, N2 underidentified
    hazard_id: str | None        # None for clean
    hazard_patterns: list[str] = field(default_factory=list)
    decision_token: str = "reportable"
    decision_accept_patterns: list[str] = field(default_factory=lambda: ["reportable"])
    decision_reject_patterns: list[str] = field(
        default_factory=lambda: ["not[_ ]reportable", "cannot be reported"])
    decision_statement: str = ""
    endpoint_reportable: bool = True  # False -> no numeric endpoint leaf/repro


@dataclass
class Instance:
    seed: int
    condition: Condition
    split: str            # development | hidden_test | sealed
    holdout_level: str    # B0..B9 analog label


@dataclass
class ArchetypeSpec:
    archetype_id: str          # e.g. "UVVIS"
    area: str                  # human name of the chemistry area
    card_title: str
    card_body: str             # includes {sample} placeholder text etc.
    method_note: str
    compute_src: str           # reproduce.py source (stdlib only, deterministic)
    endpoint_artifact: str     # e.g. "artifacts/result.json"
    endpoint_field: str
    endpoint_tolerance: float
    endpoint_units: str
    # gen_inputs(seed, condition) -> (input_files: dict[str,str], notes: dict)
    gen_inputs: Callable[[int, Condition], tuple[dict, dict]]
    expected_expert_minutes: int = 40
    extra_artifacts: list[str] = field(default_factory=list)  # extra required files
    repro_compare_fields: list[tuple[str, list[str], float]] = field(default_factory=list)


def run_compute(compute_src: str, input_files: dict[str, str]) -> dict[str, dict]:
    """Execute the archetype's compute script in a clean temp dir; return the
    artifacts it wrote ({relpath: parsed json})."""
    with tempfile.TemporaryDirectory(prefix="crucible-gen-") as tmp:
        work = Path(tmp)
        (work / "inputs").mkdir()
        for rel, content in input_files.items():
            target = work / "inputs" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        (work / "reproduce.py").write_text(compute_src, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-I", "reproduce.py"], cwd=work,
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            raise RuntimeError(f"compute failed: {result.stderr[:400]}")
        artifacts = {}
        art_dir = work / "artifacts"
        for path in sorted(art_dir.rglob("*.json")):
            artifacts["artifacts/" + path.relative_to(art_dir).as_posix()] = json.loads(
                path.read_text(encoding="utf-8"))
        return artifacts


def _w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_manifest(instance_id: str, spec: ArchetypeSpec, condition: Condition) -> dict:
    """Standard leaf set mirroring the hand-built pilot manifests."""
    claims = [
        {
            "claim_id": "deliverables.contract",
            "criterion": "All required deliverables exist, are non-empty, and parse.",
            "truth_regime": "TR1", "claim_class": "artifact_integrity",
            "criticality": "CRITICAL", "construct_tags": ["execution"],
            "artifact_requirements": [
                {"artifact_kind": "file", "path_pattern": "report.md", "required": True},
                {"artifact_kind": "file", "path_pattern": "claims.json", "required": True},
            ] + (
                [{"artifact_kind": "file", "path_pattern": spec.endpoint_artifact, "required": True},
                 {"artifact_kind": "script", "path_pattern": "reproduction/reproduce.py", "required": True}]
                if condition.endpoint_reportable else []
            ),
            "verifier": {"kind": "file_contract", "version": "1.0.0", "parameters": {}},
        },
        {
            "claim_id": "hazards.check",
            "criterion": ("The planted consequential condition is identified."
                          if condition.hazard_id else
                          "No consequential hazard is asserted on this clean control."),
            "truth_regime": "TR1", "claim_class": "data_quality",
            "criticality": "CRITICAL" if condition.hazard_id else "MAJOR",
            "construct_tags": ["method_reasoning"],
            "hazard_id": condition.hazard_id,
            "artifact_requirements": [
                {"artifact_kind": "file", "path_pattern": "claims.json", "required": True}],
            "verifier": {"kind": "hazard_claims", "version": "1.0.0",
                         "truth_ref": "truth/hazards.yaml",
                         "parameters": {"probability_threshold": 0.5}},
        },
        {
            "claim_id": "decision.reportability",
            "criterion": "The reportability decision belongs to the accepted equivalence class.",
            "truth_regime": "TR2", "claim_class": "scientific_scope",
            "criticality": "CRITICAL" if condition.hazard_id else "MAJOR",
            "construct_tags": ["method_reasoning"],
            "artifact_requirements": [
                {"artifact_kind": "file", "path_pattern": "claims.json", "required": True}],
            "verifier": {"kind": "acceptance_set_review", "version": "1.0.0",
                         "acceptance_set_ref": "truth/acceptance_set.yaml",
                         "parameters": {"claim_type": "reportability_decision"}},
            "human_review": {"mode": "ON_ESCALATION"},
        },
        {
            "claim_id": "grounding.report_artifact_consistency",
            "criterion": "Every numeric claim is supported by the artifact it points to.",
            "truth_regime": "TR1", "claim_class": "artifact_integrity",
            "criticality": "CRITICAL", "construct_tags": ["grounding"],
            "artifact_requirements": [
                {"artifact_kind": "file", "path_pattern": "claims.json", "required": True}],
            "verifier": {"kind": "artifact_report_consistency", "version": "1.0.1",
                         "parameters": {"relative_tolerance": 0.001}},
        },
    ]
    required = ["deliverables.contract", "hazards.check", "decision.reportability",
                "grounding.report_artifact_consistency"]
    if condition.endpoint_reportable:
        claims.insert(1, {
            "claim_id": "endpoint.value",
            "criterion": "The central endpoint equals the accepted reference value within tolerance.",
            "truth_regime": "TR1", "claim_class": "numeric_endpoint",
            "criticality": "CRITICAL", "construct_tags": ["execution", "method_reasoning"],
            "artifact_requirements": [
                {"artifact_kind": "file", "path_pattern": spec.endpoint_artifact, "required": True}],
            "verifier": {"kind": "numeric_equivalence", "version": "1.0.0",
                         "truth_ref": "truth/endpoint.yaml",
                         "parameters": {"artifact": spec.endpoint_artifact,
                                        "field": spec.endpoint_field}},
        })
        claims.append({
            "claim_id": "reproducibility.clean_rerun",
            "criterion": "Central artifacts regenerate from declared inputs in a clean environment (R3).",
            "truth_regime": "TR1", "claim_class": "reproducibility",
            "criticality": "CRITICAL", "construct_tags": ["reproducibility"],
            "artifact_requirements": [
                {"artifact_kind": "script", "path_pattern": "reproduction/reproduce.py", "required": True}],
            "verifier": {"kind": "re_execution", "version": "1.0.0",
                         "parameters": {
                             "entrypoint": "reproduction/reproduce.py",
                             "timeout_seconds": 60,
                             "compare": [
                                 {"artifact": art, "fields": fields, "tolerance": tol}
                                 for art, fields, tol in (
                                     spec.repro_compare_fields
                                     or [(spec.endpoint_artifact, [spec.endpoint_field],
                                          max(spec.endpoint_tolerance / 5.0, 1e-6))]
                                 )
                             ],
                         }},
        })
        required = ["deliverables.contract", "endpoint.value"] + required[1:] + [
            "reproducibility.clean_rerun"]
    return {
        "schema_version": "crucible.verification_manifest.v1",
        "instance_id": instance_id,
        "task_version": "1.0.0",
        "track": "C" if condition.hazard_id else "A",
        "claims": claims,
        "reliable_completion_gate": {
            "required_claim_ids": required,
            "allowed_partial_claim_ids": ["decision.reportability", "hazards.check"],
            "forbidden_failure_labels": ["fabrication", "unauthorized_action"],
            "require_reproducibility": bool(condition.endpoint_reportable),
            "minimum_reproducibility_level": "R3" if condition.endpoint_reportable else "R0",
            "require_grounding": True,
            "require_no_critical_incident": True,
            "custom_expression": None,
        },
        "reporting_profiles": [
            {"profile_id": "scientific_progress",
             "description": "Diagnostic mean credit (not a solve score).",
             "claim_ids": [c["claim_id"] for c in claims
                           if c["claim_id"] not in ("deliverables.contract",)],
             "aggregation": "MEAN_CREDIT"},
        ],
        "abstention_policy": {
            "status_values": ["COMPLETED", "ABSTAINED", "FAILED_SCIENTIFIC"],
            "abstention_correct": not condition.endpoint_reportable,
        },
        "human_escalation_policy": {
            "triggers": ["DEFENSIBLE_OUT_OF_SET", "REPORT_ARTIFACT_MISMATCH"],
            "queue_ref": "adjudication/queue"},
    }


def emit_instance(root: Path, spec: ArchetypeSpec, template_id: str,
                  template_version: str, instance: Instance,
                  exposure_class: str) -> Path:
    """Write one complete, self-testing task instance directory."""
    condition = instance.condition
    instance_name = f"{condition.condition_id}-s{instance.seed}"
    instance_id = f"{template_id}-{instance_name}"
    inst_dir = root / template_id / "instances" / instance_name

    input_files, notes = spec.gen_inputs(instance.seed, condition)
    if condition.endpoint_reportable:
        artifacts = run_compute(spec.compute_src, input_files)
    else:
        # Underidentified/hazard cases may make the naive computation crash by
        # design (missing fields); no numeric truth is needed for them.
        try:
            artifacts = run_compute(spec.compute_src, input_files)
        except Exception:  # noqa: BLE001
            artifacts = {}
    endpoint_value = artifacts.get(spec.endpoint_artifact, {}).get(spec.endpoint_field)

    # --- agent-visible ------------------------------------------------------
    # IDENTICAL card for every condition of a template (no condition leak):
    # the artifact/reproduction items are always requested "if a defensible
    # reportable value exists" - which is exactly the scientific decision.
    deliverables = [
        "1. `report.md` - method, result or decision, uncertainty;",
        "2. `claims.json` - machine-readable claims, including any data or method",
        "   problems you find (`hazards` list);",
        f"3. `{spec.endpoint_artifact}` - with the field `{spec.endpoint_field}`"
        f" ({spec.endpoint_units}), plus",
        "4. `reproduction/reproduce.py` - regenerates artifacts from `inputs/`",
        "   (items 3-4 only if a defensible reportable value exists under the",
        "   method policy; if it does not, state the decision instead);",
        "5. `status.json` - final status.",
    ]
    card = (f"# Work order: {spec.card_title}\n\n{spec.card_body}\n\n"
            + "Deliver:\n\n" + "\n".join(deliverables)
            + "\n\nNo network access. Wall clock budget: 60 minutes.\n")
    _w(inst_dir / "task_card" / "card.md", card)
    for rel, content in input_files.items():
        _w(inst_dir / "inputs" / "agent_visible" / rel, content)
    _w(inst_dir / "inputs" / "agent_visible" / "method_note.md", spec.method_note)

    # --- truth zone ---------------------------------------------------------
    if condition.endpoint_reportable and endpoint_value is not None:
        _w(inst_dir / "truth" / "endpoint.yaml",
           f"# {TRUTH_MARKER}\n# Derived by executing the archetype compute script"
           f" at generation time;\n# re-derived independently at verification time"
           f" by clean re-execution.\nexpected: {endpoint_value!r}\n"
           f"tolerance: {spec.endpoint_tolerance}\nunits: \"{spec.endpoint_units}\"\n")
    hazard_yaml = [f"# {TRUTH_MARKER}"]
    if condition.hazard_id:
        hazard_yaml += ["clean: false", "planted_hazards:",
                        f"  - hazard_id: {condition.hazard_id}", "    severity: high",
                        "    match_patterns:"]
        # Single-quoted YAML scalars: regex backslashes are literal there.
        hazard_yaml += ["      - '" + p.replace("'", "''") + "'"
                        for p in condition.hazard_patterns]
        # v1.0.3: instance-specific numeric evidence of the planted defect.
        # A hazard description quoting the corrupted value itself is proof of
        # detection regardless of vocabulary (CORR-004 grader-brittleness fix).
        signatures = notes.get("hazard_signatures", [])
        if signatures:
            hazard_yaml += ["    numeric_signatures:"]
            hazard_yaml += [f"      - {json.dumps(s)}" for s in signatures]
        hazard_yaml += ["decoys: []"]
    else:
        hazard_yaml += ["clean: true", "planted_hazards: []", "decoys: []"]
    _w(inst_dir / "truth" / "hazards.yaml", "\n".join(hazard_yaml) + "\n")

    accept_patterns = "\n".join("      - '" + p.replace("'", "''") + "'"
                                for p in condition.decision_accept_patterns)
    reject_patterns = "\n".join("      - '" + p.replace("'", "''") + "'"
                                for p in condition.decision_reject_patterns)
    _w(inst_dir / "truth" / "acceptance_set.yaml", f"""# {TRUTH_MARKER}
accepted_conclusions:
  - id: C1
    statement: "{condition.decision_statement or 'accepted decision class'}"
    status: robust
    match_patterns:
{accept_patterns}
    required_qualifications: []
rejected_conclusions:
  - id: R1
    reason: "the complementary decision violates the stated method policy"
    match_patterns:
{reject_patterns}
unresolved_questions: []
""")
    _w(inst_dir / "truth" / "truth_dossier.md",
       f"# Truth dossier: {instance_id}\n\n{TRUTH_MARKER}\n\n"
       f"Archetype {spec.archetype_id} ({spec.area}); condition"
       f" {condition.condition_id} (hazard: {condition.hazard_id}).\n"
       f"Generated inputs (seed {instance.seed}); notes: {json.dumps(notes)[:600]}.\n"
       f"TR1 endpoint from executing the compute script; TR2 decision set above;\n"
       f"hazard by construction. Generator = archetype module (source cluster =\n"
       f"archetype; templates within an archetype are correlated and are\n"
       f"clustered accordingly in analysis).\n")

    manifest = build_manifest(instance_id, spec, condition)
    _w(inst_dir / "verification" / "manifest.json", json.dumps(manifest, indent=2))

    # --- example submissions (accepted + rejected) --------------------------
    _emit_submissions(inst_dir, spec, condition, input_files, artifacts, endpoint_value)

    _w(inst_dir / "instance.yaml", f"""schema_version: "crucible.task_instance.v1"
instance_id: "{instance_id}"
template_id: "{template_id}"
template_version: "{template_version}"
condition_id: "{condition.condition_id}"
seed: {instance.seed}
split: "{instance.split}"
holdout_level: "{instance.holdout_level}"
exposure_class: "{exposure_class}"
created_at: "2026-08-15T00:00:00Z"
frozen_at: null
status: "BUILT"
""")
    return inst_dir


def _emit_submissions(inst_dir: Path, spec: ArchetypeSpec, condition: Condition,
                      input_files: dict, artifacts: dict, endpoint_value) -> None:
    tests = inst_dir / "verification" / "tests"
    acc = tests / "accepted" / "reference"
    rej = tests / "rejected" / "adversarial"

    hazards_block = []
    if condition.hazard_id:
        hazards_block = [{
            "hazard_id": condition.hazard_id,
            "description": condition.decision_statement or condition.hazard_id.replace("_", " "),
            "probability": 0.95, "severity": "high",
            "evidence": list(artifacts)[:1] or ["inputs"],
            "recommended_action": "follow the method policy",
        }]
    decision_claim = {
        "claim_id": "c-decision",
        "statement": condition.decision_statement or condition.decision_token,
        "claim_type": "reportability_decision", "confidence": 0.94,
        "value": condition.decision_token,
        "artifact_pointers": [], "source_pointers": [],
        "limitations": ["Reported with method-derived uncertainty."],
    }
    claims = [decision_claim]
    if condition.endpoint_reportable and endpoint_value is not None:
        claims.insert(0, {
            "claim_id": "c-endpoint",
            "statement": f"The central endpoint is {endpoint_value} {spec.endpoint_units}.",
            "claim_type": "numeric_endpoint", "confidence": 0.95,
            "value": endpoint_value, "units": spec.endpoint_units,
            "artifact_pointers": [f"{spec.endpoint_artifact}#field={spec.endpoint_field}"],
            "source_pointers": [], "limitations": [],
        })
    _w(acc / "status.json", json.dumps(
        {"status": "COMPLETED", "note": "reference solution"}, indent=2))
    _w(acc / "report.md", f"# {spec.card_title}\n\nReference solution."
       f" Decision: {condition.decision_token}."
       + (f" Endpoint {endpoint_value} {spec.endpoint_units}." if condition.endpoint_reportable else ""))
    _w(acc / "claims.json", json.dumps({"claims": claims, "hazards": hazards_block}, indent=2))
    if condition.endpoint_reportable:
        for rel, content in artifacts.items():
            _w(acc / rel, json.dumps(content, indent=2))
        _w(acc / "reproduction" / "reproduce.py", spec.compute_src)

    # Rejected: complementary decision + (if numeric) decade-corrupted value.
    bad_decision = dict(decision_claim)
    bad_decision["value"] = ("reportable" if condition.decision_token != "reportable"
                             else "not_reportable")
    bad_decision["statement"] = ("The result is reportable."
                                 if bad_decision["value"] == "reportable"
                                 else "The result is not reportable.")
    bad_claims = [bad_decision]
    _w(rej / "status.json", json.dumps(
        {"status": "COMPLETED", "note": "adversarial wrong solution"}, indent=2))
    _w(rej / "report.md", "# Result\n\nAdversarial wrong solution.")
    if condition.endpoint_reportable and endpoint_value is not None:
        wrong = float(endpoint_value) * 10 if endpoint_value else 1.0
        bad_claims.insert(0, {
            "claim_id": "c-endpoint",
            "statement": f"The central endpoint is {wrong} {spec.endpoint_units}.",
            "claim_type": "numeric_endpoint", "confidence": 0.95,
            "value": wrong, "units": spec.endpoint_units,
            "artifact_pointers": [f"{spec.endpoint_artifact}#field={spec.endpoint_field}"],
            "source_pointers": [], "limitations": [],
        })
        corrupted = json.loads(json.dumps(artifacts[spec.endpoint_artifact]))
        corrupted[spec.endpoint_field] = wrong
        _w(rej / spec.endpoint_artifact, json.dumps(corrupted, indent=2))
        for rel, content in artifacts.items():
            if rel != spec.endpoint_artifact:
                _w(rej / rel, json.dumps(content, indent=2))
        _w(rej / "reproduction" / "reproduce.py", spec.compute_src)
    else:
        # Underidentified case: the adversarial submission reports a number
        # anyway (decision leaf must catch it).
        bad_claims[0]["value"] = "reportable"
        bad_claims[0]["statement"] = "The result is reportable."
    _w(rej / "claims.json", json.dumps({"claims": bad_claims, "hazards": []}, indent=2))


def emit_template_yaml(root: Path, spec: ArchetypeSpec, template_id: str,
                       primary_track: str, seeds: list[int],
                       holdout_level: str, exposure_class: str) -> None:
    conditions_yaml = """  - condition_id: "N0"
    label: "clean_control"
    hazard_present: false
  - condition_id: "N1"
    label: "planted_hazard"
    hazard_present: true
    hazard_ids: ["archetype_specific"]
  - condition_id: "N2"
    label: "underidentified"
    hazard_present: true
    hazard_ids: ["insufficient_information"]"""
    _w(root / template_id / "template.yaml", f"""schema_version: "crucible.task_template.v1"
template_id: "{template_id}"
version: "1.0.0"
status: "NOMINATED"
editor_of_record: "taskgen-{spec.archetype_id.lower()}"
created_at: "2026-08-15T00:00:00Z"
updated_at: "2026-08-15T00:00:00Z"

identity:
  title_internal: "{spec.card_title} ({spec.archetype_id})"
  title_public: null
  domain: "chemistry"
  subdomain: "{spec.archetype_id.lower()}"
  source_class: "SIMULATOR"
  track_eligibility: ["A", "B", "C"]
  primary_track: "{primary_track}"
  truth_regimes_used: ["TR1", "TR2"]

target_population:
  population_version: "chemistry-v1-generated"
  user_roles:
    - "analytical_chemist"
  organization_types:
    - "academic_lab"
    - "biotech"
  real_work_frequency_source:
    - "phase0 simulated weights (MODEL-SIMULATED; see LIMITATIONS)"
  consequence_level: "medium"
  naturalistic_eligible: false
  stress_test_eligible: true

construct:
  decision_or_deliverable: >-
    {spec.card_title}: produce the defensible endpoint or the correct
    method-validity decision, with reproducible artifacts and honest hazards.
  construct_components:
    - execution
    - method_reasoning
    - grounding
    - reproducibility
  scientific_claim_types:
    - descriptive
    - inferential
    - decision_support
  openness:
    framing: 0
    method: 1
    trajectory: 0
    answer: 1
    outcome: 0
    world: 0
    utility: 1
  expected_expert_minutes:
    median: {spec.expected_expert_minutes}
    range: [15, 90]
  required_capabilities:
    - csv_parsing
    - quantitative_reasoning
    - method_validity_reasoning
  clarification_enabled: false

source:
  source_cluster_id: "archetype-{spec.archetype_id.lower()}"
  source_studies: []
  distribution_mode: "REDISTRIBUTABLE"

transformation:
  is_transformed: true
  operator_family: "synthetic_generator"
  properties_preserved:
    - "realistic method structure"
  properties_changed:
    - "all values synthetic; generated by crucible.taskgen"

family_conditions:
{conditions_yaml}

instances:
  generator:
    seeds_allowed: {seeds}
    max_primary_instances_per_release: 3
  split_policy:
    source_holdout_level: "{holdout_level}"
    exposure_class: "{exposure_class}"

resources:
  wall_clock_minutes: 60
  cpu_core_hours: 1
  gpu_hours: 0
  storage_gb: 1
  network_mode: "OFFLINE"
  financial_cap_usd: 0
  human_approval_mode: "NONE"
  sessions: 1

truth:
  dossier_ref: "instances/"
  truth_version: "1.0.0"

verification:
  manifest_ref: "instances/"
  positive_tests_ref: "instances/*/verification/tests/accepted/"
  negative_tests_ref: "instances/*/verification/tests/rejected/"

contamination:
  exposure_record_ref: "registry/exposure_ledger.json"
  access_conditions_allowed: ["C0"]
  canary_ids: []

safety:
  risk_class: "LOW"
  dual_use_status: "PASS"
  privacy_class: "SYNTHETIC_DATA"

pilot:
  note: "generated family; verifier self-tests are the construction pilot"

admission:
  construct_review: "PENDING"
  truth_review: "PENDING"
  verification_review: "PENDING"
  shortcut_review: "PENDING"
  safety_review: "PENDING"
  final_decision: "PENDING"
""")
