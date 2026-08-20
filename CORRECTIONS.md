# Corrections ledger

Every material error in this benchmark's construction, scoring, or campaign
conduct is published here, newest first. Nothing on this list was silently
patched: each entry links a full report stating what happened, what it
contaminated, the decision rule used to void or retain data, and the
mechanical change that prevents recurrence. Radical transparency is a design
feature: an instrument that claims near-zero label error must audit itself in
public, before outsiders do.

| ID | Date | Scope | One line | Status |
|---|---|---|---|---|
| [CORR-013](runs/corrections/CORR-013/CORR-013.md) | 2026-08-19 | tool sandbox | **Credential compromise.** `run_python` inherited the harness environment, so models that printed `os.environ` read four live provider keys - written into 26 episode records and returned to Google, OpenAI, Anthropic and DeepSeek as conversation context. Found by the pre-release audit one step before publication. Sandbox now gets an allow-listed environment with a secret-name deny-check, the leak gate scans distributed data and not just git-tracked files, records are redacted, and tests fail if either mechanism regresses. Anthropic/OpenAI/OpenRouter/NVIDIA keys require rotation. | contained; rotation pending |
| [CORR-012](runs/corrections/CORR-012/CORR-012.md) | 2026-08-18 | campaign 1.0.0 | Grok started on OpenRouter after `api.x.ai` rejected the supplied key; the key was in fact a MANAGEMENT key, and an inference key minted through it works. 236 gateway episodes ($31.51) voided content-blind (route, not results) and `grok-or` removed; Grok now runs direct on the full plan. A first stop command failed silently - shell quoting broke the task name and the errors went to Out-Null - so the run continued four hours past its cancellation; stops are now verified from a script file and voided spend counts against the ceiling. | closed |
| [CORR-011](runs/corrections/CORR-011/CORR-011.md) | 2026-08-18 | family gate | Random `access violation` / impossible-`TypeError` faults traced to the HOST, not the code: a 25-line pure-Python `sorted(key=lambda)` loop reproduces them and the rate drifts hourly. No recorded outcome affected (a dead process writes no file). Gate now runs one seed per child and charges a family only with failures that reproduce. | worked around; machine unresolved |
| [CORR-010](runs/corrections/CORR-010/CORR-010.md) | 2026-08-16 | campaign 3.0.0 | Benchmark saturated (frontier 94-100% vs single-digit target): prompts printed method recipes, answer menus and decoy hints; tolerances let wrong analyses pass. All six giveaway classes now rejected by build gates; results retained as measurements of the old instrument only. | fixed in 4.0 gates |
| [CORR-009](runs/corrections/CORR-009/CORR-009.md) | 2026-08-16 | campaign 3.0.0 | Lineup restricted to frontier systems (Gemma-4 removed mid-campaign per sponsor); 13 pre-decision outcomes moved out of the scored tree, retained for audit. | closed |
| CORR-008 (in [crucible/llm.py](crucible/llm.py) + [tests/test_spend_guard.py](tests/test_spend_guard.py)) | 2026-08-16 | spend control | The $100 OpenRouter spend guard summed a `cost_usd` field the code never recorded, so it read $0.00 through 1,151 calls (~$194). Costs now recorded per call; unreported costs estimated at the priciest tier, never $0; guard has tests that make it fire; default ceiling cut to the measured need ($30). | fixed, tested |
| [CORR-007](runs/corrections/CORR-007/CORR-007.md) | 2026-08-16 | campaign 3.0.0 | Six OpenRouter-hosted systems never reached a model (credit exhausted before launch); 336 outcomes voided content-blind; systems reported as "not evaluated", never as zero. Launcher now checks the balance before starting workers. | blocked on credit |
| [CORR-006](runs/corrections/CORR-006/CORR-006.md) | 2026-08-16 | Marigold harness | Marigold's 13/28 was driven by false alarms (8/10 clean controls); prompt iterations v2/v3 reached 24-25/28 under identical grading. Documented as a harness-sensitivity result, not a capability claim. | closed |
| [CORR-004](runs/corrections/CORR-004/CORR-004.md) | 2026-08-16 | grading 1.0.0 | Verifier brittleness found by adversarial probe; v1.0.3 shipped and every submission in the campaign rescored under the fixed grader. | closed |
| [CORR-003](runs/corrections/CORR-003/CORR-003.md) | 2026-08-15 | campaign 1.0.0 | 31 runs voided content-blind for infrastructure failures (provider billing refusals + harness kills); denominators reduced, decision rule published. | closed |
| [CORR-002](runs/corrections/CORR-002/CORR-002.md) | 2026-08-15 | campaign 1.0.0 | Marigold host saturated by a co-tenant job mid-campaign; affected runs voided, product re-hosted from the same lockfile, load guard added. | closed |
| CORR-001 ([release/0.2.0/corrections.md](release/0.2.0/corrections.md)) | 2026-08-15 | grading 0.2.0 | Verifier pointer-fragment bug; fixed and rescored. | closed |

Numbering note: CORR-005 was reserved and never issued; CORR-008 was
documented in code and tests at fix time and is summarised here rather than
in a separate report directory.

## Standing decision rules

- **Content-blind voiding only.** A run is voided only for a failure that is
  independent of its content (billing refusal, host kill, grader bug affecting
  all runs equally). No outcome-dependent selection has occurred in any
  campaign.
- **Void, don't delete.** Voided outcomes move to the correction's directory
  and stay auditable.
- **"Not evaluated" is never rendered as a score.** A blank invites the
  reader to infer failure; tables must say "not evaluated - CORR-xxx".
- **Retained-but-reframed.** When the instrument itself is found defective
  (CORR-010), its measurements are retained as measurements of that
  instrument, with the defect stated at the top of every scorecard that
  reports them.

## Audit log — discriminant tripwires investigated (not corrections)

The standing rule is that a large cross-system gap is evidence about OUR key
until proven otherwise. Every tripwire that has fired, and its verdict:

| Family | Signal | Verdict |
|---|---|---|
| admet-filter | Claude 1/14 vs GPT 15/26 | **Our defect.** The verifier required the reason text to name exactly one criterion, failing a correct answer that also mentioned the constraint it satisfied. Now anchored on the recomputed offending value. 64 episodes re-run. |
| split-leakage | GPT 0/27 | **Genuine.** The brief defines CANNOT_DETERMINE explicitly; GPT abstained on the numbers yet answered NOT_SUPPORTED, and built a holdout sharing scaffolds with training — the exact leakage error the family tests. No change. |
| assay-qc | Gemini 0.44 vs Claude 0.96, GPT 0.93 | **Genuine.** Gemini submits cleanly (18/19) and fails on the recomputed IC50 in 15 cases, averaging ~4 tool calls where the analysis needs more. A capability difference, not a scoring artifact. |
| conformer-energy | Gemini 0.59 vs GPT 1.00 | **Genuine, same shape** as assay-qc: clean submissions, wrong recomputed values. No change. |
| assay-mechanism / pose-triage / lead-opt | free-text scored as a hedge | **Our defect, twice.** "quenching, not inhibition" read as claiming inhibition; a regex fix passed in isolation and failed in situ. Replaced with literal negated-phrase removal. |

A single system underperforming is a capability finding. Two systems
CONVERGING on the same non-key answer is a key defect. Only the first pattern
appears in assay-qc and conformer-energy; the second produced every entry
above marked "our defect".
