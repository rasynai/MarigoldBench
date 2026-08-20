# Deep read: "Lessons from the Trenches on Reproducible Evaluation of Language Models" (arXiv 2405.14782v3)

Slug: lessons-trenches. Biderman, Schoelkopf, Sutawika et al. (EleutherAI + 19 institutions), v3 dated 31 May 2026. Position/infrastructure paper distilling three years of maintaining the LM Evaluation Harness (lm-eval); not a new benchmark.

## Coverage ledger

- Source PDF: A:/PERTURB-Bench/analysis/literature/pdfs/2405.14782.pdf (1,123,468 bytes, 31 pages, header `%PDF-1.7`)
- Extracted text: A:/PERTURB-Bench/analysis/literature/md/2405.14782.md
- Total size: 124,833 bytes (`wc -c`); 122,574 characters per Python `len()` (difference = UTF-8 multibyte + newline accounting); 1,617 lines (`wc -l`)
- Chunks read with Read tool (sequential, no gaps, no early stop):
  1. Lines 1-600 (abstract, §1, §2, §3, §4, §5, references start)
  2. Lines 601-1200 (references cont., NeurIPS checklist, Appendix A, Appendix B.1-B.2)
  3. Lines 1201-1617 (Appendix B.2 cont., B.3, B.4, B.5, Appendix C with YAML configs, Appendix D, E, F, G to final line)
- Span covered: lines 1-1617 = 100% of file, including all appendices and tables.

## Section-by-section notes

**Abstract (lines 15-29).** Reliable LM evaluation remains open: sensitivity to setup, difficulty of fair comparison, lack of reproducibility/transparency, and "fracturing and siloing" of conventions. The paper draws on three years of maintaining lm-eval (Gao et al., 2023) to codify tacit "folk knowledge" and recommend best practices.

**§1 Introduction (30-69).** Improper evaluation skews comparisons, misdirects research, and can cause harmful deployments. lm-eval is positioned as an *orchestration* library: non-opinionated about *what* to evaluate (unlike HELM/OpenCompass which prescribe benchmarks) but opinionated about *how* — each task ships a carefully chosen default config while allowing power-user overrides. Three stated goals: (1) collect/synthesize challenges with concrete instances, (2) recommend best practices, (3) document how lm-eval operationalizes them.

**§2.1 The Key Problem (76-123).** Central framing: many semantically equivalent but syntactically different expressions of the same idea exist, and "our best automated tools for determining whether two sentences are semantically equivalent are the very models we are seeking to evaluate." Three response families, each with trade-offs: (a) **closed-domain conversion** — MCQA with a finite answer set, structured/constrained generation, string matching, or (rarely) a "practical verifier" that checks correctness directly; (b) **model-based grading** — BLEU/ROUGE n-gram heuristics (reproducible, cheap, but flawed and with underdocumented hyperparameters) and LLM-as-judge (gaining momentum but "known to be flawed", 8 citations of judge-bias literature); (c) **human labor** — expensive, slow, biased on complex judgments like factual correctness; expert judgment alleviates but doesn't scale. "There is no 'correct' answer, only a best answer in the context that an evaluation is being done." Paper explicitly scopes to MCQA because it is their deepest experience and the most common in the literature.

**§2.2 Social Dynamics of Evaluation (124-152).** New in v3 (not in the 2024 versions' structure). Incentives work against rigor: evaluations justify capital investment — "Evaluations are not just scorecards: they are advertisements." Access is the fundamental barrier: PaLM/PaLM-2, Minerva, Med-PaLM, ERNIE 4.0, Doubao, Hunyuan were never publicly released, so only developer-published numbers exist. API models are subtler: many APIs omit log-probabilities, forcing generation-based evaluation (extra variance from prompt formatting and answer extraction) or trusting self-reported numbers; API benchmarking costs fall disproportionately on independent researchers. "The field has, in effect, adopted a norm where model developers grade their own homework." Even when independent evaluation is possible, there is pressure to cherry-pick tasks, choose flattering prompt strategies, and report single-run point estimates.

**§2.3 Fast-changing Progress and Conventions (153-205).** Figure 1 timeline (2016-2023): Lambada (sentence completion), AI2 ARC/OBQA (custom QA systems), HellaSwag/WinoGrande (fine-tuning), MMLU (in-context learning), MATH (fine-tuning; ICL), against BERT→GPT-2→GPT-3→ChatGPT paradigm shifts. Two impacts: (1) benchmarks used outside their designed paradigm with unclear validity (GLUE/SuperGLUE built for fine-tuning, used zero/few-shot); (2) no ground-truth implementation exists for "retrofitted" benchmarks (LAMBADA, ARC, HellaSwag), fragmenting community methodology. Claim: common practice today diverges from the original paper's method for all listed tasks except MMLU and MATH.

**§3 Evaluation Details are Lost in Communication (206-392).** Benchmark lifecycle is "a game of telephone": design → release → reimplementation by others, losing key details.

- **§3.1 Challenges (220-320).** (i) "Minor" implementation details matter: exact prompt string down to whitespace, and few-shot example choice, significantly change scores. Table 1 (0-shot acc ± CI): performance varies dramatically with prompt (in some cases >20%), and *which* prompt style is best varies by model — so rankings, not just scores, flip. (ii) Fourrier et al. 2023b showed three MMLU implementations (HELM, lm-eval, original) produce widely different scores and change model ranking. Authors infer (undocumented) that Mistral/Mixtral/Llama technical reports used MMLU-style prompts for ARC too, "confounding attempts to replicate the reported scores." (iii) Headline results often unreproducible because models are unavailable (Llama 1 had to copy PaLM/Chinchilla numbers from their reports). (iv) Non-prompt details matter too: nonoverlapping-window perplexity systematically favors long-context models (Press et al. 2020). (v) Every task needs individual care: Ganguli et al. 2023 report even one evaluation (BBQ) takes many researcher-hours; quirks: AI2 ARC is almost all 4-choice but a single question has 5 choices; MMLU is correctly the micro-average over documents, not macro-average over the 57 subjects — the choice "affects results by several percentage points" and is usually unreported; HumanEval has 3 documents lacking the example tests all others have. (vi) Crucial details go unreported: full prompts are "a necessary but not sufficient bar" for reproducibility; foundational loglikelihood-MCQA methodology lives in one GPT-3 appendix and lacks later tweaks.
- **§3.2 Best Practices (321-340).** Release exact evaluation code; report prompts and full methodology (amount of prompt engineering, loglikelihood/perplexity hyperparameters, generation hyperparameters, answer-extraction heuristics); create community reporting standards.
- **§3.3 Operationalizing (341-392).** lm-eval as de facto reporting standard (task name + library version). One-line YAML prompt modification; sensible defaults. Priority list for choosing eval details: (1) widespread agreement among model *trainers*; (2) clear official implementation; (3) agreement among evaluators; (4) their preferred common implementation, prioritizing LLM training papers. Four reasons trainers win: trainers are harder to influence; unreleased models force copying trainer practices; trainers are more attuned to cutting-edge models; trainers "have substantial social and political power within the field." Validation tooling: `--limit` dry runs, `--log_samples` per-sample outputs saved to disk for post-hoc reproducibility.

**§4 Evaluations are Not Just Numbers (393-527).** Conclusions should be "informed by, not constituted by" scores.

- **§4.1 Challenges (400-483).** (i) Benchmarks are proxies for imprecise constructs; validity debates (Messick 1994, Raji et al. 2021, etc.) are ignored by the current wave. Loglikelihood MCQA doesn't even agree with generative-scored MCQA (Lyu et al. 2024); safety-trained models look unbiased on bias benchmarks yet amplify bias in realistic interactions (Omiye et al. 2023; Hofmann et al. 2024). (ii) Uncertainty/variance rarely reported; benchmarks of advanced capabilities are small, so uncertainty is large. Figure 2 (data from Lukošiūtė 2024 blog): GPQA single-run point estimates vs 95% CIs over 10 runs lead to "very different conclusions" about OpenAI vs Anthropic model rankings. HumanEval has only 164 examples; small "improvements" can be "washed out simply via sampling again at the same temperature." (iii) The Benchmark Lottery (Dehghani et al. 2021): Open LLM Leaderboard's arbitrary format choices became optimization targets — practitioners fine-tuned models to match lm-eval separator tokens rather than improving capability. GPT-NeoX-20B scores ~random on ARC-C and MMLU under MMLU-style prompting but much better under cloze; ARC-Easy: cloze 72.4±1.80% vs MMLU-style 26.5±1.78%. Counterfactual: had MMLU-style been the 2020 standard, the Pile might have been wrongly judged "garbage." (iv) "Vibes tests" are widely considered as informative as benchmarks; VibeCheck, Vibe-Eval, and Chatbot Arena formalize intuition — "itself a powerful indictment of the current state of benchmarking."
- **§4.2 Best Practices (484-501).** Perform statistical analyses and report variance/error sources ("seldom done in the field"); evaluate in realistic settings mirroring deployment (exam-style prompts differ from real usage; cites GPQA, KMMLU); do qualitative/exploratory error analysis to separate superficial from fundamental errors.
- **§4.3 Operationalizing (502-527).** lm-eval reports bootstrapped standard errors by default, making CI reporting "nearly as simple as copy-pasting an additional number." Key distinction: bootstrap CIs answer "how much variation should we expect as we sample new questions from the same distribution?" — a different notion from rerunning the stochastic model (as in Figure 2). Both notions (plus prompt/scoring variation) declared valuable. Multiprompt evaluation via PromptSource (BigScience fork, now native): most BigScience papers reported score distributions across prompts.

**§5 Conclusion (528-537).** Recap: documented folk knowledge, recommended mitigations, operationalized them in lm-eval.

**References (538-1057).** ~110 entries; notable anchors: Brown et al. 2020 (GPT-3, source of loglikelihood MCQA), Dehghani et al. 2021 (Benchmark Lottery), Marie et al. 2021 (meta-evaluation of 769 MT papers), Lukošiūtė 2024 (blog, GPQA variance), Gu et al. 2024 (OLMES), Kapoor et al. 2024 (agent benchmarks; cited for HumanEval quirk), Schaeffer et al. 2023 (emergence mirage/Brier score).

**Checklist (1058-1100).** NeurIPS-style. Confirms: limitations in Appendix F, impacts in Appendix G, code/data via URL, error bars "for all experiments we perform as case studies, we report 95% confidence intervals calculated via bootstrapping," compute reported. Theory/crowdsourcing items N/A.

**Appendix A: Library Design (1101-1148).** Two extension points: Tasks (YAML config or Python subclass; data source via HF Datasets; prompt/format tools; Requests; post-processing + metrics — Figure 3) and LMs (interface mapping string inputs → string or probability outputs; tokenizer abstracted inside the LM; model+tokenizer treated as one system). Three Request types (Figure 4): conditional loglikelihoods (`loglikelihood`, multiple choice), perplexities (`loglikelihood_rolling`), generation (`generate_until`). These three primitives cover the major literature approaches.

**Appendix B: Formalizing Measurements (1149-1442).** Written explicitly because these details "do not typically make it into evaluation papers and yet can vitally impact results."

- **B.1 Preliminaries (1155-1167).** Autoregressive LM returns logits (n,|V|); one forward pass yields next-token predictions at every position.
- **B.2 Ranking-Based MCQA (1168-1271).** Four-step recipe for logP(y|x) (Eq. 1): concatenate x,y dropping final target token; forward pass; log-softmax last m positions; sum target-token logprobs. MCQA = argmax over k answer strings' logP(a_i|x); worst case k LM calls; single-token answers scored "for free" from another call's logits. **Normalization options:** token-length normalization (per-token loglikelihood; used alternately with raw by GPT-3); byte-length normalization (tokenizer-independent; lm-eval's `acc_norm`); mutual information — logP(a_i|x) − logP(a_i|null) (pointwise mutual information; nonstandard; `acc_mutual_info`; used selectively by Brown et al. 2020 and Askell et al. 2021). **Exact match via logits:** sum of indicators 1[y_i = argmax] = m iff greedy decoding would produce y verbatim. **Tokenization:** concatenating separate tokenizations of x and y may mismatch training-time tokenization; mitigations include "token healing"; lm-eval shifts trailing prompt whitespace into the target string.
- **B.3 Perplexity (1272-1379).** PPL = exp of average NLL per token (Eq. 2). Tokenizer-independent variants: bits per byte (Eq. 3-4, popularized by the Pile paper; adopted by Paloma, Chinchilla), word-level, byte-level perplexity — lm-eval reports all three. **Sliding window:** non-overlapping context-length chunks (Gao et al. 2020) vs Press et al.'s strided windows mitigating the "Early Token Curse" (tokens early in a window are inherently harder); strided costs up to L/s times the compute; lm-eval uses non-overlapping windows of size L as the cost/mitigation balance.
- **B.4 Generative Evaluation (1380-1424).** Needed because popular APIs do not provide (Anthropic, at time of writing) or greatly limit (OpenAI) logprobs. Sampling hyperparameters (temperature, top-k/top-p, beam search) significantly affect scores and must be reported. Answer extraction by regex is "highly imperfect": model-format mismatch biases toward models matching the original task's format; lm-eval's `Filter` component chains arbitrary post-processing. Without published extraction code and outputs, one cannot "separate models' compliance with the evaluation format from their answer correctness."
- **B.5 Generative vs loglikelihood (1425-1442).** Generative better proxies real chatbot use; loglikelihood works for base/weak models that can't generate well, and Brier scores give smoother measurements (Schaeffer et al. 2023, the emergence-mirage argument).

**Appendix C: Case Studies (1443-1570).** Materials for Table 1. ARC first adapted to ICL as a cloze task by GPT-3 (`Question: {q}\nAnswer:`, comparing completion-string likelihoods); MMLU shows lettered options and scores the letter; MMLU aggregates by micro average. Settings compared: ARC-C "Cloze" vs "MMLU-style"; MMLU "MMLU-style" vs "Hybrid" (MMLU-style prompt but scoring answer *strings* — used by GPT-NeoX-20B and Falcon releases and lm-eval pre-v0.4.0). Experiment = modifying two lines of YAML. All runs on lm-eval v0.4.2 (PyPI). Full YAML configs printed for arc_easy (cloze), arc_easy_mmlu, MMLU original (`doc_to_choice: ["A","B","C","D"]`), MMLU hybrid (`doc_to_choice: choices`); config inheritance shown (ARC-C includes arc_easy.yaml); few-shot sourcing priority: dedicated fewshot split > train > validation > non-overlapping test examples.

**Appendix D: Best Practices Checklist (1571-1605).** Five imperatives: (1) Always share exact prompts — and "Prompts should not be optimized for performance on a given model, and the amount of prompt engineering done should be disclosed." (2) Avoid copying results from other implementations unless verifiably same code; mark clearly if unavoidable. (3) Always provide model outputs — enables re-scoring, significance testing, cheap participation, and partial reproducibility even after API deprecation. (4) Perform qualitative analyses — review small batches before scaling; catch generation-code bugs early. (5) Perform statistical significance testing — "Most works on language modeling do not perform statistical significance testing (Marie et al., 2021)"; averaging over seeds/few-shot selections "can dramatically boost the validity and utility of results."

**Appendix E: Hardware (1606-1607).** All experiments on 8x NVIDIA A40 48GB; total usage under 1 day.

**Appendix F: Limitations (1608-1611).** Two sentences, the second cut off mid-sentence in the published PDF: scope restricted; measurement validity not discussed in detail "due to length reasons"; "There are additionally more case studies and concrete instances of our discussed" [sic — sentence ends there].

**Appendix G: Impacts (1612-1617).** No strong negative impacts foreseen; healthier benchmarking should reduce deployment of LLMs "in unsafe and unsuitable scenarios."

## Benchmark anatomy

This is an infrastructure/position paper, not a new benchmark. Anatomy of what it evaluates and of lm-eval itself:

- **n items:** No new items authored. Case studies re-run existing benchmarks: ARC-Challenge, ARC-Easy, and MMLU (57 subjects), 0-shot, on 5 open-weight pretrained models (GPT-NeoX-20B, Llama-2-7B, Falcon-7B, Mistral-7B, Mixtral-8x7B) under 2 prompt styles per benchmark. Sizes quoted in-paper for others' benchmarks: HumanEval = 164 examples; ARC contains one 5-choice question among 4-choice ones; HumanEval has 3 documents missing example tests.
- **Construction method / authorship:** lm-eval tasks are community-contributed YAML/Python implementations that "strive to match the paper originally introducing a benchmark," falling back to the first paper posing it as a prompted task (usually GPT-3).
- **Validation/review:** qualitative inspection tooling (`--limit`, `--log_samples`), per-sample score logging, task versioning (`metadata.version`), config-file reproducibility; discussion with benchmark creators "to verify intent."
- **Human baseline:** none run or reported.
- **Contamination defenses:** none; contamination is essentially not discussed.
- **Scoring:** loglikelihood-ranked MCQA (`acc` = raw loglikelihood argmax; `acc_norm` = byte-length normalized; `acc_mutual_info` optional); exact-match via greedy-argmax indicator; perplexity as PPL/BPB/word/byte-level with non-overlapping windows; generative scoring via regex/Filter extraction then exact match.
- **Judge design:** no LLM judge used; LLM-as-judge surveyed and flagged as flawed (§2.1).
- **Statistical reporting:** bootstrapped standard errors by default in lm-eval; the paper's own tables report 95% bootstrap CIs (per checklist item 3c). No significance tests, no clustered errors, no multi-seed runs performed in-paper; variance-over-reruns is illustrated only via the borrowed GPQA figure (10 runs). Micro vs macro averaging for MMLU flagged as a several-point choice.

## Reported results

All ± values are 95% bootstrap CIs (per checklist 3c), 0-shot, lm-eval v0.4.2.

Table 1 — ARC-Challenge (acc), Cloze vs MMLU-style:
- GPT-NeoX-20B: 38.0±2.78% vs 26.6±2.53% (cloze better by 11.4pp)
- Llama-2-7B: 43.5±2.84% vs 42.8±2.83% (tie within CI)
- Falcon-7B: 40.2±2.81% vs 25.9±2.51% (cloze better by 14.3pp; MMLU-style ~random)
- Mistral-7B: 50.1±2.86% vs 72.4±2.56% (MMLU-style better by 22.3pp)
- Mixtral-8x7B: 56.7±2.84% vs 81.3±2.23% (MMLU-style better by 24.6pp)

Table 1 — MMLU (acc), Hybrid vs MMLU-style:
- GPT-NeoX-20B: 27.6±0.74% vs 24.5±0.71%
- Llama-2-7B: 39.8±0.79% vs 41.3±0.80%
- Falcon-7B: 29.1±0.75% vs 25.4±0.72%
- Mistral-7B: 48.3±0.80% vs 58.6±0.77%
- Mixtral-8x7B: 59.7±0.77% vs 67.1±0.72%

Other quantitative claims:
- Prompt style shifts scores ">20%" in some cases and flips which model ranks higher (§3.1), consistent with Gu et al. 2024.
- ARC-Easy, GPT-NeoX-20B: cloze 72.4±1.80% vs MMLU-style 26.5±1.78% — a 45.9pp collapse to chance from formatting alone (§4.1).
- MMLU micro- vs macro-averaging changes results by "several percentage points" (§3.1).
- Fourrier et al. 2023b: three MMLU implementations change model ranking order (§3.1).
- GPQA (Figure 2, from Lukošiūtė 2024): single-run vs 10-run 95% CIs yield different model orderings; HumanEval n=164 makes small gains washable by resampling (§4.1).
- Marie et al. 2021 (cited): meta-evaluation of 769 MT papers; most lack significance testing.
- Compute: 8x A40 48GB, <1 day total (Appendix E).

## Limitations the authors admit, and limitations I observe that they do not admit

Admitted:
- Scope restricted; measurement validity not treated in depth "due to length reasons" (Appendix F).
- Focus on MCQA because it is their deepest experience; they "urge experts in those areas" to document other paradigms (§2.1).
- Releasing prompts is necessary but not sufficient for reproducibility (§3.1).
- Bootstrap CIs capture item-sampling variance, a different notion from rerun-the-model variance (§4.3).
- lm-eval's own defaults are choices; priority list acknowledges deference to trainer practice partly for social reasons (§3.3).

Observed (not admitted):
- Appendix F is literally truncated mid-sentence in the published v3 PDF — the limitations section of a reproducibility paper is itself incomplete, an ironic reporting failure.
- The paper recommends significance testing (Appendix D) but performs none itself; only CIs are given, with no paired tests for its own cloze-vs-MMLU-style contrasts.
- Table 1 CIs are i.i.d. bootstrap; MMLU items cluster within 57 subjects and ARC within topic families, so true uncertainty is understated — no clustered/hierarchical errors despite the paper's own micro/macro discussion implying item non-exchangeability.
- Case studies cover only 5 open-weight base models, 0-shot, two prompt styles; no chat/instruct models, no API models, and no few-shot replication of the 25-shot ARC settings they speculate about in §3.1 — thin empirical base for broad prescriptions.
- The run-to-run variance evidence (Figure 2) is borrowed from a blog post, not reproduced; the leaderboard-gaming claim (fine-tuning to separator tokens) is anecdotal with no citation or data.
- Contamination/decontamination — arguably the largest reproducibility threat of the benchmark lifecycle — is absent.
- The trainer-first priority list risks entrenching evaluation settings favorable to incumbent model developers, the same actors §2.2 says "grade their own homework"; the tension is not addressed.
- No treatment of multiple-comparison correction when scanning many tasks/models, nor of power analysis for choosing benchmark size — despite lamenting small benchmarks.

## Implications for CRUCIBLE-CHAIN

1. **Remove answer menus and recipe leaks; score free-form generation against the generator's truth.** The saturation at 94-100% is a textbook instance of this paper's closed-domain-conversion trade-off (§2.1): menus and method recipes turned 5-8-stage judgment chains into format-following, which Table 1 shows models exploit (MMLU-style letter-matching rewards format compliance, +24.6pp for Mixtral). CRUCIBLE-CHAIN possesses the thing the paper calls rare — a "practical verifier" (the deterministic generator) — so it can afford generative evaluation with no menu: require free-form stage outputs (numbers with tolerance windows, named decisions) checked mechanically by the generator, and keep every hint of the method recipe out of the prompt. Concretely: diff each template's prompt against its generator code and delete any token that narrows the judgment space.

2. **Treat prompt phrasing as a measured variable, not a constant.** The paper's core empirical result is that two equally legitimate phrasings move scores by 14-46pp and flip rankings (Falcon 40.2→25.9; NeoX ARC-Easy 72.4→26.5). A "single-digit frontier pass rate" claim from one phrasing per template is fragile: a rival lab can produce a different number with a defensible alternative prompt. Ship 2-3 registered paraphrase variants per template (PromptSource-style multiprompt evaluation, §4.3), report the score distribution across phrasings, and state the headline as the range — this also defends against the objection that difficulty is an artifact of adversarial wording.

3. **Answer the scale question with clustered uncertainty, not raw item counts.** Calibration from this paper: ~1.2k-item ARC-C gives ±2.8pp and ~14k-item MMLU gives ±0.7-0.8pp at 95%. At the target regime p≈0.05, i.i.d. binomial SE with n=144 items is ≈1.8pp (95% CI ≈ ±3.6pp) — cannot separate 3% from 9%. Worse, lm-eval's default i.i.d. bootstrap is invalid for CRUCIBLE-CHAIN: instances within a template share structure, so the effective sample size collapses toward the number of templates (8), and 8 clusters cannot support significance claims at all. Actionable scale answer: grow *independent templates* (target 30-50), not instances per template (~18 is already past the point of diminishing information per cluster); compute CIs by cluster bootstrap over templates; and run a pre-registered power analysis for the claim of record (e.g., to show model A at 5% vs model B at 15% with non-overlapping 95% CIs needs roughly n_eff ≥ 300-500 effective items given clustering).

4. **Report both variance notions the paper distinguishes (§4.3), because non-compensatory chains amplify decoding noise.** Bootstrap-over-items answers "new questions from the same distribution"; rerun variance (Figure 2's 10-run GPQA CIs) answers "same questions, stochastic model." An all-stages-must-pass score at 5-8 stages multiplies per-stage stochasticity: a model with per-stage flip probability ε loses up to ~8ε of chain passes to sampling luck. Run ≥5-10 sampled repeats per item at the deployment temperature, report pass@1 mean ± across-run CI alongside the clustered item CI, and never claim model separation smaller than the run-to-run band — the paper's GPQA figure shows exactly this mistake ("improvements... washed out simply via sampling again at the same temperature").

5. **Log per-stage, per-sample artifacts and audit extraction before scaling (Appendix B.4, D).** With menus gone, scoring depends on extraction from free-form text, which the paper calls "highly imperfect" and warns "could introduce bias towards models that generate responses in a similar format." For the flawed-premise condition this is acute: refusal detection is an extraction problem, and refusal wording varies across models as much as answer formats do. Adopt lm-eval's pattern: `--log_samples`-style persistence of every model output and every stage verdict, a Filter-style extraction pipeline published with the benchmark, and a manual audit of a fixed sample of chain failures per model to separate "compliance with the evaluation format" from "answer correctness" — otherwise single-digit pass rates may partly measure format nonconformity, which saturating models would rightly contest.

6. **Version the benchmark like lm-eval versions tasks, and never silently patch the leak.** The paper's game-of-telephone lesson (§3) and `metadata.version` mechanism (Appendix C) apply directly: the de-leaked CRUCIBLE-CHAIN is a new benchmark version; publish exact prompts, generator code+seed, extraction code, and all model outputs per release (checklist in Appendix D: share prompts, share outputs, don't copy numbers across implementations); explicitly forbid comparing v1.0 saturated scores with v2.0 scores in one table. Disclose the amount of prompt engineering performed on each condition — the paper makes undisclosed prompt optimization a named failure mode.

7. **Exploit the generator as a contamination and anti-gaming defense the paper's static benchmarks lack.** §4.1's Benchmark Lottery shows that once a benchmark matters, its idiosyncrasies (down to separator tokens) become fine-tuning targets, and §2.2 predicts developers will optimize against any benchmark used competitively. CRUCIBLE-CHAIN's deterministic generator can mint fresh instances per evaluation run: keep a public split for reproducibility, a private seed-rotated split for headline claims, and hold out several unpublished templates entirely; report public/private deltas as a gaming indicator. This turns near-zero label error into a renewable resource no static benchmark in this paper has.

8. **Pre-commit to realistic task framing to protect construct validity (§4.2).** The paper warns exam-style artificial formats poorly predict deployment behavior, and that loglikelihood and generative framings disagree (Lyu et al. 2024). CRUCIBLE-CHAIN's chains-of-judgment format is already closer to real scientific workflows than MCQA — preserve that by scoring the artifacts a scientist would actually produce (estimates, flags, refusals with stated reasons) rather than reintroducing any classification scaffold for scoring convenience; and document per §4.2 a qualitative error analysis for each frontier model in the release report, categorizing failures by stage type and condition (clean/planted-defect/flawed-premise).

## Verbatim quotes

Line-wrap hyphenation and PDF line breaks rejoined; wording exact.

1. §2.2 (Social Dynamics of Evaluation): "Evaluations are not just scorecards: they are advertisements."
2. §2.2 (Social Dynamics of Evaluation): "The field has, in effect, adopted a norm where model developers grade their own homework."
3. §2.1 (The Key Problem): "There is no “correct” answer, only a best answer in the context that an evaluation is being done."
4. §3.1 (Each Task Requires Care...): "No task is truly trivial to implement and understand with confidence, and often requires discussing with benchmark creators to verify intent."
5. §4.1 (Lack of Reporting on Uncertainty and Variance): "Practitioners frequently tout small increases in numeric score on datasets such as these, ignoring the fact that such “improvements” might be washed out simply via sampling again at the same temperature."
6. §4.1 (The Benchmark Lottery / vibes discussion): "That the community has found it necessary to build evaluation methodology around formalized intuition is itself a powerful indictment of the current state of benchmarking."
7. Appendix B.4 (Scoring and Answer Extraction): "it is difficult to separate models’ compliance with the evaluation format from their answer correctness."
8. Appendix D (Best Practices Checklist): "Prompts should not be optimized for performance on a given model, and the amount of prompt engineering done should be disclosed."
9. Appendix D (Best Practices Checklist): "Most works on language modeling do not perform statistical significance testing (Marie et al., 2021). This simple addition can dramatically boost the reliability of claimed results."
