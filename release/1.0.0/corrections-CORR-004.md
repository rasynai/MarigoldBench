# CORR-004 - grader brittleness: verifier v1.0.3 and global rescore

- Date: 2026-08-16 (UTC). Scope: every release-1.0.0 outcome with a stored
  submission (792 rescored; 10 worker-level failures kept as-is).
- What happened: forensic review of Marigold failures showed the
  deterministic graders rejecting SCIENTIFICALLY CORRECT answers over
  phrasing, in three ways:
  1. Reportability: rejected-pattern regexes ran before accepted ones over
     the prose, so correct negations ("No value is reportable", value token
     NON_REPORTABLE) matched the affirmative "reportable" pattern and
     failed. Fix: the machine-readable value token is now authoritative,
     matched accepted-first, with non->not normalization; prose is fallback.
  2. Hazard detection: keyword lists missed correct detections phrased with
     other vocabulary or bare numeric evidence (e.g. quoting the corrupted
     value 73030 mg/tablet without the word "unit"). Fix: phenomenon
     vocabulary broadened for all 10 archetypes and instance-specific
     numeric_signatures added to truth - quoting the planted defect's own
     numbers now counts as detection.
  3. Decision vocabulary: MELT tasks ask "is identity confirmed?" but the
     acceptance sets only spoke "reportable"; correct answers
     "confirmed"/"NOT_CONFIRMED" fell out of set. Fix: identity vocabulary
     added to MELT acceptance sets.
- External grounding: published evaluations report the same failure class -
  string/regex graders systematically penalize semantically correct answers
  (large judge-flip rates when re-checked semantically); and per signal
  detection theory, prompt-level threshold moves (the v1->v2 Marigold change)
  only trade misses for false alarms, so grader fixes and procedure fixes -
  not threshold nudges - are the correct response.
- Verification the fix is content-blind and fair:
  - All agent-visible files (inputs + task cards, 414 files) byte-identical
    before/after regeneration - only truth-zone grading data changed.
  - The SAME v1.0.3 verifier was re-applied to every stored submission of
    every system. 22 outcomes flipped, all false->true (grader
    false-negatives), across 7 of 9 systems: marigold 11, kimi-k3 4,
    glm-5.2 2, deepseek 2, openai 1, gemini 1, grok 1. Zero true->false.
  - Full flip list: runs/corrections/CORR-004-rescore-report.json.
- Known residual limitation (not corrected, to avoid outcome-dependent truth
  edits): accepted-conclusion sets do not cover "recalculated with the
  corrected parameter and reported, with the defect flagged" (observed once,
  GEN-STOICH-003-N1); regex vocabulary can still miss exotic phrasings. Both
  are disclosed in docs/LIMITATIONS.md; the escalation path exists for
  defensible out-of-set answers.
