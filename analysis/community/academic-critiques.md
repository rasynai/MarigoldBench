# Academic / OpenReview Critiques of Benchmark Papers

**Lens:** what peer reviewers and academic meta-critics actually complain about when they see a new AI/LLM benchmark — annotation error rates, unvalidated LLM judges, missing error bars, cherry-picked baselines, contamination, overclaimed generality.

**Method note.** OpenReview.net and its API are currently behind a Cloudflare Turnstile challenge (and web.archive.org is bot-gated), so direct forum fetches were impossible in this session. Instead, the *actual reviewer text* below was mined from full OpenReview dumps mirrored on Hugging Face: `smallari/openreview-iclr2024-peer-reviews-RAW` (7,404 ICLR 2024 submissions with per-review weaknesses/questions/ratings) and `smallari/openreview-iclr2025-peer-reviews-RAW` (11,672 ICLR 2025 submissions). Canonical OpenReview forum links are given for every quoted paper. This is supplemented with the published academic meta-critique literature (NeurIPS D&B papers, arXiv position papers, and academically authored blogs). All quotes are verbatim from the review dumps unless marked as paraphrase; reviewer typos are preserved.

**Corpus-level frequencies (rough regex lower bounds, weaknesses+questions fields only):**

- ICLR 2024: of 7,404 submissions, ~1,087 are benchmark/dataset/eval-flavored. Within those reviews: error-bars/CI/significance complaints ≈ 206 hits; annotation-quality/label-error complaints ≈ 95; contamination/leakage ≈ 57; unfair/cherry-picked baseline complaints ≈ 70; "dataset too small" ≈ 41; explicit LLM-judge reliability complaints ≈ 24 (narrow pattern) plus 12 "agreement with humans" demands.
- ICLR 2025: of 430 papers with "bench"/"benchmark" in the title: LLM-judge complaints ≈ 97 hits; contamination ≈ 178; annotation/QC ≈ 84; error-bars/CI ≈ 40.

The complaint patterns are not rare edge cases; they are the standard reviewer checklist in practice, and benchmarks that fail several of them at once (ToolTalk, JudgeLM, L-Eval, FactBench, U-MATH, Style-over-Substance, Bench-O-Matic) get rejected.

---

## 1. Distinct complaint patterns

### 1.1 Unvalidated LLM-as-judge ("who validated the grader?")

The single most consistent complaint against modern LLM benchmarks. Reviewers do not accept "we used GPT-4 to grade" without a human-agreement study, and they increasingly know the specific failure modes (position bias, self-preference, length/style bias, leniency).

- **WebArena (ICLR 2024, accepted, forum `oKn9c6ytLx`), reviewer rating 5:** "the proposed framework uses GPT4 to evaluate the answer or the execution paths, which potentially has two issues: 1. GPT4 is a commercial tool, which may limit the potential use of this environment; 2. **GPT4 is not guaranteed to be 100% right, which may make the evaluation results not convincing.**" Followed by: "Is there any analysis or discussion on the performance of GPT4 evaluation?"
- **MathOdyssey (ICLR 2025 submission), reviewer rating 3:** "**The evaluation process is flawed because the authors use GPT-4 as the judge for answers in a zero-shot manner. However, it is unclear how often this judgment aligns with human evaluators.** An analysis of judgment errors is necessary, and I recommend considering rule-based matching." A second reviewer on U-MATH (ICLR 2025, rejected) made the same point for math specifically: use SymPy/Mathematica, not an LLM, where equivalence is checkable.
- **DarkBench (ICLR 2025, accepted), reviewer rating 8:** "I don't expect the authors to validate that LLM-as-a-judge aligns perfectly with human judgment, but **only brief description such as 'poor inter-rater agreement' is not sufficient to me that the LLM judges are performing well enough to trust this benchmark.**"
- **NovelQA (ICLR 2025, accepted), reviewer rating 8:** "gpt-4 is used as an evaluator, with limited details on its evaluation process… **gpt-4 as an evaluator may score higher for gpt-4's answer. This could lead to bias in the results.**" (self-preference bias, raised unprompted by the reviewer).
- **Self-evaluation circularity.** "All Languages Matter" (ICLR 2024, rejected), rating 3: "**ChatGPT is chosen as both the tested model and the evaluator model, meaning it needs to assess its output.** … Using chatGPT as an evaluator for safety doesn't seem like a good idea to me. As such an important issue, human evaluation should be done rather than using another LLM. **Human evaluation is only conducted on 50 samples**." Tiny human-validation samples are a recurring sub-complaint.
- **Judge-distillation circularity.** JudgeLM (ICLR 2024, **rejected**, forum `87YOFayjcG`): "the main evaluation of the judge system is the agreement with GPT-4, thus training on the GPT-4 generated judges may gives the proposed method a unfair advantage"; and bluntly: "**how can we trust the evaluation results of such a judging system built by LLMs?**" Same pattern killed/wounded Generative Judge ("it is unsure whether it can replace GPT4 as judges") and Prometheus ("Let us assume that the GPT-4 evaluator is good enough…").
- **Benchmark-construction-by-LLM contaminating evaluation-by-LLM.** SOTOPIA (ICLR 2024, spotlight), rating 6: scenarios "are generated by prompting GPT-4… [and] are also evaluated by GPT-4 or other LLMs. **This raises a significant concern… it is unclear whether the evaluation using GPT-4 is biased or not.**" AlpaGasus (accepted, rating 6): "**GPT-4 selects the data samples it prefers, which can naturally be used to finetuned a model with the same output characteristics that is preferred by GPT-4**" — reviewers treat GPT-4-curates + GPT-4-grades as a closed loop.
- **Undiscussed judge biases as a rejection reason.** L-Eval (ICLR 2024, rejected), rating 5: "**The blunt recommendation of LLM-based metrics without a thorough discussion of their biases and failure cases is a strong limitation of this paper**," citing the known bias that "LLM evaluators have been reported to favor more detailed and lengthy answers."
- The published literature backs the reviewers: *Large Language Models are not Fair Evaluators* (arXiv 2305.17926) showed "Vicuna-13B could beat ChatGPT on 66 over 80 tested queries" purely by reordering candidate answers ("the quality ranking of candidate responses can be easily hacked by simply altering their order of appearance"). *Judging the Judges* (arXiv 2406.12624) found only the largest judges reach reasonable human alignment, "they are still quite far behind inter-human agreement," scores can be off "up to 5 points," judges show "a tendency toward leniency," and "judges with high percent agreement can still assign vastly different scores" — i.e., report Cohen's kappa/scaled agreement, not raw percent agreement.

### 1.2 Annotation quality, label errors, and undocumented QC ("your ground truth is wrong and you can't tell me how it was checked")

- Reviewers demand the annotation pipeline in detail — who annotated, with what instructions and pay, how disagreements were resolved, and the inter-annotator agreement (IAA). MathVista (ICLR 2024 oral, forum `KUNzEQMWU7`), rating 8: "it is not clear if inter-annotation consistency checks were conducted and how the mentioned 'rigorous review process' was conducted (details are missing)." LogicVista (ICLR 2025): "what is the inter-annotator agreement? How much payment is given to each annotator?" Battle of the Wordsmiths (ICLR 2024): "what is the inter-annotator agreement? (Some questions in the dataset are subjective and rather open-ended. **How is inter-annotator agreement even measured in such cases?**)"
- Low or unreported IAA is treated as disqualifying: FactBench (ICLR 2025, rejected): "Only three speakers were hired for annotation, with relatively low inter-annotator agreement (Cohen's Kappa scores of ≤…)". OptiBench (ICLR 2025), rating 3: quality control by expert OR researchers is claimed but "**there is not enough detail about this process to be able to trust the benchmark's quality**."
- ToolTalk (ICLR 2024, **rejected**, forum `iTddgL0lTQ`): "There is some lack of clarity about the creation of the ground-truth dialogs… **Was there any validation of the data?** Are the GPT4-generated scenarios biased in any particular way?"
- The meta-literature quantifies why this matters. *Pervasive Label Errors in Test Sets* (Northcutt et al., NeurIPS 2021 D&B, arXiv 2103.14749): "an average of at least 3.3% errors across the 10 datasets," "label errors comprise at least 6% of the ImageNet validation set," and corrected labels **flip model rankings** ("ResNet-18 outperforms ResNet-50 if the prevalence of originally mislabeled test examples increases by just 6%"). *Are We Done with MMLU?* (arXiv 2406.04127): 6.49% of MMLU questions contain errors overall and **57% of the analysed Virology subset**; errors "obscure the true capabilities of LLMs" and produce "significant discrepancies with the model performance metrics that were originally reported" (hence MMLU-Redux).
- For agentic/code benchmarks the "annotation" is the test harness, and it fails the same way: *SWE-Bench+* (arXiv 2410.06992) found **32.67% of "successful" patches had the solution leaked in the issue report/comments** and **31.08% passed only because of weak test cases**; "When we filtered out these problematic issues, the resolution rate of SWE-Agent+GPT-4 dropped from 12.47% to 3.97%." (OpenAI's SWE-bench Verified effort — human annotators screening every task and discarding a large fraction as underspecified or unfairly tested — is the industrial confirmation of the same complaint; openai.com blocked fetching in this session, but the audit is corroborated in SWE-Bench+ and widely cited.)

### 1.3 Missing error bars / no statistical rigor ("is this difference even signal?")

- MTU-Bench (ICLR 2025, accepted), rating 6: "The paper does not indicate whether the experiments were conducted multiple times or if statistical confidence measures were applied… **Without multiple runs or confidence intervals, the stability and reliability of the reported results are uncertain**… This omission limits the ability to assess whether observed differences between models (e.g., GPT-4 vs. MTU-LLaMA) **are statistically significant or simply due to random variation.**"
- MDBench (ICLR 2025): "**the dataset is too small to achieve statistical significance — only 300 human verified**." Episodic Memories benchmark (ICLR 2025, accepted), rating 8: "this benchmark does not yield easy high confidence analysis, which is showcased by **massive error bars throughout the main results table**." BRIGHT (ICLR 2025, accepted), rating 8: "Adding error bars or variance for the results, either in the paper or in a leaderboard, could help." DynaMath (ICLR 2025): "Will the evaluation result vary much when you run the evaluation multiple times? Can you provide an error bar for it?" AlpaGasus (ICLR 2024): "What are the standard deviations of the results obtained from the random data splits? And how many runs?" AndroidWorld (ICLR 2025): "How was the confidence interval in Figure 3 calculated? I couldn't find details."
- This is the single most frequent construction complaint by raw count in the ICLR 2024 corpus (~206 hits among benchmark-ish papers).
- The meta-literature is blunter. *BetterBench* (NeurIPS 2024 D&B spotlight, arXiv 2411.12990), after grading 24 prominent benchmarks against 46 lifecycle best practices: "**Most benchmarks do not report statistical significance of their results nor allow for their results to be easily replicated.**" Evan Miller, *Adding Error Bars to Evals* (Anthropic, arXiv 2411.00640): "**the literature on evaluations has largely ignored the literature from other sciences on experiment analysis and planning**" — recommending CLT-based standard errors, clustered SEs for grouped questions (clustering can inflate SEs ~3x), paired model comparisons, variance-reduction via resampling, and power analysis before running the eval. Earlier NLP work (*With Little Power Comes Great Responsibility*, EMNLP 2020) made the same point about underpowered test sets.

### 1.4 Contamination / leakage ("your test set is in the training data")

- AgentBench (ICLR 2024, forum `zAdUB0aCTQ`), rating 8 reviewer: "**There could be data leakage to the tasks selected from the pretraining data over the internet.**"
- SWE-bench (ICLR 2024 oral, forum `VTF8yNQM66`), rating 5 reviewer: "Some of the comparison is not very fair. As Claude 2 is trained on data up to early 2023, GPT's knowledge cutoff is September 2021… **evaluating these models on the dataset that contains instances before 2023 is not fair enough.**" (SWE-Bench+ later found "over 94% of issues were created before LLMs' knowledge cutoff dates.")
- MathOdyssey (ICLR 2025): even for a hand-written dataset, "a sanity check for data contamination should be done… the authors should conduct a contamination detection analysis, which has not been done." Reviewers now cite specific contamination-detection methods (e.g., Golchin & Surdeanu's "Time Travel in LLMs") and expect them to be run.
- AutoAdvExBench (ICLR 2025), rating 8: "all of their current limited success on the benchmark is due to benchmark contamination… **might the benchmark provide an illusion of progress, even if it is just due of benchmark contamination?**"
- The meta-literature: *GSM1k* (arXiv 2405.00332) rebuilt GSM8k from scratch and found "accuracy drops of up to 8%" with "several families of models showing evidence of systematic overfitting," and a positive relation (Spearman's r² = 0.36) between a model's probability of regurgitating GSM8k and its performance gap — memorization, not reasoning. SKILL-MIX's own reviewers framed "accelerating rates of leaderboard saturation, training set contamination, and training corpora secrecy" as the field's pressing issues.

### 1.5 Cherry-picked / unfair baselines and comparison hygiene

- **One prompt for all models.** AgentBench, rating 8: "The benchmark seems to use the same prompt for all models, **which might give an unfair advantage to the model where these prompts were developed for.**" Mirror-image complaint in How-FaR (rejected): "Not a fair comparison across methods. The prompt for FaR is much longer and is much more task specific."
- **Different models on different subsets.** SWE-bench, rating 5: "the experimental results of GPT-4 are on a 20% random subset of SWE-bench while there is no comparison of other models on the same subset. If we only look at this part of the subset, are all the conclusions in the paper still valid/consistent?"
- **Missing or stale baselines.** WebArena, rating 8: "The paper seems to miss out on evaluating some of the latest intelligent agents" (Tree-of-Thought, Reflexion). Countless variants of "important baselines are missing"; one noisy-labels reviewer: "For reasons that are not disclosed, such methods are simply not included in the current paper."
- **Overclaiming from a truncated comparison.** AgentBench, rating 6: "I don't know how fair it is to make a blanket claim that, currently, open-source LLMs fall behind closed-source ones when, by the authors' own admission, they only considered OSS models with ≤70B parameters. I would strongly encourage the authors to rephrase the claim."
- **Cherry-picked qualitative evidence.** "Are the results cherry-picked? Could you give more results?" (MaskINT); "the examples might just be cherry picked and observing them doesn't give me the intuition what [the method] essentially improves" (Social Reward, spotlight).
- The meta-literature names the practices: *Questionable Practices in Machine Learning* (arXiv 2407.12220) catalogs 44 "bad practices which fall short of outright research fraud" — contamination, cherry-picking baselines/checkpoints, test-set tuning, under-reported variance — driven by the "strong incentive… to report a state-of-the-art result on some metric." *The Benchmark Lottery* (arXiv 2107.07002) shows rankings flip under arbitrary task-subset choices: "many factors, other than fundamental algorithmic superiority, may lead to a method being perceived as superior." *The Leaderboard Illusion* (arXiv 2504.20879) documents the same at ecosystem scale on Chatbot Arena: "undisclosed private testing practices" (Meta testing 27 private Llama-4 variants and disclosing the best), data-access asymmetries (Google+OpenAI ≈ 39–40% of all battles vs 29.7% for 83 open-weight models), and "even limited additional data can result in relative performance gains of up to 112% on the arena distribution." Kapoor & Narayanan (AI Snake Oil): "**AI agent accuracy measurements that don't control for cost aren't useful**… for substantially similar accuracy, the cost can differ by almost two orders of magnitude"; they also "were unable to reproduce the results of the LATS and LDB agents on HumanEval" and found papers' GPT-4 baselines "drastically lower than our reproduction" (75.0% vs 89.6%) — weak baselines making agent scaffolds look better than they are.

### 1.6 Suspicious human baselines ("who are these humans and why is their score so low/high?")

- MathVista (oral), rating 8: "**The low human performance on the benchmark (~60% accuracy) is concerning. Could this indicate an issue with data quality of annotation noise?** (rather than intrinsic task difficulty)."
- WebArena, rating 5: "The success rate of human on the designed tasks are only 78%, which is a little surprising… provide more analysis… why human fails."
- WebArena, rating 8, on evaluator selection: "The choice of computer science graduate students as evaluators raises certain concerns regarding the generalizability… it's essential to address potential biases that might arise if any of the evaluators were involved in the dataset's creation… **our accuracy rates didn't match the high scores reported in the paper, which adds a touch of humor to this serious concern.**"
- GAIA (ICLR 2024, forum `fibxvahvs3`), rating 8: "Are these the same validators involved for validating the data or a new fresh set of annotators? This is important… **there are many datasets that claim suspiciously high human performance because they didn't run validation with a new set of annotators.**"

### 1.7 Too small / too narrow to support the claim ("466 questions is not 'general AI'")

- GAIA, rating 3: "**466 questions seems like a very small dataset for a general purpose AI agent.** Furthermore, most of these questions come from web browsing, which makes the benchmark quite close to a narrow AI benchmark for web browsing."
- ToolTalk (rejected): "Dataset size is very small and complete details are missing… Size of the dataset is a major concern for making any conclusions — more seems like a development set." MathVista: "Benchmark is relatively small (6141 examples)." HumanEval per Kapoor/Narayanan: "limited due to its small size (only 164 questions), lack of difficult problems… and potential contamination."
- The construct-validity version of this complaint is the classic *AI and the Everything in the Whole Wide World Benchmark* (Raji, Bender, Paullada, Denton, Hanna; NeurIPS 2021 D&B): influential benchmarks are treated as "stand-ins for a range of anointed common problems" and presented as measuring progress toward "flexible and generalizable AI systems" while actually being narrow, de-contextualized samples — a construct-validity failure. GAIA's own reviewer echoed it: "how do you ensure that good performance on your dataset (at level 3) implies a perfect general assistant?"

### 1.8 "Benchmark tells us nothing actionable" (diagnosticity)

- SWE-bench, rating 6: "It seems that none of the models is doing well… It would be nice if the benchmark can be used to more clearly indicate where the problem in the language model lies. The results… are expected and thus do not seem very interesting."
- AgentBench, rating 6: "**The benchmark does not seem to offer any insights for improvement. (i.e. If my model is not doing well on web-browsing, what should I do?)**"
- GAIA, rating 8 (accept): asks for "partial success" indicators — "When solving a question requires a complex sequence of actions, it is highly desirable to have some measure of where the process breaks down."

### 1.9 Release, reproducibility, and maintenance

- SOTOPIA reviewer (rating 8): enumerate exactly what will be released — code, plug-in interface for new models, interaction data, human judgments, GPT-4 judgments — because "**benchmark papers that don't release anything are pretty useless.**"
- WebArena reviewer: closed-source judge models impede reproducibility ("As the used LLMs for the evaluation are closed-source, this impedes reproduciability").
- BetterBench: most benchmarks fail replicability best practices; it publishes a minimum-quality checklist and a living repository (betterbench.stanford.edu). NeurIPS D&B CFP now hard-requires: "Datasets and code should be available and accessible to all reviewers… at the time of submission. Data should be found and obtained without a personal request to the PI"; Croissant machine-readable metadata; "Code should be documented and executable."

### 1.10 Venue-fit hostility toward dataset papers (an OpenReview-specific pathology)

Even good benchmarks draw "this is not research" reviews at ICLR: GAIA got a rating-3 review arguing "The majority of the contribution here is annotated dat[a]… There are no learned representations, or models, putting it out of the domain of the ICLR community"; WebArena's rating-5 review: "The major weakness of this paper is the lack of technical novelty. Though the contribution on simulated environment/datasets/resources are welcomed… such papers may not match the general style of ICLR papers." This is why the D&B track exists — and it means benchmark authors face both the rigor checklist above *and* residual "no novelty" bias.

---

## 2. What this community says would make a science benchmark trustworthy / flagship-grade

Distilled from the reviews and the meta-literature (BetterBench's 46 best practices, Miller's recommendations, NeurIPS D&B requirements, and what reviewers explicitly ask for in rebuttals):

1. **Validated grading.** If any LLM judge is used: report agreement against *fresh* human annotations on a meaningful sample (not 50 items), use chance-corrected metrics (Cohen's kappa, not raw percent agreement), test and mitigate position/self-preference/length biases (e.g., balanced position calibration, multiple judges, judge ≠ any evaluated model), and prefer deterministic/rule-based verification (unit tests, SymPy) wherever the answer is formally checkable. Publish the judge prompts and an error analysis of the judge itself.
2. **Documented, audited annotation.** Who annotated, instructions, payment, expertise; inter-annotator agreement with adjudication procedure; an estimated label-error rate from an independent audit; wrong/ambiguous items fixed or flagged (MMLU-Redux/SWE-bench-Verified-style). Assume ~3–6% label error until measured (Northcutt).
3. **Statistical reporting by default.** Multiple runs where stochastic; standard errors/CIs on every headline number (CLT-based, clustered when items are grouped); paired tests for model-vs-model claims; power analysis showing the test set is large enough to distinguish the models it claims to rank; no bold-the-best-number tables where differences are within noise.
4. **Contamination controls.** Run an explicit contamination analysis (n-gram overlap, time-travel/canary probes); align items with model knowledge cutoffs or use post-cutoff/freshly generated items; consider dynamic/perturbable variants; state training-corpus caveats honestly.
5. **Fair, strong, current baselines.** Same items and same subset for every model; prompts either standardized or tuned per model (state which); include the strongest recent methods and simple baselines; report cost/compute alongside accuracy (Pareto reporting) so scaffold gains aren't just spend.
6. **Honest human baselines.** Fresh annotators who did not construct the data; report who they are; investigate any surprisingly low/high human score before publishing it.
7. **Construct validity and scope honesty.** Say what the benchmark actually measures and for whom; no "general intelligence/assistant" claims from a few hundred items; provide difficulty structure and partial-credit/failure-localization signals so the benchmark diagnoses rather than just ranks.
8. **Full release and maintainability.** Data, harness code, per-item model outputs, judge outputs, and human judgments released at submission time; machine-readable metadata (Croissant); versioning, an error-reporting channel, and a plan for updates/retirement as models saturate it.
9. **Sensitivity analyses.** Show rankings are stable under task-subset choice, prompt variants, and judge choice (Benchmark Lottery / Leaderboard Illusion insurance).
10. **Equal-access leaderboard governance** if there is a public leaderboard: no private pre-testing with selective disclosure, symmetric sampling, transparent deprecation (Leaderboard Illusion).

The cynical summary of the community's default prior: a new benchmark is assumed to have wrong labels, an unvalidated judge, contaminated items, noise-level deltas, and baselines chosen to make the authors look good — until the paper demonstrates otherwise, per item 1–9.

---

## 3. Representative quotes

1. "GPT4 is not guaranteed to be 100% right, which may make the evaluation results not convincing." — WebArena reviewer (rating 5), ICLR 2024, openreview.net/forum?id=oKn9c6ytLx
2. "The evaluation process is flawed because the authors use GPT-4 as the judge for answers in a zero-shot manner. However, it is unclear how often this judgment aligns with human evaluators." — MathOdyssey reviewer (rating 3), ICLR 2025 (via HF review dump)
3. "Only brief description such as 'poor inter-rater agreement' is not sufficient to me that the LLM judges are performing well enough to trust this benchmark." — DarkBench reviewer (rating 8), ICLR 2025
4. "There are many datasets that claim suspiciously high human performance because they didn't run validation with a new set of annotators." — GAIA reviewer (rating 8), ICLR 2024, openreview.net/forum?id=fibxvahvs3
5. "The low human performance on the benchmark (~60% accuracy) is concerning. Could this indicate an issue with data quality of annotation noise?" — MathVista reviewer (rating 8), ICLR 2024, openreview.net/forum?id=KUNzEQMWU7
6. "Without multiple runs or confidence intervals, the stability and reliability of the reported results are uncertain… whether observed differences between models are statistically significant or simply due to random variation." — MTU-Bench reviewer (rating 6), ICLR 2025
7. "The benchmark seems to use the same prompt for all models, which might give an unfair advantage to the model where these prompts were developed for. There could be data leakage to the tasks selected from the pretraining data over the internet." — AgentBench reviewer (rating 8), ICLR 2024, openreview.net/forum?id=zAdUB0aCTQ
8. "How can we trust the evaluation results of such a judging system built by LLMs?" — JudgeLM reviewer (rating 5), ICLR 2024 (rejected), openreview.net/forum?id=87YOFayjcG
9. "Benchmark papers that don't release anything are pretty useless." — SOTOPIA reviewer (rating 8), ICLR 2024
10. "Might the benchmark provide an illusion of progress, even if it is just due of benchmark contamination?" — AutoAdvExBench reviewer (rating 8), ICLR 2025
11. "Most benchmarks do not report statistical significance of their results nor allow for their results to be easily replicated." — BetterBench, NeurIPS 2024 D&B, arXiv:2411.12990
12. "The literature on evaluations has largely ignored the literature from other sciences on experiment analysis and planning." — Evan Miller, *Adding Error Bars to Evals*, arXiv:2411.00640
13. "When we filtered out these problematic issues, the resolution rate of SWE-Agent+GPT-4 dropped from 12.47% to 3.97%." (32.67% solution leakage, 31.08% weak tests) — SWE-Bench+, arXiv:2410.06992
14. "ResNet-18 outperforms ResNet-50 if the prevalence of originally mislabeled test examples increases by just 6%." — *Pervasive Label Errors in Test Sets*, arXiv:2103.14749
15. "Vicuna-13B could beat ChatGPT on 66 over 80 tested queries" by reordering answers — *LLMs are not Fair Evaluators*, arXiv:2305.17926
16. "AI agent accuracy measurements that don't control for cost aren't useful… for substantially similar accuracy, the cost can differ by almost two orders of magnitude." — Kapoor & Narayanan, *AI leaderboards are no longer useful*
17. Paraphrase: 44 named questionable research practices — "bad practices which fall short of outright research fraud" — driven by the "strong incentive… to report a state-of-the-art result on some metric." — *Questionable Practices in ML*, arXiv:2407.12220

---

## 4. Sources

**OpenReview review corpora (actual reviewer text; OpenReview itself is currently Turnstile-gated, so mined via mirrored dumps):**
- https://huggingface.co/datasets/smallari/openreview-iclr2024-peer-reviews-RAW (7,404 ICLR 2024 submissions, full weaknesses/questions/ratings)
- https://huggingface.co/datasets/smallari/openreview-iclr2025-peer-reviews-RAW (11,672 ICLR 2025 submissions)

**Canonical OpenReview forums for quoted papers (ICLR 2024):**
- SWE-bench: https://openreview.net/forum?id=VTF8yNQM66
- GAIA: https://openreview.net/forum?id=fibxvahvs3
- AgentBench: https://openreview.net/forum?id=zAdUB0aCTQ
- WebArena: https://openreview.net/forum?id=oKn9c6ytLx
- MathVista: https://openreview.net/forum?id=KUNzEQMWU7
- ToolTalk (rejected): https://openreview.net/forum?id=iTddgL0lTQ
- JudgeLM (rejected): https://openreview.net/forum?id=87YOFayjcG

**Meta-critique literature and guidelines (all opened this session):**
- BetterBench (NeurIPS 2024 D&B): https://arxiv.org/abs/2411.12990
- Adding Error Bars to Evals (Miller, Anthropic): https://arxiv.org/abs/2411.00640 (HTML: https://arxiv.org/html/2411.00640v1)
- SWE-Bench+: https://arxiv.org/abs/2410.06992
- Are We Done with MMLU? (MMLU-Redux): https://arxiv.org/abs/2406.04127
- GSM1k / Careful Examination of Grade School Arithmetic: https://arxiv.org/abs/2405.00332
- The Leaderboard Illusion (Chatbot Arena): https://arxiv.org/abs/2504.20879
- Pervasive Label Errors in Test Sets (NeurIPS 2021 D&B): https://arxiv.org/abs/2103.14749
- LLMs are not Fair Evaluators: https://arxiv.org/abs/2305.17926
- Judging the Judges: https://arxiv.org/abs/2406.12624
- Questionable Practices in Machine Learning: https://arxiv.org/abs/2407.12220
- The Benchmark Lottery: https://arxiv.org/abs/2107.07002
- AI and the Everything in the Whole Wide World Benchmark (NeurIPS 2021 D&B): https://arxiv.org/abs/2111.15366
- Kapoor & Narayanan, "AI leaderboards are no longer useful": https://www.normaltech.ai/p/ai-leaderboards-are-no-longer-useful
- NeurIPS 2025 Datasets & Benchmarks CFP (review requirements): https://neurips.cc/Conferences/2025/CallForDatasetsBenchmarks

**Referenced but not fetchable this session:** OpenAI, "Introducing SWE-bench Verified" (openai.com returns 403 to this fetcher); its annotation-audit findings are corroborated in SWE-Bench+ above.
