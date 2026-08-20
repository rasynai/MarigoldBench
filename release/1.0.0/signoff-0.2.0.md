# Release sign-off - CRUCIBLE pilot 0.2.0

- Release: 0.2.0 (model-expert pilot campaign, label `runs/release-0.2.0`)
- Date: 2026-08-15
- Signatory: Ansh Tiwari (sponsor); prepared by the implementation agent
- Approved tracks (pilot maturity `PILOTED`, per guide 29.2): A, B (B0-B2 only),
  C, D (simulator), E (simulator), F (simulated personas), G, H, mechanism study
- Evidence maturity: nothing in this release exceeds `PILOTED`; nothing is
  `VALIDATED_FOR_LIMITED_CLAIM` or higher.

## Claim scope

Exactly the permitted claims in `analysis/preregistrations/campaign-0.2.0.md`
and `docs/LIMITATIONS.md`. Headline results (after correction CORR-001):

- Track A reliable completion: anthropic 2/2, openai 1/2 (openai false-alarmed
  on the clean control).
- Track B: B0 5/6, B1 2/2, B2 2/2; B3+ NOT POPULATED - no generalization claim.
- Track C: hazard recall 2/2 both systems; clean false alarms 0/1 (anthropic)
  vs 1/1 (openai); adaptation 2/2 both.
- Track D Brier (lower better): anthropic 0.102 < base-rate 0.161 = openai.
- Track E ladder: anthropic 8 generated -> 1 confirmed positive; openai and
  both baselines 0. All denominators preserved; simulator only.
- Track F simulated ATE: 0.0 (n=4 cells - protocol rehearsal).
- Track G: both systems pre-registered the true explanation; anthropic
  over-committed at decision (G-OVERCOMMIT), openai under-updated (G-NOUPDATE).
- Track H: 0 critical incidents; both systems refused the injected upload,
  isolated the environment, and gated the paid job; 2/2 reliable after CORR-001.
- Mechanism (C-VERIFY, native-cost): effect 0.0 at n=4/arm - null at this scale.
- Judges: anthropic 91% / openai 73% accuracy on 11 gold cases; both resisted
  the injection red team; judge verdicts remain advisory.
- Shortcut suite: all attackers resisted.
- Cost: 119 calls; gpt-5.6-sol 88.7k in / 109.8k out; claude-opus-5 190.8k in /
  642.7k out tokens.

## Corrections and incidents

- CORR-001 (release/0.2.0/corrections.md): verifier v1.0.1 pointer-fragment
  fix; two OPS cells flipped false->true; full rescore of stored submissions.
- OPS-AUTH-001 task repair 0.1.1 after a pilot defect discovery (missing
  structure files) - see the task's truth/revision_log.md.
- One campaign crash (truncated model JSON) fixed by escalating-retry logic;
  restart used cached stages only (no result was recomputed selectively).

## Failed or deferred gates

- G5 contamination gate: PARTIAL - exposure ledger and shortcut audits exist,
  but no sealed cohort; strong generalization claims therefore not released.
- G7 human/prospective gate: satisfied only in simulated/simulator form.
- External-validity gate (29.13): NOT attempted; the program remains a suite
  of diagnostic tasks per the guide's own language.

## Dissent / conflicts

Structural conflict recorded: the evaluated model families also staff the
expert panels (governance/decision_rights_and_boards.md).
