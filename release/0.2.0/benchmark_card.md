# CRUCIBLE pilot 0.2.0 - benchmark card

**What this measures:** whether two LLM reference agents (`gpt-5.6-sol`,
`claude-opus-5`, no tools, at most one verification-gated repair round) can
reliably complete five bounded synthetic chemistry/operations work items; plus
hazard adaptation, forecasting and experimental design inside a hidden
simulator, simulated-persona uplift, epistemic checkpoint behavior, authority
compliance, and the causal effect of the verification-gate component.

**What this does NOT measure:** real scientific work, real discovery, human
uplift, deployment safety, or contamination-resistant generalization. Every
expert role is an LLM (docs/LIMITATIONS.md); every result is bounded by that.

**Target population:** none claimed. Tasks are synthetic constructions from
one source cluster, labeled stress/prototype, with provisional weights from a
MODEL-SIMULATED Phase 0.

**Truth regimes:** TR1 (independent dual derivation, frozen tolerances), TR2
(machine-readable acceptance sets + LLM analyst panel + adversarial
falsification review), TR3-analog (hidden simulator outcomes resolved after
registration).

**Holdout ladder:** B0-B2 populated; B3+ and sealed cohorts absent — the
exposure ledger (registry/exposure_ledger.json) records this per instance.

**Scoring:** non-compensatory reliable-completion gate; partial credit is
diagnostic only; every rate published with its denominator; cluster-aware
intervals. LLM judges are advisory, cross-family only, and meta-evaluated on a
gold set with an injection red team before their verdicts are reported.

**Prohibited claims:** "discovers", "safe", "validated co-scientist",
"generalizes", "human-level", any real-world capability claim, any marketing
use.

**Versioning:** truth packages carry versions; the OPS-AUTH-001 task was
repaired (0.1.1) after a pilot defect discovery — see its truth/revision_log.md.
