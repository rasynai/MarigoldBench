# CRUCIBLE-CHAIN HARDENING SPECIFICATION v4.0

Target: frontier `pass^3` in [0.01, 0.06], `pass@1` VCC in [0.05, 0.15], with constructed-truth label error unchanged. Scope: `crucible/chain/{spec,score,validate,build,author,baselines,judge_chain}.py` and all 8 templates in `tasks_chain/`.

---

## §0. Root cause, stated once

The audits show the benchmark is not a K-stage conjunction. It is a 1-bit decision with K−1 deterministic readouts hung off it, and that bit is written down in candidate-visible text. Two mechanisms cause this and both are institutional, not accidental:

1. **`spec.giveaway_scan()` only inspects `payload["prompt"]`.** Every audited recipe lives in an *artifact* (`method_extract.txt`, `operating_plan.md`, `QP-17_and_run_note.txt`, `WI-MH-17_extract.txt`, `pk_analysis_plan.md`, `method_OX-S-17.txt`). The gate is blind to exactly the file that contains the answer sheet.
2. **`author.REVIEW_TEMPLATE` criterion 2 instructs the reviewer to demand spoon-feeding**: *"If so the key is unfair and must be tightened by the prompt naming the required method."* The build loop's feedback channel therefore rewards RECIPE_IN_PROMPT. Five of eight templates shipped with `"approve": true` **and** a non-empty `required_fixes` list documenting these exact problems.

Fix these two before anything else, or every rewrite below regresses on the next build.

---

## §1. Giveaway classes ranked by difficulty destroyed

Ranking metric: **ΔE**, the expected number of independent decisions restored to a chain by removing the class. Not raw frequency — a class that neutralizes the pivot destroys K stages at once.

| Rank | Class | Freq (of 61 audited stages) | ΔE per chain | Why it ranks here |
|---|---|---|---|---|
| **1** | `DEFECT_ANNOUNCED` | 3 (5%) | **+3.5 to +6** | Lowest frequency, highest destruction. It removes the single bit the whole H1 chain hangs on, so K stages collapse to one free branch. MOLBIO-010: *"seven stages but only ONE bit of judgement in it"*, and `operator_notes.txt` names both the mechanism and its exact extent (`"clear seal had a narrow lift along A6-A11"` covering precisely A7-A10). TRAN-026's addendum ships with the column header `reclassified_to_death_without_prior_relapse` and is engineered so *"Risk-set totals and total removals are unchanged"* — applying it needs no reconciliation and skipping it triggers no inconsistency. EXEMPLAR's `prep_log.txt` narrates defect, cause, direction and consequence. |
| **2** | `RECIPE_IN_PROMPT` (incl. recipe-in-artifact) | 24 (39%) | **+2 to +4** | Most frequent, and it converts every judgment stage to an execution stage simultaneously. TRAN-026's `operating_plan.md` is a 23-line written solution key (competing-event status, the AJ recursion printed step by step, the ledger columns, the tipping reclassification, the three-branch decision table, the futility boundary 0.127). SPEC-004's method answers 6 of 7 stages. It also poisons the trap: with the method printed, the only reachable "wrong path" is non-compliance, which no competent analyst takes. |
| **3** | `OPTION_MENU` | 15 (25%) | **+1 to +2.5** | Sets a 1/2 or 1/3 guess floor per categorical stage, but its real damage is to the *experimental design*: the token set enumerates the perturbation family. `SCOPE_NOT_SUPPORTED`, `CANNOT_DETERMINE_INTRACELLULAR`, `PILOT_NOT_TRANSFERABLE`, `INSUFFICIENT_INDEPENDENT_INDENTS` announce that F2 exists and what it is. Decision menus are compositional restatements — PHARM-016's correct `decision` is the *same string* as its correct `pilot_use_status`. |
| **4** | `TOLERANCE_LEAK` (split out of `ARITHMETIC_ONLY`) | 12 (20%) | **+1 to +2** | Does not leak an answer; it breaks the conjunction. Wrong upstream branches land in-band, so stages stop being conditional. EXEMPLAR H1-s12: unweighted OLS gives 1891.65 against 1881.5 ± 18.815 (pass), and 1/x² over all seven standards — missing the entire planted defect — gives 0.7758 against 0.78 ± 0.03 (pass); 3 of 4 (set × weighting) paths reach the right `BELOW_LLOQ`. SPEC-004 H1-s11: OLS 1.78768, zero-intercept 1.79644 and 1/x² 1.79298 all inside a ±0.01076 band. Effective per-stage pass probability under ignorance ≈ 0.75. |
| **5** | `DECOY_HINT` | 3 (5%) | **+0.5 to +1.5** | Rare but it zeroes `trap_rate` benchmark-wide (0/6 runs on PHARM-016, 0.0 on TRAN-026), which makes `validate.py` gate 3 vacuous: the trap is "reachable" only via the hand-written `weak_answer.md` strawman. |
| **6** | `SINGLE_FILE_LOOKUP` | 4 (7%) | **+0.5 to +1** | Answer printed as an adjacent column (`reference_stability.txt`: RPLP0 20.836 − 20.729 = 0.107, the keyed value). Cheapest to fix, smallest yield. |

**Structural leaks that outrank classes 3–6 and are not in the class taxonomy:**

- **Seed-invariant answers.** 5 of 8 templates have stages constant across all 18 instances (`RETAIN`, `NO_SIGNIFICANT_LOF`, `PROPORTIONAL_VARIANCE`, `WEIGHTED_1_OVER_X2`, `COMPETING_EVENT`, `AALEN_JOHANSEN`, `S_OXIDATION_NO_CHLORINE`, `unknown_conc_nM = 0.78`). PHARM-016's six H1 seeds carry an **identical answer vector**, so the sealed split is fully determined by the development split.
- **Condition↔token bijection.** C0→RELEASE, H1→REPROCESS, F2→PUSH_BACK with no exceptions across 18 instances.
- **Abstention cascade.** PHARM-016's prompt says *"If the pilot or objective does not justify such a fit, use the string cannot_determine for that field and all downstream numeric fields"* — the H1 defect makes the task **strictly easier than C0**, and `score.py` lines 104–108 credit all five abstentions.

---

## §2. Work-order rewrite rules

The work order is a **request from a non-expert requester**, never a protocol. `prompt.md` has exactly five permitted components and nothing else.

**W1** Requester, organisation, business context, deadline, consumer of the result.
**W2** The question in the requester's own words, with the units of the deliverable.
**W3** Attached filenames only, listed, with **no characterisation** of contents, provenance, quality or authority.
**W4** The output contract: JSON field names, per-field type and unit, per-field `conf_<field>` in [0,1].
**W5** A standing preamble that is **byte-identical across every template, seed and condition** (a module constant, not author-generated), covering rounding, units, the existence of the abstention vocabulary, and that unsupported quantities must not be invented.

### MUST NOT (each maps to an audit finding; each is linted)

| ID | Rule | Killed example |
|---|---|---|
| P1 | Must not name a method, estimator, statistic, test, weighting scheme, threshold, critical value, degrees of freedom, or acceptance limit — in the prompt **or any artifact**. | *"At n=5 and alpha=0.05, Gcrit=1.715"*; *"df_LOF=7 and df_PE=20; Fcrit at alpha=0.05 is 2.51"*; *"use the validated response repeatability SD of 0.12 log2 units"*; *"1.96"* |
| P2 | Must not enumerate allowed values for **any** field, including `decision`. | `"<one of: PFAFFL \| DELTA_DELTA_CQ>"` |
| P3 | Must not contain any sentence steering away from a wrong path. | *"Do not silently impute or average an ineligible well"*; *"it is not the unconstrained mathematical upper bound"*; *"Routine-use status does not override either eligibility limit"*; *"A good r-squared ... does not by itself answer the work order"* |
| P4 | Must not presuppose that a defect exists, how many there are, or where. No plural presupposition; no reference to an anomaly, disagreement, or out-of-range observation; no `reconcile/diagnose/verify <defect surface>`. | *"Explain all exclusions"*; *"Reconcile the endpoint classifications"*; *"after the run owner observed that the fitted potency did not match the recent control-chart range"* |
| P5 | Must not order the stages. `RECIPE_VERB_THRESHOLD` drops from 3-per-sentence to **2 per sentence and 5 per prompt**. | *"Derive amplification efficiency..., select the eligible reference, apply the observation and biological-averaging rules, choose the permitted quantitation method, and make the release decision"* |
| P6 | Must not condition one answer on another answer, and must not mention abstention outside W5. | *"use the string cannot_determine for that field and all downstream numeric fields"* |
| P7 | **All three condition prompts must be byte-identical**, F2 included. The premise flaw moves entirely into the artifacts. | F2 differing from H1 by one substring (`"intracellular"` for `"nominal-medium"`) |
| P8 | Must not characterise an artifact ("controlled", "signed", "informal", "provisional", "authoritative"). | *"A signed preparation record takes precedence over worklist metadata"* |
| P9 | JSON field names must be neutral nouns. Banned substrings: `screened_`, `passing_`, `sample_sd_`, `weighted_`, `_routine_`, `eligible_`, `corrected_`, `required_`, `governing_`. | `screened_sample_sd_hv` encodes both the set and the estimator |
| P10 | Field order in the output contract is **shuffled per seed** (`rng.shuffle`). `score_chain` looks up by name, so this is free. | Schema-as-worked-plan cue |

### MAY

Units, rounding convention, deadline, who consumes the result, that it must survive audit, the field names/types, a **generic** form exemplar per field (see §3.5).

### Enforcement

- `spec.giveaway_scan(payload)` runs over `prompt + all artifacts`, not the prompt alone.
- New payload key `rule_constants: list[float]` — every threshold, limit, critical value and coefficient the key depends on. `spec.leak_scan` is extended to scan these with `_renderings()` exactly as it scans answers. If a rule constant renders verbatim in candidate-visible text, the template is rejected. Rule constants must be **derivable** from shipped data (a qualification table, a replicate QC set, a document register), never printed.
- `author.AUTHOR_TEMPLATE` rule 7 is rewritten to forbid printing allowed values. `author.REVIEW_TEMPLATE` criterion 2 is rewritten to: *"If a competent scientist could reach a different defensible value, tighten the key by making the DATA determine the method — an acceptance criterion the alternatives measurably fail. Never by having the prompt or an artifact name the method. If no such construction exists, delete the stage."*
- `build.build_one`: materialize only when `verdict["approve"] and verdict["key_correctness_verified"] and not verdict.get("required_fixes")`.

---

## §3. Deterministic checkability without menus

**Principle: free-form ≠ judge-scored. No stage becomes judge-scored for VCC.** Every VCC-bearing field stays deterministic. LLM judges live entirely in a post-hoc fairness and diagnostics lane.

### 3.1 The five answer types

| Type | Used for | Scoring | Determinism source |
|---|---|---|---|
| **A. Numeric** | quantities, counts, rates, intervals | `score._match` with derived `tol` (§4 M5) | generator computed it |
| **B. Closed-world identifier** | *which object* — lot number, well ID, subject ID, clause number, parameter name, revision code, filename, instrument field | exact match after `_token()` | generator authored the identifier |
| **C. Free-form categorical** | *which concept* — a weighting scheme, an estimator, a variance model | `score._cat_match` with generator-authored alias sets (already implemented) | generator authored both alias sets |
| **D. Set-valued** | *which subset* — excluded observations, retained levels, eligible cultures | exact set equality after `_token()` on each element | generator built the set |
| **E. Judge** | noticing, quality, coherence | never enters VCC | n/a |

### 3.2 Type B is the primary menu replacement

Converting a menu to an identifier changes the guess floor from 1/2 to 1/N where N is the row count of the data. Mandated substitutions:

- `run_diagnosis: WRONG_WEIGHTING_IN_SEQUENCE` → `deviating_setting_name: "Weighting"` **plus** `deviating_setting_recorded_value: "None"` (two exact-match fields; the candidate must emit the parameter as spelled in the sequence file).
- `feature_assignment: S_OXIDATION_NO_CHLORINE` → `feature_delta_formula: "+O"`.
- `strength_estimate_eligibility` enum → `binding_clause_id: "5.3(b)"` (clause numbering exists only inside the SOP artifact).
- `outlier_disposition: RETAIN` → `excluded_observation_ids: []` (Type D).
- `decision` → a code drawn from a generated vocabulary matching `^[A-Z]{3,6}-[0-9]{2}$` whose semantics appear **only** in a disposition matrix artifact, with the code→meaning assignment **permuted per seed**. Gate: `(condition → decision code)` must not be constant across a template's six seeds.

### 3.3 Type D scoring (new code in `score.py`)

```python
def _set_match(given, target):
    if isinstance(given, str):
        given = [p for p in re.split(r"[;,|\s]+", given) if p]
    if not isinstance(given, (list, tuple, set)):
        return False
    return {_token(x) for x in given if str(x).strip()} == {_token(x) for x in target}
```
`_match` dispatches to `_set_match` when `spec["correct"]` is a list. An empty list is a legal, meaningful answer; `present` already distinguishes it from a missing field. Trap separation gate for sets: `len(correct ^ decoy) >= 1` **and** `len(correct ^ decoy) <= 0.4 * max(len(correct), len(decoy), 1)` — a decoy set that shares nothing with the correct set is implausible, mirroring the existing 0.1–10 ratio gate for numbers.

### 3.4 Mapping a free-form categorical to a verdict — the exact cascade

Applied to the field value only, never to prose:

1. `v = _token(strip_style(value))`.
2. If `v` parses as a number and `spec["correct"]` is categorical (and not an abstention) → **incorrect** (type mismatch).
3. If `v ∈ ABSTAIN_TOKENS` → `abstained = True`; correct iff `spec["correct"] ∈ ABSTAIN_TOKENS`.
4. `hit_c` = boundary match of `v` against `{correct} ∪ correct_aliases`; `hit_d` = same against `{decoy} ∪ decoy_aliases`. Boundary matching is the existing `f"_{token}_" in f"_{v}_"` test, so alias `weighted` cannot fire inside `unweighted_ols`.
5. Verdict: `hit_c ∧ ¬hit_d` → **correct**; `hit_d ∧ ¬hit_c` → **trapped**; both → **hedged** (incorrect, not trapped, new diagnostic counter); neither → **unmatched**.
6. **Unmatched is scored incorrect for VCC and is never overridden by a model.** Every unmatched value is appended to `runs/<label>/unmatched_categoricals.jsonl` with `(template, instance, stage, value, stage.label, stage.fork)`.

**The fairness valve.** After each campaign, both judge families independently adjudicate the unmatched file: *"does this phrase denote the same analytical choice as `<stage.label>` resolved as `<correct>`?"* — a binary verdict with a verbatim-quote requirement, both families required to agree. If `adjudicated_correct / n_categorical_stage_observations > 0.02`, the alias sets are declared under-specified: affected templates are quarantined, `correct_aliases` extended, and the campaign is re-run through `crucible/rescore.py`. This keeps constructed truth intact (judges never grant credit in the published run) while making free-form answering demonstrably fair.

### 3.5 Alias-set requirements (hardened `spec.check_stage`)

- ≥ 4 aliases per side, spanning: canonical token, the natural-language domain phrase, the abbreviation, and the symbolic/formula form (`1/x^2`, `inverse variance`, `weighted least squares`).
- Existing cross-side boundary-disjointness gate retained.
- **Alias calibration gate at build time:** for each categorical stage, ask each judge family for 20 paraphrases of the correct choice and 20 of the decoy, then require alias matching to classify ≥ 39/40 correctly on each side. Below that, the template is rejected. This is a one-time authoring cost that makes the deterministic matcher defensible in the paper.
- The output contract's per-field form exemplar (e.g. `"<name the weighting scheme as you would write it in a method section>"`) must not boundary-match any `correct_alias` or `decoy_alias`. Linted.

### 3.6 Where the LLM judges sit (sponsor requirement)

Cross-family, dual-scored, never touching VCC:
1. `judge_notice` — per-stage noticing, verbatim-quote-verified (existing).
2. `judge_quality` — advisory reasoning score (existing).
3. `judge_adjudicate_unmatched` — §3.4 step 6, post hoc only.
4. **New `judge_coherence`** — does the candidate's prose entail its own JSON values (e.g. does the reported slope follow from the well set it says it used)? Reported as `coherence_rate` beside VCC, never inside it. Every judged item scored by both families; published value is the **minimum** of the two; Cohen's kappa reported; the metric is withheld if kappa < 0.60.

---

## §4. New difficulty mechanisms

Each is deterministic, generator-computable, and grounded in an observed frontier failure rather than in added length.

### M1 — Cross-artifact identity reconstruction

**Generator emits:** the facts a stage needs, split across ≥ 3 artifacts, joined on a key that is *not* the display key (rack position ↔ acquisition index ↔ sample ID via a plate map and a re-injection log). Includes a duplicate record, a superseded revision distinguished only by effective date, a record dated after the analysis cutoff, and a benign near-miss (`trt-02` vs `TRT-02`) that must **not** be treated as a mismatch.

**Why a frontier model fails:** the audits show these systems execute in-row comparisons reliably but substitute plausible recall for lookup on multi-hop joins. TRBL-002: an Anthropic submission *"asserted which injections carried the whitespace without checking the CSV (which contradicts it)"*. The near-miss additionally punishes the raw-inequality shortcut. This is a bookkeeping failure, not a knowledge failure, so it compounds across stages instead of correlating with model scale.

**Gate:** artifact-ablation assertion in the generator — recomputing the stage from any proper subset of the joined artifacts must differ from `correct` by > 3·tol (numeric) or have non-empty symmetric difference (set).

### M2 — Internal inconsistency as the only defect signal

**Generator emits:** an H1 whose defect is detectable **only** because two independently derivable quantities disagree. Canonical forms: printed `risk_at_start` cannot be produced by subtracting the displayed event counts; the exported back-calculated recoveries reproduce only under a weighting that contradicts the stated setting; the recorded dilution factor (5.0) contradicts the recorded volumes (100 µL + 200 µL). C0 ships the identical files, consistent.

**Why a frontier model fails:** verification of a stated value against a derived one has no prompt cue and is not a habit these models invoke unprompted — they transcribe stated values. TRAN-026's own audit names this as the hard version: *"the only signal is that the printed `risk_at_start` column fails to reconcile with the displayed event counts."* MOLBIO-010's best fix is *"make the record LIE."*

**Gate (NO_NARRATION, mechanical).** Diff C0 vs H1 artifacts. Any changed line that is prose — matches `[A-Za-z]{3,}\s+[A-Za-z]{3,}\s+[A-Za-z]{3,}` and is not a CSV/TSV/fixed-width table row — rejects the template. Only numeric, tabular and identifier cells may differ between conditions. This single gate would have rejected MOLBIO-010 (`"clear seal had a narrow lift along A6-A11"`), the EXEMPLAR (`"Re-prep requested"`), and TRAN-026's addendum instruction.

### M3 — Rule selection that is underdetermined until computed

**Generator emits:** the rule governing stage *k* is selected by a quantity the candidate has not computed yet. Examples: the spacing multiplier comes from a table row keyed on hardness class, so HV must be computed first; the accepted calibration model is *whichever candidate makes every back-calculated standard fall within ±15% (±20% at LLOQ)*, so all four candidates must be fitted and tested; the LLOQ is derived from low-level QC replicates against a ≤20% CV / ±20% bias criterion rather than printed.

**Why a frontier model fails:** it defeats the linear read-then-execute strategy every audited submission used, requires speculative computation with backtracking, and — critically — a wrong early selection produces a *self-consistent* wrong chain, so the model's own verification pass will not catch it. Models also strongly prefer selecting a rule from prose over fitting four models and testing them.

**Gate:** the governing rule must differ across ≥ 2 of a template's 6 seeds, and on ≥ 1 seed the correct rule must be the *a priori* unlikely one (unweighted OLS correct at least once per template). "Always weighted" must be a losing prior.

### M4 — Conjunctive eligibility with distractor density

**Generator emits:** exclusion requires **both** a statistical trigger **and** a documented assignable cause (or both a date match and a study match). Every instance contains: a point failing the statistic with no cause (retain), a point with a documented cause that passes the statistic (retain), a point failing both (exclude), and a legitimately different-but-qualified alternative lot (retain). True exclusion count drawn per seed from {0, 1, 2, 3}.

**Why a frontier model fails:** the audits measure the exact prior this defeats. TRBL-002: `RETAIN` correct in all 18 instances so *"the default no-action prior already wins"* — invert it and pattern-matchers fail. LLMs satisfice on the salient conjunct and drop the second. A 0-exclusion H1 seed is the first real test of the false-alarm penalty C0 was supposed to provide.

**Gate:** across a template's 18 instances the exclusion-count distribution must have entropy ≥ 1.0 bit; ≥ 1 H1 instance must have 0 exclusions; ≥ 1 C0 instance must present a tempting-but-invalid exclusion candidate that must be rejected.

### M5 — Wrong-path enumeration and derived tolerances

**Generator emits:** a new payload key `wrong_paths: list[dict]` — the Cartesian product of {eligible set} × {weighting} × {response variable} × {rule choice} × {unit convention}, each evaluated to a value for every numeric stage. Then

```python
gap  = min(abs(correct - w["value"]) for w in wrong_paths)
tol  = 0.4 * gap
```
with rejection if `tol` falls below the value's own reporting precision (≈ 1e-3 relative). All enumerated wrong values are stored in `key.json` as `decoys[]` so `score_chain` reports **which** wrong path was taken (`decoy_id`).

**Why this matters:** it does not create difficulty; it stops the chain being compensatory, which is the precondition for p^K to multiply at all. Under today's tolerances, EXEMPLAR H1 has four analysis paths of which three pass — an effective per-stage pass probability of 0.75 under total ignorance of the fork. Under this gate it is 0.25.

**Gate:** `spec.check_stage` requires `len(wrong_paths) >= 2` for every numeric stage and asserts `abs(correct - w) > 3*tol` for **all** of them, replacing today's single-decoy check. `validate.py` gains gate 7: the "best single wrong path" (the most attractive `wrong_path` applied at every stage) must score VCC = 0.

### M6 — Consequential abstention

**Generator emits:** in **every** condition, a mix of determinable and non-determinable sub-quantities. Plus two traps: a *looks-unavailable-but-is-derivable* quantity (the conversion factor exists, reachable only by a two-artifact join) and a *looks-available-but-is-not-qualified* quantity (a factor is printed but its qualification metadata — cell line, revision date, matrix — rules it out).

**Why a frontier model fails:** both failure modes are currently free. PHARM-016 abstained on 5 of 7 stages and scored `stage_accuracy 1.0`. MOLBIO-010's entire F2 fork is selectable from one adjective. Making abstention a *subset-identification* task penalises over- and under-abstention symmetrically, and models are strongly biased toward computing whenever a number is present and toward abstaining whenever warning-shaped language is present.

**Gate:** no instance may be all-abstain or all-numeric. F2 requires `1 <= n_abstain <= K-2` and ≥ 1 numeric correct answer; ≥ 1 non-F2 instance per template must contain an abstention. `score.py` must stop treating abstention as a mode: `abstained` remains a diagnostic and is credited only where `spec["correct"] ∈ ABSTAIN_TOKENS`, which it already does — but P6 removes the prompt sentence that hands the cascade over.

### Supporting dial (not a mechanism) — artifact scale

Raise artifacts from ~4 short files to 6–8 files, 200–400 data rows, with a governing fact that is present but not adjacent to any flag. **Caution, stated as policy:** scale must never be the sole source of difficulty for any stage. Alone it degrades into a retrieval test, inflates run-to-run variance, and correlates with context length rather than reasoning. Every stage must remain solvable from a correctly identified 20-row subset; the difficulty is in *identifying* the subset (M1–M4), not in reading everything.

### Structural gates added alongside

- **G1 answer entropy** — per template, each stage's correct value takes ≥ 3 distinct values across 18 instances (numeric: ≥ 6 distinct to 3 s.f.; categorical: ≥ 2 with neither exceeding 60%).
- **G2 condition independence** — `I(condition; decision) < 0.6` bits over 18 instances; `I(condition; stage_i) < 1.0` bit for all but at most one stage.
- **G3 stage independence** — no stage's correct value may be a deterministic function of another's across the 18 instances (`I(stage_i; stage_j) < H(stage_j) − 0.3` bits). This forces merging `absorption_half_life_h` into `absorption_rate_h_inv` and forces `decision` off `report_status`.
- **G4 sealed-split independence** — the answer vectors of seeds {14, 16} must not be reconstructible from seeds {11, 12, 13, 15}: no stage may have identical values across all six seeds, and the full 8-tuple must be distinct per seed.

---

## §5. Validation

### 5.1 Acceptance windows

Per-stage accuracy needed for a target VCC, assuming near-independent stages: `p* = VCC^(1/K)`.

| K | p* for VCC 0.03 | p* for VCC 0.09 |
|---|---|---|
| 5 | 0.50 | 0.62 |
| 6 | 0.55 | 0.66 |
| 7 | 0.61 | 0.71 |
| 8 | 0.65 | 0.74 |

**Ship criteria (strongest frontier system, hidden_test split, ≥ 3 replicates per instance):**

| Metric | Accept | Read as |
|---|---|---|
| `pass_hat_k` (k=3) | 0.01 – 0.06 | headline |
| `pass_at_1` VCC | 0.05 – 0.15 | guard rail (`pass^k` collapses to a hard zero below ~8% per `score.reliability`) |
| `mean_stage_accuracy` | within ±0.06 of `VCC^(1/K̄)` | difficulty is distributed |
| **concentration ratio** = max stage hazard / Σ hazards | ≤ 0.40 | difficulty is a chain, not one gate |
| every stage's hazard | 0.05 – 0.45 | no free stages, no impossible stages |
| `stage_trap_rate` | ≥ 0.15 | wrong paths are actually reachable |
| `flip_rate` | ≤ 0.35 | not a coin flip |
| `answer_block_rate` | ≥ 0.95 | format is not the difficulty |

A high `mean_stage_accuracy` (say 0.85) alongside a low VCC means difficulty is concentrated in one stage — the current disease in a new costume. The hazard profile, not the mean, is the acceptance instrument.

### 5.2 Baseline ladder (integrity gates; headline withheld if any fails)

| Rung | Requirement |
|---|---|
| B8 reference | VCC = 1.00. With free-form categoricals this also validates alias coverage. |
| B1 degenerate | VCC = 0.00 |
| B9 adversary | VCC = 0.00 |
| B5 naive (all-decoy) | VCC = 0.00 **and** mean stage accuracy ≤ 0.25 |
| **B5b best-wrong-path** (new) | the single most attractive enumerated `wrong_path` applied throughout: VCC = 0.00 |
| B0 prior-only (artifacts withheld) | VCC ≤ 0.02 **and** mean stage accuracy ≤ 0.15. Without menus this should crater; if it does not, answers remain guessable. |
| **B10 artifact ablation** (new) | for each shipped artifact, withhold it and re-run. Every artifact must be load-bearing for ≥ 1 stage: ≥ 0.15 absolute drop in that stage's accuracy. Catches decorative artifacts (MATSCI's `material_certificate.txt`, where *"a model that never opened it still scores 7/7"*). |
| **B11 condition indistinguishability** (new) | `sha256(prompt.md)` identical across C0/H1/F2 for every seed. Mechanical proof of P7. |
| **B12 seed transfer** (new) | run the frontier system on sealed seeds with the *development-split* `key.json` for the same template in context. Accept only if `VCC_sealed ≤ VCC_hidden_test + 0.05`. Directly tests the lookup-key failure (EXEMPLAR's constant 0.78; PHARM-016's identical six-seed answer vector). |

### 5.3 Over-correction: the red line

**Presumed over-corrected until proven otherwise** if any of:
- `pass_at_1` VCC < 0.02, or
- `mean_stage_accuracy` < 0.45 across the two strongest systems, or
- any single stage with hazard > 0.60 for **both** frontier families, or
- `unmatched` categorical rate > 2%.

### 5.4 Distinguishing genuine difficulty from unfairness

Six discriminants, run in this order. D2 and D3 are automated and free; D1 is decisive and expensive.

**D2 — Convergent-wrongness signature (primary automated test).** Genuinely hard stages produce *converging* failures: most wrong answers land on one enumerated `wrong_path`. Ambiguous or mis-keyed stages produce *diverging* failures. Metric: `enumerated_failure_share` = failures matching some `decoys[]` entry ÷ all failures at that stage.
- ≥ 0.60 → **hard**. The wrong path is a real analytical choice and the model took it.
- 0.30 – 0.60 → inconclusive; escalate to D1.
- < 0.30 → **ambiguous**. Failures scatter, meaning the stage admits values the designer never considered.

This is the single best return on M5's engineering cost.

**D3 — Unmatched-categorical rate.** > 2% is a scoring artifact, not difficulty: extend aliases and rescore. Never leave it in the headline.

**D4 — Prose/value dissociation.** Using `judge_coherence` on failed stages: does the prose reach the key's conclusion while the emitted value misses? If ≥ 25% of failures are prose-correct/value-wrong, the **tolerance or the output contract** is broken, not the science — check units, rounding, and derived `tol` before concluding difficulty.

**D5 — Notice/act direction.** `judge_chain.notice_act_gap` already computes P(named the fork) − P(got the stage). A large positive gap with low `acted_given_noticed` is the target signature: the system saw the judgment and failed to propagate it. A *high* notice rate with correct detailed reasoning and a wrong scored value is D4, not difficulty.

**D6 — Cross-family convergence on a non-key value.** **Automatic escalation rule:** any stage where ≥ 2 systems × ≥ 2 replicates agree on the same non-key value triggers a mandatory human key audit before publication. Two independent frontier families converging on an answer the key rejects is the standard signature of a wrong key, not of a hard question.

**D1 — Expert-panel solvability (decisive; mandatory for any stage crossing §5.3's red line).** Three independent expert solvers attempt the instance blind, then see the key.
- **Genuine difficulty:** solvers agree with the key once shown and describe the miss as an oversight they should have caught.
- **Over-correction:** ≥ 1 of 3 solvers produces a *different defensible* value, or disputes the key, or cannot identify the governing rule from the shipped artifacts within the time budget.
Threshold: one defensible alternative from three experts condemns the stage. Fix it or delete it — do not ship a stage that survives only because no expert was asked.

Recorded per stage in `runs/<label>/difficulty_audit.json` as `{stage, enumerated_failure_share, unmatched_rate, prose_value_dissociation, notice_act_gap, cross_family_convergence, expert_verdict}`. A template ships only when every stage is classified `hard` or `hard_after_repair`.

### 5.5 Rollout

1. Land the two root-cause fixes (§0): `giveaway_scan` over artifacts; `required_fixes` blocking materialization. Re-run the existing 8 templates through `validate_chain_template` — expect all 8 to be rejected. That rejection is the acceptance test for the gate work.
2. Land `spec.py` / `score.py` changes: set matching, `wrong_paths`, `rule_constants` leak scan, NO_NARRATION diff gate, G1–G4, F2 symmetry, alias hardening.
3. Rewrite **two** templates first — the EXEMPLAR (it seeds every author call via `exemplar.EXEMPLAR_GENERATOR`, so its defects propagate to all future templates) and `OEC-MOLBIO-TRBL-010` (cleanest single-bit case). Run the full ladder plus 3 replicates × 2 frontier families.
4. Gate propagation on the two-template result: mean stage accuracy in the §5.1 window and `enumerated_failure_share ≥ 0.60`. Only then regenerate the remaining six.
5. Publish with the full bracket, never the bare number: *"pass^3 = X% against a Y% naive floor, a Z% no-artifact floor, and a 100% verified reference ceiling."*