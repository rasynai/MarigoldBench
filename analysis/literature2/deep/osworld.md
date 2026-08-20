# OSWorld — full-text deep read

## Coverage ledger

| Item | Value |
|---|---|
| PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2404.07972.pdf` (36,863,784 bytes, `%PDF-1.5`) |
| MD | `A:/PERTURB-Bench/analysis/literature2/md/2404.07972.md` |
| Pages | 51 |
| Chars extracted | 155,841 |
| Lines | 2,763 |
| Chars actually paged through | 155,841 (100%) |

Chunk ranges read with the Read tool:

1. lines 1–60 (title/abstract check)
2. lines 61–760 (Intro → §5.2 start)
3. lines 761–1400 (§5.2 → App. A.3 / computer_13 table)
4. lines 1401–2040 (computer_13 params → App. C.2 SoM prompt)
5. lines 2041–2763 (SoM prompt → App. D.6, end of file)

No gaps. Appendices A–D read in full, including all prompt text, the per-app breakdown table (Table 14), the qualitative failure transcripts, and the SoM ablation appendix.

## Actual paper identity (as printed)

- **Title:** "OSWORLD: Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments" — matches the assigned topic. (The short title given in the task, "OSWorld: real computer environments for open-ended tasks", is a paraphrase; the printed title is the above.)
- **Authors (printed):** Tianbao Xie, Danyang Zhang, Jixuan Chen, Xiaochuan Li, Siheng Zhao, Ruisheng Cao, Toh Jing Hua, Zhoujun Cheng, Dongchan Shin, Fangyu Lei, Yitao Liu, Yiheng Xu, Shuyan Zhou, Silvio Savarese, Caiming Xiong, Victor Zhong, Tao Yu.
- **Affiliations:** The University of Hong Kong; CMU; Salesforce Research; University of Waterloo.
- **Venue as printed:** "Preprint. Under review." / `arXiv:2404.07972v2 [cs.AI] 30 May 2024`. (Subsequently a NeurIPS 2024 Datasets & Benchmarks paper, but the PDF on disk is the v2 preprint.)
- **Artifact:** https://os-world.github.io

## Section-by-section notes with numbers

### Abstract / §1 Introduction
- First scalable **real** computer environment (VM-backed) for multimodal agents: task setup, execution-based evaluation, interactive learning; Ubuntu / Windows / macOS.
- Benchmark: **369 tasks** on Ubuntu, plus **43 Windows** tasks (license-gated).
- Human success **72.36%**; best model **12.24%** (GPT-4 with a11y tree). Baseline span across all settings: **0.99%–12.24%**. Multi-app workflow best: **6.57%**.
- **134 unique evaluation functions** — "orders of magnitude larger than prior work" (WebArena has 5).
- Diagnosed failure axes: GUI grounding, operational knowledge, repetitive actions, noise from unexpected windows.

### §2 Environment
- Formalized as POMDP (S, O, A, T, R). Reward `R: S × A → [0,1]`; 1 (or a positive decimal <1 for partial credit) awarded **at the final step** if state transitions meet the objective **or** if the agent correctly predicts an infeasible task; 0 otherwise.
- Episode ends on DONE / FAIL or **max 15 steps**; 30-minute wall-clock cap per task.
- Infrastructure: Coordinator + Task Manager + Setup Interpreter + Evaluation Interpreter + Getters + Metrics, driving VMs via `vmrun` and Flask. VMs chosen over Docker for cross-kernel/OS support and snapshot reset; parallel VMs on one host; headless supported.
- Config file is a single JSON with four colored phases: `config` (setup: download/open/resize), `postconfig` (activate window, force-save), `result`+`expected` getters (vm_file, cloud_file, a11y tree, cookies), and `func`+`options` (the evaluator, e.g. `compare_table` with per-range fuzzy rules).
- Initial state is deliberately **intermediate** ("simulate human work in progress"), not a clean boot — hybrid config rather than per-example snapshots, which "would store much unnecessary hardware state information, resulting in each example requiring gigabytes of space."
- Evaluation reaches **inside application internals**: openpyxl / python-docx / python-pptx / raw OOXML, VLC HTTP interface + config file, Playwright over socat to the VM's Chrome, a **custom VS Code extension** installed in the VM, GIMP config files + pillow, and **Firefox Decrypt (a reverse-engineering tool)** to read Thunderbird credentials.
- **Dynamic getters:** for tasks with real-time content (citation counts, blog contents) the getter runs crawler scripts **at evaluation time** and compares against what the agent produced.
- Observation space: full 1920×1080 screenshot including cursor; XML a11y tree (pyatspi on Ubuntu, pywinauto on Windows); terminal output; a video recorder exists but was not modeled.
- Action space: raw `pyautogui` Python code (clicks, drag, hotkeys, typing, loops allowed) plus three special actions **WAIT / FAIL / DONE**. A finite-enumeration variant `computer_13` (13 action types) is provided for RL.

### §3 Benchmark construction
- **369 Ubuntu tasks**: 268 single-app (72.6%), 101 multi-app workflow (27.4%), 84 integrated from other benchmarks (22.8%: NL2Bash, Mind2Web, SheetCopilot, PPTC, GAIA), **30 infeasible (8.1%)**. 302 distinct initial states, 134 eval scripts.
- Per-app counts (Table 10): OS 24, Calc 47, Impress 47, Writer 23, VLC 17, Thunderbird 15, Chrome 46, VS Code 23, GIMP 26, Workflow 101. Avg instruction tokens 33.36 overall (workflow 51.24).
- Infeasible tasks concentrate in GIMP (10), OS (5), VS Code (5), Thunderbird (3), Chrome (3).
- **Cost of construction: ~1800 man-hours** by 9 CS-student authors over 3 months — 650 h single-app, 750 h workflow, 400 h double-checking; plus ~400 h for the integrated examples. Per example: **~1 h for setup config, ~2 h for the evaluator + its examination.**
- Sourcing: official docs, YouTube/TikTok tutorials, WikiHow, Reddit/Quora/SuperUser/StackOverflow, Coursera/Udemy, personal blogs (full source table in App. B.3), selected by views/votes. Cross-app tasks had to be **brainstormed** because the internet lacks them.
- **Quality control (4 rounds):** each example cross-checked by 2 other authors for feasibility/ambiguity/source alignment; then two authors who did **not** annotate it attempt it as human agents; then each example is scrutinized 3 more times "from the perspective of alignment with the instruction and correctness under different solutions." Explicitly hunting **false positives and false negatives**. They still admit: "Further investment of time and a more red teaming could further reduce false positives and negatives."
- Software chosen on 5 criteria: availability on Ubuntu 22.04, open-source license, popularity, community/doc support, category diversity. macOS excluded for legal reasons; Windows tasks license-gated.

### §3.4 Human performance
- Median human completion time **111.94 s** on OSWorld vs **35.38 s** on a 100-task WebArena sample; a significant tail at ≥900 s.
- Human accuracy **72.36%** vs **88%** on WebArena. Annotators were CS students with basic software skills, **not previously exposed to the samples or the software**.
- Human accuracy is nearly flat across categories: OS 75.00, Office 71.79, Daily 70.51, Professional 73.47, Workflow 73.27 (<5% spread). Per-app human floor is Thunderbird at 46.67%.

### §4 Baselines and results
- Models: Mixtral-8x7B, Llama-3-70B, CogAgent, GPT-3.5, GPT-4, GPT-4V, GPT-4o, Gemini-Pro, Gemini-Pro-1.5, Gemini-ProV, Claude-3 Opus, Qwen-Max.
- Scaffolding: chat-mode prompting with the **most recent 3 observations and actions**; temperature 1.0, top_p 0.9, max 1500 output tokens, max 15 steps, 30-min cap. Few-shot (obs, action) pairs were tried first and gave only **2.79%** screenshot-only — history encoding in chat mode was the fix.
- Four input settings: a11y tree (filtered to a tab-separated table; raw XML is "usually over 1 million tokens"), screenshot, screenshot + a11y tree, Set-of-Mark (boxes derived from the a11y tree, not a segmentation model).
- Headline numbers (Table 5, overall): GPT-4 a11y **12.24%**; GPT-4V screenshot+a11y **12.17%**; GPT-4V SoM **11.77%**; GPT-4o a11y **11.36%**; GPT-4o screenshot+a11y **11.21%**; Qwen-Max a11y 6.87%; Claude-3 Opus best 6.72% (SoM); Gemini-Pro-1.5 best 7.79% (SoM); CogAgent 0.99–1.32%; Mixtral 2.98%; Llama-3-70B 1.61%. **Human 72.36%.**
- Category variance is enormous within a single model (GPT-4o screenshot+a11y: OS **41.67%**, Calc 4.26%, GIMP **0.00%**). LibreOffice Calc scores 0.00% for many configurations. Gaps between settings/models "even exceeding 20%".
- SoM **hurt** GPT-4V relative to screenshot+a11y (11.77 vs 12.17) — attributed to high resolution + huge element counts (spreadsheet cells) generating box noise, and to coordinate-level tasks not being representable by boxes.

### §5 Analysis
- **Difficulty** (bucketed by human time): Easy (0–60 s, 28.72% of tasks) 16.78% SR; Medium (60–180 s, 40.11%) 13.12%; Hard (>180 s, 30.17%) **4.59%**. Human: 84.91 / 81.08 / 49.57%.
- **Feasibility:** infeasible subset 16.67% vs feasible 13.34% — but the authors warn agents sometimes "easily output FAIL and refuse to continue trying," which "leads to some false positives in infeasible tasks."
- **Multi-app:** 6.57% vs single-app 13.74%.
- **Resolution:** pure screenshot SR rises monotonically with resolution; SoM peaks at a 0.4 down-sample (768×432) and collapses at 0.2.
- **History:** a11y-tree observations need ~6,000 tokens to cover the 90th percentile (90th pct = 6343.60 tokens) for a **single** observation. More history helps SoM/text; it does **not** help pure-screenshot — "contemporary advanced VLMs might not be as adept at extracting robust contextual information from images as they are from textual data."
- **Perturbation study (the most important experiment for MarigoldBench):** on a 28-task subset where the agent scored **50.79%**, three environment perturbations at episode start — move the window (→ **36.5%**), shrink the window to minimal (→ **15.04%**), open irrelevant maximized apps to clutter the screen (→ **25.39%**). Drops of ~28% to ~70% relative. Agents can switch windows but "fail to maximize the window as an intermediate step."
- **Cross-OS:** GPT-4V screenshot-only scores 4.88% on Ubuntu vs 2.55% on Windows for the migrated subset; correlation coefficient **0.7**.
- **Error taxonomy** from **550 sampled failed episodes**: **>75% contain mouse-click inaccuracies** — "strong planning but weak execution"; derived errors are repetitive clicks and the "environmental noise dilemma" (accidental pop-ups / unrelated apps, from which the agent cannot recover); missing prior software knowledge (GIMP brightness menu hunted at random until step budget exhausted); no human-like web cognition (won't dismiss cookie banners/ads); misinterpreted instructions; visual oversight.
- **Reward-hacking-adjacent finding:** for "use GIMP to cut out the 2s to 4s part of a video" the agent used `ffmpeg` in a terminal — task effect achieved, instruction violated. Marked "Done, but doesn't follow the instruction."
- **Claude-3 vs GPT-4V:** Claude trails by 2.84–7.76 points; "Claude can provide satisfactory high-level solutions, but its grounding ability contains hallucinations in detail" — misreads double-click as select, treats column B as column C, types into the replace box without clicking global replace. In one transcript (App. D.4) Claude fabricates a completed search result and prints "Task complete." / "DONE" twice while having done nothing — a pure self-report failure that only the execution-based checker catches.
- App. D.6: SoM shortens the action space and thereby **hinders exploration**; without SoM the agent solved the VS Code task by editing `settings.json`, with SoM it hunted for a checkbox and failed.

### §7 Conclusion / future work
Four directions: VLM GUI grounding + long context; agent architectures for exploration/memory/reflection; **safety**; broader domains and painless data collection.

## Benchmark card

| Dimension | Value |
|---|---|
| Task count | 369 (Ubuntu) + 43 (Windows, license-gated) |
| Task types | 268 single-app / 101 multi-app workflow / 30 infeasible / 84 integrated from other benchmarks |
| Construction | Human-sourced from forums/tutorials/docs; ~1800 man-hours by 9 annotators; ~1 h setup + ~2 h evaluator per task; 4 rounds of cross-checking including two blind human attempts per task |
| Verification | Execution-based, **example-specific** scripts. Getter functions pull ground-truth state from the VM (files, a11y tree, cookies, app config, VS Code extension output, decrypted Thunderbird profile) or from the cloud/live web; evaluator functions compare to a gold artifact or assert properties. **134 unique evaluation functions.** Agent self-report (DONE) only terminates the episode; it never scores it. |
| Scoring | Binary or partial in [0,1] at the final step; correct FAIL on infeasible tasks scores 1. Reported as mean success rate. |
| Scaffolding | Chat-mode prompt, last 3 (obs, action) turns, `pyautogui` code output, T=1.0, top_p=0.9, 1500 max output tokens, 15-step / 30-min budget; four observation configurations |
| Reported scores | Human 72.36%; best model 12.24% (GPT-4 + a11y tree); range 0.99–12.24%; workflow max 6.57% |
| Uncertainty | **No confidence intervals, no error bars, no seed replication reported anywhere.** Ablations (resolution, history) were run on **10% subsets**; the perturbation study on a 28-task subset. Sampling temperature is 1.0, so per-run variance exists but is not quantified. |
| Contamination handling | Not addressed as such. Partial mitigations: 84 tasks imported from public benchmarks are *acknowledged* as such; instructions are rewritten from sources by authors; resolution can be varied "to avoid potential memorization of absolute pixel values"; but there is no held-out split, no canary, no train/test separation discussion. |
| Cost per run | Not reported in dollars or tokens. Inferable: ≤15 steps × (screenshot + up to ~6.3k-token a11y tree) × 3-turn history; 30-min wall clock cap per task; VMs parallelizable on one host. |

## Limitations admitted

- False positives and false negatives in the evaluators remain; more red-teaming needed (§3.2 Quality control).
- Evaluators check **only** task-relevant outcomes and "pay little attention to potential unnecessary damaging actions of agents"; no metric for agent safety or side effects; "we didn't work out an efficient way to detect the latent side effects of the agent" (§7).
- Agents sometimes output FAIL trivially, producing false positives on the infeasible subset (§5.1).
- a11y tree quality varies by application and developers may not honor conventions; better filtering needed (§7).
- macOS unsupported (legal); Windows set requires user license activation.
- SoM implementation derives boxes from the a11y tree, and low-quality/misleading boxes appear in some apps (App. C.4).
- Closed-model results "could be changed from time" since the endpoints are not versioned-stable (App. C.1).

## Limitations not admitted

- **No uncertainty quantification at all.** With 369 tasks and a 12% success rate, the binomial SE is ~1.7 points; differences like 12.24 vs 12.17 vs 11.77 across settings are reported as if meaningful and are not. Sub-category numbers (OS n=24, Thunderbird n=15) carry SEs of ~8–10 points; "OS 41.67%" is 10/24.
- **No repeated runs** despite temperature 1.0 — every headline number is a single sample.
- **Dynamic getters (live crawlers) make the benchmark non-reproducible over time** for those tasks; the gold value changes with the world. This is presented as a feature with no discussion of drift or of re-scoring old runs.
- **The 15-step cap silently conflates "cannot do it" with "ran out of budget."** The step histogram (Fig. 15) shows a large mass at ≥15 for screenshot and SoM settings, so a substantial share of the 88% failure rate is truncation, not incapacity.
- **Partial credit (positive decimals <1) is mentioned in §2.1 but never characterized** — how many tasks use it, on what scale, or how it enters the reported means.
- **Infeasible-task scoring is degenerate:** a constant-FAIL policy scores 8.1% overall for free, and 16.67% on that subset — approaching the best model's 12.24% overall. The paper notes the false-positive risk but does not correct for it or report a FAIL-rate-adjusted score.
- **Instruction-vs-effect conflation:** the GIMP/ffmpeg case shows the checker can reward achieving the state while ignoring an explicit constraint in the instruction; no systematic audit of how often evaluators are constraint-blind.
- **The 84 imported tasks overlap with training-visible public benchmarks** (Mind2Web, GAIA, NL2Bash) — 22.8% of the suite — with no leakage analysis.

## Implications for MarigoldBench

1. **The recompute-from-artifact pattern is validated at scale, and the cost is knowable: budget ~3 hours of expert time per task family (≈1 h environment/setup config + ≈2 h verifier + examination).** OSWorld spent ~1800 man-hours for 369 tasks with 134 verifiers. For 100+ MarigoldBench families with three conditions each (sound / planted-defect / flawed-premise) the verifier is the dominant cost, not the task prose. Plan for one verifier per family reused across its three conditions, and expect the verifier to reach *inside* the tool's native format (PDB/mmCIF fields, RDKit mol properties, model confidence arrays) the way OSWorld reaches into OOXML, VLC config files, and the Thunderbird profile — not just at a summary number the model typed.

2. **Never let the model's terminal signal carry score, and instrument the DONE/refuse channel separately.** OSWorld's DONE only ends the episode; the reward comes from getters + evaluator. Their Claude-3 transcript literally prints "Task complete." after doing nothing. But they also created a scoring hole: correct-FAIL earns 1, so a constant-refuse policy banks 8.1% overall and 16.67% on the infeasible subset — close to the best model's 12.24%. For MarigoldBench's flawed-premise condition this is the single most important design lesson: **report refusal rate on sound-control tasks alongside the refusal credit on flawed-premise tasks, and make the non-compensatory rule reject any run whose refusal rate on controls exceeds a threshold.** Credit for correct refusal should also require a *correctly identified* reason (e.g., the model must name the specific physical impossibility), verified by a recomputable check on its stated premise, not just the FAIL token.

3. **Plant defects as environment perturbations, not just as prompt lies — the perturbation study is the most transferable result in the paper.** Moving a window took a 50.79% subset to 36.5%; shrinking it to 15.04%; cluttering the screen with irrelevant maximized apps to 25.39%. None of these changed the task; they changed only the incidental state. The lab analogues to plant: a stale/mislabeled file already present in the working directory, a NIM endpoint returning a valid-but-wrong-chain PDB, a prior run's cached output with a plausible name, an input with silently swapped units (Å vs nm, kcal vs kJ), a truncated FASTA, a ligand SMILES that parses but has the wrong stereocenter. Measure the delta against the unperturbed control on the *same* family — that paired design is what makes the 50.79 → 15.04 number legible, and it converts noisy absolute rates into a within-family effect.

4. **Difficulty should be calibrated by human expert time, and the >180 s bucket is where the cliff is.** Success fell 16.78 → 13.12 → **4.59%** across Easy/Medium/Hard while humans only fell 84.91 → 81.08 → 49.57%. Agent-vs-human difficulty is *not* monotone: agents beat humans on "code-solvable" tasks (CPU monitoring, force-kill) and lose on fine-grained GUI manipulation. For MarigoldBench, where every action is already code-shaped through tool calls, the equivalent hardness axis is **the number of dependent artifacts that must survive intact across calls** — a chain where call 7 consumes call 3's output, and where call 3's output was subtly wrong, is the analogue of the >180 s bucket. Target the 5–40% band by tuning chain depth and cross-artifact dependency, not by making individual tool calls harder.

5. **Cap the episode and then report truncation separately, or the score is uninterpretable.** OSWorld's 15-step cap plus a step histogram with a large ≥15 mass means an unknown fraction of failures are budget exhaustion. With 8–25 tool calls per MarigoldBench episode, log and report the **three-way split: verified pass / verified fail / budget-exhausted**, and check that the pass rate is not still climbing at the cap on a pilot subset. Otherwise a scaffolding change (more history, cheaper calls) will look like a capability change.

6. **A sound physical/statistical check must be example-specific and property-based, not one generic metric — and it must be constraint-aware.** OSWorld needed 134 distinct evaluators for 369 tasks, and even so, the GIMP/ffmpeg case shows an evaluator that checked the *effect* and missed the *constraint* ("use GIMP"). For MarigoldBench every verifier should assert a conjunction: (a) the physical/statistical property (RMSD threshold, pLDDT distribution, ΔΔG sign, enrichment factor with a null model), (b) the provenance constraint (the artifact was produced by the tool the task specified, checkable from the file's own metadata/header, not from the transcript), and (c) a negative control (the same check applied to a shuffled/decoy input must fail). Condition (c) is what makes the check *sound* rather than merely stringent — without it you cannot distinguish a real signal from a check that passes on anything.

7. **Budget for verifier false positives and negatives explicitly, with an adversarial pass, and expect it to be the largest residual error term.** OSWorld ran four rounds — annotator self-test, two blind human attempts by non-annotators, three further audits "from the perspective of alignment with the instruction and correctness under different solutions" — and *still* admits FP/FN remain. Concretely for MarigoldBench: for each verifier, (i) have a second person solve the task by a deliberately different route and confirm it passes, (ii) submit at least one plausible-but-wrong artifact and confirm it fails, (iii) submit the planted-defect condition's artifact and confirm the sound-condition verifier rejects it. Treat any verifier that has not survived (ii) as unshipped.

8. **Report template-clustered CIs — OSWorld's absence of them is the clearest gap to beat.** Their setting comparisons (12.24 / 12.17 / 11.77) are within noise at n=369, and their sub-category claims rest on n=15–47. MarigoldBench's plan for template-clustered CIs is the right correction, and the paper gives the concrete sizing argument: at a ~12% mean, per-family n must be large enough (or families numerous enough) that the cluster-robust SE is well under the effect sizes you intend to claim. Also fix temperature/seed policy and run ≥2 replicates per (model, task, condition) so within-family variance is measurable rather than assumed.

9. **Freeze the world, or the benchmark decays.** OSWorld's dynamic getters (live crawlers for citation counts, blog content) mean the gold answer moves. MarigoldBench depends on **hosted NVIDIA NIM endpoints** whose model weights and defaults can change silently — the same hazard, worse. Pin and record model/endpoint versions in every run record, snapshot the exact inputs, and store the reference artifact alongside the tolerance so a re-score months later is comparable. Where a check depends on a remote model's output, prefer verifying a *property of the returned artifact* (geometry, chemistry, statistics) over verifying equality to a stored remote result.

10. **Contamination: treat imported/public task material as a labeled stratum.** 22.8% of OSWorld is imported from Mind2Web/GAIA/NL2Bash/SheetCopilot/PPTC with no leakage analysis. If MarigoldBench reuses any published assay, target, or dataset (PDB entries, DUD-E, MoleculeNet splits), tag those families and report scores with and without them. OSWorld's one useful mitigation is worth stealing in spirit: they vary screen resolution "to avoid potential memorization of absolute pixel values" — the lab analogue is to perturb the surface form of the input (renamed chains, shifted residue numbering, resampled negative sets) so a memorized answer does not transfer while the physics does.

11. **Grounding beats planning as the binding constraint, and the split is measurable.** >75% of 550 sampled failures were execution/grounding errors under accurate plans. Instrument MarigoldBench to separate **plan quality** (did the model choose the right tool sequence?) from **execution quality** (did it pass correct parameters, file paths, chain IDs, units?) by scoring the plan from the first call and the artifact from the last. If frontier models land in the 5–40% band mainly through parameter/handoff errors rather than scientific misjudgment, that is a different — and much more useful — finding than a single aggregate rate, and it tells you which planted defects will discriminate.

12. **Give the model an explicit "insufficient information / cannot proceed" action with a required justification, and log its distribution.** OSWorld's WAIT/FAIL/DONE triad is minimal but load-bearing, and their observation that some models "easily output FAIL and refuse to continue trying" is exactly the pathology MarigoldBench's three-condition design must detect. Make the refusal action carry structured content (which premise fails, which measurement would settle it), and recompute-check that content where possible — that turns refusal from a free 8% into something that must be earned.

## Verbatim quotes

> "Extensive evaluation of state-of-the-art LLM/VLM-based agents on OSW ORLD reveals significant deficiencies in their ability to serve as computer assistants. While humans can accomplish over 72.36% of the tasks, the best model achieves only 12.24% success, primarily struggling with GUI grounding and operational knowledge."
> — Abstract

> "Evaluating the successful execution of general computer tasks presents a significant challenge, as these tasks defy reduction to a uniform pattern or measurement by a single metric. To ensure a thorough assessment, we design example-specific evaluation metrics including pre-setup, post-processing, and dedicated functions, tailored to the software in use and the task's specific requirements."
> — §2.2.3 Execution-Based Evaluation

> "We continue to adopt the SoM setting and sample a subset of 28 tasks that agents relatively well perform (with a success rate of 50.79%) in OSW ORLD . At the beginning of each task, we introduce disturbances to the windows by 1) changing the position of the window; 2) changing the size of the window to the minimal; 3) opening some irrelevant software and maximizing them to clutter the screen. ... We find current agents are not robust in handling all these changes, which leads to a performance drop to over 60% to even 80%."
> — §5.2 Performance by Multimodal Observation Variances

> "Among the 550 failed examples from different settings in our sample, more than 75% exist mouse click inaccuracies, which is the most common error. The agent fails to click the correct coordinates despite planning detailed and accurate steps in their code comments, indicating strong planning but weak execution capabilities."
> — §5.4 Common errors by GPT-4V agents

> "It is noteworthy that we also observe in some methods and settings (such as under the pure screenshot setting with the Gemini-Pro model), agents tend to easily output FAIL and refuse to continue trying. This situation leads to some false positives in infeasible tasks."
> — §5.1 Feasibility

> "The current evaluation functions mainly focus on the results closely regarding the task instructions, assess only the correctness of task completion, and pay little attention to potential unnecessary damaging actions of agents. Owing to the complexity of a complete computer environment, we didn't work out an efficient way to detect the latent side effects of the agent."
> — §7 Addressing the safety challenges of agents in realistic environments

> "It's worth noting that completing through code sometimes mismatches with human instructions. In the task 'use GIMP to cut out the 2s to 4s part of a video,' the agent used 'ffmpeg' command to complete the video cropping, ignoring the 'use GIMP' requirement in the instructions."
> — §5.4 Tasks where agents outperform humans

> "Further investment of time and a more red teaming could further reduce false positives and negatives, which we will leave to future work."
> — §3.2 Quality control
