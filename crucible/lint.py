"""Task lint rules beyond schema validity (guide Appendix C.3, subset).

Schema validity is necessary but insufficient; these checks enforce internal
consistency of a built task directory.
"""
from __future__ import annotations

from pathlib import Path

from .schemas import load_record, validate_record


def lint_task(task_dir: Path) -> list[str]:
    problems: list[str] = []
    task_dir = Path(task_dir).resolve()

    manifest_path = task_dir / "verification" / "manifest.json"
    if not manifest_path.exists():
        return [f"verification/manifest.json missing in {task_dir}"]
    manifest = load_record(manifest_path)
    problems.extend(f"schema: {e}" for e in validate_record("verification-manifest", manifest))
    if problems:
        return problems

    claims = manifest["claims"]
    claim_ids = [c["claim_id"] for c in claims]

    # C.3 rule 1: claim IDs unique.
    duplicates = {cid for cid in claim_ids if claim_ids.count(cid) > 1}
    if duplicates:
        problems.append(f"duplicate claim_ids: {sorted(duplicates)}")

    # C.3 rule 2: gate and profile references resolve.
    gate = manifest["reliable_completion_gate"]
    known = set(claim_ids)
    for cid in gate["required_claim_ids"]:
        if cid not in known:
            problems.append(f"gate references unknown claim_id {cid}")
    for cid in gate.get("allowed_partial_claim_ids", []):
        if cid not in known:
            problems.append(f"gate allowed_partial references unknown claim_id {cid}")
    for profile in manifest["reporting_profiles"]:
        for cid in profile["claim_ids"]:
            if cid not in known:
                problems.append(f"profile {profile['profile_id']} references unknown claim_id {cid}")
        if profile["aggregation"] == "WEIGHTED_DIAGNOSTIC":
            weights = profile.get("weights", {})
            total = sum(weights.get(cid, 0) for cid in profile["claim_ids"])
            if abs(total - 1.0) > 1e-9:
                problems.append(
                    f"profile {profile['profile_id']}: WEIGHTED_DIAGNOSTIC weights sum to {total}, not 1"
                )

    # C.3 rule 3: every CRITICAL claim is gated or explicitly justified.
    justified = set(manifest.get("metadata", {}).get("justified_noncritical_gate_exclusions", []))
    for claim in claims:
        if claim["criticality"] == "CRITICAL" and claim["claim_id"] not in gate["required_claim_ids"]:
            if claim["claim_id"] not in justified:
                problems.append(
                    f"CRITICAL claim {claim['claim_id']} is not in the reliable-completion gate "
                    "and has no recorded justification"
                )

    # C.3 rules 4-6: truth references match the truth regime. Verifiers that
    # compare against a stored reference need a truth_ref; operational
    # verifiers (file contracts, consistency, re-execution) ARE the truth.
    NEEDS_TRUTH_REF = {
        "numeric_equivalence", "distribution_equivalence", "set_similarity",
        "rank_agreement", "structure_identity", "assignment_consistency",
        "hazard_claims", "authority_policy", "prospective_outcome",
    }
    for claim in claims:
        verifier = claim["verifier"]
        regime = claim["truth_regime"]
        if regime == "TR1" and verifier["kind"] in NEEDS_TRUTH_REF:
            has_ref = bool(verifier.get("truth_ref")) or (
                verifier.get("parameters", {}).get("expected") is not None
            )
            if not has_ref:
                problems.append(f"TR1 claim {claim['claim_id']} has no truth reference")
        if regime == "TR2":
            has_set = bool(verifier.get("acceptance_set_ref"))
            mandatory_human = claim.get("human_review", {}).get("mode") == "MANDATORY"
            if not has_set and not mandatory_human:
                problems.append(
                    f"TR2 claim {claim['claim_id']} needs an acceptance set or mandatory human review"
                )
        if regime == "TR3" and verifier["kind"] != "prospective_outcome":
            problems.append(f"TR3 claim {claim['claim_id']} must use the prospective_outcome verifier")
        # Rule 8: verifier version pinned.
        if not verifier.get("version"):
            problems.append(f"claim {claim['claim_id']}: verifier version not pinned")
        # Truth refs must resolve on disk.
        for key in ("truth_ref", "acceptance_set_ref"):
            ref = verifier.get(key)
            if ref and not (task_dir / ref).exists():
                problems.append(f"claim {claim['claim_id']}: {key} {ref} does not resolve")

    # Rule 7: required artifacts have a path pattern.
    for claim in claims:
        for req in claim.get("artifact_requirements", []):
            if req.get("required", True) and not req.get("path_pattern"):
                problems.append(
                    f"claim {claim['claim_id']}: required {req['artifact_kind']} artifact has no path_pattern"
                )

    # Task structure: agent-visible material and card must exist.
    if not (task_dir / "task_card" / "card.md").exists():
        problems.append("task_card/card.md missing")
    inputs_dir = task_dir / "inputs" / "agent_visible"
    if not inputs_dir.exists() or not any(inputs_dir.rglob("*")):
        problems.append("inputs/agent_visible/ missing or empty")

    # Rules 16-17: accepted and rejected example submissions must exist so the
    # verifier can be tested in both directions (no verification theater).
    for kind in ("accepted", "rejected"):
        test_dir = task_dir / "verification" / "tests" / kind
        if not test_dir.exists() or not any(test_dir.iterdir()):
            problems.append(f"verification/tests/{kind}/ missing: verifier untested in that direction")

    return problems
