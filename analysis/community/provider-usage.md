# Provider usage of benchmarks: what model cards and launch posts cite, what died, and what the discourse says

**Lens:** Benchmarks that Anthropic, OpenAI, Google, Meta, xAI, and DeepSeek actually put in model cards and launch posts — which third-party benchmarks get cited, which died, and stated reasons for choosing them. Sources are launch pages themselves, benchmark-org statements, HN threads, and the commentator layer that audits launches (Willison, Lambert/Interconnects, Zvi, AI Snake Oil, Epoch, ARC Prize, FutureHouse).

**Research date:** 2026-08-16. WebSearch quota was exhausted by the session, so discovery ran through HN Algolia's API + direct fetches; ~27 sources opened.

---

## 0. The citation landscape (context for everything below)

What launch posts cite has churned almost completely in three years:

- **2023 (GPT-4 era):** MMLU, HellaSwag, ARC-Challenge, WinoGrande, HumanEval, GSM8K, DROP, plus professional exams (bar exam "90th percentile", AP tests, Codeforces).
- **2024–2025:** MMLU quietly mutates (MMLU-Pro, MMMLU, Global-MMLU) then largely disappears from headline tables; GSM8K/MATH give way to AIME 2024/2025, USAMO, HMMT; HumanEval gives way to LiveCodeBench, Aider Polyglot, and above all **SWE-bench Verified**; **GPQA Diamond** becomes the default "science" number; **Humanity's Last Exam (HLE)** becomes the "frontier knowledge" number (Gemini 2.5, Grok 4, OpenAI Deep Research); agentic tables appear (TAU-bench/Tau2, Terminal-bench, OSWorld, Vending-Bench); ARC-AGI-1/2 as the "AGI" proxy; MMMU for multimodal; LMArena Elo as the marketing crown jewel until it self-destructs in April 2025.
- **2025–2026 deaths:** HellaSwag/WinoGrande/TriviaQA/DROP vanish without comment; HumanEval and GSM8K die of saturation; Chatbot Arena is demoted after the Llama 4 incident and "The Leaderboard Illusion"; FrontierMath is tainted by the OpenAI funding disclosure; Hugging Face archives the Open LLM Leaderboard; and by 2026 **OpenAI formally retires SWE-bench Verified** ("SWE-bench Verified no longer measures frontier coding capabilities") at 93.9% saturation, citing contamination and memorization — the first time a flagship lab published an obituary for the very benchmark it had created the canonical subset of ([OpenAI](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/), [HN 343 pts](https://news.ycombinator.com/item?id=47910388)).
- Nathan Lambert now calls this the **"post-benchmark era"**: "benchmarks associated with model releases no longer convey meaningful signal to users" ([Interconnects](https://www.interconnects.ai/p/opus-46-vs-codex-53)).

---

## 1. Distinct complaint patterns

### 1.1 Conflicted, lab-funded benchmarks (the FrontierMath debacle)
FrontierMath was marketed as an independent, ultra-hard math benchmark; when o3 launched with "over 25%" on it, it emerged that **OpenAI had commissioned and owns the benchmark and had access to problems and solutions**, under only a *verbal* agreement not to train on it, and most contributing mathematicians were never told. Epoch admitted: "our agreement did not prevent us from disclosing to our contributors that this work was sponsored by an AI company. Many contributors were unaware of these details, and our communication with them should have been more systematic and transparent," and conceded the 50-question holdout set was still being built when the 25% claim aired ([Epoch statement](https://epoch.ai/blog/openai-and-frontiermath)). The HN thread (483 pts) is straight cynicism: "'we have a verbal agreement that these materials will not be used in model training.' Ha ha ha" (agnosticmantis); aithrowawaycomm called the undisclosed funding "incredibly unethical"; bogtog noted that even without cheating, repeated private testing lets labs p-hack noise into "gains" ([HN](https://news.ycombinator.com/item?id=42763231); [LessWrong lessons post](https://www.lesswrong.com/posts/8ZgLYwBmB3vLavjKE/some-lessons-from-the-openai-frontiermath-debacle)).

### 1.2 Chart games: mismatched inference settings presented as one comparison
xAI's Grok 3 launch chart showed Grok beating o3-mini-high on AIME 2025 — by plotting Grok's cons@64 (best-of-64 consensus) against OpenAI's pass@1 and omitting o3's cons@64 bar. OpenAI's Boris Power called it "misleading benchmark results"; xAI cofounder Igor Babuschkin's defense was that "OpenAI has published similarly misleading benchmark charts in the past" — i.e., *everyone shoots first* ([TechCrunch](https://techcrunch.com/2025/02/22/did-xai-lie-about-grok-3s-benchmarks/)). The GPT-5 livestream's bar chart showing 52.8 rendered taller than 69.1 became the canonical "chart crime" / "vibe graphing" moment ([The Verge](https://www.theverge.com/news/756444/openai-gpt-5-vibe-graphing-chart-crime); Zvi's launch autopsy documents the selective comparisons: "They didn't evaluate on 23 of the 500 instances though" — [Zvi](https://thezvi.wordpress.com/2025/08/11/gpt-5s-are-alive-basic-facts-benchmarks-and-the-model-card/)). Google now counter-positions against this explicitly — Gemini 2.5's launch bragged its scores came "without test-time techniques that increase cost, like majority voting" ([Google blog](https://blog.google/technology/google-deepmind/gemini-model-thinking-updates-march-2025/)) — proof the labs themselves treat rivals' headline numbers as inflated.

### 1.3 The demo model is not the shipped model
- **o3 / FrontierMath:** claimed "over 25%" in December 2024; Epoch's independent test of the *released* o3 got ~10%. Epoch: "The difference between our results and OpenAI's might be due to OpenAI evaluating with a more powerful internal scaffold, using more test-time computing." ([TechCrunch](https://techcrunch.com/2025/04/20/openais-o3-ai-model-scores-lower-on-a-benchmark-than-the-company-initially-implied/))
- **o3 / ARC-AGI:** December o3-preview scored 76–88%; released o3-medium scored 53%. ARC Prize: "The production o3 uses a different model from the o3-preview evaluated in December 2024"; "All released o3 compute tiers are smaller than the version we [benchmarked]"; and "o3-preview included 75% of the ARC-AGI-1 dataset during training" ([ARC Prize](https://arcprize.org/blog/analyzing-o3-with-arc-agi)).
- **Llama 4 Maverick / LMArena:** Meta's launch touted "an experimental chat version scoring ELO of 1417 on LMArena" — a chat-tuned, emoji-heavy variant that was never released; the released weights later placed ~32nd. LMArena: "Meta's interpretation of our policy did not match what we expect from model providers." Meta's Ahmad Al-Dahle: "We've also heard claims that we trained on test sets — that's simply not true and we would never do that." ([TechCrunch](https://techcrunch.com/2025/04/06/metas-benchmarks-for-its-new-ai-models-are-a-bit-misleading/), [The Register](https://www.theregister.com/2025/04/08/meta_llama4_cheating/)). Nathan Lambert: "Sneaky. The results below are fake, and it is a major slight to Meta's community to not release the model they used to create their major marketing push." ([Interconnects](https://www.interconnects.ai/p/llama-4))

### 1.4 Structural leaderboard gaming (not just one bad actor)
"The Leaderboard Illusion" (arXiv 2504.20879) documented that Meta tested **27 private Llama-4 variants** on Chatbot Arena before release and published only the winner; that Google and OpenAI got ~19.2% and ~20.4% of all Arena data vs ~29.7% for 83 open-weight models combined; and that Arena data access yields "relative performance gains of up to 112% on the arena distribution" ([paper](https://arxiv.org/abs/2504.20879)). HN reaction: "well funded vendors can apparently submit dozens of variations of their models to the leaderboard and then selectively publish the model that did best" (simonwillison); "It's essentially the p-value hacking we see in social and biological sciences applied to machine learning" (j7ake) ([HN](https://news.ycombinator.com/item?id=43842380)).

### 1.5 Contamination and memorization behind headline scores
- GPT-4's launch-era Codeforces "skill" evaporated on post-cutoff problems: "10/10 pre-2021 problems and 0/10 recent problems in the easy category," and GPT-4 could even link the exact contest from a problem title — memorization presented as capability ([AI Snake Oil](https://www.normaltech.ai/p/gpt-4-and-professional-benchmarks)).
- "The SWE-Bench Illusion" (Microsoft/arXiv 2506.12286): models identify buggy file paths from the issue text alone with up to 76% accuracy on SWE-bench repos vs 53% elsewhere — "performance gains on SWE-Bench-Verified may be partially driven by memorization rather than genuine problem-solving."
- OpenAI's own SWE-bench Verified retirement conceded that "all frontier models we tested were able to reproduce the original, human-written bug fix used as the ground-truth reference" ([HN](https://news.ycombinator.com/item?id=47910388)). There is also a SWE-bench GitHub issue that agents "may look at future repository state" (git history leakage) ([issue #465](https://github.com/SWE-bench/SWE-bench/issues/465)).
- ARC Prize's disclosure that o3-preview trained on 75% of the public ARC-AGI-1 training set (above) is the same complaint at launch-livestream scale.

### 1.6 The flagship benchmarks are themselves broken inside
- **HLE:** FutureHouse found "29 ± 3.7% (95% CI)" of text-only chemistry/biology answers "directly conflicting" with peer-reviewed literature — while HLE was the headline number in Gemini 2.5, Grok 4, and OpenAI Deep Research launches. They shipped a validated HLE-Gold-Bio/Chem subset instead ([FutureHouse](https://www.futurehouse.org/research-announcements/hle-exam)).
- **SWE-bench Verified**, curated by 93 professional developers *specifically to remove broken tasks*, still had inadequate tests: UTBoost's added tests caught 15.7% more incorrect patches marked "correct," flipping rankings for 24% of agents ([ddkang](https://ddkang.substack.com/p/swe-bench-verified-is-flawed-despite)).
- Near ceiling, scores stop being information: "You can trust that a model scoring 40% vs 90% is worse. You can't trust that 93% is better than 90%, because it's impossible to distinguish between recall and reasoning" (stingraycharles, [HN](https://news.ycombinator.com/item?id=47910388)).

### 1.7 Saturate → retire → replace: benchmarks as a treadmill
Providers drop benchmarks the moment they stop producing marketing headroom, usually silently (MMLU, HellaSwag, HumanEval, GSM8K simply stopped appearing) and occasionally loudly (OpenAI retiring SWE-bench Verified at 93.9%). HN's kator: "SPECint and SPECfp went through this exact movie: benchmark, saturate, retire, replace, repeat. The treadmill is the product." wtallis: "Once you are at (or near) 100% pass rate... the test has lost any power to discriminate" ([HN](https://news.ycombinator.com/item?id=47910388)). Zvi's GPT-5 notes flag AIME as "near saturation for thinking models" ([Zvi](https://thezvi.wordpress.com/2025/08/11/gpt-5s-are-alive-basic-facts-benchmarks-and-the-model-card/)); Lambert's "post-benchmark era" post says labs are "on this transition away from standard evaluations at their own pace" ([Interconnects](https://www.interconnects.ai/p/opus-46-vs-codex-53)).

### 1.8 Footnote soup: nonstandard scaffolds, extra compute, and undisclosed cost
Launch tables are not comparable across labs because each score hides a different harness:
- Anthropic's Claude 4 post reports SWE-bench 72.5%/72.7%, but a "high-compute" footnote gets 79.4%/80.2% by sampling "multiple parallel attempts," discarding patches that fail regression tests, and using "an internal scoring model to select the best candidate"; TAU-bench used "a prompt addendum" and raised max steps from 30 to 100 ([Anthropic](https://www.anthropic.com/news/claude-4)).
- Gemini 2.5's SWE-bench score is "with a custom agent setup" ([Google](https://blog.google/technology/google-deepmind/gemini-model-thinking-updates-march-2025/)).
- Grok 4's HLE record is "Grok 4 Heavy" — parallel multi-agent test-time compute — "with Python and Internet tools," fine print included ([xAI](https://x.ai/news/grok-4)).
- Lambert on Grok 3: "the most important metric remains a mystery: the computational (and monetary) cost it took for each model to achieve its best score" ([TechCrunch](https://techcrunch.com/2025/02/22/did-xai-lie-about-grok-3s-benchmarks/)). AI Snake Oil generalizes: "AI agent accuracy measurements that don't control for cost aren't useful," showing near-identical accuracy at ~100x cost differences and proposing Pareto curves instead ([AI Snake Oil](https://www.normaltech.ai/p/ai-leaderboards-are-no-longer-useful)).

### 1.9 Training *for* the benchmark (legal, undisclosed, and effective)
Zvi on Grok 4's ARC-AGI-2 and eval suite: "I don't think xAI cheated, not exactly, but I do think they were given very strong incentives to deliver excellent benchmark results and then they did a ton of RL with this as one of their primary goals," and "The pattern is clear. Grok 4 does better on tests than in the real world." Also: "The further you are culturally from the big three labs, the more models tend to do better on benchmarks than in reality" ([Zvi](https://thezvi.substack.com/p/grok-4-various-things)). Artificial Analysis measured Grok 4 at 24% on HLE vs xAI's claimed 44% (tools/settings delta). Same pattern alleged in a leaked-Meta-internal-discussion Reddit thread about "blending test sets" (denied by Al-Dahle, [The Register](https://www.theregister.com/2025/04/08/meta_llama4_cheating/)).

### 1.10 Selective citation: every launch "leads," because each lab picks its own scoreboard
Labs report the benchmarks they win and omit rivals or entire categories: Zvi on GPT-5: "When you have this much consumer market share... you get no comparison scores"; HN on Claude Opus 4.5 noticed leaning on SWE-bench "makes the opposite impression that they probably intended." Meta shipped a 10M-token context claim supported by nothing but needle-in-a-haystack — "seen as a necessary condition, but not one that is sufficient" (Lambert). Professional-exam claims (GPT-4's bar exam) "overemphasize precisely the thing that language models are good at" and lack "construct validity when applied to bots" ([AI Snake Oil](https://www.normaltech.ai/p/gpt-4-and-professional-benchmarks)).

### 1.11 The audience has checked out: private evals and vibes replace launch tables
Simon Willison: "There are plenty of benchmarks full of numbers. I don't get much value out of those numbers," plus "losing some trust" in leaderboards — hence the pelican-on-a-bicycle test: "Everyone needs their own benchmark" ([Willison](https://simonwillison.net/2025/Jun/6/six-months-in-llms/)). HN (Leaderboard Illusion thread): "you can't trust any public benchmark, and you really need your own private evals" (pongogogo). HN (GPT-5 thread): "Any company relying on LLMs for a critical function should have its own internal benchmark system" (Breza). On DeepSeek-R1's launch claims: "Either the benchmarks are meaningless, or people are somehow too stupid to evaluate the 8B models and they really are as good as Claude sonnet. Which of those seems more likely?" (noodletheworld, [HN](https://news.ycombinator.com/item?id=42768072)). Notably, R1's numbers earned *more* trust than closed-lab numbers because open weights allowed independent replication (simonw, same thread).

---

## 2. What this community implies a trustworthy / flagship-grade science benchmark needs

1. **Independence with disclosed money.** No undisclosed lab funding or ownership; sponsorship, data access, and ownership agreements published up front; contributors told who is paying before they contribute (Epoch's own post-debacle commitments; LessWrong lessons post).
2. **Written, verifiable no-training agreements — verbal is a punchline.** And an access model where evaluated labs never hold problems+solutions (HN FrontierMath thread; LessWrong).
3. **A real holdout set that exists *before* any headline score**, held by an independent party who runs the eval — "verified to be state of the art" the way ARC Prize frames it, not vendor self-report; third-party verification before/at launch (ARC Prize; Zvi: "Always be somewhat cautious until you get third party verification").
4. **Score the shipped artifact.** Numbers must come from the released model at released compute tiers, or be labeled as preview-only; re-benchmark on release (Epoch's o3 retest; ARC Prize's o3-preview vs production o3 documentation).
5. **Standardized, fully disclosed inference settings.** pass@1 vs cons@N labeled, tools declared, scaffold code published, token/dollar cost per task reported — ideally cost-accuracy Pareto curves rather than single bars (Lambert; AI Snake Oil; Google's "without majority voting" framing shows labs already treat this as the honesty marker).
6. **Contamination resistance by construction.** Fresh or rotating problems (LiveCodeBench/AIME-by-year logic), canaries, memorization probes (file-path tests à la SWE-Bench Illusion), and no public ground-truth answers with fixed correct strings ("public + has a fixed correct answer" auto-leaks — marlburrow, HN).
7. **Expert-validated answer keys with published error rates.** ~29% wrong answers in HLE chem/bio and 26/500 weak-test tasks surviving 93 professional reviewers in SWE-bench Verified set the bar: validation must be adversarial (literature-checked, augmented tests), versioned, and its error bars published (FutureHouse HLE-Gold; UTBoost/ddkang).
8. **Statistical honesty at the top of the scale.** Confidence intervals; refusal to market 93-vs-90 deltas as progress; no truncated or mis-scaled bar charts (stingraycharles; GPT-5 chart crime discourse).
9. **No private variant shopping.** All submitted runs logged and disclosed; same data access and sampling for every lab; retractions public (Leaderboard Illusion's policy recommendations; LMArena's post-Llama-4 policy update).
10. **Headroom and a lifecycle plan.** Anthropic's stated reasons for adopting SWE-bench Verified are the community's own criteria read in reverse: "real engineering tasks from actual projects," "not yet saturated," and "measures an entire 'agent'" — plus a plan for what happens when it saturates, since the field just watched OpenAI shoot the benchmark it had itself Verified ([Anthropic](https://www.anthropic.com/research/swe-bench-sonnet); [OpenAI retirement](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)).
11. **Match the measure to the claim.** No professional-exam percentiles or NIAH standing in for real capability; benchmarks need construct validity for the marketed claim (AI Snake Oil; Lambert on 10M context).

---

## 3. Representative quotes (with sources)

1. "Many contributors were unaware of these details, and our communication with them should have been more systematic and transparent... we didn't clarify the data access and ownership agreement with OpenAI." — Epoch AI, on OpenAI commissioning FrontierMath ([epoch.ai](https://epoch.ai/blog/openai-and-frontiermath))
2. "'we have a verbal agreement that these materials will not be used in model training.' Ha ha ha." — agnosticmantis, HN FrontierMath thread ([HN 42763231](https://news.ycombinator.com/item?id=42763231))
3. Boris Power (OpenAI) accused xAI of "misleading benchmark results"; Igor Babuschkin (xAI): "OpenAI has published similarly misleading benchmark charts in the past." And Nathan Lambert: "the most important metric remains a mystery: the computational (and monetary) cost it took for each model to achieve its best score." ([TechCrunch](https://techcrunch.com/2025/02/22/did-xai-lie-about-grok-3s-benchmarks/))
4. "Meta's interpretation of our policy did not match what we expect from model providers." — LMArena; vs Ahmad Al-Dahle (Meta): "We've also heard claims that we trained on test sets — that's simply not true and we would never do that." ([The Register](https://www.theregister.com/2025/04/08/meta_llama4_cheating/))
5. "Sneaky. The results below are fake, and it is a major slight to Meta's community to not release the model they used to create their major marketing push." — Nathan Lambert on Llama 4's LMArena Elo ([Interconnects](https://www.interconnects.ai/p/llama-4))
6. "All released o3 compute tiers are smaller than the version we [benchmarked]." — ARC Prize Foundation, on why launch-demo o3 scores didn't survive contact with the shipped model ([ARC Prize](https://arcprize.org/blog/analyzing-o3-with-arc-agi); [TechCrunch](https://techcrunch.com/2025/04/20/openais-o3-ai-model-scores-lower-on-a-benchmark-than-the-company-initially-implied/))
7. "I don't think xAI cheated, not exactly, but I do think they were given very strong incentives to deliver excellent benchmark results and then they did a ton of RL with this as one of their primary goals... The pattern is clear. Grok 4 does better on tests than in the real world." — Zvi Mowshowitz ([thezvi](https://thezvi.substack.com/p/grok-4-various-things))
8. "SPECint and SPECfp went through this exact movie: benchmark, saturate, retire, replace, repeat. The treadmill is the product." — kator, HN thread on OpenAI retiring SWE-bench Verified ([HN 47910388](https://news.ycombinator.com/item?id=47910388))
9. "You can trust that a model scoring 40% vs 90% is worse. You can't trust it that 93% is better than 90%, because it's impossible to distinguish between recall and reasoning." — stingraycharles, same thread
10. "There are plenty of benchmarks full of numbers. I don't get much value out of those numbers... Everyone needs their own benchmark." — Simon Willison ([simonwillison.net](https://simonwillison.net/2025/Jun/6/six-months-in-llms/))
11. "benchmarks associated with model releases no longer convey meaningful signal to users." — Nathan Lambert, "the post-benchmark era" ([Interconnects](https://www.interconnects.ai/p/opus-46-vs-codex-53))
12. "29 ± 3.7% (95% CI)" of HLE text-only chemistry/biology answers "directly conflict with peer-reviewed literature." — FutureHouse, on the benchmark headlining Gemini 2.5 / Grok 4 / Deep Research launches ([FutureHouse](https://www.futurehouse.org/research-announcements/hle-exam))
13. "Without test-time techniques that increase cost, like majority voting, 2.5 Pro leads in math and science benchmarks like GPQA and AIME 2025." — Google's Gemini 2.5 launch post, a direct methodological jab at rivals' cons@64 charts ([Google](https://blog.google/technology/google-deepmind/gemini-model-thinking-updates-march-2025/))
14. "AI agent accuracy measurements that don't control for cost aren't useful." — Kapoor/Narayanan, AI Snake Oil ([normaltech.ai](https://www.normaltech.ai/p/ai-leaderboards-are-no-longer-useful))
15. "you can't trust any public benchmark, and you really need your own private evals" — pongogogo, HN Leaderboard Illusion thread ([HN 43842380](https://news.ycombinator.com/item?id=43842380))

---

## 4. Sources (opened)

**Benchmark-org and lab primary sources**
- Epoch AI, "Clarifying the Creation and Use of the FrontierMath Benchmark" — https://epoch.ai/blog/openai-and-frontiermath
- ARC Prize, "Analyzing o3 and o4-mini with ARC-AGI" — https://arcprize.org/blog/analyzing-o3-with-arc-agi
- Anthropic, "Introducing Claude 4" (benchmark table + compute/scaffold footnotes) — https://www.anthropic.com/news/claude-4
- Anthropic, "Raising the bar on SWE-bench Verified" (stated selection reasons) — https://www.anthropic.com/research/swe-bench-sonnet
- Google, "Gemini 2.5: our most intelligent AI model" — https://blog.google/technology/google-deepmind/gemini-model-thinking-updates-march-2025/
- xAI, "Grok 4" launch page — https://x.ai/news/grok-4
- OpenAI, "Introducing SWE-bench Verified" — https://openai.com/index/introducing-swe-bench-verified/ (403 to fetcher; content via HN/secondary)
- OpenAI, "Why we no longer evaluate SWE-bench Verified" — https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/ (read via HN thread)
- FutureHouse, "About 30% of Humanity's Last Exam chemistry/biology answers are likely wrong" — https://www.futurehouse.org/research-announcements/hle-exam

**Papers**
- "The Leaderboard Illusion" — https://arxiv.org/abs/2504.20879
- "The SWE-Bench Illusion: When State-of-the-Art LLMs Remember Instead of Reason" — https://arxiv.org/abs/2506.12286
- DeepSeek-R1 paper (benchmark suite in launch claims) — https://arxiv.org/abs/2501.12948

**Press**
- TechCrunch, "Did xAI lie about Grok 3's benchmarks?" — https://techcrunch.com/2025/02/22/did-xai-lie-about-grok-3s-benchmarks/
- TechCrunch, "Meta's benchmarks for its new AI models are a bit misleading" — https://techcrunch.com/2025/04/06/metas-benchmarks-for-its-new-ai-models-are-a-bit-misleading/
- TechCrunch, "OpenAI's o3 AI model scores lower on a benchmark than the company initially implied" — https://techcrunch.com/2025/04/20/openais-o3-ai-model-scores-lower-on-a-benchmark-than-the-company-initially-implied/
- The Register, "Meta accused of Llama 4 bait-n-switch to juice AI benchmark rank" — https://www.theregister.com/2025/04/08/meta_llama4_cheating/
- The Verge, "OpenAI gets caught vibe graphing" (GPT-5 chart crime; fetch blocked, cited for record) — https://www.theverge.com/news/756444/openai-gpt-5-vibe-graphing-chart-crime

**Commentators**
- Simon Willison, "Six months in LLMs" — https://simonwillison.net/2025/Jun/6/six-months-in-llms/ ; "GPT-5: Key characteristics, pricing and system card" — https://simonwillison.net/2025/Aug/7/gpt-5/
- Nathan Lambert, Interconnects: "Llama 4" — https://www.interconnects.ai/p/llama-4 ; "the post-benchmark era" — https://www.interconnects.ai/p/opus-46-vs-codex-53
- Zvi Mowshowitz: "Grok 4 Various Things" — https://thezvi.substack.com/p/grok-4-various-things ; "GPT-5s Are Alive: Basic Facts, Benchmarks and the Model Card" — https://thezvi.wordpress.com/2025/08/11/gpt-5s-are-alive-basic-facts-benchmarks-and-the-model-card/
- AI Snake Oil (Kapoor/Narayanan): "GPT-4 and professional benchmarks" — https://www.normaltech.ai/p/gpt-4-and-professional-benchmarks ; "AI leaderboards are no longer useful" — https://www.normaltech.ai/p/ai-leaderboards-are-no-longer-useful
- ddkang, "SWE-Bench Verified Is Flawed Despite Expert Review" — https://ddkang.substack.com/p/swe-bench-verified-is-flawed-despite
- LessWrong, "Some Lessons from the OpenAI-FrontierMath Debacle" — https://www.lesswrong.com/posts/8ZgLYwBmB3vLavjKE/some-lessons-from-the-openai-frontiermath-debacle

**Community threads (comment-level sources)**
- HN, "FrontierMath was funded by OpenAI" (483 pts / 199 comments) — https://news.ycombinator.com/item?id=42763231
- HN, "The Leaderboard Illusion" (184 pts) — https://news.ycombinator.com/item?id=43842380
- HN, "SWE-bench Verified no longer measures frontier coding capabilities" (343 pts) — https://news.ycombinator.com/item?id=47910388
- HN, "GPT-5: Key characteristics..." (643 pts) — https://news.ycombinator.com/item?id=44827794
- HN, "Claude Opus 4.5" (1113 pts) — https://news.ycombinator.com/item?id=46037637
- HN, "DeepSeek-R1" (1843 pts) — https://news.ycombinator.com/item?id=42768072
- SWE-bench GitHub issue #465, "agents may look at future repository state" — https://github.com/SWE-bench/SWE-bench/issues/465
