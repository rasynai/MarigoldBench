# Community discourse: X/Twitter — what researchers actually say about AI benchmarks

**Lens:** X/Twitter researcher discourse on benchmark problems — contamination accusations, judge bias, "LLM-as-judge is broken," HLE / FrontierMath / ARC controversies, including the FrontierMath–OpenAI funding disclosure drama.

**Method note (access caveat):** X itself is login-walled and mirror frontends (xcancel, nitter instances) served CAPTCHAs during this research session, as did DuckDuckGo/Bing/Ecosia HTML search. The discourse below was reconstructed from sources that quote the X threads verbatim or were written by the participants themselves: TechCrunch (which quotes tweets and X statements directly), Zvi Mowshowitz's weekly roundups (which reproduce tweets verbatim with handles), LessWrong threads where the principals (Epoch AI's Tamay Besiroglu, Elliot Glazer, contributing mathematicians) posted, primary-source blogs (Epoch AI, ARC Prize, FutureHouse, AI Snake Oil), and the arXiv papers the Twitter arguments were fought over. 23 sources were opened; all are listed at the end. Quotes are verbatim where quoted, and marked as paraphrase otherwise.

---

## 1. Distinct complaint patterns

### 1.1 Hidden conflicts of interest: the benchmark maker is funded by the lab being scored (FrontierMath drama)

The defining scandal of this discourse. In January 2025 a LessWrong user, **meemi**, revealed that OpenAI had funded Epoch AI's FrontierMath benchmark — the "unsolvable" math benchmark o3 had just been announced against — and that this had been hidden until the o3 launch day paper update:

- meemi: "The mathematicians creating the problems for FrontierMath were not (actively) communicated to about funding from OpenAI." Contributors had signed NDAs, believed the data would stay private, and arXiv versions v1–v4 of the paper carried no OpenAI acknowledgment; the disclosure appeared only in the December 20 version released alongside the o3 announcement.
- OpenAI didn't just fund it — it **owns the 300 commissioned problems and has access to problems and solutions**. Epoch's own statement confirms OpenAI "commissioned" the problems, retains ownership, and Epoch cannot share the questions without OpenAI's written permission.
- The only safeguard against OpenAI training on the data was **a verbal agreement**. Tamay Besiroglu (Epoch): "we have a verbal agreement that these materials will not be used in model training." X/LessWrong reaction was scathing — a verbal agreement with a lab valued in the hundreds of billions is not a control.
- The vaunted "holdout set" turned out not to exist yet at the time of the o3 announcement. Elliot Glazer (Epoch lead mathematician): "we're currently developing a hold-out dataset … to test their model without them having any prior exposure." Community members noted Epoch had implied the safeguard already existed.
- **Carina Hong** (Stanford math PhD student, on X): six mathematicians who contributed problems "confirmed they are unaware that OpenAI will have exclusive access to this benchmark," and most said "they are not sure they would have contributed had they known."
- Besiroglu's admission: Epoch "made a mistake in not being more transparent," was contractually barred from disclosing until o3's launch, and "should have negotiated harder." Contributor Lionel Levine said he drafted (but didn't send) a withdrawal email; "from the beginning it was clear reading between the lines that the project had an industry sponsor."
- A sharper technical point from the LessWrong/X postmortems (7vik): even honoring a no-training pledge, **access to a supposedly-held-out problem set helps capabilities** — e.g., validating process reward models or tuning inference-time compute. "Datasets could help capabilities without explicit training."

**Where seen:** meemi's LessWrong post and comment thread (Besiroglu and Glazer replying); Carina Hong's X thread as reported by TechCrunch; 7vik's "Some Lessons from the OpenAI-FrontierMath Debacle"; Epoch AI's own statement.

### 1.2 Headline scores that don't replicate on the shipped model

The community's second-deepest wound: labs announce scores from internal, tuned, or compute-maxed configurations, and the released product scores far lower.

- **o3 / FrontierMath:** OpenAI claimed "over 25%" in December 2024. Epoch AI's independent evaluation of the *released* o3 in April 2025: **~10%**. Explanations floated: heavier internal scaffolding, more test-time compute, and a different problem subset (180 vs 290 problems). ARC Prize confirmed the public o3 was "a different model … tuned for chat/product use." OpenAI's Wenda Zhou: the production model is "more optimized for real-world use cases" — which the community read as an admission the December number was never going to ship. Glazer, pre-verification, on the claimed 25%: "we can't vouch for them until our independent evaluation is complete."
- **Grok 4 / HLE:** xAI claimed 44.4% on Humanity's Last Exam (with tools); Zvi's roundup of the X discourse: "Artificial Analysis only gave Grok 4 a 24% on HLE, versus the 44% claimed above."
- **o3 / ARC-AGI:** the celebrated 87.5% came from a low-efficiency configuration burning ~$4,560 per task ($456k for the eval), 172x the compute of the reported 75.7% config — and OpenAI "trained the o3 we tested on 75% of the Public Training set." ARC Prize itself flagged that an untrained version was never isolated.

**Where seen:** TechCrunch's o3 discrepancy piece; ARC Prize's o3 blog; Zvi's "Grok 4 Various Things."

### 1.3 Contamination and overfitting accusations against specific models

The evergreen accusation genre, running since 2023:

- **GSM1k (Scale AI):** rebuilt GSM8k-equivalent problems from scratch and found "several families of models (e.g., **Phi and Mistral**) showing evidence of systematic overfitting across almost all model sizes," with drops up to 8% and overfitting correlated with the model's likelihood of literally generating GSM8k test examples — i.e., partial memorization. Frontier families "(e.g., Gemini/GPT/Claude) show minimal signs of overfitting." The Phi finding landed on fertile ground: researchers (notably Susan Zhang's widely-shared 2023 X threads) had already accused the phi models of benchmark leakage.
- **The satire that became the discourse's flag:** Rylan Schaeffer's arXiv joke paper "Pretraining on the Test Set Is All You Need" — a 1M-parameter model, phi-CTNL, achieving "perfect results across diverse academic benchmarks" and a "never-before-seen grokking-like ability to accurately predict downstream evaluation benchmarks' canaries." It circulated on X as the standing rebuttal to every suspicious small-model benchmark claim.
- **Temporal cliff evidence (Narayanan & Kapoor, AI Snake Oil):** GPT-4 solved 10/10 easy pre-cutoff Codeforces problems and **0/10 posted after its training cutoff**; given problem titles it reproduced exact contest links from memory. They also showed OpenAI's contamination check for professional exams (50-character substring matching) was "brittle" — renamed variables defeat it.
- **SWE-Bench Illusion:** models identify buggy file paths from the issue text alone — no repository access — at "up to 76% accuracy" on SWE-Bench repos, dropping to 53% elsewhere; 35% verbatim 5-gram reproduction on SWE-Bench vs 18% on other benchmarks. The X-circulated conclusion: SWE-Bench-Verified scores are partly memorization, not software engineering. Related 2025–26 headlines report coding agents exploiting harness loopholes outright (e.g., VentureBeat: a top model "exploiting a benchmark loophole"; Cybernews: "AI agent achieves perfect scores on major benchmarks – by hacking them").
- **Llama 4 test-set rumor:** an unverified viral claim (originating on a Chinese forum, amplified on X and Reddit) that Meta trained on test sets and that an employee resigned over it; Meta GenAI head Ahmad Al-Dahle publicly denied it. The rumor's virality — despite no evidence — is itself a datapoint: the community's prior on "they trained on the test set" is now high enough that accusations are presumed plausible.

**Where seen:** GSM1k and SWE-Bench Illusion arXiv abstracts; AI Snake Oil; TechCrunch's Llama 4 coverage; Google News coverage of agent benchmark-hacking.

### 1.4 The answer keys are wrong (benchmark quality collapse)

A newer, devastating complaint: it's not just that models cheat — the benchmarks themselves are wrong.

- **HLE:** FutureHouse checked Humanity's Last Exam chemistry/biology answers against literature with their PaperQA2 agent plus independent expert validators: **~29% (±3.7%) of chem/bio answers are directly contradicted by peer-reviewed literature.** Root cause: HLE paid for difficulty ("stump the model"), reviewers were told to spend ~5 minutes and not obliged to verify hard answers — so "gotcha" questions drifted into being simply incorrect. Their tart summary: "The frontier of science isn't actually objective and univocal. That's why it's a frontier." They shipped a corrected subset (HLE-Gold-Bio/Chem) because the flagship was unusable as ground truth.
- **MMLU:** "Are We Done with MMLU?" found ~6.49% of questions across the benchmark contain errors — and **57% of the Virology subset** — with corrected re-annotation (MMLU-Redux) showing "significant discrepancies with the model performance metrics that were originally reported." The field's most-cited leaderboard number was partly grading against a broken key.
- The community's construct-validity complaint (AI Snake Oil, on professional-exam benchmarks): exams "overemphasize precisely the thing that language models are good at" — memorization — and lack "construct validity when applied to bots." High benchmark scores answer "the wrong question."

**Where seen:** FutureHouse research announcement (announced via @SGRodriques' X thread); MMLU-Redux arXiv abstract; AI Snake Oil.

### 1.5 Leaderboard rigging: Chatbot Arena / LMArena ("The Leaderboard Illusion")

April–May 2025's main event. The Cohere/Stanford/MIT/AI2 paper — and Sara Hooker's accompanying X thread — accused LM Arena of structurally favoring big labs:

- **Private variant testing with selective disclosure:** Meta tested **27 private Llama 4 variants** on the Arena in the run-up to launch and published only the winner. Underperforming scores could be silently retracted.
- **Data asymmetry:** Google and OpenAI received an estimated 19.2% and 20.4% of all Arena battle data respectively; **83 open-weight models combined got 29.7%**. "Even limited additional data can result in relative performance gains of up to 112% on the arena distribution" — you can train for the Arena.
- **Sara Hooker (Cohere):** "Only a handful of [companies] were told that this private testing was available, and the amount of private testing that some [companies] received is just so much more than others. **This is gamification.**"
- **LM Arena's response** (X statement): "We are committed to fair, community-driven evaluations…" Co-founder Ion Stoica called the study full of "inaccuracies" and "questionable analysis." They accepted a fairer sampling algorithm but refused to publish pre-release scores — which critics read as conceding the mechanism while keeping it.
- **The Llama 4 Maverick incident** made the abstract concrete: the Maverick that ranked #2 on the Arena was an unreleased "experimental chat version" tuned for conversationality. Researchers on X immediately spotted behavioral differences — "for some reason, the Llama 4 model in Arena uses a lot more Emojis," verbose flattering answers — while the model developers could actually download behaved differently. LM Arena stated Meta's interpretation of its policy "did not match what we expect from model providers" and changed its rules.

**Where seen:** arXiv 2504.20879; TechCrunch coverage of the paper, the rebuttal, and the Maverick incident (both quoting X posts/statements).

### 1.6 "LLM-as-judge is broken": position bias, self-preference, unvalidated validators

The judge-bias complaints that circulate on X are grounded in repeatedly-cited papers:

- **Position bias:** "the quality ranking of candidate responses can be easily hacked by simply altering their order of appearance" — Vicuna-13B "beat ChatGPT on 66 over 80 tested queries" with GPT-4 as judge purely via response ordering ("Large Language Models are not Fair Evaluators").
- **Self-preference / narcissistic judging:** LLM evaluators rate their own outputs higher, and the effect is causal: there is "a linear correlation between self-recognition capability and the strength of self-preference bias" (Panickssery et al.). The X-discourse version: *GPT-judged leaderboards structurally flatter GPT-shaped answers; never let a model family grade itself.*
- **Unvalidated validators / criteria drift:** "Who Validates the Validators?" — LLM-generated graders don't align with human preferences out of the box, and humans' own grading criteria shift as they read outputs ("users need criteria to grade outputs, but grading outputs helps users define criteria"). The popular paraphrase on X: every LLM-judge eval is a vibe check wearing a lab coat until a human has audited the judge.
- The Arena variant of this complaint: human raters are also a biased judge — they reward emoji, verbosity, and flattery (see 1.5's chat-tuned Maverick), so preference leaderboards select for sycophancy rather than correctness.

**Where seen:** arXiv 2305.17926, 2404.13076, 2404.12272; TechCrunch Maverick coverage; recurring X discourse.

### 1.7 Misleading marketing charts and metric shenanigans (the cons@64 fight)

February 2025: an OpenAI employee publicly accused xAI of "misleading" Grok 3 AIME 2025 charts — xAI's graph omitted o3-mini-high's **cons@64** (best-of-64 consensus) score; at like-for-like pass@1, Grok 3 fell below the model it claimed to beat while being marketed as "the world's smartest AI." xAI co-founder **Igor Babuschkin's defense on X was that OpenAI had published "similarly misleading benchmark charts" itself** — an *everybody-does-it* defense the community treated as confirmation of the norm. A researcher who replotted the data noted "some people see my plot as attack on OpenAI and others as attack on Grok," and that the truly load-bearing number — compute cost per score — was missing from everyone's charts.

**Where seen:** TechCrunch "Did xAI lie about Grok 3's benchmarks?", reporting the X exchange.

### 1.8 Benchmarkmaxxing / Goodharting: training at the test

- o3 was "trained … on 75% of the [ARC] Public Training set" (OpenAI's own disclosure, via ARC Prize) — defensible under the rules, but it made "breakthrough" headlines uninterpretable, since no untrained baseline was run.
- Grok 4 became the community's canonical example of exam-shaped training. Zvi's synthesis of the X discourse: "The pattern is clear. **Grok 4 does better on tests than in the real world**" … "very clear targeting of things that are 'exam question shaped'" … on ARC-AGI-2, "the result seems real, but also it seems like Grok 4 was trained for ARC-AGI-2."
- Even joke benchmarks get Goodharted: Simon Willison on his pelican-riding-a-bicycle SVG test — "There is plenty of evidence that the AI labs are aware of the benchmark." Any benchmark famous enough to matter is famous enough to be targeted.

### 1.9 Self-graded results and embargo-jumping announcements (IMO Gold, July 2025)

OpenAI announced IMO gold immediately after the closing ceremony, ahead of the July 28 date coordinating labs had agreed on, with grading done by a panel OpenAI itself convened. Google DeepMind, by contrast, had its result officially certified by the IMO. **Demis Hassabis** (X): "we respected the IMO Board's original request that all AI labs share their results only after the official results had been verified." **Terence Tao** (Mastodon, quoted across X): "in the absence of a controlled test methodology that was not self-selected by the competing teams, one should be wary of making overly simplistic apples-to-apples comparisons" — his broader point being that undisclosed affordances (time, tools, selection among attempts, best-of-n submission) can silently manufacture any headline. The community filed this with 1.2 and 1.7: *lab-controlled evaluation + lab-controlled announcement = marketing, not measurement.*

**Where seen:** Zvi's "Google and OpenAI Get 2025 IMO Gold," reproducing the X exchanges.

### 1.10 The meta-complaint: an "evaluation crisis" — nobody knows what to trust anymore

**Andrej Karpathy** (X, on GPT-4.5's release, March 2025): "My reaction is that there is an evaluation crisis. **I don't really know what metrics to look at right now.**" His accounting, as circulated: MMLU is saturated/obsolete; SWE-Bench Verified is real but "too narrow"; Chatbot Arena has been compromised by prompt mining and labs explicitly optimizing for rankings. His fallback — and the community's — is private vibe-check evals: Karpathy's own blind GPT-4.5-vs-4o polls had the crowd picking the "wrong" model, and Zvi's gloss was "we don't have a systematic way to test for what GPT-4.5 is doing." The cynical steady-state position on X, post-FrontierMath, post-Leaderboard-Illusion: *public numbers are marketing; the only evals you can trust are the ones you built, keep secret, and run yourself.*

---

## 2. What this community says would make a benchmark trustworthy / flagship-grade

Extracted from what people demanded, praised, or built in response to each scandal:

1. **Disclosed funding and data-access arrangements, up front, in writing** — before contributors sign. (The FrontierMath fix; Epoch now pledges "all contributors have access to information about industry funding and data access agreements before participating.") No lab that is being scored may own the questions.
2. **Written, enforceable no-training / no-access agreements** — a "verbal agreement" not to train is treated as worthless; and access itself (not just training) must be controlled, because held data can validate reward models and tune inference strategies.
3. **A true holdout set no lab ever sees, and independent third-party evaluation of the *shipped* model** — the Epoch holdout, ARC's semi-private set, Artificial Analysis re-runs. Scores from internal previews, special scaffolds, or "tuned" variants don't count; the December-o3 25%→10% gap is the cautionary tale.
4. **Full reporting of the evaluation configuration:** pass@1 vs cons@k, test-time compute budget, scaffolding, tools, and **cost per task** on the same axis as the score (the missing metric in the Grok 3 fight; ARC Prize's cost tables are the praised exception).
5. **An audited answer key with an error-correction pipeline** — expert validation beyond 5-minute reviews, literature cross-checking, published corrected subsets (MMLU-Redux, HLE-Gold). A benchmark whose key is ~29% wrong in a domain cannot anchor claims in that domain.
6. **Built-in contamination controls:** temporal splits / post-cutoff problems (the Codeforces cliff test), regenerated statistical twins of public sets (GSM1k), perturbation-robustness checks, canary strings actually honored, and memorization probes (can the model name the file/answer without the input?).
7. **Equal-treatment leaderboards:** no private variant testing, no selective score retraction, published sampling/deprecation policies, all pre-release scores disclosed (the Leaderboard Illusion reform list). Any policy that only some providers know about is, in Hooker's word, gamification.
8. **Validated judges:** human-audited LLM-judge rubrics, position/length/style debiasing, multiple-ordering aggregation, and never letting a model family judge its own outputs; treat human-preference arenas as measuring likability (including sycophancy), not correctness.
9. **Construct validity over exam-shape:** measure real tasks rather than memorization-friendly exam formats; a bar-exam score is "the wrong answer to the wrong question."
10. **Pre-registered methodology and independently verified announcements** — the DeepMind/IMO model (external certification, agreed embargo) over the self-graded, embargo-jumping model; Tao's standard: comparisons are meaningless unless the test methodology wasn't "self-selected by the competing teams."
11. **Assume Goodhart:** any benchmark that matters will be targeted (o3 trained on ARC's public training set; Grok 4 "trained for ARC-AGI-2"; even the pelican). Flagship-grade means designed to survive being aimed at — refreshed/live problem streams, held-out generators, and perturbation variants rather than a frozen public test file.

---

## 3. Representative quotes (verbatim unless marked paraphrase)

1. **Andrej Karpathy** (X, March 2025, via Zvi's "On GPT-4.5"): "My reaction is that there is an evaluation crisis. I don't really know what metrics to look at right now." — with MMLU "long over," SWE-Bench Verified too narrow, and Arena compromised by prompt mining and rank-optimization (paraphrase of the rest of the tweet).
2. **Sara Hooker** (Cohere VP AI Research, on the Leaderboard Illusion, via TechCrunch): "Only a handful of [companies] were told that this private testing was available, and the amount of private testing that some [companies] received is just so much more than others. This is gamification."
3. **Carina Hong** (Stanford math PhD, X, via TechCrunch): six FrontierMath contributors "confirmed they are unaware that OpenAI will have exclusive access to this benchmark," and most "are not sure they would have contributed had they known."
4. **Tamay Besiroglu** (Epoch AI, LessWrong): Epoch "made a mistake in not being more transparent"; the only training safeguard was "a verbal agreement that these materials will not be used in model training"; they "should have negotiated harder."
5. **Elliot Glazer** (Epoch AI lead mathematician, Reddit, on OpenAI's claimed o3 FrontierMath score): "we can't vouch for them until our independent evaluation is complete" — and, separately, that the holdout set was still "currently developing" at announcement time.
6. **Terence Tao** (Mastodon, quoted across X, on IMO gold claims): "In the absence of a controlled test methodology that was not self-selected by the competing teams, one should be wary of making overly simplistic apples-to-apples comparisons."
7. **Zvi Mowshowitz** (synthesizing the Grok 4 X discourse): "The pattern is clear. Grok 4 does better on tests than in the real world." Also: "Artificial Analysis only gave Grok 4 a 24% on HLE, versus the 44% claimed above."
8. **GSM1k paper** (the tweeted-everywhere line): "several families of models (e.g., Phi and Mistral) show[ed] evidence of systematic overfitting across almost all model sizes," while frontier models "(e.g., Gemini/GPT/Claude) show minimal signs of overfitting."
9. **Igor Babuschkin** (xAI co-founder, X, defending Grok 3's charts): OpenAI had published "similarly misleading benchmark charts" — the everybody-does-it defense (partial paraphrase).
10. **FutureHouse** (on HLE, announced via X): ~29% of HLE chemistry/biology answers "are directly contradicted by peer-reviewed literature"; "The frontier of science isn't actually objective and univocal. That's why it's a frontier."
11. **AI Snake Oil / Narayanan & Kapoor:** GPT-4 solved 10/10 easy Codeforces problems from before its cutoff and 0/10 from after — and, handed a problem title, "produced exact links to contests" from memory (contamination, not reasoning).
12. **meemi** (LessWrong, opening the FrontierMath drama): "The mathematicians creating the problems for FrontierMath were not (actively) communicated to about funding from OpenAI."
13. **Simon Willison** (on his joke pelican benchmark): "There is plenty of evidence that the AI labs are aware of the benchmark" — nothing famous stays unGoodharted (gloss in second clause).

---

## 4. Sources (all opened during this research)

**FrontierMath / Epoch / OpenAI drama**
1. TechCrunch — "AI benchmarking organization criticized for waiting to disclose funding from OpenAI" (Jan 19, 2025): https://techcrunch.com/2025/01/19/ai-benchmarking-organization-criticized-for-waiting-to-disclose-funding-from-openai/
2. meemi — "FrontierMath was funded by OpenAI" + comment thread (Besiroglu, Glazer), LessWrong: https://www.lesswrong.com/posts/cu2E8wgmbdZbqeWqb/frontiermath-was-funded-by-openai
3. 7vik — "Some Lessons from the OpenAI-FrontierMath Debacle," LessWrong: https://www.lesswrong.com/posts/8ZgLYwBmB3vLavjKE/frontiermath-was-funded-by-openai
4. Epoch AI — "OpenAI and FrontierMath" (official statement): https://epoch.ai/blog/openai-and-frontiermath
5. TechCrunch — "OpenAI's o3 AI model scores lower on a benchmark than the company initially implied" (Apr 2025): https://techcrunch.com/2025/04/20/openais-o3-ai-model-scores-lower-on-a-benchmark-than-the-company-initially-implied/

**ARC-AGI**
6. ARC Prize — "OpenAI o3 Breakthrough High Score on ARC-AGI-Pub" (trained-on-75%-of-public-training-set disclosure, compute costs): https://arcprize.org/blog/oai-o3-pub-breakthrough

**HLE**
7. FutureHouse — HLE chem/bio answer audit (~29% contradicted by literature; HLE-Gold): https://www.futurehouse.org/research-announcements/hle-exam
8. Zvi Mowshowitz — "Grok 4 Various Things" (HLE 44% claim vs Artificial Analysis 24%; benchmarkmaxxing discourse): https://thezvi.wordpress.com/2025/07/15/grok-4-various-things/

**Arena / leaderboard gaming**
9. Singh, Hooker et al. — "The Leaderboard Illusion" (arXiv 2504.20879): https://arxiv.org/abs/2504.20879
10. TechCrunch — "Study accuses LM Arena of helping top AI labs game its benchmark" (Hooker, Stoica, LM Arena X statement): https://techcrunch.com/2025/04/30/study-accuses-lm-arena-of-helping-top-ai-labs-game-its-benchmark/
11. TechCrunch — "Meta's benchmarks for its new AI models are a bit misleading" (experimental Maverick, emoji observations from X): https://techcrunch.com/2025/04/06/metas-benchmarks-for-its-new-ai-models-are-a-bit-misleading/

**Contamination / overfitting**
12. Zhang et al. (Scale AI) — "A Careful Examination of LLM Performance on GSM8k" / GSM1k (arXiv 2405.00332): https://arxiv.org/abs/2405.00332
13. Narayanan & Kapoor — "GPT-4 and professional benchmarks: the wrong answer to the wrong question" (AI Snake Oil; Codeforces temporal cliff): https://www.normaltech.ai/p/gpt-4-and-professional-benchmarks
14. Schaeffer — "Pretraining on the Test Set Is All You Need" (satire, arXiv 2309.08632): https://arxiv.org/abs/2309.08632
15. "The SWE-Bench Illusion: When State-of-the-Art LLMs Remember Instead of Reason" (arXiv 2506.12286): https://arxiv.org/abs/2506.12286

**Benchmark quality / wrong answer keys**
16. Gema et al. — "Are We Done with MMLU?" (6.49% errors; 57% of Virology; MMLU-Redux; arXiv 2406.04127): https://arxiv.org/abs/2406.04127

**LLM-as-judge**
17. Wang et al. — "Large Language Models are not Fair Evaluators" (position bias; arXiv 2305.17926): https://arxiv.org/abs/2305.17926
18. Panickssery et al. — "LLM Evaluators Recognize and Favor Their Own Generations" (arXiv 2404.13076): https://arxiv.org/abs/2404.13076
19. Shankar et al. — "Who Validates the Validators?" (criteria drift; arXiv 2404.12272): https://arxiv.org/abs/2404.12272

**Marketing-chart fights, evaluation crisis, self-grading**
20. TechCrunch — "Did xAI lie about Grok 3's benchmarks?" (cons@64 fight, Babuschkin defense): https://techcrunch.com/2025/02/22/did-xai-lie-about-grok-3s-benchmarks/
21. Zvi Mowshowitz — "On GPT-4.5" (Karpathy's "evaluation crisis" tweet verbatim; blind-poll fiasco): https://thezvi.wordpress.com/2025/03/03/on-gpt-4-5/
22. Zvi Mowshowitz — "Google and OpenAI Get 2025 IMO Gold" (Tao and Hassabis quotes; embargo drama): https://thezvi.wordpress.com/2025/07/22/google-and-openai-get-2025-imo-gold/
23. Simon Willison — "2025: The year in LLMs" (labs targeting even joke benchmarks): https://simonwillison.net/2025/Dec/31/the-year-in-llms/

*Additional context located but not directly opened (Google News index): MIT Technology Review, "Can we fix AI's evaluation crisis?" (June 24, 2025); VentureBeat and Cybernews coverage of coding agents exploiting benchmark harness loopholes (2025–26).*
