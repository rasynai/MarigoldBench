# GAIA: A Benchmark for General AI Assistants — deep read

## Coverage ledger

| Item | Value |
|---|---|
| PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2311.12983.pdf` (4,254,059 bytes, header `%PDF-1.5`) |
| Extracted md | `A:/PERTURB-Bench/analysis/literature2/md/2311.12983.md` |
| Pages | 24 |
| Total chars | 82,236 |
| Total lines | 1,118 |
| Chunk 1 | lines 1–600 (title page through references A–I) |
| Chunk 2 | lines 601–1118 (references J–Z, Appendix A extended related work, Appendix B datacard, Appendix C extended description, Appendix D question-design framework, D.1 extended evaluation, Figures 9–11 traces) |
| Chars actually paged through | 82,236 (100%) |
| Extraction quality | Good. Ligature/accent noise in author names (`Gr´ egoire`), figure axis labels flattened into loose numeral runs (Figures 3, 6), one LaTeX brace mangle in Figure 2 code (`f"$–total_food_sales:,.2f˝"`). All tables (1–4) and all prose survived intact. No re-fetch needed (82k >> 15k threshold). |

**Identity check performed:** page 1 line 1–2 reads "GAIA: A Benchmark for General AI Assistants". arXiv id 2311.12983 is correct; no substitution needed.

## Actual paper identity (as printed)

- **Title:** GAIA: A Benchmark for General AI Assistants
- **Authors:** Grégoire Mialon¹, Clémentine Fourrier², Craig Swift³, Thomas Wolf², Yann LeCun¹, Thomas Scialom⁴
- **Affiliations:** ¹FAIR, Meta; ²HuggingFace; ³AutoGPT; ⁴GenAI, Meta
- **Date printed:** November 23, 2023. arXiv stamp: `arXiv:2311.12983v1 [cs.CL] 21 Nov 2023`
- **Venue:** arXiv preprint (later ICLR 2024). Code/leaderboard: `https://huggingface.co/gaia-benchmark`
- **Correspondence:** gmialon@, tscialom@meta.com, clementine@huggingface.co
- **Annotation vendor:** Surge AI (footnote 5), "in a collaboration between our teams and compensated annotators"

## Section-by-section notes with numbers

### Abstract + §1 Introduction (lines 6–111)
Core claim: humans 92% vs GPT-4-with-plugins 15%. 466 questions devised; 166 released with annotations (dev), 300 released **without** annotations to power a leaderboard. Framing is explicitly anti-trend: rather than chase tasks harder for humans (MMLU, GSM8k "already close to be solved", partly "due to rapid LLM improvement possibly combined with data contamination"), GAIA targets tasks conceptually simple for humans but requiring "accurate execution of complex sequences of actions, with large combinatorial spaces."

The controlling design analogy is **Proof of Work** (Jakobsson & Juels 1999; Dwork & Naor 1993): "a computer is asked to solve a complex problem whose solution is easy to verify." The output "could only be obtained upon successful completion of the task and be easy to validate."

Footnote 1: GPT-4 does 86.4% on MMLU; human non-specialist accuracy on MMLU is only 34.5%; expert human ≈ 89.8%. Footnote 4 defines t-AGI (alignmentforum): a t-AGI beats most human experts given time t. Human times on GAIA: 6 min (simplest) to 17 min (most complex), so GAIA solved ⇒ roughly a 6–17-minute-AGI.

Four stated targets: real-world/challenging; interpretability (few, highly curated, non-expert-solvable, reasoning trace inspectable); non-gameability; simplicity of use.

Explicit swipe at MCQ formats: "multiple choice answers (e.g., MMLU) make contamination assessment more difficult since a wrong reasoning trace can more easily get to the correct choice."

### §2 Related work (lines 112–151)
GLUE fell within a year; SuperGLUE within a couple. Model-based eval "relies on using a more capable LLM (often GPT4) than the one currently evaluated," so it structurally cannot grade frontier models, and carries biases such as position preference (Zheng et al. 2023).

Agent-benchmark critique, directly relevant to MarigoldBench: ToolQA / Gentopia recombine existing datasets (MMLU, MATH) "at the risk of contamination during training, and without ensuring tool usage is actually tested." Gorilla/APIBench and API-Bank test "how well an agent like system calls its specific API." AgentBench uses closed-box environments and therefore "risk[s] evaluating how well the assistants have learned to use specific APIs, instead of more general results grounded in real world interactions." GAIA's counter-position: "GAIA does not specify possible APIs, and relies on interactions with the real world." OpenAGI is nearest neighbour; difference is that OpenAGI "focus[es] on current model capabilities rather than upcoming advancements."

### §3.1 Design (lines 155–189)
466 human-designed, human-annotated, text-based questions, some with an attached file. Three principles restated: (1) conceptually simple / real-world / varied; (2) interpretability (human success 92% makes traces checkable by non-experts); (3) robustness against memorization — "the resulting answer is absent by design in plain text from current pre-training data… A progress in accuracy reflects actual system progress." Mitigations against contamination: answer accuracy required, absence from pretraining text, trace inspectability, and the escape hatch that new questions are cheap to craft from the published guidelines.

### §3.2 Evaluation (lines 228–235)
Answer types: string (one or few words), number, or comma-separated list of strings/floats. **One** correct answer. Grading = **quasi exact match** after type-tied normalization. A system/prefix prompt enforces format (full text at lines 191–200 and repeated at 1012–1021): "finish your answer with the following template: FINAL ANSWER: [YOUR FINAL ANSWER]", no thousands commas, no units/$/%, no articles, no abbreviations, digits in plain text. "In practice, GPT4 level models easily follow our format." Scoring function shipped with the leaderboard.

### §3.3 Composition (lines 267–301)
Capabilities (Figure 3 left, questions requiring **at least** that capability):
- Web browsing: **355**
- Coding: **154**
- Multi-modality: **138**
- Diverse filetype reading: **129**
- N/A (no tool needed): **32**

Explicit scope cut: browsing is read-only — "we do not require assistants to perform actions other than 'clicks' on a website such as uploading a file, post a comment or book a meeting." Reason: doing so in real environments without spamming sites "requires careful consideration that we leave for future work."

Also explicit: GAIA deliberately does **not** publish a per-question required-capability list, "since most questions can be solved equally well via different combinations of capabilities," and offers "no fine-grained benchmarking of tool usage."

Level definitions (proxied by annotator steps/tools, not hard constraints):
- **Level 1:** no tools, or ≤1 tool and ≤5 steps
- **Level 2:** ~5–10 steps, combining different tools
- **Level 3:** "arbitrarily long sequences of actions, use any number of tools, and access to the world in general"
Override rule stated: "a question with less than 10 annotator steps but that requires complex web navigation might be categorised as Level 3 rather than 2."

### §3.4 Building and extending (lines 302–341)
Sources of truth: durable web pages (Wikipedia, Papers With Code, arXiv), or an attached document, or self-contained puzzles. No fixed source list, deliberately, "to enforce question diversity and avoid memorisation."

**Validation protocol:** two *new* annotators independently answer every question. Agreement with the creator ⇒ validated; disagreement ⇒ simple fix, else removal. 68% of questions were good as is. Creation cost: **two hours of annotator time per question**, including validation and repair. Conclusion drawn: "question creation can hardly be automated while keeping the interest and variety of questions high."

Web-dependence hazards named: evidence drift over time (mitigated by specifying page versions/dates and preferring durable evidence) and `robots.txt` compliance (checked so evidence pages are bot-accessible).

### §4 LLM results (lines 343–449) + Table 4 (lines 990–1004)
Systems: GPT-4, GPT-4 Turbo, GPT-4 + plugins (manual selection), AutoGPT with GPT-4 backend (git hash `ed172dec1947466cc0942abf75bb77b027cd433d`), plus two non-LLM baselines: human annotators and a **search-engine baseline** (type the question into a search engine, check whether the first results page yields the answer).

| Method | L1 % | L2 % | L3 % | L1 min | L2 min | L3 min |
|---|---|---|---|---|---|---|
| n questions | 146 | 245 | 75 | — | — | — |
| GPT4 | 9.1 ± 2.5 | 2.6 ± 0.6 | 0 | 0.19 | 0.15 | N.A. |
| GPT4 Turbo | 13.0 ± 2.1 | 5.5 ± 1.4 | 0 | 0.24 | 0.12 | N.A. |
| AutoGPT (GPT4) | 14.4 | 0.4 | 0 | 7.6 | 11.7 | N.A. |
| GPT4 + plugins* | 30.3 | 9.7 | 0 | 0.65 | 0.53 | N.A. |
| Search engine | 7.4 | 0 | 0 | 7.4 | N.A. | N.A. |
| Human annotator** | 93.9 | 91.8 | 87.3 | 6.8 | 10.5 | 17.7 |

Uncertainty is reported **only** for the two API-accessible models (± over 3 runs). Where an API exists, the model is run 3× and averaged; times were measured on 20 questions at a single point in time and are explicitly not meant to compare GPT4 vs GPT4-Turbo speed.

The `*` caveat is important: "our score for GPT4 with plugins is an 'oracle' estimate of GPT4 potential with more stable and automatically selected plugins rather than an easily reproducible result." Plugins had to be hand-picked from at most three third-party slots, or Advanced Data Analysis mode; the plugin store churned; the official search tool was removed (paywall circumvention) then restored.

Key qualitative results:
- **Every** system scores exactly **0** on Level 3.
- AutoGPT-4 (the actual autonomous scaffold) *underperforms* bare GPT-4 on Level 2 (0.4 vs 2.6) and is 40–60× slower (7.6–11.7 min vs 0.15–0.24 min). "AutoGPT4 … offer disappointing results for Level 2, and even Level 1 compared to GPT4 without plugins." Its output is "much longer, denser and less interpretable" than GPT-4's.
- Human + GPT-4-with-plugins "seem to offer the best ratio of score versus time needed so far."
- Figure 5 (Level 1 per capability) shows non-zero scores for tool-less GPT-4 on filetype-reading and multi-modality rows because those questions admit alternate solution paths; and non-zero web-browsing scores "mostly due to correct memorization of information required to complete intermediate steps" — i.e. an explicit, measured leakage channel.
- GPT-4 + plugins does exhibit "backtracking or query refinement when the result is not satisfying, and relatively long plan execution" (traces in Figures 9–10).

### §5 Discussion (lines 450–494)
- **Reproducibility:** closed API capabilities drift (Chen et al. 2023); plugins change and are not API-exposed. GAIA is robust to sampling randomness because only the unique final answer is graded.
- **Static vs dynamic:** 466 vs MMLU's ~15,000, but GAIA's are open-ended not MCQ; "we preferred to favour quality over quantity." Decay is expected via (i) catastrophic pretraining contamination or (ii) disappearance of web evidence. "Static benchmarks are broken benchmarks in the making"; the proposal is yearly removal of broken questions plus addition of new ones.
- **System-level attribution:** errors are not attributed to sub-modules (e.g. a bad image classifier label). Defended as intentional: "GAIA aims at evaluating AI systems rather than the current architectural standard."
- **Partial vs full automation:** two systems at 1% and 0% error are "as close as a few percentage" yet represent different paradigms. "Solving GAIA requires full automation since no approximation is allowed in the answer."

### §6 Limitations (lines 495–530)
1. **No trace evaluation.** "In its current form, GAIA does not evaluate the trace leading to the answer." Different paths reach the same answer; no simple grading. Human/model-based trace grading is deferred; noted that a judge "can rely on the ground truth: it is often faster to verify than to independently derive the answer."
2. **No tool-call logs.** "OpenAI's API does not provide the detailed log of tool calls yet, which would be required for fine-grained analysis." Only the strongest tool-enabled LLMs were evaluated.
3. **Annotation cost / residual ambiguity.** Two rounds of annotation needed; "In spite of this thorough process, possible ambiguities remain." Over-specified questions "seem unnatural: these details ensure the question admits only one correct answer and are therefore necessary." Real users ask under-specified questions and a good assistant would cite sources — "Both are difficult to factually evaluate," deferred.
4. **Language/culture.** English only; "will therefore not validate the usefulness of assistants for non-English speakers (80% of the global world population)" nor the non-English web ("about half of its content") nor dialectal English.

### Appendix A (lines 786–799)
Taxonomy of assistant approaches: single-agent CoT (GPT-Engineer, AutoGPT); multi-agent debate (CAMEL, MetaGPT, ChatEval); tool-augmented single agents (BlenderBot 3, BOLAA, AssistGPT, Socratic Models, Visual ChatGPT, WebGPT, Toolformer, ViperGPT, HuggingGPT); tooling libraries (OpenAI plugins, SemanticKernel, LangChain, MiniChain).

### Appendix B Datacard (lines 800–823)
Bender & Friedman style. Annotators all US-based, en-US; all authors are French L2-English speakers, flagged as a possible source of non-standard phrasing. Demographics: age 18–25 17%, 26–35 39%, 36–45 26%, 45–55 13%, 56–65 4%; gender 57% M / 43% F; education Bachelor's 61%, Master's 26%, PhD 17%. **No domain experts** — this is a lay-annotator benchmark by construction.

### Appendix C (lines 825–916)
Capability→tool mapping as reported by annotators: Web browsing (browser, search engine, website widget, YouTube, Street View); Multi-modality (speech-to-text, video recognition, image recognition, OCR, Street View); Coding (Python, calculator, substitution-cipher encoder, C++ compiler, word-reversal script); Diverse filetype reading (PDF, Excel, PowerPoint, CSV, txt); N/A (Tetris rules DB, German translator, spell checker, text editor, bass note data). Caveat: categories overlap (Street View is web + multimodal) and are "indications … not a perfect typology."

File-type distribution (Figure 6, 108 attached files total): xlsx 29, png 18, pdf 15, txt 13, mp3 7, jpg 7, csv 6, docx 2, pptx 2, zip 2, xml 2, py 1, json 1, m4a 1, **pdb 1**, MOV 1, jsonld 1. (The single `.pdb` is the only structural-biology artifact in the whole benchmark — a useful marker of how thin scientific-computation coverage is here.)

Figures 7–8: annotator time correlates with number of steps, but "correlation is less clear with the number of different tools used." Times range up to ~60 minutes.

### Appendix D (lines 917–1004)
Verbatim annotator instructions (8 bullets), the operative constraints being: base on a source of truth; **"Make sure the answer to your question does not exist on the internet in plain text"**; answer is a number or a few words; answer does not change with time (including deletion of source); unambiguous; "interesting"; answerable in reasonable human time; check `robots.txt` (added later).

Table 1 shows the annotation schema: Question, File, Level, Steps (enumerated, 8 for the example), Number of steps, Answer, Time to answer (8 minutes), Tools, Number of tools. Table 2 shows validation schema: Verifier response, Answer match (yes/no), Cause of mismatch.

**Table 3 validation statistics (623 newly crafted questions, 1,246 annotations):**
- Two new annotators agree with original: **55%**
- One agrees, other disagrees: **27%**
- Both disagree: **18%**
- Valid questions aggregated: **68%** (L1 75%, L2 68%, **L3 47%**)
- Human score aggregated: **92%** (L1 94%, L2 92%, L3 87%)

Note the funnel: 623 crafted → 466 shipped (≈75% survival), and Level 3 questions failed validation more than half the time. Also note the definitional subtlety in the footnote: a question counts as valid if both annotators match the designer **or** one matches and the other "made a mistake" — human error is adjudicated away, which is what lets the human score sit at 92% rather than the 55% raw two-of-two agreement rate.

### D.1 Qualitative traces (Figures 9–11, lines 1005–1118)
- Fig 9: bare GPT-4 refuses ("unable to browse the internet… FINAL ANSWER: Unable to provide", ✗); GPT-4 with Bing browsing hits the Internet Archive catalogue and answers "Saint Petersburg" ✓ in one search. Caption: "Proper web search is very effective to answer GAIA questions."
- Fig 10: Goldfinger parachute colour — the browsing plugin **refines** its query ("ending scene object color" → "ending scene parachute color") and answers "Orange, White" ✓, matching ground truth "orange, white" (so normalization is case-insensitive). Caption notes this trace "could not be reproduced with the new version" of the plugin.
- Fig 11: the Rubik's-cube deduction puzzle. GPT-4 produces a long, confident, well-formatted step-by-step derivation and lands on "Red, Yellow" vs ground truth "green, white" ✗. Caption: "GPT4 and other assistants struggle on puzzles, which often are Level 1 questions." This is the single most instructive trace in the paper: fluent structured reasoning, zero external grounding, wrong answer, no self-doubt signalled.

## Benchmark facts, consolidated

- **Task count:** 466 (146 L1 / 245 L2 / 75 L3). Split: 166 dev with annotations, 300 test held out (answers retained).
- **Construction:** human-crafted from seed examples + written guidelines; each question annotated by creator with steps/tools/time; validated by 2 independent annotators; 623 → 466 after repair/removal; ~2 h annotator-hours per shipped question.
- **Verification method:** quasi-exact string match against a single ground-truth answer with type-dependent normalization. No trace grading, no partial credit, no rubric, no LLM judge. Deliberately Proof-of-Work-shaped: hard to produce, trivial to check.
- **Scoring:** per-level accuracy, plus aggregate. Non-compensatory in the sense that no approximation earns credit ("Solving GAIA requires full automation since no approximation is allowed in the answer").
- **Agent scaffolding used:** none imposed. Zero-shot prompt + format prefix. Baselines happen to use ChatGPT plugin modes and AutoGPT, but the benchmark specifies no API surface.
- **Reported scores with uncertainty:** ± std over 3 API runs for GPT-4 (9.1 ± 2.5 L1, 2.6 ± 0.6 L2) and GPT-4 Turbo (13.0 ± 2.1, 5.5 ± 1.4). No error bars for AutoGPT, plugins (manual, n=1), search engine, or humans. No clustering, no bootstrap, no per-family CIs.
- **Contamination handling:** answers required to be absent from the web in plain text; combination of ≥2 sources of truth for L2/L3; open answers rather than MCQ so a wrong trace cannot land on a right choice; trace inspectability; acknowledgment that decay will happen and questions must be rotated yearly.
- **Cost per run:** not reported in dollars. Wall-clock proxies only: GPT-4 ~0.15–0.24 min/question, GPT-4+plugins ~0.53–0.65 min, AutoGPT 7.6–11.7 min, humans 6.8–17.7 min. Construction cost is the reported cost: 2 annotator-hours/question ⇒ ~930 h for 466 (plus the ~157 discarded).

## Limitations admitted vs unadmitted

**Admitted:** no trace/plan evaluation; no tool-call logs from the OpenAI API; residual ambiguity despite double validation; unnatural over-specification of questions; no handling of under-specified real user queries or source-citation behaviour; English/US-only; benchmark decay from contamination and link rot; GPT-4+plugins is an unreproducible oracle; system-level (not module-level) error attribution.

**Unadmitted or under-weighted:**
1. **No refusal or false-premise condition.** Every question has a correct answer. A model that answers everything confidently is never penalized for failing to say "this cannot be determined." Figure 9's GPT-4 refusal is scored as a plain failure even though it was epistemically honest, which actively *rewards* guessing.
2. **No penalty asymmetry at all.** Wrong = blank = refusal. There is no false-alarm cost, so calibration is invisible.
3. **Level 3 is degenerate as a measurement.** All systems score 0, so it contributes zero discriminative signal in this paper, and its questions are the ones that failed validation 53% of the time — the hardest tier is also the least reliable tier.
4. **No per-family or clustered uncertainty.** ±2.5 pp on 146 L1 questions is a run-to-run std, not a sampling CI over questions; question-level correlation (questions sharing a source of truth or an annotator) is unmodelled.
5. **Annotator error is adjudicated out of the human baseline.** The raw both-annotators-agree rate is 55%; the headline 92% comes after excluding invalid questions and re-labelling disagreements as "human mistake."
6. **The 15% headline is a weighted mean over an oracle configuration** (hand-picked plugins per question, n=1, non-reproducible). The reproducible best is GPT-4 Turbo at ~7.5% weighted.
7. **Read-only world.** No write actions, so no way to test whether an agent does something irreversible or harmful, and no notion of side-effect correctness.
8. **Answer-format brittleness is a confound.** With quasi-exact match and an elaborate format prompt, some fraction of failures are formatting, not capability; the paper asserts "GPT4 level models easily follow our format" without measuring it.

## Implications for MarigoldBench

1. **Adopt the Proof-of-Work asymmetry explicitly, and note that MarigoldBench can go further than GAIA.** GAIA's whole verification story is "easy to validate" *because* the answer is a scalar string. MarigoldBench's recompute-the-check design is strictly stronger: instead of matching a memorized ground-truth token, the harness re-runs the physical/statistical test on the submitted artifact, so there is no ground-truth string to leak. Frame this as the fix to GAIA's admitted decay problem — GAIA rots when its answers hit the web; a recomputed check on a *submitted structure/model/dataset* cannot rot the same way, because the artifact is generated fresh per episode. Write that argument into the MarigoldBench paper's related-work section with 2311.12983 as the foil.

2. **Plant the Figure-11 failure mode as a first-class defect class: fluent unverified deduction.** GPT-4 wrote a clean, structured, six-bullet derivation of the Rubik's cube answer and was simply wrong, with zero hedging, on a *Level 1* question. The lab analogue is a model that reasons about a binding pose, a ddG, or a scaffold's plausibility in prose instead of calling Boltz-2/ESMFold and checking. Build a planted-defect family where the shortest path is a confident analytical answer (e.g. "this mutation is clearly stabilizing", "this docking pose is obviously the native one") and the only way to pass the recomputed check is to actually run the tool. Score the prose-only path as a hard fail, not partial credit.

3. **Fix GAIA's biggest hole: no false-premise / refusal condition.** GAIA has no question where "cannot be determined" is correct, so it silently rewards guessing — and it scored GPT-4's honest "unable to provide" as a flat failure. MarigoldBench's flawed-premise condition is the right correction, but make the asymmetry explicit in the scoring writeup: in the sound-control condition a spurious "defect found" must cost as much as a miss, and in the flawed-premise condition an answer produced anyway must cost as much as a wrong answer. That is precisely the axis GAIA cannot measure, and it is the strongest differentiation claim available.

4. **Verify without trusting self-report by never grading the trace — but do log tool calls, which GAIA could not.** GAIA explicitly declines to grade traces (no simple way to grade multiple valid paths) and explicitly could not even *see* tool calls ("OpenAI's API does not provide the detailed log of tool calls yet"). MarigoldBench owns its harness, so log every NIM/RDKit call with inputs, outputs, and hashes, then use the log **only** for post-hoc failure taxonomy and audit — never as a scoring input. Grade solely on the recomputed check over the artifact. This gets GAIA's non-gameability plus the diagnostic power GAIA admits it lacks.

5. **Make the check sound by requiring the artifact to carry its own provenance.** GAIA's soundness rests on "the answer does not exist on the internet in plain text." The lab equivalent: the submitted artifact must be reproducible from the logged tool calls. Have the harness re-derive the claimed quantity from the raw artifact (recompute pLDDT/PAE from the returned structure, re-dock the returned ligand, recompute the AUC from the returned predictions and held-out labels) rather than parsing any number the model states. Concretely: reject submissions whose stated metric and recomputed metric differ beyond tolerance, and report the disagreement rate as a headline honesty statistic — that number has no analogue in GAIA and would be a novel contribution.

6. **Copy the double-blind independent-validation protocol and budget for its yield.** GAIA: 2 fresh annotators answer every question independently; 623 crafted → 466 valid (68% aggregated, only **47% at Level 3**); 2 hours per shipped question. For 100+ MarigoldBench task families with three conditions each, expect to author ~150 families to ship 100, and expect hardest-tier attrition to be worst. Budget the validator pass as a *rerun of the harness by an independent implementer* rather than a human answering — two independent implementations of the physical check that must agree on the same artifact. Any family where the two checks disagree gets repaired or dropped, exactly as GAIA drops ambiguous questions.

7. **Do not let a tier go to all-zero.** All five GAIA baselines scored exactly 0 on Level 3 (75 questions, 16% of the benchmark), producing no signal and wasting a sixth of the annotation budget. With MarigoldBench targeting the 5–40% band, pilot every family against the strongest candidate before shipping and cut or re-tier any family at 0/N and any at N/N. GAIA also shows the converse hazard: the search-engine baseline solved 7.4% of Level 1, so include a trivial baseline (single-tool call, no planning; and a no-tool prose-only model) and drop families that the trivial baseline passes.

8. **Expect the agent scaffold to hurt, and measure it.** AutoGPT-4 scored **0.4%** on Level 2 versus bare GPT-4's 2.6%, while taking 11.7 minutes versus 0.15 — an autonomous scaffold that was net-negative on capability and ~78× the latency. For 8–25-call episodes this is the central risk: long horizons let a weak planner accumulate error. Log per-episode call counts and success-vs-calls curves, and report whether accuracy degrades with episode length. If frontier models show the AutoGPT pattern (worse with more autonomy), that is a publishable finding in its own right and directly justifies the episode-length range.

9. **Steal the format-discipline prompt but measure format loss separately.** GAIA leans on a rigid FINAL ANSWER prefix prompt and asserts frontier models "easily follow our format" without evidence. MarigoldBench submissions are artifacts (PDB files, SMILES, arrays, JSON manifests), where malformed output is far more likely than a stray comma. Define a strict submission schema, validate it separately from the science check, and report `schema_fail` and `science_fail` as distinct rates so a chemistry failure is never confused with a serialization failure. GAIA's inability to separate these is an unadmitted confound worth avoiding.

10. **Report clustered CIs and a reproducible-configuration policy, both of which GAIA lacks.** GAIA reports ± only for two models (run-to-run std over 3 API calls), none for its headline 15% oracle number, and none clustered by question. MarigoldBench's template-clustered CI plan is already the right answer; additionally adopt GAIA's honesty about non-reproducible configurations — pin NIM model versions, record container digests, and mark any hand-configured run as an oracle estimate the way GAIA marks its plugin row with an asterisk. Also mirror GAIA's dev/test split: release a ~1/3 developer set with full verification code, hold back the rest, since the harness code itself is the answer key here.

11. **Real-world grounding beats closed synthetic environments — but you inherit drift.** GAIA's critique of AgentBench (closed environments "risk evaluating how well the assistants have learned to use specific APIs") applies to MarigoldBench with force, since NVIDIA NIM endpoints are a specific API surface that will version-drift. Mitigate the way GAIA mitigates web drift: prefer checks that are invariant to model-version changes (does the designed binder fold to the target topology? is the ROC AUC above chance on held-out data?) over checks tied to a specific endpoint's exact numeric output. Any family whose ground truth is "Boltz-2 returns 0.83" is a broken family in the making.

12. **Capability-coverage bookkeeping.** GAIA's 355/466 web-browsing skew shows how a benchmark drifts into a single dominant capability. Track a MarigoldBench analogue (structure prediction / generative design / docking / cheminformatics / statistics-and-ML) and enforce a floor per capability. Worth noting: GAIA's 108 attached files contain exactly **one** `.pdb`, which is a concrete, citable demonstration that no existing general assistant benchmark covers computational structural biology at all.

## Verbatim quotes

1. §1 Introduction (p. 2, lines 68–74): *"Alternatively to tasks that are harder for humans, AI systems could be asked to solve conceptually simple tasks yet that require accurate execution of complex sequences of actions, with large combinatorial spaces. The output could only be obtained upon successful completion of the task and be easy to validate, analogous to the Proof of Work algorithm (Jakobsson and Juels, 1999; Dwork and Naor, 1993), where a computer is asked to solve a complex problem whose solution is easy to verify."*

2. §3.1 Design choices, third principle (p. 4, lines 180–190): *"Our third principle is robustness against memorization: GAIA aims to be less gameable than most current benchmarks. To complete a task, a system has to plan and successfully complete some number of steps since the resulting answer is absent by design in plain text from current pre-training data. A progress in accuracy reflects actual system progress. … In contrast, multiple choice answers make contamination assessment difficult since a wrong reasoning trace can still get to the correct choice."*

3. §3.2 Evaluation (p. 5, lines 229–234): *"GAIA is designed such that evaluation is automated, fast, and factual. In practice, each question calls for an answer that is either a string (one or a few words), a number, or a comma separated list of strings or floats, unless specified otherwise. There is only one correct answer. Hence, evaluation is done via quasi exact match between a model's answer and the ground truth (up to some normalization that is tied to the 'type' of the ground truth)."*

4. §6 Limitations, Missing evaluations (p. 10, lines 497–503): *"In its current form, GAIA does not evaluate the trace leading to the answer. Indeed, as opposed to the ground truth which is unique, different paths could lead to the correct answer and there is no obvious and simple ways to grade those, while we prioritized easiness of use for GAIA. … the judge can rely on the ground truth: it is often faster to verify than to independently derive the answer."*

5. §5 Discussion, Partial versus full automation (p. 10, lines 488–492): *"Systems that respectively allow partial automation and full automation can be as close as a few percentage of error on a given task—the former would have say 1% and the latter 0%—, yet yield these two fundamentally different paradigms. … Solving GAIA requires full automation since no approximation is allowed in the answer."*

6. §4 Results, on AutoGPT (p. 9, lines 442–446): *"AutoGPT4, which allows GPT4 to automatically use tools, offer disappointing results for Level 2, and even Level 1 compared to GPT4 without plugins. … AutoGPT4 is also slow compared to other LLMs. Overall, the collaboration between a human and GPT4 with plugins seem to offer the best ratio of score versus time needed so far."*

7. §5 Discussion, Static versus dynamic benchmarks (p. 9–10, lines 466–470): *"Static benchmarks are broken benchmarks in the making, and making GAIA evolve year-by-year through the removal of broken questions and the addition of new ones might be an important component to better assess the generalization and robustness of AI systems."*

8. Appendix D, annotator instructions (p. 19, lines 923–928): *"Make sure the answer to your question does not exist on the internet in plain text. Make sure the answer to your question is a number or at most a few words to make evaluation robust. Make sure the answer to your question does not change with time. This includes potential deletion of the source of truth."*
