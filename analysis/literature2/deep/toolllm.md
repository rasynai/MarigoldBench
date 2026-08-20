# Deep read: ToolLLM / ToolBench / ToolEval (arXiv 2307.16789v2)

## 1. Coverage ledger

| Item | Value |
|---|---|
| PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2307.16789.pdf` (2,048,075 bytes, `%PDF-1.5`) |
| MD | `A:/PERTURB-Bench/analysis/literature2/md/2307.16789.md` |
| Pages | 24 |
| Extracted chars | 83,423 (85,873 bytes on disk with CRLF) |
| Lines | 1362 (final line unterminated, rendered as 1363) |
| Chunk 1 | lines 1-700 (title page through references, p.1-11) |
| Chunk 2 | lines 701-1363 (references end, Appendix A.1-A.8, p.11-24) |
| Chars actually paged through | 83,423 (100%) |
| Extraction fallback needed? | No (83k >> 15k threshold) |
| Title check | PASSED on page 1 — arXiv id is correct |

Read order was strictly sequential; no skipping. Appendix A.7 (prompts, ~lines 914-1285) contains a
verbatim 240-line JSON API list dump, which is low-information but was read.

## 2. Actual paper identity (as printed)

- **Title (p.1):** "TOOLLLM: FACILITATING LARGE LANGUAGE MODELS TO MASTER 16000+ REAL-WORLD APIS"
- **Header on every page:** "Preprint" (this v2 is the ICLR 2024 submission version; dated `arXiv:2307.16789v2 [cs.AI] 3 Oct 2023`)
- **Authors:** Yujia Qin*, Shihao Liang*, Yining Ye, Kunlun Zhu, Lan Yan, Yaxi Lu, Yankai Lin†, Xin Cong,
  Xiangru Tang, Bill Qian, Sihan Zhao, Lauren Hong, Runchu Tian, Ruobing Xie, Jie Zhou, Mark Gerstein,
  Dahai Li, Zhiyuan Liu†, Maosong Sun† (* equal contribution, † corresponding)
- **Affiliations:** 1 Tsinghua University, 2 ModelBest Inc., 3 Renmin University of China, 4 Yale University,
  5 WeChat AI / Tencent Inc., 6 Zhihu Inc.
- **Artifacts:** https://github.com/OpenBMB/ToolBench

This is simultaneously a **dataset/benchmark paper** (ToolBench + ToolEval), a **method paper** (DFSDT
search algorithm + neural API retriever), and a **model paper** (ToolLLaMA). All three are covered below.

## 3. Section-by-section notes with numbers

### Abstract / §1 Introduction (lines 10-221)
Claim: open-source LLMs (LLaMA) lack tool-use ability because instruction tuning ignores the tool domain.
Three-phase pipeline: (i) API collection — 16,464 real RESTful APIs, 49 categories, from RapidAPI Hub;
(ii) instruction generation via ChatGPT; (iii) solution-path annotation via a novel depth-first-search
decision tree (DFSDT). Evaluation via ToolEval (ChatGPT-as-judge, pass rate + win rate).

Stated deficiencies of prior tool datasets (the design brief for ToolBench): **limited APIs** (not real
RESTful, or tiny/low diversity), **constrained scenario** (single tool only; users must hand-specify the
ideal API set), **inferior planning** (CoT/ReACT only; several prior works "do not even execute APIs to
obtain real responses").

Table 1 (line 166-186) comparison, ToolBench vs prior:

| | ToolBench | APIBench | API-Bank | ToolAlpaca | ToolBench (Xu) |
|---|---|---|---|---|---|
| Real-world API | yes | no | yes | no | yes |
| Real API call & response | yes | no | yes | no | yes |
| Multi-tool | yes | no | no | no | no |
| API retrieval | yes | yes | no | no | yes |
| Multi-step reasoning | yes | no | yes | yes | yes |
| # tools | 3,451 | 3 | 53 | 400 | 8 |
| # APIs | 16,464 | 1,645 | 53 | 400 | 232 |
| # instances | 126,486 | 17,002 | 274 | 3,938 | 2,746 |
| # real API calls | 469,585 | 0 | 568 | 0 | 3,926 |
| Avg. reasoning traces | 4.0 | 1.0 | 2.1 | 1.0 | 5.9 |

Note the average episode length is only **4.0 API calls** — shorter than MarigoldBench's 8-25.

### §2.1 API collection (lines 269-288)
RapidAPI hierarchy: category (49 coarse) → collection (500+ fine, e.g. "Chinese APIs", "database APIs")
→ tool → API. Per API they crawl name, description, HTTP method, required params, optional params,
request body, executable code snippet, and one **example response**.

**Filtering is brutal and is the most quantitatively interesting number in the paper:** initial crawl
10,853 tools / **53,190 APIs**; after (1) basic functionality testing and (2) example-response evaluation
(discarding slow responders and low-quality responses such as HTML source or error messages), only
3,451 tools / **16,464 APIs** survive. That is a **69% API mortality rate** — i.e. two-thirds of a
real-world tool marketplace is non-functional enough to be unusable as a benchmark substrate.

### §2.2 Instruction generation (lines 289-380)
Inverted generation: sample API subsets first, then ask ChatGPT to invent instructions that use them
(rather than brainstorm tasks then find APIs). Prompt = task description + full docs of sampled APIs +
3 in-context seed examples drawn from a hand-written pool of **12 single-tool / 36 multi-tool seeds**.

Three instruction families:
- **I1** single-tool: 87,413 pairs
- **I2** intra-category multi-tool (2-5 tools from same category, ≤3 APIs each): 84,815 pairs
- **I3** intra-collection multi-tool: 25,251 pairs
Total ≈ 197,479 (instruction, relevant-API) pairs. Multi-tool combos are drawn within category/collection
because "the interconnections among different tools in RapidAPI are sparse" and random combination yields
tools that cannot be unified by a natural instruction.

Only filter applied: drop instructions whose "relevant APIs" are hallucinated (not in the sampled set
S_sub_N). Diversity verified by Atlas visualization + "rigorous human evaluation" (no numbers given).

### §2.3 Solution path annotation + DFSDT (lines 381-414, plus A.4 lines 790-811)
Action format: `Thought: ..., API Name: ..., Parameters: ...`, delivered through ChatGPT's function-call
field with each API as a function. Two synthetic terminal functions: **"Finish with Final Answer"** and
**"Finish by Giving Up"**. The give-up action is what makes DFSDT's backtracking expressible.

DFSDT motivation — two named failure modes of ReACT/CoT:
1. **Error propagation**: a mistaken action cascades, trapping the model in a faulty loop (repeatedly
   calling an API wrong, or hallucinating APIs).
2. **Limited exploration**: only one direction explored.

Implementation detail (A.4): classical DFS would need to score/sort child nodes, ~O(n log n) LLM calls.
They **skip the sort entirely** and use pre-order traversal, on the empirical finding that "the nodes
ranked highest are often the node generated at first". Consequences: if no retraction happens, DFSDT
degrades exactly to ReACT (same cost); the explored node set is "almost the same" as classical DFS.
Child-node diversity is enforced by a `diversity_user_prompt` that shows previous sibling attempts and
demands a different action.

Yield: 126,486 (instruction, solution path) pairs retained out of ~197k instructions — a **~64% annotation
pass yield**, and only passed paths are kept (so the SFT data is success-biased with no negative traces).

### §3.1 Preliminary experiments (lines 419-476)

**ToolEval design rationale (critical for us):** "Considering the API's temporal variability on RapidAPI
and the infinite potential solution paths for an instruction, it is infeasible to annotate a fixed
ground-truth solution path for each test instruction." So they follow AlpacaEval and use ChatGPT as judge.
Two metrics: **pass rate** (completed within budget; "basic requirement") and **win rate** (pairwise
preference vs a reference solution path). Judge is run ≥4 times with majority vote.

Human agreement: **87.1% on pass rate, 80.3% on win rate**, measured over 300 test instructions per method
across 4 methods (ChatGPT+ReACT, ChatGPT+DFSDT, ToolLLaMA+DFSDT, GPT4+DFSDT).

**API retriever** (Sentence-BERT over BERT-BASE, contrastive with sampled negatives), Table 2 NDCG:

| Method | I1@1 | I1@5 | I2@1 | I2@5 | I3@1 | I3@5 | Avg@1 | Avg@5 |
|---|---|---|---|---|---|---|---|---|
| BM25 | 18.4 | 19.7 | 12.0 | 11.0 | 25.2 | 20.4 | 18.5 | 17.0 |
| OpenAI Ada | 57.5 | 58.8 | 36.8 | 30.7 | 54.6 | 46.8 | 49.6 | 45.4 |
| Ours | 84.2 | 89.7 | 68.2 | 77.9 | 81.7 | 87.1 | 78.0 | 84.9 |

Multi-tool retrieval (I2) is markedly harder than single-tool (I1) for every method.

**DFSDT vs ReACT pass rate (ChatGPT backbone), Table 3:**

| Method | I1 | I2 | I3 | Avg |
|---|---|---|---|---|
| ReACT | 37.8 | 40.6 | 27.6 | 35.3 |
| ReACT@N (cost-matched repeats) | 49.4 | 49.4 | 34.6 | 44.5 |
| DFSDT | 58.0 | 70.6 | 62.8 | 63.8 |

DFSDT beats even the **cost-matched** ReACT@N by ~19 points average, and the gap widens on the harder
multi-tool splits (I3: 34.6 → 62.8). Search structure, not just extra sampling budget, is what pays.

### §3.2 Main experiments (lines 477-536)
ToolLLaMA = LLaMA-2 7B fine-tuned on the 126,486 pairs; context extended 4096 → 8192 via positional
interpolation (A.3: lr 5e-5, warmup ratio 4e-2, batch 64, max seq len 8192, PI ratio 2, 2 epochs,
best-dev-checkpoint selection).

Three generalization levels: **Inst.** (unseen instructions, seen tools), **Tool** (unseen tools, seen
category), **Cat.** (unseen tools, unseen category). Six evaluation splits: I1-Inst, I1-Tool, I1-Cat,
I2-Inst, I2-Cat, I3-Inst. All reported numbers are multiples of 0.5, implying **200 test instructions per
split (~1,200 total)**. Except for the retriever row, all methods are fed the **oracle (ground-truth) API
set**.

Table 4 averages (Pass / Win, win vs ChatGPT-ReACT reference):

| Model | ReACT Pass/Win | DFSDT Pass/Win |
|---|---|---|
| ChatGPT | 40.2 / — | 64.8 / 64.3 |
| Claude-2 | 6.8 / 34.4 | 22.6 / 43.5 |
| Text-Davinci-003 | 16.5 / 33.2 | 43.1 / 46.3 |
| GPT-4 | 57.2 / 64.4 | **71.1 / 70.4** |
| Vicuna | 0.0 / 0.0 | 0.0 / 0.0 |
| Alpaca | 0.0 / 0.0 | 0.0 / 0.0 |
| ToolLLaMA (7B) | 29.0 / 47.0 | 66.7 / 60.0 |
| ToolLLaMA + own retriever | — | 67.3 / 63.1 |

Findings: (1) Vicuna/Alpaca score exactly **zero** everywhere despite extensive prompt engineering —
general instruction tuning transfers nothing to tool use; (2) ChatGPT+DFSDT (64.8) **beats GPT-4+ReACT**
(57.2) on pass rate — scaffolding substitutes for a model generation; (3) ToolLLaMA-7B ≈ ChatGPT and is
second only to GPT-4+DFSDT.

**The retriever result that undermines the oracle:** feeding top-5 *retrieved* APIs instead of the
ground-truth set **improves** both pass and win rate (66.7 → 67.3 pass, 60.0 → 63.1 win). Their own
explanation: many ground-truth APIs "can be replaced by other similar APIs with better functionalities".
So the "ground truth" label is soft — a strong signal about label validity in agentic benchmarks.

Table 6 (A, lines 904-913) reports pre-tie-merge numbers, e.g. GPT-4+DFSDT 64.2 win / 12.4 tie;
ToolLLaMA+DFSDT 55.2 / 9.8; retriever variant 59.2 / 7.8. Ties are 5-15% of comparisons and are split
50/50 into win/lose in the headline table — a presentation choice that inflates apparent separation.

### §3.3 OOD generalization to APIBench (lines 537-565, A.6 lines 895-901)
No further training; APIs presented as a single "select an API" function. Table 5:

| Method | HF Hallu↓ / AST↑ | TorchHub Hallu↓ / AST↑ | TensorHub Hallu↓ / AST↑ |
|---|---|---|---|
| ToolLLaMA + our retriever | 10.60 / 16.77 | 15.70 / 51.16 | 6.48 / 40.59 |
| Gorilla-ZS + BM25 | 46.90 / 10.51 | 17.20 / 44.62 | 20.58 / 34.31 |
| Gorilla-RS + BM25 | 6.42 / 15.71 | 5.91 / 50.00 | 2.77 / 41.90 |
| ToolLLaMA + oracle | 8.66 / **88.80** | 14.12 / 85.88 | 7.44 / 88.62 |
| Gorilla-ZS + oracle | 52.88 / 44.36 | 39.25 / 59.14 | 12.99 / 83.21 |
| Gorilla-RS + oracle | 6.97 / 89.27 | 6.99 / 93.01 | 2.04 / 94.16 |

Note the enormous **oracle-vs-retrieved gap** (16.77 → 88.80 AST on HuggingFace): with imperfect retrieval
the task is ~5x harder. Retrieval quality, not reasoning, dominates measured performance here. They also
note Gorilla cannot run on ToolBench at all ("due to our more complex settings, such as the multi-tool use
and multi-step reasoning").

### §4 Related work / §5 Conclusion (lines 566-614)
DFSDT positioned as generalizing Reflexion and as distinct from Tree-of-Thought: "our DFSDT targets
general decision-making problems where the decision space is infinite, compared to ToT's relatively simple
tasks that can be addressed by brute-force search, such as Game of 24 and Crosswords."

### Appendix A.1-A.2 (lines 758-781)
Filtering = (1) initial functionality test, (2) example-response evaluation on latency and quality.
**Response compression**: ChatGPT is used offline per-API to learn which response keys are droppable
(prompted with tool docs + 3 expert-written compression schemas). At inference, responses >1024 tokens
are compressed; if still >1024, **hard-truncated to the first 1024 tokens**. Validated only by
unquantified "human evaluation".

### Appendix A.5 — ToolEval rules (lines 812-894) — the most important appendix for us
Pass rate is *conditioned on a solvability judgment*. An instruction is **solvable** (some provided tool
is potentially helpful) or **unsolvable** (all APIs irrelevant, or the instruction contains invalid
information such as an invalid email address). Labels are Pass / Fail / **Unsure**.

If **solvable**:
- Give Up after extensively trying all APIs with no helpful info → **Pass**
- Give Up after only a few calls, or after receiving valid info → **Fail**
- Final Answer that fully resolves the instruction → **Pass**
- Final Answer that is a refusal *when tools did provide valid info* → **Fail**
- Final Answer that is a refusal *after all APIs genuinely provided nothing* → **Pass**
- Cannot tell from the answer → **Unsure**

If **unsolvable**:
- Final Answer that is a refusal → **Pass**
- Final Answer that is **hallucinated / false-positive** ("I've completed the task, the final answer is *")
  → **Fail**
- Give Up → **Pass**

This is a direct precedent for MarigoldBench's three-condition design: it already encodes *refusal is
correct on flawed premises* and *false-positive completion claims are failures*. What it lacks is any
independent recomputation — the judgment is made by reading the model's own narrative.

Win rate criteria (6 rules): **information richness**, **factuality** ("whether it accurately describes
what has been done, and what failed"), **reasoning** (quality of failure explanation), **milestone**
(count of milestones reached), **exploration** ("The use of a greater number of APIs is better"), **cost**
(fewer redundant calls better, as a tie-break only).

Admitted evaluation fragility: "even human experts often disagree with each other in deciding which
solution path is better, leading to a relatively low agreement" — one expert prefers few-API speed,
another prefers extensive cross-validation.

### Appendix A.7-A.8 — prompts (lines 914-1362)
Instruction-generation prompt demands 10 queries per call, ≥30 words each, 2-5 APIs per query, varied
sentence mood/tone/subject, invented concrete parameters ("don't merely say 'an address', provide the
exact road and district names"), first 7 specific and last 3 "complex and lengthy". The full JSON of a
sampled tool (EntreAPI Faker) is dumped as an example. The solution-path system prompt tells the model
"The state changes are irreversible, and you cannot return to a previous state", caps thoughts at five
sentences, and defines the `Finish` function with enum `["give_answer","give_up_and_restart"]`.

## 4. Benchmark card (ToolBench / ToolEval)

- **Task count:** 126,486 training instances; test = 6 splits × 200 instructions ≈ **1,200 evaluated tasks**.
  Task *families* are effectively the 3 instruction types × 3 generalization levels = 6 cells, not 100+
  independent families. Instruction provenance is a single ChatGPT prompt template with 48 human seeds —
  so template clustering is severe and unmeasured.
- **Construction:** fully automatic via ChatGPT (gpt-3.5-turbo-16k) with function calling; human input =
  48 seed examples + compression schemas + prompt engineering. "requires minimal human supervision".
- **Verification method:** **no recomputation.** A ChatGPT judge reads the trajectory + final answer and
  applies the A.5 rule list; ≥4 samples, majority vote. Ground-truth solution paths are explicitly declared
  infeasible to annotate.
- **Scoring:** pass rate (binary, solvability-conditioned, Unsure allowed) and pairwise win rate against
  ChatGPT-ReACT, with ties split evenly into win/lose in the headline table. Compensatory, not
  non-compensatory: rich, well-narrated answers score well on 5 of 6 win-rate criteria.
- **Agent scaffolding:** ReACT vs DFSDT (pre-order-traversal decision tree with explicit give-up/backtrack
  and a sibling-diversity prompt), optionally plus a Sentence-BERT top-5 API retriever. Scaffolding choice
  moves pass rate more than model choice does (ChatGPT+DFSDT 64.8 > GPT-4+ReACT 57.2).
- **Reported scores with uncertainty:** **no confidence intervals, no error bars, no seed variance, no
  significance tests anywhere in the paper.** The only uncertainty-adjacent numbers are the judge-vs-human
  agreement rates (87.1% / 80.3%) and the tie fractions in Table 6.
- **Contamination handling:** only via the Inst/Tool/Cat generalization split (unseen tools, unseen
  category). Nothing about pretraining contamination of the closed baselines, and RapidAPI docs are public
  web content. The test instructions came from the same generator as the training instructions.
- **Cost per run:** never reported in dollars or tokens. Only a qualitative argument (A.4) that skipping
  child-node sorting avoids O(n log n) OpenAI calls, and that ReACT@N was constructed to be cost-matched.
  469,585 real API calls total for dataset construction.

## 5. Method card (DFSDT + neural API retriever)

- **DFSDT does:** turns a linear ReACT rollout into a pre-order DFS over an action tree; at any node the
  model may call "Finish by Giving Up" to backtrack and expand a sibling, with a diversity prompt listing
  prior siblings. Any single passing leaf ends the search.
- **Measured effect:** ChatGPT pass rate 35.3 → 63.8 average (vs 44.5 for cost-matched ReACT@N); largest
  gains on hardest split (I3: 27.6 → 62.8). Applies to every backbone tested (Claude-2 6.8 → 22.6;
  Davinci-003 16.5 → 43.1; GPT-4 57.2 → 71.1; ToolLLaMA 29.0 → 66.7).
- **Known failure modes it targets:** error propagation into faulty loops (repeated bad calls, hallucinated
  API names) and single-path exploration.
- **What a naive user gets wrong:** (a) assuming ReACT + more samples is equivalent — it is not, 44.5 vs
  63.8; (b) assuming the oracle API list is optimal — retrieval beat it; (c) assuming DFSDT costs much more
  — it degrades to ReACT when no retraction occurs; (d) forgetting response truncation at 1024 tokens
  silently deletes evidence the model then reasons over.
- **Inputs / outputs:** inputs are API documentation in the function-call field plus the instruction;
  outputs are a trajectory of (thought, API name, parameters) plus a terminal `Finish` with either
  `give_answer` + final_answer string or `give_up_and_restart`.
- **Retriever:** Sentence-BERT/BERT-BASE bi-encoder, contrastive with sampled negatives; NDCG@5 84.9 avg vs
  Ada 45.4 and BM25 17.0. But on OOD APIBench, swapping oracle → retrieved drops AST from 88.80 to 16.77
  (HuggingFace), so retrieval is the dominant failure surface out of domain.

## 6. Limitations

**Admitted:**
- No fixed ground-truth solution path is annotatable (API temporal variability + infinite valid paths).
- Human experts disagree on which path is better; agreement is "relatively low"; "there is still a long way
  to go for a fair evaluation of the tool-use domain".
- Judge agreement is imperfect: 87.1% pass, 80.3% win.
- Even GPT-4 often fails to find valid paths, which is why annotation needed DFSDT.
- API responses are lossy-compressed and truncated at 1024 tokens.
- Gorilla cannot be evaluated on ToolBench (asymmetric comparison).

**Unadmitted / structural:**
1. **Circularity.** ChatGPT generates the instructions, ChatGPT annotates the solution paths, ChatGPT is
   the judge, and ChatGPT is a scored baseline. Its 64.8 pass rate is measured by its own distribution.
2. **Self-report is the evidence.** Pass/fail is decided by reading the final answer text; nothing
   re-executes the APIs or checks the returned values against reality. A model that narrates a plausible
   completion with fabricated numbers is only caught if the judge happens to notice.
3. **Gameable win-rate criteria.** "Information richness" rewards verbosity and "Exploration: the use of a
   greater number of APIs is better" rewards padding the trajectory; cost is only a tie-break.
4. **No uncertainty quantification at all.** 200 instructions per split gives roughly ±3.5 pts standard
   error at p≈0.5, so several highlighted differences (e.g. 66.7 vs 64.8) are within noise.
5. **Soft labels.** The oracle API set is beaten by retrieval, i.e. the ground-truth annotation is not
   optimal, yet it is the input for every baseline.
6. **Non-reproducible substrate.** Live RapidAPI endpoints change and die (69% were already dead/degraded
   at crawl time); scores are not comparable across time and cannot be re-run identically.
7. **Success-only training data.** Only passed DFSDT paths are retained, so ToolLLaMA never sees a labeled
   failure or a correct abstention trace, yet abstention is graded at test time.
8. **Solvability is itself LLM-judged**, so the unsolvable-instruction rules rest on an unvalidated label.
9. **Ceiling.** Best system is at 71.1 pass rate — a saturated regime, far from a discriminative band.

## 7. Implications for MarigoldBench

1. **Do not let a judge read the narrative — recompute the artifact.** ToolLLM's entire scoring apparatus
   (A.5) is a rule list applied by ChatGPT to the model's own final answer, and the single clearest failure
   they had to write a rule for is the hallucinated false-positive completion. Their own construction shows
   why: they could not annotate ground truth. MarigoldBench's premise (recompute the physical/statistical
   check on the submitted artifact) is exactly the missing piece — and it is *only* available to us because
   our tools return checkable objects (PDBs, SMILES, arrays, models) rather than opaque JSON. Design every
   task so the deliverable is an artifact with a deterministic recheck (e.g. re-run ESMFold pLDDT on the
   submitted sequence, recompute the ROC-AUC from the submitted split indices, re-dock the submitted pose),
   and never accept a number that appears only in prose.
2. **Steal and harden their unsolvable-instruction rule table as the flawed-premise rubric.** Their
   unsolvable branch already says refusal = Pass, give-up = Pass, confident false completion = Fail. Port
   that structure but make each branch machine-checkable: the flawed-premise condition should require the
   model to *name the specific defect* (e.g. "the provided 'binding pocket' residues are not solvent-
   accessible", "the training and test sets share compound scaffolds"), and the harness should string/ID-
   match that named defect against the planted one. Bare refusal without diagnosis should score below
   diagnosed refusal, or models will learn to refuse everything and farm the flawed-premise condition.
3. **Scaffolding is a bigger lever than model identity — so fix it and report it.** ChatGPT+DFSDT (64.8)
   beat GPT-4+ReACT (57.2), and cost-matched resampling recovered only half the DFSDT gain (44.5 vs 63.8).
   If MarigoldBench wants Gemini 3.1 Pro / GPT-5.6 Sol / Claude Opus 5 in a 5-40% band, the harness must
   pin the scaffold (retry policy, backtracking allowance, max calls, whether failed calls are visible)
   and publish it, because a permissive scaffold can move a model 25+ points. Consider reporting each
   model under both a plain-ReACT and a search-enabled scaffold to show the elasticity.
4. **Plant failures in the tool *responses*, not just the task statement.** 69% of real RapidAPI endpoints
   were dead or degraded, and DFSDT exists specifically because a bad call cascades into a faulty loop.
   Realistic planted defects for our lab: a NIM endpoint that returns a 200 with a silently truncated
   structure; MolMIM returning valid-looking but chemically invalid SMILES; ProteinMPNN returning
   sequences for the wrong chain; a Boltz-2 confidence field that is present but always 0.5; an ESMFold
   call that succeeds on a sequence containing an 'X' the model injected. Each of these is invisible in
   self-report and only caught by recomputation, which is precisely the discriminative regime we want.
5. **Truncation of tool output is a first-class, testable hazard.** ToolLLM silently compresses and then
   hard-truncates responses at 1024 tokens, and validates this with unquantified "human evaluation". Our
   lab tools emit large artifacts (multi-model PDBs, affinity tables, embedding matrices). Make at least
   one task family turn on evidence that lies beyond a truncation boundary — the sound-control version
   requires the model to page/subset/aggregate the full output (e.g. read all 5 Boltz-2 models, not the
   first), while a model that reasons off the truncated head reaches a confidently wrong conclusion. Log
   whether the model ever requested the tail.
6. **Beware compensatory scoring; their win rate literally rewards calling more tools.** "Exploration: the
   use of a greater number of APIs is better" and "information richness" mean a verbose, wandering
   trajectory can outscore a correct terse one. Non-compensatory Verified Episode Completion avoids this
   by construction, but keep the discipline everywhere: no partial credit for a rich write-up, and treat
   tool-call count as a *cost* covariate reported alongside the binary outcome, never as a quality signal.
7. **A "ground truth" tool set is not ground truth — measure that.** Their retriever beat the oracle API
   list (67.3 vs 66.7 pass), because human/LLM-designated relevant tools were replaceable by better ones.
   For MarigoldBench, do not score on "did the model use the intended tool"; score only on the verified
   result. Where a task family has a canonical route (RFdiffusion → ProteinMPNN → ESMFold), still accept
   any route whose artifact passes the recheck, and separately log route divergence as a descriptive
   statistic, not a penalty.
8. **Their false-alarm analogue is the solvable-refusal rule — mirror it exactly.** On solvable
   instructions, refusal *when tools returned valid information* is a Fail, but refusal *after all tools
   genuinely returned nothing* is a Pass. That is the sound-control condition with false-alarm penalty.
   Implement it as a state check, not a text check: the harness knows whether the tool responses contained
   the needed signal, so a model that abstains on a sound task while the logs show it had sufficient data
   is unambiguously penalized, and a model that abstains after genuine infrastructure failure is not.
   This also protects us from grading infra flakiness as model failure — record tool-level HTTP/exit status
   and exclude or re-run episodes with genuine service outages.
9. **Report uncertainty they never did, and cluster by template.** ToolLLM gives 200 items per cell and
   zero CIs; at that n, ±3.5 pts of standard error swallows most of their claimed gaps, and every item in
   a cell came from one prompt template with 48 seeds, so the effective n is far smaller than 200.
   MarigoldBench's plan for ≥100 independent task families with template-clustered CIs is the right
   correction — enforce it by requiring each family to have a distinct verification function, not just a
   distinct wording, and by bootstrapping over families rather than episodes.
10. **Episode length and difficulty: 4.0 average calls is not enough, and neither is one attempt.** Their
    average trajectory is 4 calls; hard splits (I3) were where search mattered most. Our 8-25 call target
    is the right zone, but the difficulty must come from *dependency depth* (each step's output constrains
    the next, so an early error is unrecoverable) rather than from step count. Deliberately include tasks
    where the correct move is to backtrack — e.g. the first designed binder fails an ESMFold/Boltz-2 check
    and the model must redesign rather than submit — and score whether it detected its own failure before
    submitting.
11. **Report cost per episode; nobody else does.** ToolLLM reports 469,585 API calls but never a dollar or
    token figure, which makes its cost-matched ReACT@N baseline unauditable. Since NVIDIA NIM calls and GPU
    time are metered, publish median tokens, median wall-clock, and median GPU-seconds per episode per
    model. This is also the only honest way to compare a model that thinks a lot against one that calls a
    lot.
12. **Guard against the circularity that quietly weakens their result.** ChatGPT wrote the tasks, solved
    them, and graded them. For MarigoldBench, tasks and verification functions must be authored
    independently of any candidate model's outputs, verification must be code (not a model), and if an LLM
    is used to draft task prose, the check must still be hand-written and unit-tested against known-good
    and known-bad artifacts.

## 8. Verbatim quotes

1. §A.5, *Details for Pass Rate*, unsolvable-instruction rules (line 845-847):
   > "If the final answer is hallucinated by the model itself and provides a false positive response (such
   > as "I've completed the task, the final answer is *"), the solution path is deemed a Fail."

2. §3.1, *ToolEval* (lines 420-423):
   > "Considering the API's temporal variability on RapidAPI and the infinite potential solution paths for
   > an instruction, it is infeasible to annotate a fixed ground-truth solution path for each test
   > instruction."

3. §A.5, *Comparing Human Evaluation and ToolEval* (lines 887-892):
   > "In our initial investigations, we surprisingly found that even human experts often disagree with each
   > other in deciding which solution path is better, leading to a relatively low agreement. For instance,
   > one may prefer a solution path that uses only a few APIs to derive the final answer quickly; while
   > another may prefer a solution path that extensively tries all the APIs to cross-validate specific
   > information."

4. §3.2, *Integrating API Retriever with ToolLLaMA* (lines 529-534):
   > "using retrieved APIs even improves the performance (both pass rate and win rate) compared to the
   > ground truth API set. This is because many APIs in the ground truth API set can be replaced by other
   > similar APIs with better functionalities, which our API retriever can successfully identify."

5. §2.3, *Depth First Search-based Decision Tree* (lines 398-403):
   > "(1) error propagation: a mistaken action may propagate the errors further and cause the model to be
   > trapped in a faulty loop, such as continually calling an API in a wrong way or hallucinating APIs;
   > (2) limited exploration: CoT or ReACT only explores one possible direction, leading to limited
   > exploration of the whole action space."

6. §A.5, *Details for Win Rate*, criterion 5 (lines 869-870):
   > "Exploration: whether more potentially useful APIs were attempted during the execution process. The
   > use of a greater number of APIs is better."

7. §2.1, *API Filtering* (lines 284-288):
   > "Initially, we gathered 10, 853 tools (53, 190 APIs) from RapidAPI. However, the quality and
   > reliability of these APIs can vary significantly. In particular, some APIs may not be well-maintained,
   > such as returning 404 errors or other internal errors. ... Finally, we only retain 3, 451 high-quality
   > tools (16, 464 APIs)."
