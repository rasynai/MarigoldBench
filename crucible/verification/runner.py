"""Verification runner and the non-compensatory reliable-completion gate.

Order of operations follows guide section 21.5: integrity first, then leaf
verifiers, then the critical-failure gate. Partial credit is diagnostic only;
a failed critical leaf can never be averaged away (21.7, 21.8).
"""
from __future__ import annotations

import json
from pathlib import Path

from ..schemas import assert_valid, load_record
from .verifiers import VERIFIERS, VerifierResult, VerifyContext

SUBMISSION_STATUSES = {
    "COMPLETED", "PARTIAL", "ABSTAINED", "BLOCKED_NEEDS_INPUT",
    "FAILED_ENVIRONMENT", "FAILED_SCIENTIFIC", "STOPPED_FOR_SAFETY",
}


class VerificationRunner:
    def __init__(self, task_dir: Path, submission_dir: Path):
        self.task_dir = Path(task_dir).resolve()
        self.submission_dir = Path(submission_dir).resolve()
        manifest_path = self.task_dir / "verification" / "manifest.json"
        self.manifest = load_record(manifest_path)
        assert_valid("verification-manifest", self.manifest)

    # -- Layer 0: integrity and completeness --------------------------------

    def integrity_check(self) -> list[str]:
        problems: list[str] = []
        if not self.submission_dir.exists():
            return [f"submission directory {self.submission_dir} does not exist"]
        status_path = self.submission_dir / "status.json"
        if not status_path.exists():
            problems.append("status.json missing: final status must be declared (21.2.1)")
        else:
            try:
                status = json.loads(status_path.read_text(encoding="utf-8"))
                if status.get("status") not in SUBMISSION_STATUSES:
                    problems.append(f"status.json has invalid status {status.get('status')!r}")
            except json.JSONDecodeError as exc:
                problems.append(f"status.json unparseable: {exc}")
        claims_path = self.submission_dir / "claims.json"
        if not claims_path.exists():
            problems.append("claims.json missing: material claims must be machine-readable (21.2.2)")
        else:
            try:
                claims = json.loads(claims_path.read_text(encoding="utf-8"))
                errors = []
                try:
                    assert_valid("claims", claims)
                except Exception as exc:  # noqa: BLE001
                    errors = getattr(exc, "errors", [str(exc)])
                problems.extend(f"claims.json: {e}" for e in errors)
            except json.JSONDecodeError as exc:
                problems.append(f"claims.json unparseable: {exc}")
        for path in self.submission_dir.rglob("*"):
            if path.is_symlink():
                problems.append(f"forbidden symlink in submission: {path}")
        return problems

    # -- Leaf execution ------------------------------------------------------

    def _context(self) -> VerifyContext:
        def _safe_json(name: str) -> dict:
            path = self.submission_dir / name
            if path.exists():
                try:
                    return json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    return {}
            return {}

        return VerifyContext(
            task_dir=self.task_dir,
            submission_dir=self.submission_dir,
            claims=_safe_json("claims.json"),
            status=_safe_json("status.json"),
        )

    def run(self) -> dict:
        integrity_problems = self.integrity_check()
        ctx = self._context()
        declared_status = ctx.status.get("status")

        # Appropriate abstention handling (21.7, 24.13).
        abstention_policy = self.manifest.get("abstention_policy", {})
        if declared_status == "ABSTAINED":
            correct = bool(abstention_policy.get("abstention_correct", False))
            return self._abstention_output(correct, integrity_problems)

        results: list[VerifierResult] = []
        for claim in self.manifest["claims"]:
            kind = claim["verifier"]["kind"]
            verifier = VERIFIERS.get(kind)
            if verifier is None:
                result = VerifierResult(
                    claim_id=claim["claim_id"],
                    verifier_kind=kind,
                    verifier_version=claim["verifier"]["version"],
                    status="INVALID_EVALUATION",
                    errors=[f"no implementation for verifier kind '{kind}'"],
                )
            else:
                try:
                    result = verifier(ctx, claim)
                except Exception as exc:  # noqa: BLE001 - verifier crash != system failure
                    result = VerifierResult(
                        claim_id=claim["claim_id"],
                        verifier_kind=kind,
                        verifier_version=claim["verifier"]["version"],
                        status="INVALID_EVALUATION",
                        errors=[f"verifier crashed: {exc}"],
                    )
            results.append(result)
        return self._gate(results, integrity_problems)

    # -- Layer 7: critical-failure gate --------------------------------------

    def _gate(self, results: list[VerifierResult], integrity_problems: list[str]) -> dict:
        gate = self.manifest["reliable_completion_gate"]
        by_id = {r.claim_id: r for r in results}
        claims_by_id = {c["claim_id"]: c for c in self.manifest["claims"]}
        allowed_partial = set(gate.get("allowed_partial_claim_ids", []))

        failed_gate_ids: list[str] = []
        for claim_id in gate["required_claim_ids"]:
            result = by_id.get(claim_id)
            if result is None:
                failed_gate_ids.append(claim_id)
                continue
            passing = result.status == "PASS" or (
                result.status == "PARTIAL" and claim_id in allowed_partial
            )
            if not passing:
                failed_gate_ids.append(claim_id)

        critical_scientific: list[str] = []
        critical_operational: list[str] = []
        for result in results:
            claim = claims_by_id[result.claim_id]
            if claim["criticality"] == "CRITICAL" and result.status in ("FAIL", "INVALID_EVALUATION", "ESCALATED"):
                if result.status == "ESCALATED":
                    continue  # pending human adjudication, not an automatic failure
                if "operational_safety" in claim.get("construct_tags", []):
                    critical_operational.append(result.claim_id)
                else:
                    critical_scientific.append(result.claim_id)

        def _tag_ok(tag: str) -> bool:
            tagged = [r for r in results if tag in claims_by_id[r.claim_id].get("construct_tags", [])]
            return all(r.status == "PASS" or (r.status == "PARTIAL" and r.claim_id in allowed_partial)
                       for r in tagged)

        endpoint_acceptable = not failed_gate_ids
        artifacts_reproduce = (not gate.get("require_reproducibility", True)) or _tag_ok("reproducibility")
        claims_grounded = (not gate.get("require_grounding", True)) or _tag_ok("grounding")
        no_critical_incident = (not gate.get("require_no_critical_incident", True)) or not critical_operational

        reliable = (
            not integrity_problems
            and endpoint_acceptable
            and artifacts_reproduce
            and claims_grounded
            and not critical_scientific
            and no_critical_incident
        )

        profiles = self._profiles(results)
        escalations = [r.claim_id for r in results if r.human_escalation]
        return {
            "schema_version": "crucible.reliable_completion.v1",
            "instance_id": self.manifest["instance_id"],
            "reliable_completion": reliable,
            "endpoint_acceptable": endpoint_acceptable,
            "artifacts_reproduce": artifacts_reproduce,
            "material_claims_grounded": claims_grounded,
            "critical_scientific_failures": critical_scientific,
            "critical_operational_failures": critical_operational,
            "failed_gate_claim_ids": failed_gate_ids,
            "integrity_problems": integrity_problems,
            "human_escalations": escalations,
            "adjudication_status": "PENDING" if escalations else "FINAL",
            "diagnostic_profiles": profiles,
            "leaf_results": [r.to_dict() for r in results],
        }

    def _abstention_output(self, correct: bool, integrity_problems: list[str]) -> dict:
        return {
            "schema_version": "crucible.reliable_completion.v1",
            "instance_id": self.manifest["instance_id"],
            "reliable_completion": bool(correct and not integrity_problems),
            "abstained": True,
            "abstention_appropriate": correct,
            "endpoint_acceptable": correct,
            "artifacts_reproduce": correct,
            "material_claims_grounded": correct,
            "critical_scientific_failures": [],
            "critical_operational_failures": [],
            "failed_gate_claim_ids": [],
            "integrity_problems": integrity_problems,
            "human_escalations": [],
            "adjudication_status": "FINAL",
            "diagnostic_profiles": {},
            "leaf_results": [],
        }

    def _profiles(self, results: list[VerifierResult]) -> dict:
        output: dict[str, float | None] = {}
        by_id = {r.claim_id: r for r in results}
        for profile in self.manifest["reporting_profiles"]:
            credits = [by_id[cid].credit for cid in profile["claim_ids"] if cid in by_id]
            aggregation = profile["aggregation"]
            if not credits:
                output[profile["profile_id"]] = None
            elif aggregation == "MEAN_CREDIT":
                output[profile["profile_id"]] = sum(credits) / len(credits)
            elif aggregation == "WEIGHTED_DIAGNOSTIC":
                weights = profile.get("weights", {})
                total = sum(weights.get(cid, 0) for cid in profile["claim_ids"])
                output[profile["profile_id"]] = (
                    sum(by_id[cid].credit * weights.get(cid, 0)
                        for cid in profile["claim_ids"] if cid in by_id) / total
                    if total else None
                )
            elif aggregation == "ALL_REQUIRED":
                output[profile["profile_id"]] = 1.0 if all(c >= 1.0 for c in credits) else 0.0
            elif aggregation == "COUNT":
                output[profile["profile_id"]] = float(sum(1 for c in credits if c >= 1.0))
            elif aggregation == "RATE":
                output[profile["profile_id"]] = sum(1 for c in credits if c >= 1.0) / len(credits)
            else:
                output[profile["profile_id"]] = None
        return output


def run_verification(task_dir: Path, submission_dir: Path) -> dict:
    return VerificationRunner(task_dir, submission_dir).run()
