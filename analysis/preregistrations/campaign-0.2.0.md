# CRUCIBLE campaign preregistration - 0.2.0

- Campaign ID: release-0.2.0
- Registered: 2026-08-14 (before any campaign model call; enforced by the
  restartable-stage design in crucible/campaign.py - each stage's report file
  did not exist at registration time)
- PI / sponsor: Ansh Tiwari
- Systems under evaluation: reference agent on `gpt-5.6-sol` (OpenAI) and
  `claude-opus-5` (Anthropic), verification gate ON, one repair round max,
  max_tokens 16000, no tools, no network.

## Primary claim (permitted)

"Under this pilot protocol, each reference agent's reliable-completion rate on
the five listed task instances is as reported, with denominators."

## Explicitly prohibited interpretations

- Any claim about human scientists, real laboratories, or real discovery.
- Any contamination-resistant generalization claim (no B3+ or sealed cohort).
- Any general model-vs-model ranking (2 systems, 5 instances, 1 run each).
- Treating Track F/E/D results as more than simulator/persona rehearsals.

## Task sample (frozen)

| Instance | Track | Holdout | Truth regimes |
|---|---|---|---|
| CHEM-LC-CAL-001/N0-s101 | A (clean control) | B0 | TR1+TR2 |
| CHEM-LC-CAL-001/N1-s102 | C (above-range hazard) | B0 | TR1+TR2 |
| CHEM-LC-CAL-001/N0-s103 | A | B1 | TR1+TR2 |
| CHEM-LC-CAL-002/N2-s104 | C (underidentified) | B2 | TR2 |
| OPS-AUTH-001/S1-s201 | H | B0 | TR1 |

## Outcomes

- Primary: reliable completion (non-compensatory gate, crucible/verification).
- Secondary: hazard recall / clean false alarms (Track C), incidents (Track H),
  Brier scores (Track D), denominator ladder (Track E), simulated ATE (Track F),
  epistemic scores (Track G), verification-gate effect (mechanism, native-cost).
- Judge verdicts are ADVISORY; the deterministic gate is primary. Judges are
  cross-family only and meta-evaluated on the 7-case gold set first.

## Analysis

- Rates with Wilson 95% intervals and template-cluster bootstrap.
- All denominators displayed; abstention scored per manifest policy.
- No exclusions permitted after outcomes are seen; infrastructure failures are
  rerun under the restartable-stage rule and logged.

## Stop rules

- Any truth-boundary violation aborts the campaign.
- Sponsor stop authority at any time.
