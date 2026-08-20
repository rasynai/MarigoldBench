# Governance bodies and decision rights (pilot scale)

Because the program has one human (the sponsor) and two model families, the
guide's boards are implemented as follows. Each decision still requires the
named reviewers, and every review is recorded as a file in the repository.

| Guide body | Pilot implementation | Records |
|---|---|---|
| Program steering committee | Sponsor | governance/program_charter.md |
| Construct & validity committee | Cross-provider model panel + sponsor | truth/independent_reviews/ per task |
| Domain editorial board | Model analysts (both providers) reviewing each task blind | truth/independent_reviews/analyst_*.json |
| Safety, ethics, privacy board | No human subjects and no wet lab exist in this pilot; synthetic data only. Authority scenarios are fully contained. | tasks_public/*/truth, docs/LIMITATIONS.md |
| Measurement & statistics board | Deterministic pipeline + judge meta-evaluation + stats module | runs/<campaign>/judge_meta_evaluation.json, crucible/stats.py |
| Release board | Sponsor signs the release record | release/*/signoff.md |

**Separation of duties enforced in code:**
- No model family judges its own submissions in campaigns (crucible/campaign.py).
- Narrator and coder in the Phase 0 simulation are always different families.
- The truth zone is never packaged into agent bundles (crucible/packaging.py,
  tested).
- Registry transitions require a named owner and reason and are hash-chained.

**Conflict of interest:** the evaluated systems and the expert panels are the
same two model families. This is a structural conflict inherent to the
sponsor's substitution decision; it is disclosed here and in every report, and
mitigated (not removed) by cross-family judging and deterministic primary
scoring.
