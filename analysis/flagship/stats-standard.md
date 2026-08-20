# The statistical reporting standard — CRUCIBLE-CHAIN

Date: 2026-08-16. Workstream: flagship statistics. Status: working document —
every formula below is either from a named source fetched today or measured
from `runs/release-3.0.0/` outcomes; every n is computed, not asserted.
Companion evidence: `analysis/statistical_power.md` (ICC/design-effect
analysis, same date), `analysis/power_analysis.py`, `crucible/chain/score.py`,
`release/1.0.0/scorecard-1.0.0.md`, `release/1.0.0/prereg-3.0.0.md`.

**The one-sentence standard:** every number the benchmark publishes carries a
template-clustered 95% interval and a cluster count; every model-vs-model claim
is a *paired, clustered, multiplicity-corrected* difference or it is a tie; and
every campaign states its minimum detectable effect before it runs.

---

## 1. Findings: where current practice falls short of bulletproof

The field context first. BetterBench (Reuel et al., arXiv:2411.12990) assessed
24 AI benchmarks against 46 criteria and found "most benchmarks do not report
statistical significance of their results nor allow for their results to be
easily replicated"; our own literature record (`analysis/literature/README.md`
§7) counts 14 of 24 reporting no uncertainty at all. HELM (arXiv:2211.09110)
standardized *metrics* (7 of them) but not *uncertainty* — its abstract-level
reporting carries no error bars. Miller (Anthropic, arXiv:2411.00640) measured
that ignoring question clustering understates standard errors by up to **3.05x**
on DROP (Table 4 of the paper). The bar for "industry flagship" is therefore
low and specific: report what Miller/BetterBench/Biderman (arXiv:2405.14782,
"Perform Statistical Analyses, and Report on Sources of Variance and Error")
say almost nobody reports. We are already partway there; the gaps:

| # | Finding | Evidence | Severity |
|---|---|---|---|
| F1 | **No paired-comparison machinery exists anywhere in the repo.** `crucible/chain/score.py` has Wilson, cluster bootstrap, pass^k, hazard — and no function that takes two systems. `scorecard-1.0.0.md` prints 9 per-system rows; any reader subtracts point estimates by eye, which is exactly the anti-pattern Miller's §4 exists to kill | `score.py` (no paired fn); scorecard rows 10–31 | **Critical** — the flagship claim is model separation |
| F2 | **Model-vs-model differences are strongly clustered too.** Measured today on release-3.0.0 hidden runs: ICC of the *paired difference* within template ρ_d = 0.00–0.44 (median 0.33, working 0.28). Differencing does not cancel the template effect; a paired test that ignores it overstates significance | `paired_stats.py` run 2026-08-16 (scratchpad; measured on 178 hidden runs, 5 systems) | **Critical** |
| F3 | **Printed Wilson CIs assume independent runs.** Scorecard 1.0.0 prints "62/66 (94%; Wilson 85–98%)" while the same runs have within-template ICC 0.27–0.44 (measured; `analysis/statistical_power.md` puts the working value at 0.26 and shows nemotron's per-template rates 1.00/0.75/0.40/…/0.00). At m≈5 runs/template and ρ=0.30, DEFF=1+(m−1)ρ≈2.2 → the honest interval is ~√2.2 ≈ 1.5x wider | scorecard-1.0.0 lines 23–31; `power_analysis.py`; Miller Eq. 4 | **High** |
| F4 | **The percentile cluster bootstrap is the primary interval, with 8–10 clusters.** Cluster-robust inference is unreliable below ~30–50 clusters (econometrics practitioner consensus; CR2/CR3 and wild-cluster bootstrap exist precisely for this); percentile bootstrap on 10 binary-ish cluster means yields the lumpy [0.87, 1.0]-type intervals visible in scorecard-1.0.0 | scorecard-1.0.0 lines 23–31 ("10 clusters"); Wikipedia/Cameron–Miller guidance fetched today | **High** until T≥100 |
| F5 | **No multiple-comparison policy.** A 9-system scorecard implies 36 pairwise claims; 3 conditions and ~8 hazard stages per system multiply the grid into hundreds of implicit tests. Nothing in prereg-3.0.0 or the scorecards names a family, a correction, or an adjusted α | prereg-3.0.0 (no α policy); scorecard grids | **High** |
| F6 | **pass^3, the headline, is printed with no interval.** `reliability()` returns point estimates only (`score.py:268–301`); prereg-3.0.0 promises cluster bootstrap for rates but not specifically for the pass^k family | `score.py:295–301` | **High** |
| F7 | **Judge agreement is reported as raw fractions ("5/6 agree") with no κ, no CI, and no bias correction**, although judge-scored metrics (reasoning quality, notice-act gap) will be compared across models | scorecard-1.0.0 lines 44–53 | Medium |
| F8 | **Per-stage hazard CIs pool runs across templates un-clustered** (`hazard_profile()` uses raw Wilson at `score.py:347`), and stage-level model contrasts have no multiplicity control | `score.py:317–355` | Medium |
| F9 | **Power was unstated until today.** `analysis/statistical_power.md` (2026-08-16) now shows the 8-template design cannot separate models closer than ~33 pp and that only new templates — not instances or repeats — buy effective n (48→144 runs moves n_eff only 21→26). This standard builds the paired version of that analysis and fixes the scorecard so the MDE is printed | `analysis/statistical_power.md` | Fixed by this doc |

What is already right and must be kept: Wilson over Wald (`score.py:304–314`;
Brown–Cai–DasGupta 2001 verdict, confirmed via the standard reference today:
Wilson is "the most accurate and the most robust", Wald "heavily criticised");
unbiased pass^k/pass@k estimators (`score.py:268–301`, matching τ-bench
arXiv:2406.12045 and Chen et al. arXiv:2107.03374 exactly); template as
preregistered cluster unit (prereg-3.0.0); the pass^3 ≤ pass@1 ≤ pass@3 ladder;
right-censoring in hazards; the baseline-ladder integrity gates; preregistration
itself — which is the natural vehicle for the multiplicity families below.

---

## 2. Measured inputs (release-3.0.0 pilot, 207 outcome files, 2026-08-16)

All power arithmetic below uses these, re-measured by
`analysis/power_analysis.py` + the paired script; re-estimate them in the
first post-saturation-fix campaign and re-print the tables.

| Quantity | Symbol | Measured | Working value |
|---|---|---|---|
| ICC of VCC within template (per system) | ρ | 0.27 / 0.40 / 0.44 (unsaturated systems); 0.00 (deepseek-flash, sparse) | **0.30** |
| ICC of paired difference within template | ρ_d | 0.00–0.44, median 0.33 | **0.28** |
| Discordance P(A≠B), frontier pair (anthropic vs openai, saturated) | q | **0.062** (b=0, c=3, n=48) | 0.05–0.10 post-fix guess for near pairs |
| Discordance, adjacent unsaturated pair (nemotron-super vs -ultra) | q | **0.200** (n=25) | **0.20** for mid-band pairs |
| Paired/unpaired variance ratio | — | 0.55 (close pair) – 1.0 (far pairs) | pairing is free precision exactly where it is needed |
| Repeat flip rate (instances with 0<c<3 of 3) | — | 0.00 frontier; 0.20 / 0.42 / 0.67 mid-tier | repeats stabilize mid-tier, add nothing at frontier |
| Attempt-level pass@1 spread | — | 0.154 → 1.000 across 5 systems | post-fix band expected ~0.1–0.7 |

The saturation-bug context matters: anthropic 0.938 and openai 1.000 on the
pilot are the leaked-recipe scores. After the fix, expect the frontier in the
0.3–0.7 band, where binary variance is maximal — the tables below use q and p
in that regime, which is the conservative case.

---

## 3. The standard: exact formulas

Notation: templates c = 1…T (the cluster unit, preregistered), runs i within
template, N total runs, m̄ = N/T runs per template, s_i ∈ {0,1} the outcome
(VCC, or the pass^3 indicator when the unit is an instance), s̄ the mean.

### 3.1 Single-system rate

**Point estimate:** s̄. **Primary interval (T ≥ 30):** clustered standard error
(Miller, arXiv:2411.00640, Eq. 4):

    SE_clust = sqrt( SE_CLT² + (1/N²) · Σ_c Σ_i Σ_{j≠i} (s_ic − s̄)(s_jc − s̄) )
    SE_CLT   = sqrt( s̄(1−s̄) / N )
    CI95     = s̄ ± t_{T−1, .975} · SE_clust        ← t with T−1 df, not z

Equivalent moment form for design tables: `Var(s̄) ≈ s̄(1−s̄)·DEFF/N` with
`DEFF = 1 + (m̄−1)·ρ` and ρ the one-way-ANOVA ICC (implementation:
`power_analysis.py::icc_anova`). Report **DEFF and T next to every interval**
(Miller Table 3 format: "n = 360 runs, 120 clusters").

**Bounded-rate display (near 0 or 1 — false-alarm on C0, B-ladder gates):**
Wilson score interval on the *effective* count, n_eff = N/DEFF:

    center = (p̂ + z²/2n_eff) / (1 + z²/n_eff)
    half   = z·sqrt( p̂(1−p̂)/n_eff + z²/4n_eff² ) / (1 + z²/n_eff)

Never Wald (zero-width at 0/N — `score.py:304` comment is correct). Raw-n
Wilson may appear only labeled *diagnostic*, per the adopted rule in
`analysis/statistical_power.md`.

**Sensitivity intervals (always computed, shown in the appendix table):**
(a) percentile cluster bootstrap (existing `cluster_bootstrap_ci`, ≥2000
draws); (b) for any legacy campaign with T < 30, the **wild cluster bootstrap**
(Rademacher weights on template residuals, 9,999 draws) — the small-G remedy of
the econometrics literature (Cameron–Miller JHR 2015; CR2/CR3 df-corrections);
below ~30–50 clusters plain CRVE and percentile bootstrap under-cover.

### 3.2 Two-system comparison (the flagship claim) — always paired

Both systems run byte-identical instances (prereg-3.0.0 fixes the evaluated
subset), so every comparison is paired by run key (template, instance,
repeat). Let d_i = s_{A,i} − s_{B,i} ∈ {−1, 0, +1}, Δ̂ = d̄.

**Paired clustered SE** (Miller Eq. 8 — the exact estimator to implement):

    SE_paired,clust = (1/N) · sqrt( Σ_c Σ_i Σ_j (d_ic − d̄)(d_jc − d̄) )
    CI95 = Δ̂ ± t_{T−1,.975} · SE_paired,clust      z-score: Δ̂ / SE

Why paired: Var(d̄) = [Var(s_A)+Var(s_B) − 2Cov(s_A,s_B)]/N; model scores
correlate 0.3–0.7 on shared items (Anthropic research post, fetched today), and
our measured close-pair variance ratio is 0.55 — pairing is a ~2x sample-size
gift precisely for adjacent models, which are the comparisons that matter.

**Exact test (reported beside the CI):** McNemar on discordant runs. b = #(A=1,
B=0), c = #(A=0, B=1); two-sided exact p = binomial tail of min(b,c) on
Binomial(b+c, ½). Pilot example: anthropic vs openai b=0, c=3 → p = 0.25 — the
pilot cannot even distinguish the top two systems, which is the honest
statement of its resolution.

**Robust default when T is small or outcomes are lumpy:** template-level
sign-flip permutation — flip the sign of all d's in a template together
(2^T orbits, sample 10,000), p = share of flips with |d̄*| ≥ |d̄|. Valid under
within-template dependence; use it as the primary p-value whenever T < 30.

**Print the correlation** r = Corr(s_A, s_B) with every pair (Miller Table 5
format: Δ, SE, CI, r) so readers see the pairing gain.

### 3.3 The pass^k ladder (headline family)

Unit = instance; per instance, n runs with c successes; unbiased estimators
(already in `score.py`, matching the sources exactly):

    pass^k = mean_i [ C(c_i, k) / C(n_i, k) ]          (τ-bench, arXiv:2406.12045)
    pass@k = mean_i [ 1 − C(n_i−c_i, k) / C(n_i, k) ]  (Chen et al., arXiv:2107.03374)

The plug-in p̂³ and 1−(1−p̂)³ are biased (Chen: "consistent underestimate";
our own docstring measured plug-in pass^3 overstating ~3x) — keep the
combinatorial forms. **Interval:** cluster bootstrap over templates of the
per-instance unbiased estimates (the estimate is a mean of per-instance
quantities, so §3.1 machinery applies with instance-level rows); with n_i = 3
and k = 3 the per-instance estimate is the all-3 indicator, so the whole §3.1/
§3.2 binary machinery carries over verbatim. **Paired pass^3 comparisons** use
d_i on the indicator. If budget ever allows n_i = 5 runs on a subset, the
estimator C(c,3)/C(5,3) takes values {0,.1,.3,.6,1} and per-instance variance
drops ~40% at p≈0.5 — worth it for mid-tier systems only (frontier flip rate
measured 0/16).

### 3.4 Power analysis / minimum detectable effect

General form (Miller Eq. 9–10, cluster-adjusted per his Appendix C):

    n   = (z_{α/2} + z_β)² · (ω² + σ_A²/K_A + σ_B²/K_B) / δ²
    MDE = (z_{α/2} + z_β) · sqrt( (ω² + σ_A²/K_A + σ_B²/K_B) / n )

Binary paired specialization used for all tables (d ∈ {−1,0,1}, P(disagree)=q
⇒ Var(d) = q − δ², clustered by DEFF_d = 1+(m̄−1)ρ_d):

    MDE = (z_{α/2} + z_β) · sqrt( (q − MDE²) · DEFF_d / N )     (solve by iteration)
    N   = (z_{α/2} + z_β)² · (q − δ²) · DEFF_d / δ²

with z_{.025}+z_{.20} = 1.960+0.842 = 2.80 at α=.05 two-sided, power .80.
q is directly measurable from any prior campaign (§2) — never guess it when
data exists. Every preregistration states this MDE for its design before any
run; every scorecard prints it (§5). Card et al. (arXiv:2010.06595) is the
governing citation for why: GLUE-size test sets leave "most attempted
comparisons to state of the art … not adequately powered."

### 3.5 Multiple comparisons — the family policy

Preregister three families per campaign; each has its own correction. Exact
procedures (both fetched and verified today):

- **Family 1 — primary pairwise claims** (leaderboard separations; with 9
  systems declare the 8 adjacent-rank pairs, or all 36 if the sponsor wants
  the full matrix): **Holm–Bonferroni**, strong FWER control. Sort p_(1) ≤ …
  ≤ p_(m); reject H_(k) while p_(k) ≤ α/(m+1−k); stop at the first failure.
  Uniformly more powerful than plain Bonferroni, no independence assumption.
  Any pair not rejected is *published as a tie* — the scorecard prints
  WIN/TIE/LOSS, never a bare rank.
- **Family 2 — secondary/diagnostic grids** (per-condition contrasts, per-stage
  hazard contrasts, calibration deltas): **Benjamini–Hochberg** at q* = 0.05.
  Largest k with p_(k) ≤ (k/m)·q*; reject p_(1..k); controls FDR = E[false
  discoveries / discoveries]. Use **Benjamini–Yekutieli** (divide by
  c(m)=Σ1/i) only if a grid mixes strongly negatively-dependent statistics —
  our grids are positively dependent, BH is the right default.
- **Family 3 — simultaneous display intervals** (a figure showing all 9 system
  CIs at once): Bonferroni-widened z so the *picture* has ≥95% simultaneous
  coverage: m=9 → z=2.773; m=36 → z=3.197 (computed today). Label the figure
  "simultaneous 95%".

Rule of interpretation: two overlapping CIs do **not** establish a tie and
non-overlap is not the test — the paired Δ CI is the only claim-bearing object
(Chatbot Arena, arXiv:2403.04132, makes the same move: sandwich/bootstrap CIs
on Bradley–Terry coefficients, ties when intervals overlap, active sampling on
the closest pairs — the leaderboard-grade precedent for rank uncertainty).

### 3.6 Judge-derived metrics (reasoning score, notice-act gap)

Deterministic VCC needs none of this; judge-scored *secondary* metrics get:

- **Gate stats with intervals**: gold-set agreement per prereg-3.0.0 (ref ≥
  0.80, weak ≤ 0.50, κ ≥ 0.60) reported with a bootstrap CI over gold items,
  not "5/6 agree".
- **Prediction-powered inference (PPI)** to debias judge scores against the
  gold set (AutoEval Done Right, arXiv:2403.07008 — "increase the effective
  human-labeled sample size by up to 50%"). With judge scores Ẽ on all N
  campaign items and n gold-labeled items with truth Y:

      θ̂_PPI = (1/N)·Σ_N Ẽ_i  +  (1/n)·Σ_n (Y_j − Ẽ_j)         (rectified mean)
      SE²    = Var(Ẽ)/N + Var(Y−Ẽ)/n     → CI95 = θ̂_PPI ± 1.96·SE

  A 40–60-item gold set (the meta-eval set already exists) makes every judge
  metric publishable with an honest interval instead of an asterisk.

### 3.7 Sources of variance disclosure

Per Biderman et al. (arXiv:2405.14782) and Madaan et al. (arXiv:2406.10229 —
"carefully factor in variance when comparing models"): the benchmark card
states which variance sources the intervals cover (template sampling, instance
seeds, decoding stochasticity via repeats) and which they do not (prompt
phrasing, harness class, model version drift). The three-level decomposition
measured today (template / instance / repeat variance for unsaturated systems ≈
0.04–0.10 / 0.06–0.20 / 0.11–0.22 on the outcome scale) is the quantitative
backing: repeats are real noise for mid-tier systems, and the template level is
the binding constraint on the mean (`analysis/statistical_power.md`).

---

## 4. The n for the 300–400 expansion — computed answer

All tables: α=.05 two-sided, power .80, ρ=0.30, ρ_d=0.28 (measured, §2).
Designs are templates × evaluated instances (1 run each unless noted); MDE in
percentage points. Computed 2026-08-16 by the scratchpad script; regenerate
with `analysis/power_analysis.py` after the next campaign.

**Paired MDE between two systems** (q = measured discordance; q=0.10 ≈ near
pairs, q=0.20 ≈ mid-band adjacent pairs, q=0.30 ≈ conservative):

| Design | N runs | q=0.05 | q=0.10 | q=0.20 | q=0.30 |
|---|---|---|---|---|---|
| pilot 8T×5 | 40 | 12.1 | 17.1 | 24.2 | 29.7 |
| prereg-3.0.0 31T×7 | 217 | 6.6 | 9.4 | 13.3 | 16.3 |
| 100T×3 | 300 | 4.4 | 6.3 | 8.9 | 10.8 |
| **120T×3** | **360** | **4.1** | **5.7** | **8.1** | **9.9** |
| 135T×3 | 405 | 3.8 | 5.4 | 7.7 | 9.4 |
| **200T×2** | **400** | **3.5** | **4.9** | **7.0** | **8.6** |

**Same, at the Holm-corrected α for 8 primary comparisons** (z=2.734 — the
honest headline number for a 9-system leaderboard):

| Design | N | q=0.05 | q=0.10 | q=0.20 | q=0.30 |
|---|---|---|---|---|---|
| 100T×3 | 300 | 5.6 | 7.9 | 11.2 | 13.7 |
| 120T×3 | 360 | 5.1 | 7.2 | 10.2 | 12.5 |
| 135T×3 | 405 | 4.8 | 6.9 | 9.7 | 11.9 |
| 200T×2 | 400 | 4.4 | 6.3 | 8.9 | 10.9 |

**Per-condition paired MDE** (each condition holds ~N/3 runs, ~1 run/template
per condition so DEFF≈1): 120T×3 → 7.8 pp at q=0.10, 11.1 pp at q=0.20. C0
false-alarm vs H1 detection contrasts between two models are detectable at
~8–11 pp, not finer — say so in the campaign report.

**Single-system rate, 95% CI full width** (n_eff = N/DEFF): 120T×3 → n_eff 225,
width 5.8 pp at p=.05, 7.9 pp at p=.10, 13.0 pp at p=.50. 200T×2 → n_eff 308,
5.0 / 6.7 / 11.1 pp. (The 8-template pilot: 24–42 pp — unpublishable, as
`analysis/statistical_power.md` concluded.)

**pass^3 headline** (unit = instance, 3 repeats each): 120T×2 instances = 240
instances → paired MDE 6.3 pp at q=0.10, 9.0 pp at q=0.20. Going to 3 instances
per template (360 instances, 1,080 runs/system) buys ~1 pp — prefer more
templates over the third instance if generation capacity allows.

**Discordant-run view (exact McNemar intuition):** a significant separation
needs ~47 discordant runs when the better model wins 75% of disagreements
(π=0.75 → n_disc≈29 at 80% power; π=0.70 → 47). At q=0.20 that is N≈145–235
shared runs; at q=0.10, N≈290–470. The 300–400-run designs sit exactly at this
threshold — which is why every run must be paired and none wasted.

**What 300–400 cannot do:** separate models ~2–3 pp apart. δ=2.5 pp at q=0.10,
m=2, ρ_d=0.28 needs N ≈ 1,600 paired runs (≈800T×2); at m=3, ≈1,950. Publish
such pairs as ties by design, and let repeated campaigns accumulate: k
campaigns of 400 runs pool to a ~√k-narrower paired CI provided templates are
fresh each time.

**Adopted design recommendation** (consistent with
`analysis/statistical_power.md`, now with the paired analysis): **120–135
templates × 3 evaluated instances** (condition-rotated, byte-identical C0/H1
maintained), or **200×2 if template authoring scales** — 200×2 dominates every
statistical column at equal run count; its only cost is authoring+review
throughput and per-template fixed cost. Floor: never below 100 templates. Keep
3 repeats on hidden instances for pass^3 (the reliability headline retrying
cannot inflate — and mid-tier flip rates of 0.20–0.67 mean the repeats carry
real information there); do not add repeats for precision (48→144 runs moved
n_eff 21→26 on the pilot).

Sealed split at 1 run/template: T=120 → Wilson width ~±5 pp at p=.10 —
adequate for its only job (memorization gap detection at the ~10 pp scale seen
in scorecard-1.0.0: gaps of +3 to +15 pp).

---

## 5. What every scorecard prints — the normative block

Ten lines, in order. If a line cannot be printed, the scorecard says why.

1. **Denominators**: N runs, N instances, **T templates (= clusters)**, split
   sizes, censoring/void counts with content-blind rules cited (CORR-003
   style). Cluster count appears *inside* every interval line: "(95% CI x–y,
   120 clusters)".
2. **Headline ladder**: pass^3 ≤ pass@1 ≤ pass@3, each with template-clustered
   95% CI (§3.3). pass^3 in bold; pass@1 labeled "calibration guard rail".
3. **Condition panel**: C0 false-alarm rate, H1 detection rate, F2
   refusal/pushback rate — Wilson on n_eff, cluster CI in the appendix table.
4. **Pairwise matrix** (or adjacent-pair column): Δ̂, paired-clustered SE, 95%
   CI, corr(s_A,s_B), exact-McNemar p, **Holm-adjusted verdict WIN/TIE/LOSS**.
   No rank column without this matrix. (Miller Table 5 format + Family-1
   policy.)
5. **MDE line** (verbatim template): "This campaign separates systems differing
   by ≥{MDE_q=0.2} pp (paired, template-clustered, Holm-corrected across
   {m} primary comparisons, power .80). Smaller gaps are reported as ties."
6. **Multiplicity note**: family definitions, m per family, method (Holm / BH
   q*=.05 / Bonferroni-z for the CI figure).
7. **Calibration**: Brier + RMS calibration error + mean overconfidence, each
   with cluster-bootstrap CI.
8. **Hazard/survival profile**: per-stage h_k with clustered CIs; any
   cross-model stage contrast flagged only if it survives BH (Family 2).
9. **Judge block**: meta-eval gate values with CIs (κ, gold-set agreement),
   PPI-corrected secondary metrics, and the sentence "judge verdicts cannot
   alter VCC."
10. **Provenance**: campaign id, prereg link+hash, corrections-log version
    (currently 9 corrections), generator/verifier versions, seeds, harness
    class per system, sealed-vs-hidden gap with paired CI.

Language rules: "A outperforms B" only for Holm-significant paired
differences; otherwise "indistinguishable at this n (Δ̂ = x, CI −y…+z)".
Never compare across harness classes causally (prereg-3.0.0 rule stands).
Baseline-ladder gates (B1/B8/B9) print PASS/FAIL, not scores.

---

## 6. Ranked recommendations (execute top-down)

| # | Action | Effort | Payoff |
|---|---|---|---|
| R1 | **Commit the expansion shape: ≥120 templates × 3 evaluated instances (accept 200×2 if authoring scales; never <100T).** Vary generator family/area/defect mechanism across templates to keep ρ from creeping up; ρ is re-measured each campaign | design decision, 0 code | Converts the benchmark from "cannot support any public claim" (8T) to 5–8 pp paired resolution — the single highest-leverage decision |
| R2 | **Implement `paired.py` in `crucible/chain/`**: `paired_diff(A, B)` → Δ̂, Miller-Eq.8 clustered SE, t_{T−1} CI, corr, exact McNemar, template sign-flip permutation p. Wire into the scorecard as the pairwise matrix (§5.4) | ~1 day | Kills F1/F2 — makes every separation claim defensible |
| R3 | **Preregister the multiplicity families in prereg-3.0.0 (addendum) and all future preregs**: Family 1 = adjacent pairs, Holm; Family 2 = BH q*=.05; Family 3 = Bonferroni-z display. Add the §3.4 MDE table to the prereg *before* the campaign runs | ~0.5 day, prose + one table | Kills F5; this is what "preregistered" must mean statistically |
| R4 | **Fix printed intervals**: every Wilson goes to n_eff = N/DEFF (ρ from the same campaign, floored at 0.15); primary mean intervals switch to clustered-SE + t_{T−1} once T≥30; percentile bootstrap demoted to sensitivity; wild cluster bootstrap for any T<30 table | ~1 day in `score.py` + scorecard generator | Kills F3/F4; intervals stop lying by ~1.5x |
| R5 | **Give pass^3 its CI** (cluster bootstrap over templates of per-instance unbiased estimates) and a paired variant; print the ladder with three CIs | ~0.5 day | Kills F6 — the headline becomes publishable |
| R6 | **Scorecard generator implements the §5 ten-line block verbatim**, including the MDE sentence and WIN/TIE/LOSS column | ~1 day | The visible artifact of the whole standard; BetterBench-proof |
| R7 | **Judge stats upgrade**: κ with bootstrap CI on the gold set; PPI-rectified reasoning-quality means (§3.6) using the existing meta-eval gold set (target n=40–60) | ~1 day | Kills F7; secondary metrics inherit honest intervals; +~50% effective gold labels for free (arXiv:2403.07008) |
| R8 | **Hazard grid**: cluster the per-stage CIs (template bootstrap) and run cross-model stage contrasts through BH; publish the per-stage q-values | ~0.5 day | Kills F8; the diagnostic layer stops generating false "model X fails at stage 4" stories |
| R9 | **Re-estimation loop**: after every campaign, auto-run `power_analysis.py` + the paired-stats script; write ρ, ρ_d, q, DEFF, achieved MDE into the campaign report; feed next prereg | ~0.5 day (wire into `campaign.py`) | The standard stays calibrated to reality instead of to the 2026-08 pilot |
| R10 | **Leaderboard rank uncertainty** (when public): joint template bootstrap across all systems → rank intervals / tie groups, Arena-style; active top-pair sampling in future campaigns if budget-constrained (arXiv:2403.04132 shows up to ~half the sample needed vs random) | ~0.5–1 day | Flagship-grade presentation; pre-empts "is #2 really #2" criticism |

Total new engineering: ~6–7 focused days. Everything else is preregistration
prose and design discipline.

---

## 7. Sources

Opened and used today (2026-08-16):

- Miller, *Adding Error Bars to Evals*, arXiv:2411.00640 — full text local
  (`analysis/literature/md/2411.00640.md`): Eq. 4 (clustered SE), Eq. 7–8
  (paired, paired-clustered), Eq. 9–10 + App. B/C (power, cluster-adjusted),
  Table 3–5 reporting formats; DROP clustered/naive SE ratio 3.05.
- Anthropic research post, *A statistical approach to model evals*
  (anthropic.com/research/statistical-approach-to-model-evals): five
  recommendations; cross-model correlations "between 0.3 and 0.7".
- BetterBench, arXiv:2411.12990 (+ betterbench.stanford.edu): 46 criteria;
  "most benchmarks do not report statistical significance … nor allow …
  easily replicated".
- HELM, arXiv:2211.09110: 7-metric standardization, no uncertainty reporting
  at headline level.
- τ-bench, arXiv:2406.12045 (ar5iv full text): pass^k = E[C(c,k)/C(n,k)],
  "the chance that all k i.i.d. task trials are successful"; gpt-4o pass^8
  <25% retail.
- Chen et al., arXiv:2107.03374 (ar5iv): unbiased pass@k = E[1−C(n−c,k)/C(n,k)];
  plug-in is a "consistent underestimate".
- Card et al., *With Little Power Comes Great Responsibility*,
  arXiv:2010.06595: GLUE comparisons underpowered; 2,000-sentence MT sets ≈75%
  power for 1 BLEU.
- Biderman et al., *Lessons from the Trenches*, arXiv:2405.14782 (local):
  "Perform Statistical Analyses, and Report on Sources of Variance and Error".
- Madaan et al., *Quantifying Variance in Evaluation Benchmarks*,
  arXiv:2406.10229: variance sources; IRT-style fixes "struggle to
  meaningfully reduce variance".
- Boyeau et al., *AutoEval Done Right*, arXiv:2403.07008: PPI rectification,
  "+up to 50% effective human-labeled sample size".
- Chiang et al., *Chatbot Arena*, arXiv:2403.04132 (HTML full text): BT MLE,
  sandwich + pivot-bootstrap CIs, tie-by-overlap ranking, active sampling
  (random needs up to "54% … more data").
- Holm–Bonferroni procedure (en.wikipedia.org/wiki/Holm–Bonferroni_method):
  reject H_(k) while p_(k) ≤ α/(m+1−k); strong FWER; uniformly more powerful
  than Bonferroni.
- Benjamini–Hochberg / FDR (en.wikipedia.org/wiki/False_discovery_rate):
  largest k with p_(k) ≤ (k/m)α; BY divisor c(m)=Σ1/i under arbitrary
  dependence.
- Binomial proportion CIs / Brown–Cai–DasGupta 2001
  (en.wikipedia.org/wiki/Binomial_proportion_confidence_interval): Wilson "most
  accurate and the most robust"; Wald deprecated.
- Clustered standard errors practice (en.wikipedia.org/wiki/
  Clustered_standard_errors; Cameron & Miller, *A Practitioner's Guide to
  Cluster-Robust Inference*, JHR 2015, PDF fetched): ~30–50-cluster floor,
  CR2/CR3, df corrections, wild cluster bootstrap.
- Inspect (UK AISI) docs (inspect.aisi.org.uk/scorers.html, /metrics.html):
  `stderr(cluster="…")` — clustered SEs are already standard in flagship
  tooling.

Repo evidence: `runs/release-3.0.0/systems/*/outcomes/*.json` (207 files;
paired stats measured 2026-08-16), `analysis/statistical_power.md`,
`analysis/power_analysis.py`, `crucible/chain/score.py`,
`release/1.0.0/scorecard-1.0.0.md`, `release/1.0.0/prereg-3.0.0.md`,
`analysis/literature/README.md`.
