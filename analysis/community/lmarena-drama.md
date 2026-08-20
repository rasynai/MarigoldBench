# LMArena / Chatbot Arena: what the community actually says about leaderboard trust

Venue lens: the LMArena (formerly LMSYS Chatbot Arena) controversies — the Llama-4 special-variant scandal (April 2025), style/sycophancy bias, "The Leaderboard Illusion" paper discourse (arXiv 2504.20879, April 2025), the Surge AI "LMArena is a Cancer on AI" pile-on (Dec 2025–Jan 2026), and the MIT/IBM statistical-fragility study (Feb 2026).

Method note: web search quota was exhausted in this session, so everything below comes from directly opened pages: three full HN comment trees (via the Algolia items API), the primary blogs/papers, and press coverage that quotes the actors verbatim. Reddit (all subdomains), web.archive.org, The Verge, and Ars Technica are unfetchable from this environment; r/LocalLLaMA and X sentiment is captured via aggregators that quote it directly (Zvi Mowshowitz's roundup, The Register, TechCrunch, The Decoder). ~16 sources actually opened.

## Timeline anchor (for orientation)

- Aug 2024: LMSYS itself publishes "style control," conceding that response length and markdown formatting materially move Arena rankings.
- Dec 2024: Karpathy publicly doubts the leaderboard after a Gemini model ranks "way above the second best" while underperforming in his own use.
- Apr 5, 2025 (a Saturday): Meta ships Llama 4, marketing Maverick's #2 Arena rank — ELO 1417 — earned by an unreleased "Llama-4-Maverick-03-26-Experimental" variant "optimized for conversationality."
- Apr 6–8, 2025: Community notices the Arena model is not the shipped model; a "I have submitted my resignation" rumor from a claimed Meta employee alleges blending test sets; Meta GenAI VP Ahmad Al-Dahle denies it; LMArena rebukes Meta and changes policy.
- Apr 11, 2025: The actually-released Maverick lands around 32nd on the Arena.
- Apr 30, 2025: "The Leaderboard Illusion" (Cohere Labs, Princeton, Stanford, MIT, AI2 et al.) drops: 27 private Meta variants, sampling asymmetries, silent deprecations. LMArena calls it "inaccuracies" and "questionable analysis."
- May 2025: LMArena the academic project becomes LMArena the company ($100M raise, $600M valuation; later cited at $1.7B). Community reads the COI writing on the wall.
- Dec 2025–Jan 2026: Surge AI's "LMArena is a Cancer on AI" (246 points, 100 comments on HN) — 52% of sampled Arena votes disagreed with expert review.
- Feb 2026: MIT/IBM study: removing 2 of 57,477 Arena ratings flips the #1 model.

---

## 1. Distinct complaint patterns

### 1.1 Private variant testing + selective disclosure = institutionalized p-hacking

The single loudest complaint. Vendors privately test many variants on the Arena and publish only the winner, which inflates scores by construction (max of N draws).

- The Leaderboard Illusion documented "27 private LLM variants tested by Meta in the lead-up to the Llama-4 release" (Google tested 10, Amazon 7), and that submitting ~10 near-identical variants could inflate a score by ~100 Elo (arXiv 2504.20879; The Decoder coverage).
- Sara Hooker (Cohere): "Only a handful of [companies] were told that this private testing was available," calling it "gamification" (TechCrunch, Apr 30, 2025).
- HN (43842380): simonw noted well-funded vendors "submit dozens of variations of their models to the leaderboard and then selectively publish the model that did best"; j7ake: "It's essentially the pvalue hacking we see in social and biological sciences applied to machine learning"; amelius compared it to being allowed to retake a multiple-choice exam until you pass.

### 1.2 The Llama-4 bait-and-switch: the number you market is not the model you ship

- Meta's announcement touted an "experimental chat version scoring ELO of 1417 on LMArena"; the deployed Arena model was verbose, emoji-laden, and sycophancy-tuned, while the released Maverick behaved differently and later ranked ~32nd (The Register; Simon Willison's Llama 4 notes; HN story 43652957).
- Nathan Lambert (Interconnects): "Sneaky. The results below are fake, and it is a major slight to Meta's community to not release the model they used to create their major marketing push." He also noted the Arena variant's "character is juvenile" while the real model "is quite smart and has a reasonable tone."
- LMArena's public rebuke: "Meta should have made it clearer that Llama-4-Maverick-03-26-Experimental was a customized model to optimize for human preference" — plus a policy update (The Register, Apr 8, 2025). Headlines ran as "Meta got caught gaming AI benchmarks" (HN 43620452, 347 points).
- The side-plot: a viral post from a claimed resigning Meta employee alleged leadership discussed "blending test sets"; Al-Dahle: "We've also heard claims that we trained on test sets — that's simply not true and we would never do that" (TechCrunch, Apr 7, 2025). No evidence emerged, but the rumor stuck because the variant stunt made it plausible to people.

### 1.3 Style beats substance: verbosity, markdown, emoji, sycophancy win votes

- LMSYS's own style-control post (Aug 2024) admitted length is the dominant preference factor (coefficient ~0.25 vs ~0.02–0.11 for markdown) and that controlling for style reshuffles ranks (Claude 3.5 Sonnet rises to tie #1 on hard prompts; mini models fall).
- Surge AI: "The easiest way to climb the leaderboard isn't to be smarter; it's to hack human attention span"; "Confidence beats accuracy and formatting beats facts." Their audit of 500 Arena votes: disagreed with 52%, strongly disagreed with 39% — voters picked answers with hallucinated Wizard of Oz dialogue and a mathematically impossible cake-pan substitution.
- Zvi's roundup of the Llama-4 battle transcripts: Morgan: "the lmsys voter's preference for sycophantic yapping is particularly clear this time"; TDM: "Struggling to find a single answer in this that is less than 100 lines and doesn't make me throw up."
- HN: ekidd — the Arena favors "lots of bullet points in every response. Emoji... even at the expense of accurate answers"; g947o — "bold text, emojis, and plenty of sycophancy... to avoid answering the question"; stared — GPT-4.5 "was miles ahead... yet never at top of the arena."

### 1.4 The raters themselves: anonymous, unpaid, two-second judgments, zero accountability

- gwern (HN 43620452): Arena voters are "self-selected" with "zero incentive to be honest."
- light_hue_1 (HN 43620452): LMArena "was always junk... it measures how good they feel," not capability.
- HN 46522632 got openly contemptuous: michaelmrose — "Average human is a moron you wouldn't trust to watch your hamster"; kazinator — the average voter "cannot calculate a 10% tip." (Pushback existed: aucisson_masque doubted emoji-clickers are the majority; countWSS defended the Arena as "the only testing ground where you examine entire breadth of internet users.")
- A r/MachineLearning thread put it plainly in its title: "LM arena public voting is not objective for LLM evaluation" (Jan 2025).

### 1.5 The house is not neutral: sampling, data, and deprecation favor the big labs

- The Leaderboard Illusion: Google and OpenAI got ~19.2% and ~20.4% of all Arena data (61.4% combined per The Decoder's readout of proprietary-favoring stats); 83 open-weight models shared ~29.7%; 205 of 243 models were silently deactivated, disproportionately open ones; and "even limited additional data can result in relative performance gains of up to 112% on the arena distribution" — i.e., a data flywheel that lets insiders overfit the Arena's prompt distribution.
- Surge AI added: ~9% of monthly Arena prompts are exact duplicates from previous months — an "answer key" leak for anyone with the data feed.
- Goodhart is the community's shorthand: the paper's epigraph is Goodhart's law; HN repeats it (hooloovoo_zoo: "When a measure becomes a target it is no longer a good measure"; sharkjacobs: "Any metric that can be targeted can be gamed").

### 1.6 Statistical fragility: the crown sits on 2 votes

- MIT/IBM (Feb 2026): removing 2 of 57,477 Chatbot Arena ratings — 0.003% — flips the #1 model; Vision Arena flips on 0.094%, Search Arena on 0.253%. Tamara Broderick: "If it turns out the top-ranked LLM depends on only two or three pieces of user feedback out of tens of thousands, then one can't assume the top-ranked LLM is going to be consistently outperforming all the other LLMs when deployed" (The Decoder). Bradley-Terry breaks down when top models are close.

### 1.7 Conflicts of interest all the way down — including the critics and the platform

- LMArena commercialized mid-scandal: Bloomberg — "LMArena Goes from Academic Project to $600M Startup"; HN 46522632: minimaxir cited the $150M raise at $1.7B; koakuma-chan: they're "selling model evaluations, powered by volunteer users"; fuddle: with "$250 million raised... I don't see reflection happening anytime soon." By 2026 the rebranded arena.ai was blogging "Arena Reaches $100M in 8 Months" — and its blog archive no longer surfaces the 2025 Leaderboard-Illusion response or Llama-4 policy posts.
- The community also discounts the critics' motives: HN noted Cohere (whose models rank poorly) authored the paper, and htrp pointed out Surge AI is "basically selling expert advice via training data review" — a direct competitor to free crowdsourced evals. Nobody in this discourse is presumed neutral.
- LMArena's defensive posture compounded distrust: Ion Stoica dismissed the paper as "inaccuracies" and "questionable analysis"; LMArena argued that more submissions is not unfair treatment and rejected the transparency recommendations on pre-release scores (TechCrunch, Apr 30, 2025), insisting rankings "reflect millions of fresh, real human preferences" (The Decoder).

### 1.8 Arena rank does not transfer to real work

- refulgentis (HN): DeepSeek "has a very, very, hard time tool calling" yet shines on chat-trivia-shaped evals.
- Nathan Lambert: many open models "maximize on ChatBotArena while destroying the model's performance on important skills like math or code."
- Surge AI: models behave differently on LMArena than in their native products, so the measured artifact isn't the used artifact.

### 1.9 Net effect: trust collapse, retreat to vibes and private evals

- Zvi's aggregation: Wh — "These examples are extremely damning on the utility of Chatbot arena as a serious benchmark... This is the clearest evidence that no one should take these rankings seriously"; Hasan Can — "Now, time has come to put a final nail in lmarena's coffin"; AKR — "you should never believe these benchmarks unless you really try it out yourself."
- Karpathy's Gemini episode (Dec 2024) became the canonical citation for "leaderboard rank is decoupled from my experience" (invoked by name in HN 43620452 and The Decoder).
- HN 43842380's constructive consensus: pongogogo — "You really need your own private evals"; AstroBen — study how a model's failures change on tasks it currently fails.
- The emergent HN summary line: LMArena has become unreliable; labs optimize the metric, not the capability. Even the meta-discourse turned toxic enough that at one point linking lmarena.ai was banned site-wide on Reddit ("Tell HN," Dec 2024).

---

## 2. What this community says would make a benchmark trustworthy / flagship-grade

Distilled from the paper's five reforms, the HN threads, Surge's critique, and the MIT/IBM recommendations:

1. One final submission per model; no retraction, no best-of-N. Prohibit private test-then-selectively-publish; require disclosure of every variant tested (paper rec 1; simonw wanted a footnote reading "they tried 22 variants, most of which scored lower"; sebastiennight: "1 model per company per month, max").
2. Hard cap on concurrent private variants (paper rec 2: max ~3 per provider).
3. Evaluate the shipped artifact, verified. The scored endpoint must be bit-identical to what users get; a marketed score for an unreleased tune is treated as fabrication (the whole Llama-4 lesson; Lambert's "the results below are fake").
4. Equal, transparent sampling and criteria-based deprecation — published removal lists and rationales, uniform rules across proprietary/open (paper recs 3–5; the 205-of-243 silent-deactivation complaint).
5. Control for presentation. Separate substance from style (length/markdown/emoji/sycophancy) as a default view, not an optional toggle (LMSYS's own style-control work; Surge: a system that "can't be gamed by bolding more aggressively").
6. Ground truth over applause. Verify factual claims rather than counting two-second preference clicks: expert raters or rater-quality modeling (RA_Fisher: "We need LMArena rated by experts" plus Bayesian rater-quality inference), graded scales instead of binary votes (jpollock), rubric-based LLM-as-judge (thorum), confidence-weighted votes, low-quality-prompt filtering, mediator review (MIT/IBM).
7. Anti-contamination hygiene. Fresh, non-repeating prompts (Surge's 9%-duplicates finding); no data-feed flywheel where insiders can overfit the eval distribution (the 112% claim); test-set secrecy with audited handling.
8. Report statistical robustness. Confidence intervals plus sensitivity analysis — if 2 votes flip #1, say so; don't present a total order where none exists (Broderick).
9. Independent, non-commercial governance with disclosed conflicts. The community treats a leaderboard operator that sells services to the ranked labs — or a critic that sells rival evals — as presumptively motivated; a flagship benchmark needs open data/code, published policies enforced symmetrically, and no privileged lab relationships.
10. Validity against real tasks. Correlate with downstream capability (tool use, math, code, long context), and expect users to keep private task-specific evals as the final arbiter — the benchmark should aim to predict those, not replace them.

The cynical floor of the discourse is worth preserving: a large fraction of this community now believes any public leaderboard will be Goodharted the moment it matters ("Any metric that can be targeted can be gamed"), so a trustworthy benchmark must be designed assuming adversarial vendors, adversarial raters, and a motivated operator — and must make its own gaming surface measurable.

---

## 3. Representative quotes

1. "Sneaky. The results below are fake, and it is a major slight to Meta's community to not release the model they used to create their major marketing push." — Nathan Lambert, Interconnects, on Llama-4-Maverick-03-26-Experimental (interconnects.ai/p/llama-4).
2. "The easiest way to climb the leaderboard isn't to be smarter; it's to hack human attention span." — Surge AI, "LMArena is a Cancer on AI" (surgehq.ai).
3. Arena voters are "self-selected" with "zero incentive to be honest." — gwern, HN 43620452 ("Meta got caught gaming AI benchmarks").
4. LMArena "was always junk... it measures how good they feel." — light_hue_1, HN 43620452.
5. "It's essentially the pvalue hacking we see in social and biological sciences applied to machine learning." — j7ake, HN 43842380 ("The Leaderboard Illusion").
6. "Only a handful of [companies] were told that this private testing was available." — Sara Hooker, Cohere, TechCrunch (Apr 30, 2025); also: "The Arena is powerful, and its outsized influence demands scientific integrity" (The Decoder).
7. "These examples are extremely damning on the utility of Chatbot arena as a serious benchmark... This is the clearest evidence that no one should take these rankings seriously." — "Wh," quoted in Zvi Mowshowitz's Llama-4 roundup; in the same post, Hasan Can: "Now, time has come to put a final nail in lmarena's coffin."
8. "We've also heard claims that we trained on test sets — that's simply not true and we would never do that." — Ahmad Al-Dahle, Meta VP of GenAI (TechCrunch, Apr 7, 2025).
9. "Meta should have made it clearer that Llama-4-Maverick-03-26-Experimental was a customized model to optimize for human preference." — LMArena statement (via The Register, Apr 8, 2025); LMArena on the Cohere paper: it contains "inaccuracies" and "questionable analysis" — Ion Stoica (TechCrunch).
10. "If it turns out the top-ranked LLM depends on only two or three pieces of user feedback out of tens of thousands, then one can't assume the top-ranked LLM is going to be consistently outperforming all the other LLMs when deployed." — Tamara Broderick, MIT (The Decoder, Feb 2026).
11. "Average human is a moron you wouldn't trust to watch your hamster." — michaelmrose, HN 46522632, on why popularity voting can't measure intelligence; counterpoint in-thread: the Arena is "the only testing ground where you examine entire breadth of internet users" (countWSS).
12. "You really need your own private evals." — pongogogo, HN 43842380; echoed by AKR via Zvi: "you should never believe these benchmarks unless you really try it out yourself."
13. Karpathy (paraphrase, The Decoder / HN): he stopped trusting the Arena after a Gemini model ranked "way above the second best" while underperforming every other model in his real-world testing.
14. They're "selling model evaluations, powered by volunteer users." — koakuma-chan, HN 46522632, on LMArena's business model; fuddle: with "$250 million raised... I don't see reflection happening anytime soon."

---

## 4. Sources (opened and used)

Primary community threads (full comment trees via HN Algolia items API):
1. HN 43842380 — "The Leaderboard Illusion" discussion (184 pts, 51 comments, Apr 30, 2025) — https://news.ycombinator.com/item?id=43842380
2. HN 43620452 — "Meta got caught gaming AI benchmarks" (347 pts, 161 comments, Apr 8, 2025) — https://news.ycombinator.com/item?id=43620452
3. HN 46522632 — "LMArena is a cancer on AI" (246 pts, 100 comments, Jan 2026) — https://news.ycombinator.com/item?id=46522632
4. HN 43595585 — "The Llama 4 herd" release megathread, arena-related comments (1235 pts) — https://news.ycombinator.com/item?id=43595585

Primary documents:
5. The Leaderboard Illusion, arXiv 2504.20879 (abstract + claims) — https://arxiv.org/abs/2504.20879
6. Cohere research page for the paper (five reform recommendations) — https://cohere.com/research/lmarena
7. Surge AI, "LMArena is a Cancer/Plague on AI" — https://surgehq.ai/blog/lmarena-is-a-plague-on-ai
8. LMSYS, "Does style matter? Style control in Chatbot Arena" (Aug 28, 2024) — https://lmsys.org/blog/2024-08-28-style-control/
9. Arena (rebranded LMArena) blog index — historical 2025 response posts absent post-rebrand — https://arena.ai/blog/ (blog.lmarena.ai and news.lmarena.ai both 301 here)

Commentary and aggregation:
10. Nathan Lambert, Interconnects, "Llama 4" — https://www.interconnects.ai/p/llama-4
11. Zvi Mowshowitz, "Llama Does Not Look Good 4 Anything" (community quote roundup) — https://thezvi.wordpress.com/2025/04/09/llama-does-not-look-good-4-anything/
12. Simon Willison, "Initial impressions of Llama 4" + site search for lmarena — https://simonwillison.net/2025/Apr/5/llama-4-notes/

Press with primary quotes:
13. The Register, "Meta accused of Llama 4 bait-n-switch to juice LMArena rank" — https://www.theregister.com/2025/04/08/meta_llama4_cheating/
14. TechCrunch, "Meta exec denies the company artificially boosted Llama 4's benchmark scores" — https://techcrunch.com/2025/04/07/meta-exec-denies-the-company-artificially-boosted-llama-4s-benchmark-scores/
15. TechCrunch, "Study accuses LM Arena of helping top AI labs game its benchmark" — https://techcrunch.com/2025/04/30/study-accuses-lm-arena-of-helping-top-ai-labs-game-its-benchmark/
16. The Decoder, "Popular AI benchmark LMArena allegedly systematically favors large providers" — https://the-decoder.com/popular-ai-benchmark-lmarena-allegedly-systematically-favors-large-providers-study-claims/
17. The Decoder, "Popular LLM ranking platforms are statistically fragile" (MIT/IBM study) — https://the-decoder.com/popular-llm-ranking-platforms-are-statistically-fragile-new-study-warns/

Referenced but not directly fetchable from this environment (title/metadata via HN Algolia; content via the aggregators above): The Verge "Meta got caught gaming LMArena" (theverge.com/meta/645012); r/MachineLearning "LM arena public voting is not objective for LLM evaluation" (reddit.com/r/MachineLearning/comments/1i83mhj); Bloomberg "LMArena Goes from Academic Project to $600M Startup" (May 21, 2025); "Tell HN: Linking to lmarena.ai is banned site-wide on Reddit" (HN 42551846); "Released Llama 4 Maverick places 32nd in LMArena" (HN 43652957); "GPT-5.2-high LMArena scores released, OpenAI falls from #6 to #13" (HN 46298597).
