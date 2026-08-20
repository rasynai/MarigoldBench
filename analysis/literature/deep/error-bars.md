# Deep read: Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations

- **Paper**: Evan Miller (Anthropic), arXiv:2411.00640v1 [stat.AP], 1 Nov 2024 (dated November 4, 2024 on title page)
- **Slug**: error-bars
- **Files**: PDF `A:/PERTURB-Bench/analysis/literature/pdfs/2411.00640.pdf` (330,983 bytes, 14 pages); extracted text `A:/PERTURB-Bench/analysis/literature/md/2411.00640.md`

## Coverage ledger

- Total characters (wc -c on md file): **37,251**
- Total lines (wc -l): **762**
- Extraction: pypdf over all 14 PDF pages; python-side string length 35,881 chars (37,251 bytes on disk after UTF-8 + CRLF encoding)
- Chunks read with Read tool (sequential, spanning entire file):
  - Chunk 1: lines 1–762 (offset 1, limit 1200; file ends at line 762)
- Coverage: 762/762 lines = 100%, including references and Appendices A–C. Nothing skipped.

## Section-by-section notes

**Abstract.** Evals are experiments, but the eval literature ignores the experiment-analysis literature from other sciences. Conceptualizes eval questions as drawn from an unseen super-population; presents formulas for analyzing eval data, measuring differences between two models, and planning experiments; makes reporting recommendations that "minimize statistical noise and maximize informativeness."

**1 Introduction.** Notes industry "highest number is best" practice: SOTA bolded without significance testing (cites Madaan et al. [15]). Chatbot Arena popularized CIs on Elo; Llama 3 report [7] is a rare Q&A-eval exception with simple CIs — which this paper later shows are "likely too narrow in some cases and too wide in other cases." Motivating fiction: models "Galleon" vs "Dreadnought" on MATH (65.5% vs 63.0%, +2.5%), HumanEval (83.6% vs 87.7%, −3.1%), MGSM (75.3% vs 78.0%, −2.7%) (Table 1). Superficially Dreadnought wins 2 of 3. Five recommendations enumerated: (1) CLT-based standard errors of the mean; (2) clustered SEs when questions come in related groups; (3) variance reduction via answer resampling and next-token probabilities; (4) paired question-level differences when comparing two models; (5) power analysis to size an eval or subsample.

**2 Analysis framework (preamble).** Core assumption: questions are random draws from a "(hypothetical, infinite, unseen) super-population." This lets inference target the underlying skill rather than the specific question set.

**2.1 Independent questions.** Score decomposition s_i = x_i + ε_i (conditional mean + zero-mean noise); σ²_i = Var(ε_i). µ = E[s] = E[x] is the super-population mean; estimate µ̂ = s̄; SE_CLT = sqrt(Var(s)/n) with the n−1 sample variance (Eq 1); Bernoulli special case SE = sqrt(s̄(1−s̄)/n) (Eq 2). Bootstrapping (e.g. OpenAI Evals) deemed unnecessary when CLT applies (finite variance, many questions). Flags that Llama 3 [7] wrongly used SE_Bernoulli even for fractional scores (F1) — conservative (too wide); UK AISI's Inspect stderr() metric is correct. Reporting recommendation: SE in parentheses beneath each score, plus question counts (Table 2: MATH 5,000 Qs, SE 0.7%; HumanEval 164 Qs, SE 3.2%/3.0%; MGSM 2,500 Qs, SE 0.9%). 95% CI = s̄ ± 1.96·SE (Eq 3).

**2.2 Clustered questions.** DROP, QuAC, RACE, SQuAD have multiple questions per passage; MGSM is the same question translated across languages. Non-independent inclusion violates CLT/bootstrap assumptions → naive Eq 1 is inconsistent. Imports clustered standard errors from social science (Abadie et al. [1]): Eq 4 adds cross-term covariances within clusters to SE²_CLT; acts as a "sliding scale" between perfectly correlated (cluster = one observation) and uncorrelated (reduces to unclustered). Table 3 reporting format: question count AND cluster count (DROP 9,622 Qs / 588 clusters; RACE-H 3,498 / 1,045; MGSM 2,500 / 250). Table 4 (real data, Anthropic models): clustered vs naive SE — DROP 1.34 vs 0.44 (ratio **3.05**), RACE-H 0.51% vs 0.46% (1.10), MGSM 1.62% vs 0.86% (1.88). Concludes the Llama 3 reading-comprehension CIs are "likely anti-conservative (too narrow)."

**3 Variance reduction (preamble).** Law of total variance: Var(µ̂) = Var(s)/n = (Var(x) + E[σ²_i])/n. Var(x) is a property of the super-population and "immutable"; only more questions n or attacking E[σ²_i] helps.

**3.1 Resampling.** Answer each question K times; score = mean of K → conditional variance σ²_i/K. Rule: pick K such that E[σ²_i]/K ≪ Var(x); beyond that, more K does little. Worked example (binary scores, difficulty x ~ U[0,1]): Var(x) = 1/12, E[σ²_i] = 1/6, so K ≫ 2; Var(µ̂|K) = Var(µ̂|K=1)·(1 + 2/K)/3. K=2 cuts total variance by 1/3; K=4 by 1/2; K=6 by 5/9; asymptotic ceiling 2/3. Warning: pooling all K·N answers into one SE is inconsistent (violates independence) — compute SE across question-level means.

**3.2 Next-token probabilities.** For evals without chain-of-thought, read the correct-answer token probability p_i directly: s_i = x_i = p_i, ε_i = 0, killing conditional variance entirely — achieves the resampling ceiling (2/3 reduction in the uniform example) at one forward pass.

**3.3 Don't touch the thermostat!** Advises against lowering sampling temperature to reduce variance (unless the goal is to study the model at that temperature). Example 1: single-token true/false with x_{T=1} ~ U[0,1]: T=0 rounds scores to Bernoulli(1/2), inflating Var(x) from 1/12 to 1/4 — "inadvertently tripled the minimum variance." Example 2: x_{T=1} ~ U[1/3,1] → T=0 gives Bernoulli(3/4): E[x] shifts from 2/3 to 3/4 (bias) and Var(x) rises ~five-fold (1/27 → 3/16). Recommended two-pronged strategy: use next-token probabilities when possible; otherwise resample with K sized so E[σ²_i]/K ≪ Var(x); never adjust temperature for variance reasons.

**4 Comparing models (preamble).** A single model's eval score "usually does not have any inherent meaning; it primarily makes sense in relation to the scores of other models."

**4.1 Unpaired analysis.** µ̂_{A−B} = µ̂_A − µ̂_B; SE_{A−B} = sqrt(SE²_A + SE²_B); CI (Eq 5) and z-score (Eq 6). Works even when two reports used non-identical random question subsets.

**4.2 Paired analysis.** When both models answer the same questions, compute question-level differences s_{A−B,i}; SE from their sample variance (Eq 7). Variance identity: paired variance = unpaired − 2·Cov(x_A, x_B)/n — a gain whenever models agree on which questions are easy/hard. Example: continuous next-token scores, corr 0.5 → variance falls 1/3 in relative terms (1/6 → 1/9). Since scores are "likely to be positively correlated, even across unrelated models," pairing is a "free" variance reduction. Recommends reporting pairwise differences, pairwise SEs, and score correlations; equivalent formula via Pearson correlation. Eq 8 gives the paired+clustered SE. Table 5 (fictional): MATH +2.5% (0.7%), CI (+1.2%, +3.8%), corr 0.50 → significant; HumanEval −3.1% (2.1%), CI (−7.2%, +1.0%), corr 0.64 → not significant; MGSM −2.7% (1.7%), CI (−6.1%, +0.7%), corr 0.37 → not significant. Resolves the intro puzzle: the careful analyst concludes Galleon (not Dreadnought) has the only significant win.

**5 Power analysis.** Defines α (Type I), 1−β (power), Minimum Detectable Effect δ. With ω² = Var(x_A) + Var(x_B) − 2Cov(x_A,x_B) and per-model mean conditional variances σ²_A, σ²_B, resample counts K_A, K_B: n = (z_{α/2} + z_β)²(ω² + σ²_A/K_A + σ²_B/K_B)/δ² (Eq 9). Worked example: σ² = 0, ω² = 1/9, δ = 0.03, α = 0.05, β = 0.20 → n ≈ **969** → "new evals should contain at least 1,000 questions." Inverted MDE formula (Eq 10); second example: σ²_A = σ²_B = 1/6, ω² = 1/9, corr 0.5, n = 198 → raising K from 1 to 10 cuts MDE from **13.2% to 7.5%**. Uses: subsample sizing, choosing K, deciding whether an eval is worth running, commissioning new evals.

**6 Conclusion.** Recaps: naive/clustered SEs for single models; unpaired/paired/paired-clustered for two models; variance reduction via resampling, next-token probabilities, question-level pairing; temperature warning; reporting recommendations (SEs, pairwise stats, correlations); sample-size formula. Closing plea: treat evals "as informative experiments rather than a series of contests to produce the largest number."

**References.** 18 entries: clustering theory (Abadie et al. QJE 2022), NLP power analysis (Card et al. 2020 "With Little Power Comes Great Responsibility"), the evals critiqued/used (MATH, HumanEval, MGSM, DROP, QuAC, RACE, SQuAD), Llama 3 report, Chatbot Arena, Madaan et al. 2024 variance quantification, Imbens & Rubin causal inference text, List/Sadoff/Wagner NBER power rules-of-thumb, OpenAI Evals and UK AISI Inspect frameworks, Anthropic "Challenges in evaluating AI systems," Hinton et al. distillation (temperature citation).

**Appendix A: Clustered standard errors.** Derives Eq 4 via regression: s_{i,c} = µ + δ_{i,c} + ε_{i,c} with question-level fixed effects not separately estimated; sandwich estimator (X′X)⁻¹(Σ_c X′_c Ω X_c)(X′X)⁻¹ with X = 1_n, Ω_c = u_c u′_c collapses to Var_clustered(µ̂) = Var_unclustered(µ̂) + Σ_c Σ_i Σ_{j≠i}(s_{i,c}−s̄)(s_{j,c}−s̄)/n². Two-sample version: apply to question-level score differences.

**Appendix B: Sample-size formula derivation.** Following [14], posits a threshold measurement s̃_{A−B} triggering Type I error with prob α and Type II with prob β; solves the two z-score equations to eliminate s̃ and get the MDE (Eq 10), inverts to get n (Eq 9).

**Appendix C: Cluster-adjusted sample-size formula.** Clustered analogues of ω², σ²_A, σ²_B via triple sums over clusters and cross-terms; decomposition Var_clustered(µ̂_{A−B}) = ω²_clustered + σ²_A,clustered + σ²_B,clustered; these drop into Eqs 9/10 unchanged. Practical estimation recipe from previous data with K ≫ 1: x̂_{M,i,c} = mean over K samples; σ̂²_M,clustered divides by K−1 (not K) for consistency at small K. If subsampling questions for variance estimation, sample whole clusters "in order to capture the intra-cluster variance structure."

## Benchmark anatomy

This is a **statistical methodology paper, not a benchmark paper** — it introduces zero new items, so most anatomy fields are N/A by design; statistical reporting is its entire subject.

- **n items**: none new. Operates on existing public evals: MATH (5,000 questions), HumanEval (164), MGSM (2,500 questions in 250 clusters — same problem × ~10 languages), DROP (9,622 questions / 588 passages-as-clusters), RACE-H (3,498 / 1,045), plus QuAC and SQuAD named as clustered evals.
- **Construction method**: N/A (framework). The core modeling move is treating any eval's questions as iid draws (or cluster-iid draws) from an infinite unseen super-population.
- **Item authors / validation / review**: N/A. No new data collection; no annotation pipeline.
- **Human baseline**: none.
- **Contamination defenses**: none discussed at all — a notable silence (see Limitations).
- **Scoring method**: assumes scores s_i are given (binary or fractional, e.g. F1); scoring correctness/judge error is out of scope. No judge design.
- **Statistical reporting (the paper's substance)**: CLT standard errors (Eq 1) and Bernoulli special case (Eq 2); 95% normal CIs (±1.96 SE); clustered SEs via social-science sandwich estimator (Eq 4, Appendix A); paired-difference SEs (Eq 7) and paired+clustered (Eq 8); z-tests on differences (Eq 6); power/sample-size formula n = (z_{α/2}+z_β)²(ω² + σ²_A/K_A + σ²_B/K_B)/δ² (Eq 9, Appendix B) with clustered variants (Appendix C). Recommends reporting: question count, cluster count, SE in parentheses under every score, pairwise differences with SEs and correlations.
- **Real-data validation**: one table (Table 4) of real numbers on unnamed Anthropic models; everything else fictional-but-reasonable.

## Reported results

All fictional numbers are labeled as such by the paper; Table 4 is the only real-data table.

- Table 1 (fictional): Galleon vs Dreadnought — MATH 65.5% vs 63.0% (+2.5%); HumanEval 83.6% vs 87.7% (−3.1%); MGSM 75.3% vs 78.0% (−2.7%).
- Table 2 (fictional, reporting format): MATH n=5,000, 65.5% (0.7%) vs 63.0% (0.7%); HumanEval n=164, 83.6% (3.2%) vs 86.7% (3.0%); MGSM n=2,500, 75.3% (0.9%) vs 78.0% (0.9%).
- Table 4 (**real**, Anthropic models): clustered vs naive SE — DROP 1.34 vs 0.44, ratio 3.05; RACE-H 0.51% vs 0.46%, ratio 1.10; MGSM 1.62% vs 0.86%, ratio 1.88.
- Table 5 (fictional, paired analysis): MATH +2.5% (SE 0.7%), 95% CI (+1.2%, +3.8%), corr 0.50 — significant; HumanEval −3.1% (2.1%), CI (−7.2%, +1.0%), corr 0.64 — n.s.; MGSM −2.7% (1.7%), CI (−6.1%, +0.7%), corr 0.37 — n.s.
- Resampling arithmetic (uniform-difficulty binary example): Var(x)=1/12, E[σ²]=1/6; variance reduction 1/3 at K=2, 1/2 at K=4, 5/9 at K=6, ceiling 2/3 (= next-token-probability gain).
- Temperature examples: T=0 inflates Var(x) 1/12 → 1/4 (3×); second example biases mean 2/3 → 3/4 and inflates Var(x) 1/27 → 3/16 (~5×).
- Paired-differences example: corr 0.5 → 1/3 relative variance reduction (1/6 → 1/9 absolute).
- Power: n ≈ 969 to detect δ=3% at α=0.05, power 80%, ω²=1/9, σ²=0 → "at least 1,000 questions" guidance. MDE example: n=198, σ²=1/6, ω²=1/9 → K: 1→10 shrinks MDE 13.2% → 7.5%.
- Llama 3 critique: Bernoulli SEs on fractional scores → conservative (too wide); unclustered reading-comprehension SEs → anti-conservative (too narrow).

## Limitations

**Admitted by the authors (explicitly or implicitly):**
- The super-population is acknowledged as hypothetical — the framework rests on a "simple supposition" of random draws from an infinite unseen population (Section 2), which no curated eval literally satisfies.
- CLT machinery requires finite variance and "a large number of questions" (Section 2.1); bootstrap reserved for complicated schemes.
- Var(x) is "immutable" — nothing reduces question-selection variance except more questions (Section 3).
- Next-token probability trick applies only to evals without chain-of-thought/generation (Section 3.2), i.e., not to agentic or multi-step tasks.
- Power-example parameters are "fictional" though "reasonable" (Section 5); ω² and σ² must be estimated from previous eval data, and Appendix C notes this needs prior data with K ≫ 1.

**Observed by me, not admitted:**
- **No small-cluster theory.** Clustered sandwich SEs are known to be downward-biased with few clusters (rule of thumb <30–50); the paper's examples have 250–1,045 clusters and it never warns about the few-cluster regime, nor mentions wild cluster bootstrap or t(G−1) critical values. This is exactly the regime of a benchmark with 8 templates.
- **Normal CIs break near the boundary.** ±1.96·SE intervals misbehave at scores near 0% or 100% (can exceed bounds; poor coverage); no Wilson/Jeffreys/exact binomial alternative is discussed. Saturated (94–100%) and target single-digit regimes both live at the boundary.
- **No multiple-comparison control** across many evals × many models — each test is at 5% in isolation; a leaderboard with dozens of comparisons will produce false "significant" wins.
- **Cross-model residual independence** is asserted ("recognizing that the cross-model residuals are uncorrelated") but can fail with shared scaffolds, shared judges, or same-seed sampling infrastructure.
- **Scores assumed error-free**: no treatment of grader/judge error, label noise, or parsing failures as variance or bias components.
- **No contamination or selection-bias discussion**: the super-population fiction quietly assumes questions were not chosen adversarially or leaked into training.
- **Minor erratum**: Table 1 gives Dreadnought HumanEval 87.7% while Table 2 gives 86.7% for the same fictional setup.
- **Thin empirical validation**: one real table (Table 4), unnamed models, no code or data release mentioned.
- Static design only: no sequential testing, early stopping, or adaptive sampling, which real eval loops use.

## Implications for CRUCIBLE-CHAIN

1. **Templates are clusters; the effective sample size is ~8, not ~144.** Instances generated from one template share the method recipe, surface structure, and the same attractive wrong path, so within-template scores will be strongly correlated. Under Eq 4 the SE slides toward the "one observation per cluster" end: with 8 templates the clustered SE on a mean pass rate is bounded below by roughly sqrt(Var(template means)/8) — at p≈0.5 that is ±15–18 points, and even at p≈0.1 it's several points. Action: (a) always compute and report template-clustered SEs (Table 3 format: n items AND n clusters); (b) grow the number of independent templates, not instances per template — cluster count, not item count, buys power. The paper's real-world 3.05× DROP ratio is the mild case; ours will be worse because instances-per-cluster is high (18) and intra-cluster correlation is high.

2. **Answer the question of record with Eq 9 + Appendix C, parameterized from the 828-run pilot.** Estimate ω²_clustered, σ²_A,clustered, σ²_B,clustered from existing repeat data (Appendix C's estimator, dividing by K−1), then solve n = (z_{α/2}+z_β)²(ω² + σ²_A/K_A + σ²_B/K_B)/δ² where n counts **independent templates**. Ballpark: for binary chain scores with paired ω² ≈ 0.1, detecting a 10-point difference between two frontier models at α=0.05/power 0.8 needs ~78 independent template-clusters; a 5-point difference needs ~314. The paper's own headline — ~969 independent questions for a 3-point MDE — says 8 templates cannot support any between-model significance claim at realistic effect sizes; plan for tens-to-hundreds of independent templates and publish the MDE (Eq 10) of whatever size ships.

3. **Choose K (repeats per instance) by the E[σ²]/K ≪ Var(x) rule, and never pool.** Multi-stage chains at generation temperature have large conditional variance σ²_i (a model stochastically survives or dies across 5–8 judgment calls), and the next-token-probability shortcut is unavailable for chain-of-thought tasks (Section 3.2's explicit scope limit), so resampling is the only conditional-variance lever. Measure E[σ²_i] from pilot repeats; the paper's example (K: 1→10 halves MDE from 13.2% to 7.5% at n=198) shows repeats matter most when per-item variance rivals between-item variance — likely true for near-threshold chains. Score each instance as its mean over K, compute SEs across instances (clustered by template); pooling all K·N runs into one SE is inconsistent per Section 3.1. Given chain compute costs, use Eq 10 to trade K against template count — once E[σ²]/K ≪ Var(x), spend the budget on new templates instead.

4. **Do not fight saturation or noise by dropping temperature to 0.** Section 3.3 shows T=0 both biases the estimand (E[x] 2/3 → 3/4 in its example) and can inflate the variance of conditional means several-fold by rounding latent pass-probabilities to 0/1. For CRUCIBLE-CHAIN the per-stage judgment calls are exactly where the distribution over reasoning paths lives; evaluate at the deployment temperature with K repeats and report mean pass rates, treating "94–100% saturation" claims themselves as estimates with clustered SEs — at 97% on 144 items in 8 clusters, the CI is wide enough that "94–100" may not distinguish models at all.

5. **Use paired, clustered differences (Eq 8) for every claim — between models and between conditions.** The three-condition design (clean / planted defect / flawed premise) shares generator seeds across conditions, so the scientifically interesting quantities — the within-instance drop from clean to defect, and the refusal rate delta on flawed premises — are natural paired differences with "free" variance reduction (1/3 at corr 0.5 in the paper's example, likely more here since conditions share everything but the perturbation). Report Table 5-style: difference, paired SE, 95% CI, and correlation, clustered at template level. This also applies to before/after leak-fix comparisons of the same model.

6. **Non-compensatory scoring makes the top-level score cleanly Bernoulli — exploit it, and avoid Llama 3's mistake in the other direction.** All-stages-must-pass chain outcomes are 0/1, so SE_Bernoulli (Eq 2) is exact at the instance level (before clustering); but any stage-level partial-credit diagnostics are fractional scores and must use SE_CLT (Eq 1), not the Bernoulli formula (the exact error the paper catches in the Llama 3 report, where it inflates SEs). Also: the 5–8 stages of one chain are one observation, never 5–8 — the instance is the unit, the template is the cluster.

7. **Adopt the paper's reporting standard wholesale in the CRUCIBLE-CHAIN release package.** Every reported score carries (SE) beneath it; every table lists n instances and n templates; model comparisons come as paired differences with CIs rather than bolded maxima; the benchmark card states α, power, and the minimum detectable effect at the shipped size so consumers know what claims the eval can and cannot support ("If the number of questions in the eval is fixed, consumers can calculate the Minimum Detectable Effect and decide whether the eval is worth running"). Given single-digit target pass rates, supplement the paper's normal CIs with exact/Wilson binomial intervals — a gap the paper itself doesn't address but that matters at the boundary.

8. **Guard the small-cluster regime the paper ignores.** If the redesign ships with fewer than ~30 templates, plain sandwich clustered SEs will be optimistically small; use wild cluster bootstrap or t-critical values with (G−1) degrees of freedom, and say so. Conversely, this is a quantitative argument for the redesign target: template count is the binding statistical constraint, ahead of instances-per-template and repeats.

## Verbatim quotes

(Exact strings from the extracted text; line-wrap hyphenation removed where the PDF broke a word across lines.)

1. Section 1 (Introduction): "Evals are commonly run and reported with a “highest number is best” mentality; industry practice is to highlight a state-of-the-art (SOTA) result in bold, but not necessarily to test that result for any kind of statistical significance."
2. Section 2 (Analysis framework): "Suppose that the questions in an eval do not represent all possible questions, but instead were drawn at random from a (hypothetical, infinite, unseen) super-population of questions."
3. Table 4 caption (Section 2.2): "Clustered and naive standard errors computed on two popular evals using Anthropic models (non-fictional numbers). Analyzing the same data, clustered standard errors can be over 3X larger than naive standard errors."
4. Section 2.2 (Clustered questions): "Failure to adjust standard errors for clustered sampling may lead an unsuspecting analyst to suppose that the measurement of the overall eval score is much more precise than it actually is."
5. Section 4.2 (Paired analysis): "Because eval question scores are likely to be positively correlated, even across unrelated models, paired differences represent a “free” reduction in estimator variance when comparing two models."
6. Section 5 (Power analysis): "Although these parameters are fictional, they are reasonable, and suggest that new evals should contain at least 1,000 questions in order to have good signaling ability."
7. Section 3.3 (Don't touch the thermostat!): "It may be tempting to reduce the “sampling temperature”[10] of the model in order to reduce (or eliminate) the conditional variance. However, we advise against this practice, unless the purpose is to study the model at the new temperature."
8. Section 6 (Conclusion): "We hope that with proper statistical tools, such as those presented in this article, machine learning practitioners will think of their model evaluations as informative experiments rather than a series of contests to produce the largest number."
