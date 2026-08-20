# Deep read: τ-bench (arXiv 2406.12045)

## Coverage ledger

| Item | Value |
|---|---|
| PDF | `A:/PERTURB-Bench/analysis/literature2/pdfs/2406.12045.pdf` (663,224 bytes, header `%PDF-1.5`) |
| Extracted MD | `A:/PERTURB-Bench/analysis/literature2/md/2406.12045.md` |
| Pages | 50 |
| Total chars | 129,791 |
| Total lines | 2,435 |
| Chars read | 129,791 (100%) |
| Chunk ranges read | L1–600, L600–1199, L1200–1819, L1820–2435 |
| Extraction fallback needed? | No (>15k chars; pypdf clean) |

Structure of the file by line range: title/abstract L1–17; §1 Intro L18–103; §2 Related work L104–138; §3 Benchmark formalism (POMDP, reward, pass^k) L139–274; §4 Construction + domains + characteristics L275–338; §5 Experiments/results/failure analysis L339–505; §6 Discussion L506–539; refs L543–625; NeurIPS checklist L627–662; §A additional results L663–678; §B construction (API code, full retail + airline policy text, data-gen code) L679–1151; §C retail data + 3 full trajectories L1152–2047; §D airline data + 1 full successful trajectory L2049–2435.

## Actual paper identity (as printed)

- **Title:** "τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains" — matches the assigned title. ID correct.
- **Authors:** Shunyu Yao*, Noah Shinn, Pedram Razavi, Karthik Narasimhan. Affiliation printed: **Sierra**. (* "Work done during internship.")
- **Venue:** "Preprint. Under review." arXiv:2406.12045v1 [cs.AI] 17 Jun 2024. NeurIPS-style checklist included (L627).
- **Code/data:** https://github.com/sierra-research/tau-bench (L41).

## Section-by-section notes with numbers

### Abstract / §1 Intro (L1–103)
Claim: existing agent benchmarks test neither human-user interaction nor domain-rule following. Three desiderata for deployment: (1) long-horizon interaction with humans *and* APIs to incrementally gather information, (2) accurate adherence to domain-specific policy, (3) consistency across millions of interactions. Headline numbers stated up front: gpt-4o function-calling gets ~61% (retail) / ~35% (airline) pass^1, and **pass^8 < 25%** on retail.

### §3 Formalism (L139–274)
Each task is a POMDP (S, A, O, T, R, U) with S = S_db ⊗ S_user, A = A_db ∪ A_user. Database state is hidden from both agent and user; only reachable via API tools. DB transition is **deterministic Python**; user transition is **stochastic** (LM sample). Episode ends when the user emits `###STOP###`.

- **User simulator:** `gpt-4-0613`, system-prompted with the task instruction, sees only the user↔agent dialogue — **not** the agent↔tool trace (L161–162). This is a deliberate information asymmetry.
- **Policy enforcement is deliberately split**: some restrictions are hard-checked in the API (e.g. payment ID not in profile → `"Error: payment not found"`), others are *not* enforced and the agent must self-apply them (e.g. baggage allowance by membership tier is only in the prose policy; the agent must compute `nonfree_baggages` itself). L153–158.
- **Reward:** `r = r_action × r_output ∈ {0,1}`. `r_action` = final DB state identical to the unique annotated ground-truth DB; `r_output` = required info strings appear as substrings in agent→user messages. Example: `["54.04", "41.64"]` substring check (L220, L233–243).
- **Admitted incompleteness of the reward** (L239–241): "r = 1 might be a necessary but not sufficient condition for a successful episode e.g., the agent might issue the return without explicit user confirmation, which violates the policy."
- **pass^k** (pass-hat-k): probability that **all** k i.i.d. trials succeed, unbiased estimator `E_task[ C(c,k) / C(n,k) ]`; pass@k is the complement form `1 − E_task[ C(n−c,k) / C(n,k) ]`. pass^1 = pass@1 = E[c/n] is the headline metric.

### Table 1 / §4 Construction (L251–297)
| | τ-retail | τ-airline |
|---|---|---|
| DB size | 500 users, 50 products, 1,000 orders | 500 users, 300 flights, 2,000 reservations |
| API tools | 7 write, 8 non-write | 6 write, 7 non-write |
| Tasks | **115** | **50** |

Total **165 tasks**. Non-DB APIs shared: `calculate`, `transfer_to_human_agents` (L697). 300 flights span 20 US cities.

Three construction stages:
1. **Manual design** of schema/APIs/policies, simplified from real counterparts; "a minimally realistic domain requires at least tens of schemas, APIs, rules."
2. **LM data generation**: gpt-4 writes a sampling script from one hand-made example entry; humans polish bugs; scalable ("we can sample 10,000 users if needed"). Full 130-line generator for the retail users DB is printed at L1018–1151.
3. **Manual task annotation + validation by agent runs**: write instruction → run gpt-4-turbo FC agent → inspect trajectory → tighten instruction until the outcome is provably unique. Figure 7 (L677): **each τ-retail task was run ≥40 gpt-4-turbo trials**, sorted by success rate, so zero/low-success tasks could be audited for annotation bugs.

The stated crux of construction (L288–290): "the key challenge is to ensure the user instruction leads to a unique database outcome. For example, if the preferred payment method is not specified, the user might answer differently and cause the final database to be different across trials."

### §4.2 Characteristics (L319–338)
Explicit "quantity for quality" trade: 165 tasks × many trials + pass^k beats a large one-shot set. Faithful rule-based evaluation replaces human judgment by making the DB outcome unique. Modular: new domains = new JSON + Python + Markdown policy.

### §5 Experiments (L339–417)
- **12 models**: gpt-4o, gpt-4-turbo, gpt-4-32k, gpt-3.5-turbo; claude-3-opus/sonnet/haiku; gemini-1.5-pro/flash; mistral-large, open-mixtral-8x22b; meta-llama-3-70B (via AnyScale). Small (7/13B) models excluded "due to the difficulty of the benchmark."
- **Scaffolds**: native function calling (FC) as the main method; text ReAct; Act-only ablation. Llama-3 evaluated via text-ReAct (no native FC). Explicitly *rejected* scaffolds: self-reflection ("unrealistic as real-world agents only have one chance to serve the user") and search/planning ("might be too slow to help a user in real time").
- **Run config**: ≤30 agent actions per task; agent temperature 0.0, user temperature 1.0; **≥3 trials per task** for Table 2.

Table 2 pass^1:

| Model | retail | airline | avg |
|---|---|---|---|
| gpt-4o | 61.2 | 35.2 | 48.2 |
| gpt-4-turbo | 57.7 | 32.4 | 45.1 |
| gpt-4-32k | 56.5 | 33.0 | 44.8 |
| claude-3-opus | 44.2 | 34.7 | 39.5 |
| mistral-large | 30.7 | 22.4 | 26.6 |
| claude-3-sonnet | 26.3 | 27.6 | 27.0 |
| mixtral-8x22b | 17.7 | 31.6 | 24.7 |
| gemini-1.5-flash | 17.4 | 26.0 | 21.7 |
| gemini-1.5-pro | 21.7 | 14.0 | 17.9 |
| claude-3-haiku | 19.0 | 14.4 | 16.7 |
| gpt-3.5-turbo | 20.0 | 10.8 | 15.4 |
| meta-llama-3-70B | 14.8 | 14.4 | 14.6 |

Average is weighted by domains, not tasks. **No confidence intervals or error bars are printed anywhere in the paper**, despite the checklist answering "[Yes]" to "Did you report error bars?" (L643–644). The only uncertainty signal is the pass^k curve and the ≥40-trial per-task plot.

- **Scaffold effect** (Fig 3): native FC > ReAct > Act for the GPT family; reasoning traces help text-format agents; adding a "think" *function* to FC agents "did not boost performance."
- **Reliability collapse** (Fig 4): gpt-4o at >60% pass^1 falls to **pass^8 < 25%** on retail. pass@k rises with k while pass^k falls — the two curves fan apart, which is the paper's central reliability picture.
- **Cost** (L414–417): retail, gpt-4o FC agent + gpt-4 user sim = **$0.38 agent + $0.23 user per task**; "running one trial per task costs around 200 dollars." **95.9% of agent cost is input tokens, 4.1% output** — dominated by the long system prompt (policy + function definitions).

### §5.2 Failure analysis (L418–505)
Sample: 115 gpt-4o FC retail trajectories, 1 trial each → 40 failures (pass^1 = 65.2% in this single-trial sample, vs 61.2% in Table 2). **4 of the 40 failures were annotation bugs (user-instruction typo/ambiguity) and were fixed**; the remaining 36 are genuine agent failures. Figure 5 breakdown (matching the % to the prose: 22.2+33.3 ≈ "~55%", partial = "19%"):
- Wrong info **33.3%** — omitted required info (tracking ID), wrong arithmetic (totals), or wrong info that causes the *user* to diverge.
- Wrong decision **25.0%** — misunderstands/ignores an ad-hoc policy rule, picks the wrong tool type.
- Wrong argument **22.2%** — right tool, wrong argument after failing to reason over the inventory.
- Partial resolution **19.4%** — compound requests only partly served; harder as ground-truth write count rises (Fig 6).

**Hallucinated identifiers, per retail task:** gpt-4o FC **0.46** tool calls with non-existent user/product/order/item IDs; gpt-3.5-turbo FC **2.08**; gpt-3.5-turbo Act **6.34**.

**Policy-ablation (Table 3, L464–468)** — remove the domain policy from the system prompt:
- retail: gpt-4o 61.2 → 56.8 (−4.4); gpt-3.5 20.0 → 14.5 (−5.5)
- airline: gpt-4o **33.2 → 10.8 (−22.4)**; gpt-3.5 10.8 → 9.6 (−1.2)

Interpretation given: on retail, models mostly succeed by commonsense tool use rather than actually consulting the policy; on airline, the ad-hoc rules are load-bearing for gpt-4o but gpt-3.5 "does not have the capacity to process complex airline rules." (Note the internal inconsistency: Table 3's un-ablated airline gpt-4o is 33.2 while Table 2 says 35.2.)

### §6 Discussion (L506–539)
Named limitations: instruction typos/ambiguity; user instructions lack domain knowledge (a realistic property — real users don't know the policy); user-simulator LM has limited reasoning/calculation/long-context/instruction-adherence (e.g. the simulated user rubber-stamps a lamp without checking features); need for more systematic uniqueness checks; policies could be more complex; more metrics (e.g. LM rule-following checks) could be added; annotation requires deep domain+agent expertise; and **"There is also some element of implicit bias during the task curation process since we use the gpt-4-turbo FC agent to tune the user's system prompt."**

### §B Appendix — policies and API code (L679–1151)
The full retail and airline policy documents are printed verbatim. Structurally instructive for MarigoldBench:
- Retail: mandatory authentication before anything; one user per conversation; explicit "yes" confirmation before any DB write; **"You should not make up any information or knowledge or procedures not provided from the user or the tools, or give subjective recommendations"**; at most one tool call per turn, never a tool call and a user message in the same turn; transfer to human "if and only if the request cannot be handled."
- Retail hard invariants: exchange/modify tools **callable once per order**; status gates (`pending` for cancel/modify, `delivered` for return/exchange); no product-type changes; gift card must cover the difference.
- Airline: ≤5 passengers per reservation; ≤1 certificate + ≤1 credit card + ≤3 gift cards; baggage free-allowance matrix over 3 membership tiers × 3 cabins (regular 0/1/2, silver 1/2/3, gold 2/3/3), $50 per extra bag; insurance $30/passenger; basic economy cannot be modified; cabin must be uniform across segments; bags can be added but not removed; insurance cannot be added after booking; passenger identities editable but not passenger count; compensation certificates $100×passengers (cancelled) / $50×passengers (delayed), and **"Do not proactively offer these unless the user complains … Do not compensate if the user is regular member and has no travel insurance and flies (basic) economy."**
- Twice, verbatim: **"The API does not check these for the agent, so the agent must make sure the rules apply before calling the API!"** — the environment deliberately leaves a class of rules unenforced so that violations are silently accepted and only caught at grading.
- The printed `exchange_delivered_order_items` implementation (L703–753) shows the guard style: string error returns ("Error: order not found", "Error: non-delivered order cannot be exchanged", "Error: insufficient gift card balance…"), and writes that sort item lists before storing (`sorted(item_ids)`) so that DB comparison is order-insensitive.

### §C/§D Appendix — trajectories (L1152–2435)
Four full transcripts, explicitly "not cherry-picked."
- **C.2.1 (Task 0, wrong decision):** agent exchanges one item, then the second exchange returns `"Error: non-delivered order cannot be exchanged"` (the order status already flipped to `exchange requested`). The agent then **misreads its own environment feedback** and escalates to a human with the summary "the order status is indeed 'delivered'" — a confident false report of environment state after a self-inflicted state change.
- **C.2.2 (Task 7, wrong argument):** user wants a *less bright* lamp with power-source preference AC > battery > USB. Ground truth is item `1569765161` (silver, **low**, AC). The agent proposes `5320792178` (black, **medium**, AC) — it satisfied the power-source preference but silently dropped the "less bright" constraint (medium == the original's brightness). Wrong-argument failures look completely fluent.
- **C.2.3 (Task 42, partial resolution):** ground truth requires 4 writes (two order-address fixes + user-address fix + item swap); the agent fixes only the order the user names and skips the second pending order. The *implicit* action ("all order addresses") is the one dropped.
- **D.2 (airline Task 0, success):** an 8-tool-call booking where the agent correctly infers JFK from "New York", re-searches after the user rejects pre-11am flights, applies the gold/economy 3-free-bag rule, and enforces the one-certificate rule against the user's stated preference for using two.

## Since this is a BENCHMARK

- **Task count:** 165 (115 retail + 50 airline), 2 domains.
- **Construction:** hand-designed schema/API/policy → gpt-4-generated data-sampling code (human-polished) → hand-written user instructions iteratively tightened against live gpt-4-turbo agent runs until the DB outcome is provably unique; ≥40 trials/task used as an annotation audit.
- **Verification:** programmatic diff of the final database JSON against a single annotated ground-truth state (`r_action`), ANDed with substring presence of required output values in agent→user text (`r_output`). No LM judge, no human rating, no trajectory matching — the agent may take any read actions and any dialogue path.
- **Scoring:** binary per episode; pass^1 headline; pass^k (all k trials succeed) for reliability; averages weighted by domain.
- **Scaffolding:** native function calling (primary), ReAct, Act; temperature 0.0 agent / 1.0 user; ≤30 agent actions; ≥3 trials/task.
- **Reported scores with uncertainty:** Table 2 above; best = gpt-4o 48.2 avg. **No CIs / std devs / error bars reported.** Reliability is expressed only through the pass^k curve (gpt-4o pass^8 < 25% on retail) and the ≥40-trial per-task success plot (Fig 7).
- **Contamination handling:** **none discussed.** Databases are synthetic and randomly generated (which incidentally lowers memorization risk), but there is no held-out split, no canary, no regeneration protocol, no discussion of the public GitHub release leaking tasks into future training sets. This is an unadmitted gap.
- **Cost per run:** $0.61/task in retail with gpt-4o FC + gpt-4 user sim ($0.38 agent, $0.23 user); "~200 dollars" for one trial per task as reported; 95.9% of agent spend is input tokens.

## Limitations — admitted vs unadmitted

**Admitted:** reward is necessary-not-sufficient (a policy-violating path can still score 1, e.g. writing without explicit confirmation); user instructions may carry typos/ambiguity (4/40 sampled failures were annotation bugs); the simulated user is weak at reasoning/arithmetic/long-context and rubber-stamps agent proposals; user instructions omit domain knowledge; curation is biased by using gpt-4-turbo FC as the tuning oracle; policies are simplified vs. reality; annotation is expensive and expertise-heavy; only 2 domains, both low-stakes commerce.

**Unadmitted / under-discussed:**
1. No contamination or data-freshness protocol despite a public repo.
2. No confidence intervals anywhere, though the checklist claims error bars were reported; with 50 airline tasks and 3 trials, differences of a few points among mid-tier models are not resolvable.
3. `r_output` is a **substring** check — "54.04" appearing anywhere in any agent message passes, including inside a wrong sentence or a hallucinated table; it can also be satisfied by a lucky echo of a tool result.
4. Unique-outcome enforcement is empirical (iterate until the annotators are "certain no ambiguities exist"), not proved; the 4 discovered annotation bugs were found only because a strong agent failed on them, so ambiguities that *no* tested agent trips over remain invisible.
5. The user simulator is a single model (gpt-4-0613) at temperature 1.0; there is no measurement of how much of the pass^k variance is agent stochasticity vs. user-simulator stochasticity — a benchmark whose reliability metric is partly measuring its own simulator's variance.
6. Judging the *agent* while the *user* is also an LM means an agent that manipulates or over-leads the simulated user is rewarded; no check on user-simulator capture.
7. Table 2 vs Table 3 disagree on the un-ablated airline gpt-4o number (35.2 vs 33.2), and §5.2's sampled retail pass^1 (65.2%) differs from Table 2 (61.2%) — small internal inconsistencies with no reconciliation.
8. No refusal/false-alarm condition: every task has a correct completion, so there is no measurement of over-refusal or of hallucinated action on infeasible requests (the closest proxy is `transfer_to_human_agents`, which is not separately scored).

## Implications for MarigoldBench

1. **Recompute the world state, not the transcript — and make the ground-truth state unique by construction.** τ-bench's whole trick is that a diverse trajectory space collapses onto one legal terminal database, so grading is a JSON diff, and the API sorts list fields (`sorted(item_ids)`) so equal states compare equal. MarigoldBench should adopt the same discipline at the artifact level: canonicalize the submitted artifact (e.g. sort/round/normalize a PDB's chain ordering, a SMILES string, an SDF pose, a metrics dict) *before* comparison, and design each task so exactly one artifact family passes the recomputed physical check. Wherever a task admits several legal outcomes, the τ-bench remedy is to over-specify the *task premise* (as they over-specify the user's payment preference) rather than to loosen the checker.
2. **Split rules into API-enforced and agent-enforced, and plant defects in the unenforced half.** The single most productive design choice in τ-bench is stated twice in the policy: "The API does not check these for the agent, so the agent must make sure the rules apply before calling the API!" That is exactly the planted-defect surface MarigoldBench needs — let the NIM/RDKit wrappers happily accept a DiffDock pose scored against the wrong receptor, an ESMFold pLDDT averaged over a masked region, a scikit-learn CV split that leaks scaffolds, or a Boltz-2 affinity read from a run whose input protonation was silently wrong. The tool returns 200 OK; only the harness's recomputation catches it. Conversely, keep a *few* rules hard-enforced (like τ-bench's "Error: payment not found") so the agent learns the environment sometimes speaks up, which makes silence on the unenforced rules genuinely misleading.
3. **Report pass^k, not just pass@1 — an 8-25% band on pass^1 can hide near-zero reliability.** gpt-4o's 61.2% pass^1 became <25% pass^8. For a non-compensatory VEC score across 8–25 tool calls, the per-step reliability implied by any given episode score is brutal, and single-trial scores will be dominated by luck. Budget ≥3 trials/task minimum (τ-bench's floor), and prefer τ-bench's unbiased estimator `E_task[C(c,k)/C(n,k)]` over ad-hoc "all runs passed" counts. This composes naturally with template-clustered CIs: cluster on template, and report pass^k *within* cluster so a template that passes once and fails three times cannot masquerade as half-solved.
4. **Use ≥40-trial per-task success curves as an annotation-bug detector before trusting any task.** τ-bench ran every retail task ≥40 times with gpt-4-turbo and audited the zero/low-success tail — that is how they found the 4/40 failures that were their own instruction bugs, not agent bugs. MarigoldBench should treat "no frontier model ever passes this task" as a *suspect-the-task* signal, not a difficulty trophy, and require a human to re-derive the ground truth for any family at 0% before it ships. The corollary caveat: this only surfaces ambiguities that some tested agent actually trips over, so also require an independent second annotator to re-derive the expected artifact from the prompt alone.
5. **Substring/threshold checks are the weak link — make the check reconstructive, not containment-based.** τ-bench's `r_output` passes if "54.04" appears anywhere in any agent message, which an agent can satisfy by dumping a tool result verbatim. For MarigoldBench, never score "the model reported RMSD < 2 Å"; instead re-load the submitted pose, recompute symmetry-corrected RMSD against the crystal ligand, and compare. Where a number must be reported, require it to match the harness's independently recomputed value within a tolerance *and* require the supporting artifact to exist and hash-match the run that produced it — otherwise the reported number and the artifact can drift apart with no penalty.
6. **Plant the four failure modes τ-bench actually measured, in lab form.** Their empirical distribution over 36 real failures gives a defensible prior for defect design: wrong info 33.3% (report the right kind of number, computed wrong — e.g. mean pLDDT over the whole chain when the task asked for the binder interface); wrong decision 25% (use the wrong tool for the regime — MolMIM optimization where the premise demands a scaffold-constrained GenMol run, or docking a covalent binder with DiffDock); wrong argument 22.2% (correct tool, one poisoned argument — wrong chain ID, wrong pocket center, wrong random seed reused across "independent" replicates); partial resolution 19.4% (compound request where an *implicit* sub-task is dropped — τ-bench's Task 42 fixed the named order's address and silently skipped the second one). Their Fig 6 result — success falls monotonically with the number of required write actions — argues directly for grading MarigoldBench episodes non-compensatively on the count of required irreversible steps, and for deliberately including families with 3–4 required writes.
7. **Count hallucinated identifiers as a cheap, model-discriminating side metric.** τ-bench's 0.46 vs 2.08 vs 6.34 non-existent-ID tool calls per task separated gpt-4o FC from gpt-3.5 FC from gpt-3.5 Act more sharply than the headline score did. MarigoldBench gets this for free: log every call referencing a non-existent PDB ID, UniProt accession, chain, residue index, ligand code, or output file path. It is a self-report-independent signal, it needs no ground truth, and it will discriminate models that all sit in the 5–40% VEC band.
8. **Design the flawed-premise condition to be one τ-bench cannot express — and grade escalation explicitly.** Every τ-bench task is completable; the only refusal-shaped affordance, `transfer_to_human_agents`, is never separately scored, so over-escalation and under-escalation are invisible. That is precisely the gap MarigoldBench's third condition fills. Learn from their C.2.1 trajectory though: the agent escalated with a *factually false* summary ("the order status is indeed 'delivered'") after its own write had changed the state. So score refusal on two axes — did it refuse, and was the stated reason the actual defect — otherwise a model that refuses everything with plausible boilerplate scores as calibrated. This is also the natural place to penalize false alarms on the sound control.
9. **Budget for the input-token tax, and expect a lab episode to cost ~5-20× a τ-bench episode.** τ-bench: $0.61/task, of which 95.9% of agent spend is *input* tokens because the policy document plus tool schemas ride in every turn. MarigoldBench's tool schemas (8 NIM services + RDKit/PyTorch/sklearn) plus any protocol document will be larger, episodes are 8–25 calls, and pass^k needs ≥3 trials. Two concrete consequences: (a) aggressively cache the static system prompt, since it is by construction identical across every trial of every task, and (b) treat prompt-caching as a benchmark-fairness variable to hold fixed across the three candidate models rather than an implementation detail.
10. **Fix the scaffold and justify the exclusions in print.** τ-bench standardized on native FC, showed FC > ReAct > Act, and explicitly excluded self-reflection ("real-world agents only have one chance") and tree search ("too slow"). MarigoldBench has an analogous and stronger argument: a wet-lab-shaped episode where a run costs GPU-minutes and an irreversible artifact is submitted once should forbid retry-after-seeing-the-grade scaffolds. State that rule up front, because otherwise a 5–40% band is trivially inflated by best-of-n against the harness's own checker.
11. **Beware measuring your own simulator's variance.** τ-bench never decomposes pass^k variance into agent stochasticity vs. gpt-4-0613 user-simulator stochasticity, so part of its reliability signal is noise it injected. MarigoldBench's tools are stochastic too (RFdiffusion seeds, DiffDock sampling, ESMFold determinism caveats). Pin and log every seed, and run a tools-only control — same seeds, scripted oracle trajectory, N repeats — to quantify the environment's own pass^k floor before attributing inconsistency to the model.

## Verbatim quotes

1. §3, Reward (L239–241): "Note that r = 1 might be a necessary but not sufficient condition for a successful episode e.g., the agent might issue the return without explicit user confirmation, which violates the policy. Nevertheless, our proposed rule-based reward is fast to compute and faithful, and already poses significant challenges for current models and methods as we show in § 5."

2. §4, Stage III (L288–291): "Here, the key challenge is to ensure the user instruction leads to a unique database outcome. For example, if the preferred payment method is not specified, the user might answer differently and cause the final database to be different across trials."

3. §4.2, Faithful rule-based evaluation (L332–334): "In τ-bench, we trade off slow, careful task annotation for fast, faithful evaluation. By ensuring that only one database outcome is possible based on domain policies and user desires, subjective and noisy human judgments can be replaced by simple and objective database state comparisons."

4. §B.1, Airline policy, Modify flight (L966–969): "Change flights: Basic economy flights cannot be modified. Other reservations can be modified without changing the origin, destination, and trip type. Some flight segments can be kept, but their prices will not be updated based on the current price. The API does not check these for the agent, so the agent must make sure the rules apply before calling the API!"

5. §5.1, Agent consistency (L409–413): "As shown in Figure 4, the chance of reliably and consistently solving the same task multiple times significantly drops as the number of trials k increases. Even for the best-performing gpt-4o function calling agent which has a > 60% average task success, pass^8 drops to < 25%."

6. §5.1, Cost analysis (L414–417): "When we pair gpt-4o FC agent with gpt-4 user simulation on τ-retail, the agent / user simulation costs are $0.38 / $0.23 per task respectively, so running one trial per task costs around 200 dollars. For the agent, the input prompt / completion output take up 95.9% / 4.1% of the price respectively, so the cost is mainly due to long system prompt (domain policy + function definitions)."

7. §6, Discussion (L528–530): "There is also some element of implicit bias during the task curation process since we use the gpt-4-turbo FC agent to tune the user's system prompt."

8. §5.2, Failure 1 (L447–449): "while gpt-4o FC agent only makes 0.46 tool calls with non-existent user/product/order/item IDs per τ-retail task, gpt-3.5-turbo FC / Act agents make 2.08 / 6.34, respectively."
