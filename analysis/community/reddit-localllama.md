# Community Discourse: r/LocalLLaMA on Benchmark Distrust

**Venue:** Reddit r/LocalLLaMA (the largest practitioner community for open-weight/local LLMs)
**Researched:** 2026-08-16. Method: direct thread retrieval via Reddit mirror (search + full comment pages), 31 threads opened and read; thread dates span Nov 2023 - Aug 2026. All URLs below are canonical reddit.com links.
**Character of the venue:** practitioners who download weights and run them the same day. They treat vendor benchmark tables as marketing until independently reproduced, and "benchmaxxed" is default vocabulary — it appears in thread titles, flairs, and even jokes ("Qwen is Finno-Ugricmaxxing", "Countries trying to benchmax GDP lmao"). The cynicism is not fringe; it is the community's baseline posture.

---

## 1. Distinct complaint patterns

### 1.1 Benchmaxxing / Goodhart's law: scores are optimized at, not earned

The foundational complaint: any public benchmark becomes a training target and dies. Goodhart's "when a measure becomes a target, it ceases to be a good measure" is quoted *verbatim* across three years of threads — by u/amroamroamro (Nov 2023, rephrased-test-set thread), as the title thesis of "LLM Leaderboards are Bullshit — Goodhart's Law Strikes Again" (Mar 2024, 204 pts), and again by u/Mashic in the Apr 2026 SWE-bench thread. It is the community's liturgy.

- "Confirmed: SWE Bench is now a benchmaxxed benchmark" (Apr 2026, 460 pts) — reacting to OpenAI's "Why we no longer evaluate SWE-bench Verified" post. Top reply, u/Velocita84: **"The final destination for any public benchmark, unfortunately."**
- "With no update in 4 months, livebench was getting saturated and benchmaxxed" (Apr 2025) — even LiveBench, *designed* to resist contamination via refresh, is treated as compromised the moment refreshes lag.
- The 2024 Goodhart thread walks the graveyard: GLUE, SuperGLUE, Winograd, HellaSwag, PIQA — "models quickly achieved SOTA on those benchmarks while still being dumb as rocks."
- The pattern is now priced in at every release: "How Benchmaxxed is gpt-oss-120b?" (Aug 2025), "Qwen 3.8 max is really 56 points or benchmaxxed?" (Aug 2026), "in other words benchmaxxed" — the question is asked *before* anyone has evidence, because the prior is that high scores are suspect by default.

### 1.2 "Wins the benchmarks, loses reality" — high scores, dumb in practice

The single most common experiential complaint: the model that tops the chart feels lobotomized in real work, and the model the charts rank mid feels smart.

- "I'm starting to think ai benchmarks are useless" (Jan 2025, 470 pts): OP's agents work best on Claude, which "is usually beat in benchmarks by OpenAI and Google models." u/foo-bar-nlogn-100: **"I stopped trusting benchmarks when [the new OpenAI model] was still shit at coding my projects... my lived experience was that it was not much greater at coding."**
- "Benchmarks are a lie, and I have some examples" (Feb 2025, 172 pts): a model author (u/Sicarius_The_First) shows his own un-gamed 8B outscoring the beloved Midnight Miqu 70B across the HF eval board — "It's not even close. Midnight Miqu is orders of magnitude better than ANY 8B model." Kicker: he removed 8 of 40 layers from a Phi-4 finetune ("literally lobotomized it") and its IFEval went *up*. "The high benchmarks are randomly high... almost no correlation to actual 'organic' smarts."
- "Qwen 3.6 wins the benchmarks, but Gemma 4 wins reality" (May 2026, 102 pts): "Since official benchmarks are pretty much gamed at this point, I threw real-world, unoptimized junk at them... Benchmaxing seems real."
- u/hyperdynesystems (Feb 2025): "These models aren't nearly as good as they claim on paper in the benchmarks IMO, none of em."
- u/ArchdukeofHyperbole (Mar 2026): "I've used benchmaxxed ai, fell for them lots of times... **You could tell within a few minutes that they weren't really that smart tho.**" — the "feel" test is treated as more sensitive than the score.
- u/vorwrath (Aug 2026): "it's not like I can really tell the difference between a model that scores 50 points on a benchmark and one that scores 60... don't get an unlucky roll in the **hallucination casino**."

### 1.3 Contamination: the test set is in the training set (and rephrasing hides it)

- Canonical thread: "Training on the rephrased test set is all you need: 13B models can reach GPT-4 performance in benchmarks with no contamination detectable by traditional methods" (Nov 2023, 236 pts). u/a_beautiful_rhind: "Stuff like this is how shitty models top the leaderboard and actual good models languish."
- "Imagine if we gave high school students the same test 4 years in a row" (Apr 2024, 248 pts) — call for MMLU v2; u/Hugi_R's fatalism: "It takes weeks or months of work to make a benchmark... it takes only 1 day for a cheater to train on the test set. It's a losing battle."
- Perturbation-sensitivity is cited as the smoking gun. u/CumDrinker247 (Jan 2025): **"There was a paper that showed that even simply shuffling the questions of common benchmarks leads to significantly worse scores. Benchmarks that find their way into the training data aren't worth paying attention to."** u/EverythingGoodWas, same thread: **"I demonstrated during my Master's that rewording benchmark questions lead to dramatically reduced scores, however misspelling several words but keeping the order and wording the same did not. These things get vastly overtrained on benchmarks."**
- Community folk-tests rot the same way: u/mrjackspade (Mar 2024): "Sally's sisters isn't a valid test of model intelligence. You can find the same problem and answer solution verbatim on hundreds of sites... Stop testing models with riddles." By Apr 2026 the same fate hits the community's own "car wash test": u/Interesting-Print366: "Car wash vibe check got so famous and I believe some of model learned it from its learning stage."
- u/Tight_Range_5690 (Mar 2024) on contaminated riddle-variants: "Somehow the contamination fries the neurons so badly that they proudly declare that 2 > 1 > 2."

### 1.4 The scandals: Reflection 70B, Llama 4 on LMArena, FrontierMath

Three named events function as the community's proof-by-example that distrust is warranted, and get invoked as shorthand years later.

- **Reflection 70B (Sep 2024).** "Independent eval results: We have been unable to replicate the eval results claimed" (709 pts). Top comment (u/ArtyfacialIntelagent) is effectively the community's trust checklist: stop the "dog-ate-my-homework claims," "post reproducible methodology used for the original benchmarks," "demonstrate that they were not caused by benchmark contamination," "prove that their model is superior also in real world applications, and not just in benchmarks and silly trick questions." Companion PSA thread (528 pts): creator hadn't disclosed his investment in GlaiveAI, the data vendor he credited — u/_raydeStar: "If this was a stock or crypto, I would peg it as a pump and dump and pass." The phrase "Reflection 70B vibes" is now reusable slander (e.g., "Manus turns out to be just Claude Sonnet + 29 other tools, Reflection 70B vibes ngl", Mar 2025).
- **Llama 4 / LMArena (Apr 2025).** "lmarena.ai confirms that meta cheated" (334 pts): Meta submitted an "experimental" Maverick tuned for human preference; the released weights were a different model. "The Llama4 on LMArena and the open Llama4 are TOTALLY different models" (115 pts) shows the arena version producing a multi-page emoji-laden answer to "Who are you?" — u/dubesor86: "Probably a system prompt specifically to game arena style voting... the rankings there were completely alien when I compared to my own testing." Meanwhile "Llama 4 Maverick scored 16% on the aider polyglot coding benchmark" (313 pts) — u/davewolfs: "What the fuck Zuck"; u/PhilosophyforOne: "Marketing is powerful, but you know that people will benchmark these independently in a few days, and you'll get shit on."
- **FrontierMath (Jan 2025).** "OpenAI has access to the FrontierMath dataset; the mathematicians involved in creating it were unaware of this" (737 pts). The lab funding the "independent" benchmark had the data; the promised holdout set didn't exist yet. This thread is where the shuffling/rewording contamination quotes above appear — funder access and contamination are treated as one disease.
- **The Leaderboard Illusion (Apr 2025).** "New study from Cohere shows Lmarena... is heavily rigged" (530 pts): Meta tested 27 private variants and retracted all but the winner; big labs get ~40% of battle data. u/thezachlandes: "They are literally bench maxing and not disclosing it... smaller labs can't bench max in the same way. That's an unfair playing field." Notable: the thread contains real pushback (u/-p-e-w-: "rigged" overstates it; unequal exposure ≠ manipulated rankings) — the community argues about *degree*, not about whether gaming happens.

### 1.5 Human-preference arenas measure slop appeal, not competence

Post-Llama-4, LMArena went from "the one benchmark you can't train on" to a case study in optimizing for raters.

- u/boxingdog: "this also proves lmarena is almost a worthless eval." u/jugalator: "that response is what people vote for?? ... **The people voting are actually overwhelmingly dumb as bricks.**" u/guyinalabcoat: "Do people just vote for long responses regardless of how much of it is just fluff?"
- u/killver (Feb 2025): "The issue is that companies figured out how to overfit to lmsys benchmark. Like with many other benchmarks."
- The defense exists too: "Unpopular opinion. The chatbot arena benchmark is not useless, rather it is misunderstood... it measures 'what if the LLM would answer common queries for search engines'" (Feb 2025); u/-p-e-w- argues optimizing for user preference is a legitimate target, and u/AlanCarrOnline notes the Llama 4 ejection cuts both ways: "Or, it proves they'll kick even Meta out if cheating."
- As early as Apr 2024 (MMLU-v2 thread), u/TNTOutburst flagged both failure modes at once: arena conversations are public ("for models to be trained and overfitted on") and "the arena has too much of an incentive towards sounding good rather than being intelligent."

### 1.6 LLM-as-judge is a hack's methodology

- "Can we finally agree that creative writing benchmarks like EQBench are totally useless?" (Aug 2025, 99 pts): "All this shows is which AI writing appeals to another AI... Imagine GPTslop as a judge." Reply meme: "ObamaGivingObamaMedal.jpg". u/nonerequired_: **"using LLMs as judges is not an appropriate benchmark for anything."**
- "The LLM world is an illusion of progress" (Aug 2025, 307 pts) applies it to Humanity's Last Exam: "the answers provided by LLMs are evaluated by... another LLM. This introduces bias and makes the results non-reproducible. How can we trust a benchmark where the judge is as fallible as the models being tested?"
- "Your unpopular takes on LLMs" (Jul 2025, 582 pts), OP: "Any ranker who has an LLM judge giving a rating to the 'writing style' of another LLM is a hack who has no business ranking models... Stop wasting carbon with your pointless inference."
- Nov 2024 (coding-leaderboard thread), u/Ralph_mao already asking: "proLLM is using gpt4 as the judge, will this give openai models an advantage?"
- Counterpoint (u/Lakius_2401, EQBench thread): the bench is redeemable *because every generated transcript is published* — "you can go drill down and see the entire corpus of work that is being scored... all the capability to do it yourself is right there." Transparency of raw outputs, not the score, is what buys the residual trust.

### 1.7 Private-eval culture: never publish your questions

The community's institutional response to contamination is secrecy as hygiene. Personal benchmarks with undisclosed prompts are a respected genre of post.

- u/dubesor86, "Small scale personal benchmark results (28 models tested)" (Jul 2024): 83 tasks from his own life, categories and difficulty-weighted scoring disclosed, prompts not: **"I am not going to share my exact prompts as them leaking into any training sets would render them as a test tool useless."** (His dubesor.de bench is repeatedly cited by others as more trustworthy than public leaderboards.)
- u/pr1vacyn0eb (Nov 2023): "Yep, its why I never give it feedback on my tests. I just mix it in randomly with 50 other questions." — practitioners actively obfuscate against providers harvesting API traffic.
- u/_sqrkl (EQ-bench author, Apr 2024): "I have a private set for eq-bench that I test models with if their result looks sus on the public set." — even benchmark authors run shadow sets to police their own public set.
- "Your unpopular takes" OP: "No one but hobbyists has enough integrity to keep their benchmark questions private? Bleak."
- The advice given to every newcomer asking "which benchmark can I trust": u/relmny (Jul 2026): **"Nothing beats your own benchmarks. Come up with your own real life scenarios and nothing will be as accurate as that."** u/its_just_andy (Nov 2023): "you really should build your own evaluation dataset for the scenarios you care about... all the public benchmarks are such a mess." u/Unlucky-Message8866 (Jan 2025): "simply by writing your own benchmarks against your particular use cases."

### 1.8 Vibes-based evals: the fallback everyone uses and half distrusts

Every model release generates "vibe check" threads within 48 hours — small idiosyncratic probes standing in for dead public benchmarks.

- The genre: "V4-Flash-0731 — vibes after first weekend of use" (Aug 2026, 204 pts: "wanted to share my vibes... I sent it through a bit of real-work and some of my personal benchmarks"); "My Qwen 3.6 fails the car wash vibe check" (Apr 2026); u/Goldandsilverape99: "I usually vibe check a model with the Resonance Chamber puzzle in Indiana Jones and the Great Circle"; mastermind/bulls-and-cows probes ("A little reasoning and coherence test," Apr 2025); the strawberry/riddle family.
- The community knows vibes are contaminable (car wash test learned in training, §1.3) and biased. u/obvithrowaway34434 (Jan 2025), pushing back on the "benchmarks are useless" OP: "That's not a benchmark... this shows why good benchmarks are essential. They help others to cut through these fanboy bs." u/ThaisaGuilford: "OP basically said 'Benchmarks are wrong because I like Claude'."
- Self-correction from within: "I stopped 'vibe-checking' my LLMs and started using a weighted rubric" (Mar 2026): "that trap where you read a few samples and think 'yeah this sounds smarter' but then you don't realize your hallucination rate just spiked 30% because you were only looking at the tone."
- And the reductio, delivered half-seriously in the 582-pt unpopular-takes thread (u/xoexohexox): **"The only meaningful benchmark is how popular a model is among gooners. They test extensively and have high standards."** — upvoted and seconded ("all the real good info comes from these communities... people that have tested the fuck out of their models"). RP/ERP power users are considered harder to fool than leaderboards because they run long-context, instruction-heavy, adversarial sessions daily.

### 1.9 Community benchmarks are the trusted alternative — until they saturate too

The community continuously builds its own evals, then watches each one decay, and has internalized the lifecycle.

- Aider's benchmark: "Aider has released a new much harder code editing benchmark since their previous one was saturated" (Dec 2024, 224 pts). Even here, instant suspicion — u/MikeLPU: "I believe these benchmarks are bullshit"; u/boxingdog: "also if the questions are public they are useless"; u/femio after reading the repo: "I clicked on 5 random questions for JS and they're all the equivalent of Leetcode easy's lol."
- Misguided Attention (community eval of reasoning under misleading cues, u/cpldcpu): update post explicitly frames community contributions as needed "to fight saturation of the benchmark."
- SimpleBench, used to accuse gpt-oss of benchmark training ("scored rank 34... worse than grok 2", 191 pts), gets attacked in its own thread — u/Accomplished_Ad9530: **"That benchmark is more sus than any benchmaxxed model"** — with commenters listing its absurd orderings (Llama 4 Maverick above Claude 3.5 Sonnet, GPT-4 Turbo above GPT-4o).
- The frontier of community design (Apr 2026 SWE-bench thread) is anti-gaming architecture: u/Deep90: "benchmarks need to be seeded or have a private counterpart. Have a public seed so that people can independently verify... then private seeds only the benchmarking website knows. If results drop, then you know a model was overfit." u/iperson4213's sharpening: "Private bench isn't sufficient, **the data needs to be sourced privately as well**" (SWE-Bench-Pro's private questions still come from public repos). u/pm_me_github_repos's counter-cynicism: "posttraining can be applied on any signal, including private scoring. So one could still hill climb on a private dataset as long as you can [get] a score." u/Luke2642 (Jul 2026) on swe-rebench: "They can't cheat this, testing is done by release cut off date."
- Other community instruments cited as more trustworthy than lab tables: LiveBench (while fresh), EQ-bench (because transcripts are public), farel-bench, FamilyBench, FoodTruckBench (seeded), dubesor.de, personal 70-real-repo evals ("Qwen 3.5 craters on hard coding tasks — tested... on 70 real repos so you don't have to").

### 1.10 Benchmarks measure a narrow, wrong slice (and one number is a lie)

- Goodhart thread OP: "You can't boil down something as complex and multifaceted as language understanding to a single number. Yet that's exactly what leaderboards attempt to do."
- "Illusion of progress" OP: GPQA covers three subjects; English-only evals speak for "about 20% of the world's population"; deterministic settings still yield non-deterministic outputs, so point-comparisons are "an illusion"; agentic results don't disclose which tools/harness ("we constantly get benchmarks of models with tools, but which tools? What context?... The whole enchilada is a fucking mess; benchmarks can't be trusted" — comment).
- What benchmarks miss, per practitioners: hallucination rate under real context ("o3-mini... will constantly make shit up, is poor at instruction following, and has a bad context recall" — u/master-killerrr), long-context collapse ("maverick collapses at 3k" — u/BriefImplement9843; "the attention degenerates at 20k context" — u/SmartCustard9944), multilingual quality (u/tomakorea: "Qwen is pretty bad [for European languages], even the larger versions"), refusal/censorship behavior (dubesor scores it; Gemini scoring *negative* on his reasoning category due to refusals — "And people pay to use that kind of model?"), quantization sensitivity (community KLD tests: "Quantization hits this thing like a truck... it behaves like an entirely different model").
- u/sometimeswriter32 (Mar 2024): "unless riddles generalize to useful tasks like coding, summarizing, roleplaying, what the heck is the point? The only intelligence you're testing for is riddle solving."

### 1.11 Incentives are rotten and everyone knows it

- "benchmarks are useless" OP: labs "are absolutely incentivised to do it [overfit]" and "we can never be sure."
- Undisclosed financial interest (Reflection/GlaiveAI PSA), vendor-run leaderboards judged by the vendor's own model (proLLM/GPT-4), lab-funded "independent" benchmarks (FrontierMath), private variant testing for the rich (Cohere study), launch-stream chart gushing (Llama 4).
- The community turns it on itself too: "Why are people so quick to say Closed frontiers are benchmaxxed while they gulp this [Qwen chart] without any second thought?" (Mar 2026) — u/Technical-Earth-3254: "I'm calling overfitted bullshit on closed and open source. Especially for small models (<10B) that 'beat' full models in whatever. It's just cap and hinders development for real tasks." u/hieuphamduy on benchmark-hype accounts: "those accounts earn money by farming clicks and impressions."
- Score-vs-cost cynicism, u/laterbreh (Aug 2026, on Qwen 3.8 Max): "HEY MAN 6 POINTS IS 6 POINTS. Needing 2.4T parameters to barely clear a 300B model is a dogshit exchange rate. Cope accordingly."

---

## 2. What this community implies a trustworthy / flagship-grade science benchmark looks like

Assembled from what they praise, demand, and build; the strongest signals come from the Reflection checklist (1fbclkk), the SWE-bench post-mortem (1swfdbj), and the private-eval culture:

1. **Held-out data with a public verification slice.** Public seed/subset so anyone can reproduce; private counterpart(s) whose scores are compared against the public slice — divergence is the overfit alarm (u/Deep90's public/private seeds; u/hapliniste's "benchmarking institute with private test sets"; u/_sqrkl's shadow set; Scale's public/private SWE-bench-Pro cited approvingly).
2. **Privately *sourced*, not just privately held.** If tasks derive from public artifacts (open repos, textbooks), the answers are trainable even when questions are secret (u/iperson4213). Fresh tasks post-training-cutoff are the gold standard ("They can't cheat this, testing is done by release cut off date" — swe-rebench).
3. **Perturbation robustness as an explicit test.** The community's own evidence standard for contamination: shuffle question order, reword, rename entities, reparameterize — a real capability survives; a memorized one collapses (CumDrinker247's shuffling paper; EverythingGoodWas's reword-vs-misspell experiment; u/opi098514 "just adapt the riddle... many won't get it"; u/Briskfall: replacing names with CHARACTER1/CHARACTER2 "makes the model dumber"; u/IrisColt tweaks numeric parameters; seeded task generation à la FoodTruckBench). *This is the single most PERTURB-Bench-relevant norm in the venue: perturbation deltas are already this community's home-grown contamination detector.*
4. **Independent execution, never self-reported.** Scores count when a third party runs the released artifact (Artificial Analysis re-running Reflection; independent aider runs of Llama 4 within days). Test the shipped weights/endpoint, version-pinned — the LMArena "experimental variant" trick is the canonical sin. No funder access to items (FrontierMath), disclosed conflicts of interest (GlaiveAI), equal rules for all vendors (no 27-private-variants privilege), and public ejection of cheaters (LMArena booting Llama-4-experimental is the one thing that *raised* trust).
5. **Reproducible methodology, open harness, full config disclosure.** "Post reproducible methodology" is line one of the Reflection checklist. Community results are expected to state quant, inference engine, flags, template — half the gpt-oss "benchmaxxed" fight dissolved into a chat-template parsing bug (1mntn9u), and they know it.
6. **Real tasks over trick questions.** Real repos, real documents, agentic/tool use with the harness specified, long-context under load — "not just in benchmarks and silly trick questions" (Reflection checklist); "70 real repos so you don't have to"; riddles explicitly disqualified.
7. **No LLM-as-judge for headline claims — or radical transparency if unavoidable.** Deterministically scorable tasks preferred; if judged, publish every transcript so humans can audit (the only reason EQ-bench retains defenders).
8. **Multi-dimensional reporting, not one number.** Category breakdowns (dubesor's reasoning/STEM/utility/censorship split), difficulty weighting, style-controlled variants, refusal counts scored as failures.
9. **Statistical honesty.** Report noise and treat small deltas as noise ("within statistical noise of each other" — u/returnity; "can't tell the difference between a model that scores 50 and one that scores 60" — u/vorwrath); decompose which sub-score drives a headline rank (Tau3-banking driving Qwen 3.8 Max's index, per 1vgtq3y comments).
10. **A maintenance covenant.** Continuous refresh/rotation with versioned releases; a benchmark whose updates stop is presumed saturated within months (LiveBench thread). Saturation is expected and must be designed for, not denied.
11. **Coverage beyond English one-shots.** Multilingual performance and multi-turn/long-context behavior are where "wins benchmarks, loses reality" gaps live (1ml77rq; 1t1te8y comments).

The implicit meta-criterion: **trust is earned by surviving hostile replication.** This community's flagship-grade signal is not a score — it's "independent people ran it, perturbed it, and it held up."

---

## 3. Representative quotes (verbatim unless noted)

1. **"The final destination for any public benchmark, unfortunately."** — u/Velocita84, on SWE-bench being abandoned by OpenAI as gamed ("Confirmed: SWE Bench is now a benchmaxxed benchmark," Apr 2026).
2. **"When a measure becomes a target, it ceases to be a good measure."** — Goodhart's law, quoted verbatim by u/amroamroamro (Nov 2023), the "LLM Leaderboards are Bullshit" OP (Mar 2024), and u/Mashic (Apr 2026). Three years, same liturgy.
3. **"A model can be in practice almost orders of magnitude smarter than the rest, yet people will ignore it because of low benchmarks. There might be somewhere in hugging face a real SOTA model, yet we might just dismiss it due to mediocre benchmarks."** — u/Sicarius_The_First, "Benchmarks are a lie, and I have some examples" (Feb 2025), after showing a layer-removed ("lobotomized") model scoring *higher* on IFEval.
4. **"I am not going to share my exact prompts as them leaking into any training sets would render them as a test tool useless."** — u/dubesor86, personal-benchmark thread (Jul 2024). The private-eval culture in one sentence.
5. **"All the popular public benchmarks are nearly worthless when it comes to a model's general ability... No one but hobbyists has enough integrity to keep their benchmark questions private? Bleak."** — OP of "Your unpopular takes on LLMs" (Jul 2025, 582 pts).
6. **"There was a paper that showed that even simply shuffling the questions of common benchmarks leads to significantly worse scores. Benchmarks that find their way into the training data aren't worth paying attention to."** — u/CumDrinker247, FrontierMath thread (Jan 2025). Companion: **"rewording benchmark questions lead to dramatically reduced scores, however misspelling several words but keeping the order and wording the same did not. These things get vastly overtrained on benchmarks."** — u/EverythingGoodWas, same thread.
7. **"Stop making nonsensical dog-ate-my-homework claims... Post reproducible methodology used for the original benchmarks. Demonstrate that they were not caused by benchmark contamination. Prove that their model is superior also in real world applications, and not just in benchmarks and silly trick questions."** — u/ArtyfacialIntelagent, top comment on the Reflection 70B replication failure (Sep 2024, 709 pts).
8. **"This also proves lmarena is almost a worthless eval."** / **"The people voting are actually overwhelmingly dumb as bricks."** — u/boxingdog and u/jugalator, "lmarena.ai confirms that meta cheated" (Apr 2025).
9. **"Benchmarks need to be seeded or have a private counterpart... If results drop, then you know a model was overfit."** — u/Deep90; with u/iperson4213's refinement: **"Private bench isn't sufficient, the data needs to be sourced privately as well."** (Apr 2026).
10. **"Nothing beats your own benchmarks. Come up with your own real life scenarios and nothing will be as accurate as that."** — u/relmny, answering "I am tired of benchmaxxed numbers" (Jul 2026).
11. **"The only meaningful benchmark is how popular a model is among gooners. They test extensively and have high standards."** — u/xoexohexox, unpopular-takes thread (Jul 2025); seconded: "all the real good info comes from these communities."
12. **"That benchmark is more sus than any benchmaxxed model."** — u/Accomplished_Ad9530, on SimpleBench being used to call gpt-oss benchmaxxed (Aug 2025). Distrust is fully recursive: even the anti-benchmaxxing benchmarks are suspected of being bad measures.
13. **"I've used benchmaxxed ai, fell for them lots of times... You could tell within a few minutes that they weren't really that smart tho."** — u/ArchdukeofHyperbole (Mar 2026).
14. (Tight paraphrase) *Every release now gets a vibes thread instead of a scores thread: "wanted to share my vibes... I sent it through a bit of real-work and some of my personal benchmarks."* — OP, "V4-Flash-0731 — vibes after first weekend of use" (Aug 2026, 204 pts).

---

## 4. Sources (threads opened and read)

Core distrust / benchmaxxing:
- https://www.reddit.com/r/LocalLLaMA/comments/1i4vwm7/im_starting_to_think_ai_benchmarks_are_useless/ (Jan 2025, 470 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1iwn617/benchmarks_are_a_lie_and_i_have_some_examples/ (Feb 2025, 172 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1bjvjaf/llm_leaderboards_are_bullshit_goodharts_law/ (Mar 2024, 204 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1swfdbj/confirmed_swe_bench_is_now_a_benchmaxxed_benchmark/ (Apr 2026, 460 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1m0z1zx/your_unpopular_takes_on_llms/ (Jul 2025, 582 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1ml77rq/the_llm_world_is_an_illusion_of_progress/ (Aug 2025, 307 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1t1te8y/qwen_36_wins_the_benchmarks_but_gemma_4_wins/ (May 2026, 102 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1rj0mxt/why_are_people_so_quick_to_say_closed_frontiers/ (Mar 2026)
- https://www.reddit.com/r/LocalLLaMA/comments/1mntn9u/how_benchmaxxed_is_gptoss120b/ (Aug 2025)
- https://www.reddit.com/r/LocalLLaMA/comments/1miupht/gpt_oss_is_heavily_trained_on_benchmark_scored/ (Aug 2025, 191 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1vgtq3y/qwen_38_max_is_really_56_points_or_benchmaxxed/ (Aug 2026)

Contamination:
- https://www.reddit.com/r/LocalLLaMA/comments/17v6kp2/training_on_the_rephrased_test_set_is_all_you/ (Nov 2023, 236 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1c2ff0m/imagine_if_we_gave_high_school_students_the_same/ (Apr 2024, 248 pts)

Scandals:
- https://www.reddit.com/r/LocalLLaMA/comments/1fbclkk/reflection_llama_31_70b_independent_eval_results/ (Sep 2024, 709 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1fb1h48/psa_matt_shumer_has_not_disclosed_his_investment/ (Sep 2024, 528 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1ju5aux/lmarenaai_confirms_that_meta_cheated/ (Apr 2025, 334 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1jsnfus/the_llama4_on_lmarena_and_the_open_llama4_are/ (Apr 2025, 115 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1jt4asx/llama_4_maverick_scored_16_on_the_aider_polyglot/ (Apr 2025, 313 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1i50lxx/openai_has_access_to_the_frontiermath_dataset_the/ (Jan 2025, 737 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1kb6bbl/new_study_from_cohere_shows_lmarena_formerly/ (Apr 2025, 530 pts)

Arenas / LLM-as-judge:
- https://www.reddit.com/r/LocalLLaMA/comments/1ij4c7h/unpopular_opinion_the_chatbot_arena_benchmark_is/ (Feb 2025)
- https://www.reddit.com/r/LocalLLaMA/comments/1mlsos9/can_we_finally_agree_that_creative_writing/ (Aug 2025, 99 pts)

Private evals / vibes culture:
- https://www.reddit.com/r/LocalLLaMA/comments/1dxfw72/small_scale_personal_benchmark_results_28_models/ (Jul 2024)
- https://www.reddit.com/r/LocalLLaMA/comments/1txuoya/gemma_4_12b_q4_k_xl_private_benchmark_results/ (Jun 2026)
- https://www.reddit.com/r/LocalLLaMA/comments/1rk17h6/i_stopped_vibechecking_my_llms_and_started_using/ (Mar 2026)
- https://www.reddit.com/r/LocalLLaMA/comments/1vee1ob/v4flash0731_vibes_after_first_weekend_of_use/ (Aug 2026, 204 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1sn8t4a/my_qwen_36_fails_the_car_wash_vibe_check/ (Apr 2026)
- https://www.reddit.com/r/LocalLLaMA/comments/1jqeahi/a_little_reasoning_and_coherence_test_with/ (Apr 2025)

Community alternatives:
- https://www.reddit.com/r/LocalLLaMA/comments/1hl5ntq/aider_has_released_a_new_much_harder_code_editing/ (Dec 2024, 224 pts)
- https://www.reddit.com/r/LocalLLaMA/comments/1jsagyr/with_no_update_in_4_months_livebench_was_getting/ (Apr 2025)
- https://www.reddit.com/r/LocalLLaMA/comments/1ilc325/updated_misguided_attention_eval_to_v03_4x_longer/ (Feb 2025)
- https://www.reddit.com/r/LocalLLaMA/comments/1utrrmi/what_are_some_best_benchmark_for_the_llm_like_i/ (Jul 2026)
- https://www.reddit.com/r/LocalLLaMA/comments/1gve7cw/what_leaderboard_do_you_trust_for_ranking_llms_in/ (Nov 2024)

Referenced within threads (not independently opened): Cohere "The Leaderboard Illusion" (arxiv.org/abs/2504.20879), OpenAI "Why we no longer evaluate SWE-bench Verified", aider.chat/2024/12/21/polyglot.html, labs.scale.com/leaderboard/swe_bench_pro_public, foodtruckbench.com/methodology, swe-rebench.com, dubesor.de.

---

*Fidelity note: quotes are transcribed from thread pages as rendered; a few usernames are crude and kept as-is because the register is part of the finding. The cynicism above is not exaggerated — it is the venue's median tone. The most actionable pattern for PERTURB-Bench: this community already treats perturbation sensitivity (shuffle/reword/rename/reseed) as its de-facto contamination test, and treats "survives hostile independent replication" as the only score that matters.*
