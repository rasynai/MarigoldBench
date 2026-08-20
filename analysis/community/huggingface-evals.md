# Community discourse: HuggingFace evals ecosystem (Open LLM Leaderboard, dataset cards, lm-eval-harness)

Lens: HuggingFace community — Open LLM Leaderboard retirement and its stated reasons, dataset card
discussions, lm-evaluation-harness issue threads, reproducibility complaints, prompt-format sensitivity.
Researched 2026-08-16. ~20 primary sources opened (leaderboard discussions, HF blogs/docs, GitHub issue
threads with comments, dataset card discussions, HN threads via Algolia API). Reddit was not fetchable
from this environment; HN and on-platform HF discussions carry the community voice here.

---

## 1. Distinct complaint patterns

### 1.1 Scores are implementation-defined: prompt format, tokenization, and whitespace change the answer

The founding scandal of this whole discourse: after Falcon's release, the community noticed LLaMA's MMLU
score on the leaderboard was far below the LLaMA paper. HF's investigation ("What's going on with the
Open LLM Leaderboard?") found **three respected implementations of the "same" MMLU benchmark — original
Berkeley, HELM, and EleutherAI harness — give wildly different numbers**: LLaMA-65B scored 0.637 (HELM),
0.488 (harness), 0.636 (original). The differences come from exactly the things a casual reader assumes
don't matter: whether you compare loglikelihoods of "A" vs the full answer text, whether you generate a
token, prompt details, tokenization. The blog's own conclusion: *"Evaluations are strongly tied to their
implementations — down to minute details such as prompts and tokenization"* and *"The mere indication of
'MMLU results' gives you little to no information"* about comparability.
(Source: HF blog `evaluating-mmlu-leaderboard` / `open-llm-leaderboard-mmlu`; HN 36449424.)

Concrete micro-examples of the same pattern in lm-eval-harness threads:

- Issue #2211: harness maintainer Hailey Schoelkopf explains that a fix changed MMLU's task-description
  whitespace from **one newline to two** — enough to change scores and force a task-version bump: *"I
  highly recommend reporting or keeping track of the task versions when you report results!"*
- Issue #1292 (TriviaQA "low results"): adding the literal string `description: "Answer these
  questions:\n\n"` to the prompt moved Llama-2-7B from 0.525 to 0.584 exact match — ~6 points from one
  boilerplate sentence, and still below Meta's reported 65.8.
- Issue #2583: a user gets **39.04 vs the leaderboard's 56.53 on BBH** for Qwen-2.5-32B-Instruct, with
  the delta traced to chat-template / `fewshot_as_multiturn` handling.
- Issue #1098 (the chat-template design thread, 27 comments): the harness was designed for base models;
  bolting on chat templates raised unresolved questions (where do few-shot examples go? system prompt?
  tokenize segments separately?) — with the maintainers explicitly worried about adding it "in a way that
  doesn't hurt reproducibility."
- Clémentine Fourrier (leaderboard lead), in her evaluation essay: LLM *"scores on automated benchmarks
  are extremely susceptible to minute changes in prompting."*

### 1.2 Reproducibility failures — including non-determinism nobody can explain

The single most common complaint category in the harness issue tracker is "I cannot reproduce X" —
against papers, against the leaderboard, or against the same machine yesterday:

- **Batch size changes scores.** The leaderboard docs themselves admit *"You can expect results to vary
  slightly for different batch sizes because of padding."* Users found it is not slight: issue #2583:
  *"our personal experience shows that evaluation scores with batch_size=1 and batch_size=8 could
  sometimes differ by as much as 10%, suggesting the issue could be more significant than described."*
  Also issues #1625, #704 ("loglikelihood changes with the batch size"), #873 (stopping criteria depend
  on batch size), #1293 (different score under `accelerate`).
- **Fixed seed + greedy decoding still isn't deterministic.** Issue #3357: "Lack of reproducability
  despite set batch size, seed, greedy sampling" — maintainer response speculates GPU op differences
  between cards; suggests `VLLM_BATCH_INVARIANT=1`.
- **The leaderboard's own published numbers don't reconcile.** Issue #2583: a user shows HF's own raw
  results JSON for Llama-3.1-70B-Instruct (0.6915) doesn't match the webpage's displayed 55.93% (the
  normalization is opaque to users); another user gets three different MMLU-Pro numbers: leaderboard page
  0.3068, HF's raw details file 0.3746, own run 0.1629.
- **The official reproduction path was broken.** Issue #2338 ("Locally reproducible HF-Leaderboard
  evals"): the leaderboard pointed at a special HF fork/branch of the harness; contributors report it
  *"crashes with `--apply_chat_template` + vllm"* and *"I also failed to use their repo/branch via vllm.
  The results are very off!"* (maziyarpanahi).
- **Vendor-reported numbers are irreproducible by construction.** EleutherAI's Stella Biderman, issue
  #982: *"LLaMA and LLaMA 2 results are, in general, irreproducible. Both papers use custom prompts and
  other formatting changes that they do not disclose. We have tried to work with Meta to replicate their
  work using their custom prompts, but they don't want to disclose them... LLaMA results are not even
  reproducible within Meta"* (LLaMA-1 numbers differ between the LLaMA-1 and LLaMA-2 papers).
- A steady stream of "far off" reports for individual tasks: LongBench (#2932), Gemma3 GSM8K 22.2% vs
  reported 62.8% (#3258), Deepseek-math (#2555), Qwen3-32B GSM8K (#3129), "reproduce llama 3 evals"
  (#2557), GPQA near-random (#2513).

### 1.3 Harness/scoring bugs that silently corrupt scores

Not sensitivity — outright bugs, discovered only because someone read the transcripts:

- **DROP had to be removed from the leaderboard.** HF's post-mortem: the normalization tripped on any
  whitespace other than a plain space, and the `.` end-of-generation token truncated every
  floating-point answer — *"not a single model got a correct result on floating point answers"* — and
  punished verbose good models. Fixing it would have required re-running "more than 50% of the examples."
  (HF blog `open-llm-leaderboard-drop`.)
- **GSM8K on v1 used `:` as a stop token,** which "unfairly pushed down the performance of many verbose
  models" (v2 blog).
- **Unparseable ≠ wrong, but the harness scores them identically.** Issue #4007 (2026): a census found
  2,936 of 4,524 generative tasks (64.9%) score an unparseable response exactly like a wrong answer, with
  no `unparsed_rate` signal surfaced — so a formatting quirk is indistinguishable from incapability.
- Long tail of similar: stderr published as exactly 0.0 for non-degenerate scores (#3966), request cache
  ignoring `generation_kwargs` and silently reusing stale generations (#3881), metric-name mismatches that
  leave aggregates empty (#3986).

### 1.4 The benchmark data itself is wrong (dataset-card discussions)

- **MMLU**, cais/mmlu discussion #29 "Not all samples are correct": users post specific questions where
  the labeled gold answer is wrong (a European-history question keyed to "Nineteenth-century Prussia"
  that AP resources say is "Eighteenth-century France"; an abstract-algebra ring-homomorphism question
  keyed D that should be C). The leaderboard v2 blog concedes MMLU was "recently investigated in depth by
  several groups... which surfaced mistakes in its responses" (MMLU-Redux/MMLU-Pro), and the docs describe
  original MMLU as having "noisy data (some unanswerable questions)."
- **GSM8K**, openai/gsm8k discussions #5 and #20 ("Some bad data with wrong answers in this dataset",
  "Wrong answer in test set"): e.g. the "three times more points than Sara" item, where the gold answer
  hinges on reading "3 times more" as "(3+1) times as many" — Jonas Mueller (Cleanlab): *"in everyday
  language: '3 times more' usually means '3 times as many'."* Ground truth by idiom dispute.
- **TruthfulQA**, truthful_qa discussion #8: a user verified that in `mc1_targets` the correct choice is
  the **first option in 100% of 817 questions** — a positional artifact any contaminated or
  pattern-exploiting pipeline can ride.

### 1.5 Contamination: training on the test set, accidental and otherwise

- The v2 blog is explicit that v1 died partly from contamination: some benchmarks (GSM8K, TruthfulQA)
  ended up inside popular instruction-tuning datasets, so *"scores stopped reflecting the general
  performance of the model and started to overfit on some evaluation datasets."*
- The leaderboard ran a community **flagging** system: "Flagging helps report models that have unfair
  performance on the leaderboard. For example, models that were trained on the evaluation data" (FAQ);
  "If a model's name contains 'Flagged'... it should probably be ignored!" (About page).
- v2 chose GPQA specifically because it is **gated**: "we do not provide plain text examples from this
  dataset" to "minimize the risk of data contamination" (About page).
- Clémentine Fourrier's essay: once benchmarks "are published publicly in plain text, they are very
  likely to end up (often accidentally) in the training datasets of models."
- The community's canonical in-joke is the satirical paper **"Pretraining on the Test Set Is All You
  Need"** (Schaeffer, arXiv 2309.08632): a 1M-parameter model trained on <100k tokens of benchmark data
  "achieves perfect results across diverse academic benchmarks, strictly outperforming all known
  foundation models."

### 1.6 Saturation: benchmarks stopped discriminating

- v2 blog: benchmarks "became too easy for models. For instance, models are now reaching baseline human
  performance on HellaSwag, MMLU, and ARC, a phenomenon called saturation" (human baselines: HellaSwag
  95.0, MMLU 89.8, Winogrande 94.0).
- HN thread on the v2 post (40832330), pclmulqdq: the benchmarks got too easy — "many LLMs reach ~90%,
  with ~95% appearing to be a ceiling due to inherent randomness, making the HuggingFace leaderboard less
  meaningful."

### 1.7 Leaderboard gaming: merges, layer surgery, and hill-climbing

- v1 was overrun by "experimental, fascinating and impressive concatenations of more than 20 successive
  model creation steps via fine-tuning or merging" that scored high "selectively without real-world
  utility" (v2 blog). The FAQ carries a standing disclaimer: merge models "can show superior test results
  but do not always apply for real-world situations."
- The pattern outlived the leaderboard: HN 47322887 ("How I topped the HuggingFace open LLM leaderboard
  on two gaming GPUs", 495 points, 2026) — the author took #1 by **duplicating ~7 middle layers of
  Qwen2-72B, changing zero weights**; commenters noted such leaderboard-topping tricks live on "Reddit,
  4chan, and Discord" while "papers aren't being written."
- The retirement announcement itself frames continued operation as harmful: keeping the board up "could
  encourage people to hill climb irrelevant directions in the field."

### 1.8 Vendor self-reporting is not trusted; losing the independent referee hurt

The most striking thing in the retirement thread (#1135) is that the community's grief was about
**independence**, not the benchmarks:

- Enigrand: *"Nowadays any LLM claiming to be the SOTA will present results with moderate to insane
  benchmark / sampling method / result cherrypicking. I've been using this leaderboard for about a year
  now as a non-manipulable independent third party evaluation / cross-validation / sanity check tool."*
- MarxistLeninist: *"Wow, this is a dark day for open source. Benchmarking is essential, and you have the
  most resources to do it... you'll gut the open-source community, which has no way to test
  70-billion-parameter models on budgets far smaller than corporations like yours."*
- The counterpoint accepting retirement, HDiffusion: *"These metrics have definitely lost their purpose
  in the face of new modalities and long cot models."*

### 1.9 Benchmarks lag capabilities; static suites go obsolete

The official retirement reason (clefourrier, 2025-03-13, discussion #1135): after ~13K models evaluated
over two years, *"As model capabilities change (hello reasoning and LM assistants), benchmarks need to
follow! The leaderboard is slowly becoming obsolete."* The team pointed users at 200+ community
leaderboards instead. Note the arc: v1 (2023) → rebuilt as v2 (June 2024) explicitly to outrun
saturation/contamination → retired anyway nine months later. The community reads this as: **static
benchmark suites have a shelf life measured in months.**

### 1.10 Aggregation and score presentation confuse users

v2 normalized scores to a random-baseline lower bound "to provide a fair comparison" (FAQ), but that
broke users' mental model — multiple issue threads (#2583) are people failing to reconcile raw
`results_*.json` accuracy with the displayed normalized percentage, and a contributor requesting the
leaderboard just publish the averaged number it displays. When the displayed number can't be recomputed
by readers, they file it under "irreproducible."

---

## 2. What this community says would make a benchmark trustworthy / flagship-grade

Distilled from what they praise, demand, and build in response to the above:

1. **Pin and publish the exact evaluation implementation** — harness commit, task YAML versions, prompt
   strings, chat-template flags, stop tokens, shots. "MMLU results" alone "gives you little to no
   information"; task versions must ride along with every reported score (Schoelkopf, #2211).
2. **One runnable reproduction command that actually works locally**, on hardware mortals own — the
   leaderboard published its command and fork, and the community immediately stress-tested it and filed
   issues when it crashed or diverged (#2338). Trust is earned by people re-running you.
3. **Publish full per-sample details, not just aggregates.** The leaderboard's `details` datasets (every
   input/output for every model) are what let users catch the DROP bug, the normalization confusion, and
   template mismatches. Raw and normalized scores both visible; the mapping recomputable.
4. **Characterize and disclose non-determinism** — batch-size/padding effects, GPU-op variance, backend
   (HF vs vllm) deltas — with stderr reported and honest error bars; treat third-decimal differences as
   noise, not ranking signal (#2211).
5. **Contamination defense as a design feature, not an afterthought**: gated/held-out test sets (GPQA
   model), canary strings, no plain-text test data in the repo, plus active policing (flagging policy,
   community accountability for submissions).
6. **Headroom and refresh**: pick benchmarks where models don't touch the human baseline, and plan for
   replacement when they saturate (v1→v2), or retire rather than let people "hill climb irrelevant
   directions."
7. **Separate parse failures from wrong answers** — report an `unparsed_rate` alongside accuracy so
   formatting brittleness can't masquerade as incapability (#4007).
8. **Vetted ground truth**: expert-reviewed items (MMLU-Pro's pitch), a public channel for wrong-answer
   reports on the dataset card, and no positional artifacts (TruthfulQA mc1's 100%-first-position gold).
9. **Independence from model vendors** — run by a third party on its own cluster, same environment for
   every model, undisclosed-prompt vendor numbers treated as unverifiable marketing (Stella Biderman's
   Meta experience; Enigrand's "non-manipulable... sanity check tool").
10. **Anti-gaming design**: normalize to random baseline, category-separate merges from trained models,
    flag "selective" high-scorers, and assume adversarial submitters — because the community will
    literally duplicate layers to top your chart.
11. **Track the capability frontier**: a flagship benchmark for 2025+ models must handle reasoning/long
    CoT and new modalities, or the community itself will declare its metrics to have "lost their purpose."

---

## 3. Representative quotes (verbatim or tight paraphrase)

1. *"Evaluations are strongly tied to their implementations — down to minute details such as prompts and
   tokenization... The mere indication of 'MMLU results' gives you little to no information."* — HF Open
   LLM Leaderboard team, "What's going on with the Open LLM Leaderboard?" (blog, June 2023), after
   showing LLaMA-65B MMLU = 0.637 (HELM) vs 0.488 (harness) vs 0.636 (original).
2. *"LLaMA and LLaMA 2 results are, in general, irreproducible. Both papers use custom prompts and other
   formatting changes that they do not disclose... LLaMA results are not even reproducible within Meta."*
   — Stella Biderman (EleutherAI), lm-evaluation-harness issue #982.
3. *"Not a single model got a correct result on floating point answers"* and fixing it would mean
   re-running *"more than 50% of the examples"* — HF blog on removing DROP from the leaderboard.
4. *"Evaluation scores with batch_size=1 and batch_size=8 could sometimes differ by as much as 10%,
   suggesting the issue could be more significant than described."* — user Ryuuranwlb,
   lm-evaluation-harness issue #2583 (the docs said scores "vary slightly" with batch size).
5. *"Scores stopped reflecting the general performance of the model and started to overfit on some
   evaluation datasets"* (GSM8K and TruthfulQA leaked into instruction-tuning sets); benchmarks "became
   too easy... a phenomenon called saturation." — Open LLM Leaderboard v2 announcement (June 2024).
6. *"The leaderboard is slowly becoming obsolete; we feel it could encourage people to hill climb
   irrelevant directions in the field."* — Clémentine Fourrier, retirement announcement, discussion
   #1135, 2025-03-13.
7. *"Nowadays any LLM claiming to be the SOTA will present results with moderate to insane benchmark /
   sampling method / result cherrypicking. I've been using this leaderboard... as a non-manipulable
   independent third party evaluation / cross-validation / sanity check tool."* — user Enigrand, reply
   in retirement thread #1135.
8. *"Wow, this is a dark day for open source... you'll gut the open-source community, which has no way
   to test 70-billion-parameter models on budgets far smaller than corporations like yours."* — user
   MarxistLeninist, reply in retirement thread #1135.
9. *"The number reported in the leaderboard is 56.53 [BBH, Qwen-2.5-32B-Instruct]. I got 39.04... It is
   a huge difference."* — user TingchenFu, issue #2583; and from #2338: *"I also failed to use their
   repo/branch via vllm. The results are very off!"* (maziyarpanahi).
10. *"Some of the examples in this dataset have the wrong answer... in everyday language: '3 times more'
    usually means '3 times as many'."* — Jonas Mueller, GSM8K dataset card discussion #5; cf. MMLU card
    #29 "Not all samples are correct" and TruthfulQA card #8 (gold answer is option 1 in 817/817 items).
11. *"[phi-CTNL] achieves perfect results across diverse academic benchmarks, strictly outperforming all
    known foundation models"* — by pretraining on the benchmarks. — Rylan Schaeffer, "Pretraining on the
    Test Set Is All You Need" (satire, arXiv 2309.08632), the community's shorthand for the whole
    contamination era.
12. *"These metrics have definitely lost their purpose in the face of new modalities and long cot
    models."* — user HDiffusion, retirement thread #1135.

---

## 4. Sources (opened and read)

**Open LLM Leaderboard (HF spaces/blogs/docs)**
- Retirement thread: "It's been a wild ride, folks :) (end of the Open LLM Leaderboard)" —
  https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard/discussions/1135
- Leaderboard discussions index — https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard/discussions
- "What's going on with the Open LLM Leaderboard?" (MMLU implementations) —
  https://huggingface.co/blog/open-llm-leaderboard-mmlu (also at /blog/evaluating-mmlu-leaderboard)
- "Open LLM Leaderboard: DROP deep dive" — https://huggingface.co/blog/open-llm-leaderboard-drop
- v2 announcement "Performances are plateauing, let's make the leaderboard steep again" —
  https://huggingface.co/spaces/open-llm-leaderboard/blog (content read via raw dist/index.html)
- Leaderboard About/reproducibility docs — https://huggingface.co/docs/leaderboards/open_llm_leaderboard/about
- Leaderboard FAQ (flagging, normalization, merges) — https://huggingface.co/docs/leaderboards/open_llm_leaderboard/faq
- Clémentine Fourrier, "Let's talk about LLM evaluation" — https://huggingface.co/blog/clefourrier/llm-evaluation

**lm-evaluation-harness (EleutherAI, GitHub issues incl. comments)**
- #982 SquadV2 not reproducible (Biderman on LLaMA) — https://github.com/EleutherAI/lm-evaluation-harness/issues/982
- #1098 chat-template design thread — https://github.com/EleutherAI/lm-evaluation-harness/issues/1098
- #1292 TriviaQA low results / prompt description effect — https://github.com/EleutherAI/lm-evaluation-harness/issues/1292
- #1625 batch size 1 vs 4 differ — https://github.com/EleutherAI/lm-evaluation-harness/issues/1625
- #1841 inconsistent results with chat template — https://github.com/EleutherAI/lm-evaluation-harness/issues/1841
- #2211 old vs new versions differ / MMLU whitespace — https://github.com/EleutherAI/lm-evaluation-harness/issues/2211
- #2338 locally reproducible HF-Leaderboard evals — https://github.com/EleutherAI/lm-evaluation-harness/issues/2338
- #2583 how to exactly reproduce leaderboard results — https://github.com/EleutherAI/lm-evaluation-harness/issues/2583
- #2932 LongBench scores far off — https://github.com/EleutherAI/lm-evaluation-harness/issues/2932
- #3357 non-reproducible despite seed/greedy — https://github.com/EleutherAI/lm-evaluation-harness/issues/3357
- #4007 unparseable scored as wrong (64.9% of generative tasks) — https://github.com/EleutherAI/lm-evaluation-harness/issues/4007
- (surveyed via search: #2557, #2555, #3258, #3129, #2513, #873, #704, #1293, #3966, #3881, #3986)

**Dataset cards (HF discussions)**
- MMLU "Not all samples are correct" — https://huggingface.co/datasets/cais/mmlu/discussions/29
  (index: https://huggingface.co/datasets/cais/mmlu/discussions)
- GSM8K "Some bad data with wrong answers" — https://huggingface.co/datasets/openai/gsm8k/discussions/5
  (also #20 "Wrong answer in test set"; index: https://huggingface.co/datasets/openai/gsm8k/discussions)
- TruthfulQA mc1 gold-always-first — https://huggingface.co/datasets/truthfulqa/truthful_qa/discussions/8

**Community threads elsewhere**
- HN: "Open-LLM performances are plateauing" (v2) — https://news.ycombinator.com/item?id=40832330
- HN: "What's Going on with the Open LLM Leaderboard?" — https://news.ycombinator.com/item?id=36449424
- HN: "How I topped the HuggingFace open LLM leaderboard on two gaming GPUs" —
  https://news.ycombinator.com/item?id=47322887 (post: https://dnhkng.github.io/posts/rys/)
- Rylan Schaeffer, "Pretraining on the Test Set Is All You Need" — https://arxiv.org/abs/2309.08632
