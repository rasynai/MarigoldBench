# r/MachineLearning: benchmark skepticism among ML practitioners

**Venue:** reddit.com/r/MachineLearning (the largest practitioner/researcher ML subreddit; heavier on industry applied researchers and grad students than r/LocalLLaMA's hobbyists)
**Method:** Reddit blocks anonymous scraping and this session's WebSearch budget was exhausted, so discovery was done through the Wayback Machine CDX index (thread titles are embedded in Reddit URLs — ~18k r/ML thread URLs enumerated and keyword-filtered) plus the Arctic Shift Reddit archive API (arctic-shift.photon-reddit.com) for full post bodies and comment trees. ~20 threads opened in full (OP + comments, sorted by score), spanning 2019-2026, plus ~15 windowed title searches ("benchmark", "contamination", "mmlu", "gpqa", "evals", "leaderboard", etc.). Quotes are verbatim from archived comment bodies; scores are archive-time snapshots and may differ from live.
**Date compiled:** 2026-08-16

---

## 1. Distinct complaint patterns

### 1.1 Contamination is the default explanation for a good score ("they benchmarked it on its own training data")

The canonical r/ML contamination thread is the March 2023 GPT-4 one — 925 points, the highest-scoring benchmark thread in the subreddit's LLM era: "[N] OpenAI may have benchmarked GPT-4's coding ability on it's own training data" ([124eyso]). The OP reproduces the AI Snake Oil finding: "Horace He pointed out that GPT-4 solved 10/10 pre-2021 problems and 0/10 recent problems in the easy category… it could regularly solve problems in the easy category before September 5 [2021], but none of the problems after September 12," and carries the subhead "OpenAI may have tested on the training data. Besides, human benchmarks are meaningless for bots."

- Top comment (u/mlresearchoor, +92): "OpenAI blatantly ignored the norm to not train on the ~200 tasks collaboratively prepared by the community for BIG-bench. GPT-4 knows the BIG-bench canary ID afaik, which removes the validity of GPT-4 eval on BIG-bench. OpenAI is cool, but they genuinely don't care about academic research standards or benchmarks carefully created over years by other folks."
- u/TheEdes (+8): "if the problem was word for word anywhere in the training data then the testing data is contaminated… if it can only solve problems that it has seen before, then it's nothing special, they just overfit a trillion parameters on a comparatively very small dataset."
- u/DaBobcat (+5) points out Microsoft's own paper admitting it: in the GPT-4 medical-challenge evaluation, "they found strong evidence that it was trained on 'popular datasets like SQuAD 2.0 and the Newsgroup Sentiment Analysis datasets.'"
- u/StellaAthena (EleutherAI, +4) attacks the labs' contamination *methodology* from the other side: "They used a weaker standard for deduplication than is standard as well as a weaker analysis than the one they did for the GPT-3 paper." u/fiftyfourseventeen: "they only deduplicated by exact duplicate text so there was lots of similar data in both sets."
- u/ArnoF7: "GPT-4's performance on codeforces is borderline abhorrent. And now you are telling me there is data leakage, so the actual performance would be even worse than what's on paper???"

The same reflex appears whenever a model surprises: "[D] Deepseek R1 cheating benchmarks?" ([1ic5961], Jan 2025) — "they could have distilled the knowledge of only the benchmark tests to answer them… it would be kind of cheating right?" — where the measured reply concedes the epistemic hole: "The reality is that we can't tell for sure yet. This happens with the overwhelming majority of models… most open source models don't share their training data (and of course closed source models are worse). Sometimes it's not even on purpose… we call it 'benchmark contamination'" (u/kikoncuo). A Jan 2024 thread, "Task contamination: LLMs might not be few-shot any more" ([1945r8k], +74), circulated the systematic evidence that models score better on benchmarks released *before* their training cutoff.

### 1.2 Even without literal test-set leakage, models are "overfit to the benchmark" — good on paper, bad in your hands

r/ML distinguishes contamination from benchmark-shaped training, and complains about both. GSM1k (arXiv 2405.00332) is the standard citation, and Phi is the standard example:

- u/meister2983 ([1daa68e]): "Phi is one of the worse models in terms of benchmark overfitting/data contamination. Only Anthropic, OpenAI and Deepmind seem to systemically avoid this issue."
- u/jonathanx37 ([1daa68e], +5): "after tweaking it's not necessarily any better at the task just at the benchmark. Phi medium is my biggest disappointment. Better than llama3 8b on paper and way worse than it in practice."
- u/LelouchZer12 ([1daa68e], +6): "It's totally possible that some LLMs are overfit to public benchmarks. Without even mentioning those who are blatantly cheating by training on validation/eval set." (Elsewhere in-thread he names Qwen and Aquila via the GSM1k paper.)
- The OP of "[D] Are LLM Benchmark Results Trustworthy?" ([1breffe], Mar 2024) frames the incentive: "what is really stopping the teams working on these models from intentionally/unintentionally gaming these benchmarks by simply leaking these samples into the training? Many of them have plenty of incentives to do so. Fame… Hundreds of millions (literally) in investments for startups/foundation model companies."
- The whole premise of "[D] Is it me or does it seem like benchmarks are making language models worse?" ([1daa68e], Jun 2024): "Do you think these benchmarks are making language models worse by having developers optimize for them too much? Similar situation how a GAN can sometimes break by finding a hack in the discriminator."

### 1.3 Benchmarks as marketing: selective reporting, buried numbers, unverifiable claims

- The PaLM 2 thread title is itself the complaint: "[D] Since Google buried the MMLU benchmark scores in the Appendix of the PALM 2 technical report, here it is vs GPT-4 and other LLMs" ([13e1rf9], +343, May 2023). MMLU's own creator showed up — u/DanielHendrycks (+87): "As a creator of MMLU, I really wish they reported per-subject accuracies." u/LanchestersLaw: Google's report "is riddled with obfuscating fair comparisons and hiding perceived inadequacy behind opaque language." u/kevinbranch (+31): "Face-PaLM."
- u/shadowylurking ([1daa68e], +15): "Companies are incentivized to push for higher numbers for PR reasons. But at this point personal experience on basic use cases really tells you what is going on."
- A bachelor's student trying to verify vendor claims ([1lrnruz], Jul 2025) found Google/OpenAI self-reported SoTA numbers absent from every public leaderboard: "So am I supposed to 'just blindly trust' the very company that trained the model that it is the best without any secondary source? That doesn't seem very scientific to me."
- u/new_name_who_dis_ on The Leaderboard Illusion ([1kbug62], +6): "I think everyone in ml community already knows benchmark scores should be treated with a grain of salt. It's like VCs and investors pouring billions of dollars into some startup based on these benchmarks — they are the ones who would benefit the most from reading something like this."
- Removed-but-telling: "How do we know OpenAI released benchmarks aren't being heavily optimized, through outside means?" ([16unoo7], Sep 2023) — the question keeps being asked even when automod kills the thread.

### 1.4 Leaderboards and arenas are gameable — and got provably gamed

This is the loudest 2025 pattern. In January 2025 a user posted a first-person confession of rigging LMArena with a botnet to win Polymarket bets: "LM arena public voting is not objective for LLM evaluation [D]" ([1i83mhj], +55):

> "I've wrote a python script that: changes the IP address… chooses a random prompt… identifies the model based on the responses… Voting is performed. Always in favor of Google model and always against OpenAi model… The Gemini started rising in the charts. The GPT started to drop. I've made 5k in the process… Based on the data it may be possible that at one point I've generated 10% to 30% of OpenAI vs Google votes." (u/Aplamis, post later deleted; preserved in-thread by u/ganzzahl)

- Top reply (u/Ouitos, +16): "Goodhart's Law at its best. Hopefully in a not too distant future, there will be some form of mutli-company-and-university-wise consortium [sic] for proper model evaluation that don't rely on good faith, and make it hard to identify models." He elaborates downthread: "many other industries have developped the same kind of true neutral benchmark that is the result of consensus between competitors and universities… also possible that an independent company performs this kind of benchmarks. That is the case for example with dxomark for image quality."
- Google's Logan Kilpatrick (u/LoganKilpatrick1) appeared to deny Google does this; u/gwern (+5) dissected LMArena's official response: "they don't say they blocked *this* attack, even though it's a very specific attack where OP gave every detail you could possibly need to ID it… They just assume that their protection worked." u/Scrangdorber mocked the response outright: "'They did not mention anything about valid votes' — This might be the dumbest excuse I've ever heard for anything."
- u/HelloFellow8: "I need to be more careful how I interpret the results of public benchmarks like this that were otherwise my gold standard. All hail livebench." u/ath3nA47: "bro made 10k, cashed out, started a war between OAI vs Google for the votes, and single-handedly proved LM arena is not accurate on their ranking system. Absolute chad lol."
- Cohere's "The Leaderboard Illusion" got its own threads ([1kbug62], [1kdabbd], and a dissent thread [1kdf8jw]). u/kmouratidis (+12): "we (hobbyists AND enterprise) knew for a while, and plenty of people and orgs wrote critiques of and complaints for every benchmark and leaderboard under the sun." u/new_name_who_dis_: "If model providers can submit unlimited number of models and even hide scores they don't like then this is pretty straightforwardly biased benchmark." The dissent thread's OP itself concedes the paper's critiques "appear to be solid and reasonable" and argues only that the title overstates; u/NamerNotLiteral counters: "People attacking LMArena is *good*! … It also gives models that don't have as much resources as OAI/Meta/Google a chance."
- The gameability question predates the proof: "[D] What stops SWE-bench leaderboard from being gamed?" ([1fjxy6j], Sep 2024) drew zero answers — nobody could name the mechanism.
- It isn't only industry leaderboards: "[R] Hacking an NLP benchmark: How to score 100 points on AMR parsing" ([16zoh3s], Oct 2023) demonstrates metric-protocol exploits in an academic benchmark via a parable: a cooking judge who likes salt keeps awarding higher scores until a contestant "just submit[s] a bowl of pure salt… and score[s] 100 points. When seeing this, can we trust this particular judge again to oversee a competition?"

### 1.5 The benchmarks themselves are full of errors and ambiguity (MMLU especially)

- "[D] MMLU having many questions with wrong answers?" ([163xzkz], Aug 2023), sparked by AI Explained's video audit: "It would not matter so much if the models had high failure rate, but as the models are getting closer and closer to 100%, the wrong answers will matter more and more." u/currentscurrents (+10): "This is a problem with many popular datasets, possibly all of them. About 3% of the images in Imagenet are known to be incorrectly labeled."
- "[D] Deep dive into the MMLU ('Are you smarter than an LLM?')" ([18ntia7], Dec 2023, +82) — the OP built a quiz interface after writing the Medium piece "Errors in the MMLU: The Deep Learning Benchmark is Wrong Surprisingly Often." A practicing lawyer (u/ObiWanCanownme, +32): "I think those who are critical of the MMLU have a serious point… Some of the legal questions, I do not think the MMLU's answer is correct (at least not in my jurisdiction). Others… the question was probably pulled from a test that gave it more context." u/osmarks (+11): "Wow. MMLU is terrible and LLMs really do have broad knowledge of everything ever." OP (u/brokensegue): "yeah there are lots of errors in the MMLU."
- Blunter, in the leaderboard-sensitivity thread ([1anr0hm]): u/ski233 (+10): "MMLU is a completely bogus and unreliable test."

### 1.6 Rankings are fragile: trivial format changes reshuffle leaderboards, and nobody reports variance

- "[R] Skeptical about LLM benchmarks telling the whole story? This paper shows how tiny tweaks to tests like MMLU can shuffle model rankings like a deck of cards" ([1anr0hm], Feb 2024, +76), on "When Benchmarks are Targets: Revealing the Sensitivity of Large Language Model Leaderboards" (arXiv 2402.01781 — answer-order and format perturbations moving models up to 8 rank positions). u/relevantmeemayhere (+14): "this shouldn't be a surprise to practitioners. Out of sample generalization is hard… you can [do] really robust nested [CV] or bootstrap validation and see drop off in prod."
- u/new_name_who_dis_ ([1kbug62]): test-set practice in DL "was never statistically correct or sound and yet we still made solid progress."
- There is a dedicated (quiet) thread for "[R] Quantifying Variance in Evaluation Benchmarks" ([1di354e], Jun 2024) — the concern exists but gets a fraction of the attention the scandal threads get. Same for "[D] LLMs are sensitive to choice order! — How to run MMLU benchmark?" ([1d449tv], May 2024): answer-order sensitivity is treated as a known practitioner gotcha.
- On what a 5-point MMLU gap even means (u/DangerousBenefit, [13e1rf9]): "a more intuitive way to look at the numbers is to compare the error rate… GPT-4 gets things wrong 13.6% of the time, while PALM 2 is wrong 18.8%… around 38% of a difference" — the community repeatedly complains that headline deltas are presented without any interpretable scale.

### 1.7 Benchmark scores don't transfer to real work

- OP of [1breffe]: "very often these improved models and their increased performance on these benchmarks do not really transfer into better performance on real world problem."
- "[R][D] The Disconnect Between AI Benchmarks and Math Research" ([1jjn3v6], Mar 2025, +79): "Current AI systems boast impressive scores on mathematical benchmarks. Yet when confronted with the questions mathematicians actually ask in their daily research, these same systems often struggle, and don't even realize they are struggling." u/LowPressureUsername (+16): "They struggle with high school math. It's wild." u/idontcareaboutthenam: "the big companies aren't trying to help mathematicians, but develop a product… There's a lot more families with kids trying to cheat on their math homework."
- u/meister2983 ([124eyso], +14): "GPT-4 is an extremely good pattern matcher — probably one of the best ever made. Most exams made seem to be able to executed with straight-forward pattern matching… It struggles at logical reasoning (when it can't 'pattern match' the logical reasoning to something it's trained on)."
- u/teleprax ([1lrnruz]): "I generally don't trust the popular benchmarks a ton because they are either trained for or the specific things being tested isn't the best representation of what I want/need out of an LLM."
- The exam-format complaint itself: u/Terrible_Button_1763 ([18ntia7]): "It's a bit interesting to define smartness as having a large database of facts to query."

### 1.8 Saturation and ceiling effects

- [163xzkz] OP: as models approach 100%, residual benchmark errors dominate the signal — saturation makes MMLU deltas meaningless at the top.
- The saturation frame is old here: "SuperGLUE [is] saturated, now what?" ([ph38tr], Sep 2021) predates ChatGPT; by Aug 2025 the framing has inverted — "[D] Unsaturated Evals before GPT5" ([1mjtm98]) hunts for anything left with headroom.
- u/Beginning-Ladder6224 ([1daa68e]): "A much more logical and slowly gaining opinion is that the LLMs have plateaued" (citing arXiv 2404.04125) — saturation read as a property of the models and the tests simultaneously.

### 1.9 Human-preference arenas measure style and the median voter, not capability

- u/osmarks ([1i83mhj], +3): "It was always somewhat problematic anyway, in that the median user has wrong opinions, is quite sensitive to style and does not really push the limits of the models."
- u/KallistiTMP ([1anr0hm], +2), defending arenas as least-bad while conceding the ambiguity: "a high ranking could mean more factual accuracy, or it could mean it's better at long context, or it could mean it's better at generating consistently wankable furry waifu dialogue. Which on one hand is kinda useless for any narrow use case."
- u/iamephemeral ([1anr0hm]): "The law of large numbers applicability to accuracy here is only correct if you believe that the full population of humans would converge on the truth — which is not an assumption I take."

### 1.10 Closed models mean unverifiable, irreproducible evaluation

- [1lrnruz] documents the concrete failure: vendor-claimed SoTA numbers (Gemini 2.5 Pro on YouCook2, GPT-4.1 on Video-MME) that appear on no third-party leaderboard and can't be reproduced.
- "Why can't I reproduce benchmark scores from papers like Phi, Llama, or Qwen? Am I doing something wrong?" ([1kws2jt], May 2025) — reproduction failure is common enough to be a recurring beginner question.
- u/st8ic ([124eyso], +9), on defenders saying the model is great regardless: "'bro it's great trust me' isn't exactly a scientific way to think about these issues."
- u/mocny-chlapik ([1breffe], +8): "there was even a paper that showed that LLMs tend to have worse performance on benchmarks that were released after they were trained."

### 1.11 The community's operational response: trust nothing public, build private evals

The most-upvoted comment in the "benchmarks making models worse" thread is not a defense of benchmarks but a private-eval prescription — u/Mysterious-Rent7233 (+112): "You should have your own, private benchmarks and not go based on vibes. The ChatGPT subreddit is full of people claiming that ChatGPT is getting better or worse over time and they are all just going based on vibes… As part of my job, I have benchmarks and cannot detect any degradation."

- u/LelouchZer12: "Best way to evaluate is to a totally new or private benchmark."
- OP of [1breffe] (an applied researcher): "performing our own evaluation is the way to go rather than blindly trusting academic benchmarks."
- u/PSMF_Canuck ([1daa68e]): "I pay no attention to the benchmarks. None of them. The only metric that matters to me is… does it do what I need it to do."
- u/I_will_delete_myself ([1daa68e]) states the resulting dilemma: "Kind of have to keep it secret with what you test though or everyone optimizes it. But if you don't have it open you don't get good feedback from the community. Kind of a catch 22."
- Tooling for this is a recurring ask ([1lrnruz]): promptfoo, HuggingFace YourBench, crowdsourced eval-sharing databases.

### 1.12 Prehistory: leaderboard cynicism predates LLMs

"[D] How the Transformers broke NLP leaderboards" ([cfn4bu], Jul 2019, +249) contains the whole modern debate in miniature: compute-buys-SOTA ("nobody is going to spend $250,000 just to repeat XLNet training"), leaderboard-hero worship, and gaming: u/FirstTimeResearcher (+35): "Don't hate the players, hate the game… 1. Don't measure progress based on static metrics. 2. Look at the mistakes the top models tend to make. 3. Make new metrics that amplify these mistakes. 4. Go back to step 1." The article author (u/annargrs, Anna Rogers) in-thread: "we should NOT automatically award all the hype to the leaderboard heroes. If participation gets completely out of the price range of most researchers, we're going to enter a google-beats-google cycle." Goodhart threads ([bvwocv], 2019) and "A Critique of NLP Leaderboards" ([j43nl5], 2020) round out the lineage: none of the LLM-era complaints are new to this community; the money made them louder.

---

## 2. What r/MachineLearning says would make a benchmark trustworthy / flagship-grade

Stated directly or strongly implied across the threads above:

1. **Held-out, genuinely private test sets, administered by a neutral entity.** "The only way forward is to either have an updated benchmarks every few months or to have a reliable entity that will have a hidden benchmark that is not accessible to the LLM developers" (u/mocny-chlapik, [1breffe]). Scale's SEAL ("you can only score once") cited approvingly in [1daa68e].
2. **Refresh/rotation against contamination decay.** Post-cutoff problem sets (the Codeforces pre/post-Sept-2021 test in [124eyso] is the community's model of a *convincing* contamination probe); LiveBench named as the trusted alternative after the arena rigging ("All hail livebench").
3. **Contamination defenses that are actually verified.** Canary strings and password-protected distribution (GPQA, [1817hk8]) — but the community immediately notes their limits: "New LLMs will just include this in their training data right?" (u/KevinCola). Decontamination tooling (LM-Sys LLM Decontaminator) and published contamination reports ([17kvdhk]) as trust-builders; dedup standards stronger than "exact duplicate text" ([124eyso], StellaAthena).
4. **Robustness to trivial perturbation.** Rankings that survive answer-order/format changes ([1anr0hm]); reported variance and uncertainty, not single point scores ([1di354e]); interpretable deltas (error-rate framing, [13e1rf9]).
5. **Expert-vetted, error-audited items** — wrong or ambiguous answers destroy signal precisely when models approach the ceiling ([163xzkz], [18ntia7]); domain experts should have vetoed items ([18ntia7]'s lawyer).
6. **Granular reporting, not one marketing number.** Per-subject accuracies (Hendrycks, [13e1rf9]); per-task breakdowns.
7. **Neutral multi-party governance with manipulation resistance not premised on good faith.** "Some form of mutli-company-and-university-wise consortium [sic] for proper model evaluation that don't rely on good faith, and make it hard to identify models" (u/Ouitos, [1i83mhj]) — with universities in the loop against cartels, or an independent evaluation firm on the DXOMark model; no unlimited private variants, no retractable scores, equal sampling ([1kbug62]); defenses demonstrated publicly, not asserted (gwern, [1i83mhj]).
8. **Independent reproduction of vendor claims.** Third-party leaderboards that actually list new models promptly; numbers a student can verify ([1lrnruz], [1kws2jt]); open eval code and data.
9. **Ecological validity.** Tasks drawn from real work (real research questions in [1jjn3v6]; real paid engineering tasks in the $1M benchmark study [1isbo6t]) rather than exam-style multiple choice, which the community regards as pattern-matching bait ([124eyso], [18ntia7]).
10. **Statistical soundness as a first-class property.** The community's own summary of the status quo: test-set usage in DL "was never statistically correct or sound" (u/new_name_who_dis_, [1kbug62]) — a flagship benchmark is expected to do better.

The cynicism floor to design against: a nontrivial fraction of r/ML believes *no* public number survives contact with incentives — "everyone in ml community already knows benchmark scores should be treated with a grain of salt" ([1kbug62]) — and the only trusted eval is the one you built yourself and never published ([1daa68e], [1breffe], [1lrnruz]).

---

## 3. Representative quotes

1. "OpenAI blatantly ignored the norm to not train on the ~200 tasks collaboratively prepared by the community for BIG-bench. GPT-4 knows the BIG-bench canary ID afaik… they genuinely don't care about academic research standards or benchmarks carefully created over years by other folks." — u/mlresearchoor, +92, [124eyso]
2. "if it can only solve problems that it has seen before, then it's nothing special, they just overfit a trillion parameters on a comparatively very small dataset." — u/TheEdes, [124eyso]
3. "As a creator of MMLU, I really wish they reported per-subject accuracies." — u/DanielHendrycks (MMLU author), +87, on Google burying PaLM 2's MMLU results, [13e1rf9]
4. "MMLU is a completely bogus and unreliable test." — u/ski233, [1anr0hm]
5. "I am a practicing lawyer licensed in the U.S. Some of the legal questions, I do not think the MMLU's answer is correct (at least not in my jurisdiction)." — u/ObiWanCanownme, +32, [18ntia7]
6. "You should have your own, private benchmarks and not go based on vibes." — u/Mysterious-Rent7233, +112 (top comment), [1daa68e]
7. "Companies are incentivized to push for higher numbers for PR reasons." — u/shadowylurking, +15, [1daa68e]
8. "Phi is one of the worse models in terms of benchmark overfitting/data contamination. Only Anthropic, OpenAI and Deepmind seem to systemically avoid this issue." — u/meister2983, [1daa68e]
9. "Always in favor of Google model and always against OpenAi model… at one point I've generated 10% to 30% of OpenAI vs Google votes." — u/Aplamis's LMArena vote-rigging confession, [1i83mhj]
10. "Goodhart's Law at its best. Hopefully… there will be some form of mutli-company-and-university-wise consortium [sic] for proper model evaluation that don't rely on good faith, and make it hard to identify models." — u/Ouitos, +16, [1i83mhj]
11. "the median user has wrong opinions, is quite sensitive to style and does not really push the limits of the models." — u/osmarks on LMArena voters, [1i83mhj]
12. "It's funny that this is a technical paper but I think everyone in ml community already knows benchmark scores should be treated with a grain of salt. It's like VCs and investors pouring billions of dollars into some startup based on these benchmarks." — u/new_name_who_dis_, on The Leaderboard Illusion, [1kbug62]
13. "So am I supposed to 'just blindly trust' the very company that trained the model that it is the best without any secondary source? That doesn't seem very scientific to me." — OP, [1lrnruz]
14. "'bro it's great trust me' isn't exactly a scientific way to think about these issues." — u/st8ic, [124eyso]
15. "a high ranking could mean more factual accuracy, or it could mean it's better at long context, or it could mean it's better at generating consistently wankable furry waifu dialogue." — u/KallistiTMP on what arena Elo actually measures, [1anr0hm]
16. "I need to be more careful how I interpret the results of public benchmarks like this that were otherwise my gold standard. All hail livebench." — u/HelloFellow8, after the arena-rigging confession, [1i83mhj]

---

## 4. Sources (threads opened, OP + comments read)

| ID | Date | Score | Cmts | Title | URL |
|---|---|---|---|---|---|
| 124eyso | 2023-03-28 | 925 | 139 | [N] OpenAI may have benchmarked GPT-4's coding ability on it's own training data | https://www.reddit.com/r/MachineLearning/comments/124eyso/ |
| 13e1rf9 | 2023-05-10 | 343 | 88 | [D] Since Google buried the MMLU benchmark scores in the Appendix of the PALM 2 technical report… | https://www.reddit.com/r/MachineLearning/comments/13e1rf9/ |
| 163xzkz | 2023-08-28 | 14 | 2 | [D] MMLU having many questions with wrong answers? | https://www.reddit.com/r/MachineLearning/comments/163xzkz/ |
| 1817hk8 | 2023-11-22 | 38 | 3 | [R] GPQA: A Graduate-Level Google-Proof Q&A Benchmark | https://www.reddit.com/r/MachineLearning/comments/1817hk8/ |
| 18ntia7 | 2023-12-21 | 82 | 46 | [D] Deep dive into the MMLU ("Are you smarter than an LLM?") | https://www.reddit.com/r/MachineLearning/comments/18ntia7/ |
| 1945r8k | 2024-01 | 74 | 10 | Task contamination: LLMs might not be few-shot any more | https://www.reddit.com/r/MachineLearning/comments/1945r8k/ |
| 1anr0hm | 2024-02-10 | 76 | 10 | [R] Skeptical about LLM benchmarks telling the whole story? …tiny tweaks to tests like MMLU can shuffle model rankings | https://www.reddit.com/r/MachineLearning/comments/1anr0hm/ |
| 1breffe | 2024-03 | 4 | 2 | [D] Are LLM Benchmark Results Trustworthy? | https://www.reddit.com/r/MachineLearning/comments/1breffe/ |
| 1daa68e | 2024-06-07 | 48 | 36 | [D] Is it me or does it seem like benchmarks are making language models worse? | https://www.reddit.com/r/MachineLearning/comments/1daa68e/ |
| 1fjxy6j | 2024-09-18 | 1 | 0 | [D] What stops SWE-bench leaderboard from being gamed? | https://www.reddit.com/r/MachineLearning/comments/1fjxy6j/ |
| 1i83mhj | 2025-01-23 | 55 | 36 | LM arena public voting is not objective for LLM evaluation [D] | https://www.reddit.com/r/MachineLearning/comments/1i83mhj/ |
| 1ic5961 | 2025-01-28 | 0 | 5 | [D] Deepseek R1 cheating benchmarks? | https://www.reddit.com/r/MachineLearning/comments/1ic5961/ |
| 1jjn3v6 | 2025-03-25 | 79 | 8 | [R][D] The Disconnect Between AI Benchmarks and Math Research | https://www.reddit.com/r/MachineLearning/comments/1jjn3v6/ |
| 1kbug62 | 2025-04-30 | 35 | 2 | [R] The Leaderboard Illusion | https://www.reddit.com/r/MachineLearning/comments/1kbug62/ |
| 1kdf8jw | 2025-05-02 | 0 | 5 | [D] The leaderboard illusion paper is misleading and there are a lot of bad takes because of it | https://www.reddit.com/r/MachineLearning/comments/1kdf8jw/ |
| 1lrnruz | 2025-07-04 | 1 | 5 | [D] How trustworthy are benchmarks of new proprietary LLMs? | https://www.reddit.com/r/MachineLearning/comments/1lrnruz/ |
| cfn4bu | 2019-07-20 | 249 | 50 | [D] How the Transformers broke NLP leaderboards | https://www.reddit.com/r/MachineLearning/comments/cfn4bu/ |
| 16unoo7 | 2023-09-28 | 0 | 1 | How do we know OpenAI released benchmarks aren't being heavily optimized… (removed by automod) | https://www.reddit.com/r/MachineLearning/comments/16unoo7/ |

Adjacent threads identified (titles/OPs read, comments thin or pending): [16zoh3s] Hacking an NLP benchmark: How to score 100 points on AMR parsing (2023); [17kvdhk] Open-sourced Data Contamination Reports for Llama Series Models (2023); [1kws2jt] Why can't I reproduce benchmark scores from papers like Phi, Llama, or Qwen? (2025); [1kdabbd] [R] Leaderboard hacking (2025); [ph38tr] SuperGLUE saturated, now what? (2021); [bvwocv] Goodhart's law: are academic metrics being gamed? (2019); [j43nl5] A Critique of NLP Leaderboards (2020); [1mjtm98] [D] Unsaturated Evals before GPT5 (2025); [1di354e] [R] Quantifying Variance in Evaluation Benchmarks (2024); [1isbo6t] [R] Evaluating LLMs on Real-World SWE Tasks: A $1M Benchmark Study (2025).
