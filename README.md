# MarigoldBench

**A model is handed a working computational drug-discovery lab and measured on
whether it drives that lab to a defensible result.**

Structure prediction, protein design, docking, generative chemistry, RDKit and a
Python sandbox. Eleven tools, a step budget, a brief, and a deterministic
verifier that **recomputes every physical and statistical claim from the
submitted artefact**. Nothing the model says about its own work counts as
evidence.

Seven frontier systems, 4,935 recorded episodes, every transcript published.

Dataset and full results: **https://huggingface.co/datasets/rasynai/MarigoldBench**

![Accuracy](figures/house/fig01_headline.png)

| System | n | Pass@1 | 95% CI (family-clustered) | Pass^3 |
|---|---|---|---|---|
| Grok 4.6 | 810 | **63.2%** | [51.7, 74.2] | 52.2% |
| GPT-5.6 Sol | 810 | 58.3% | [46.2, 70.1] | 49.6% |
| Claude Opus 5 | 810 | 57.9% | [45.2, 70.1] | 45.9% |
| DeepSeek V4 Pro | 270 | 51.1% | [40.0, 61.5] | - |
| Gemini 3.1 Pro | 810 | 48.9% | [39.1, 58.5] | 32.6% |
| GLM-4.7 | 270 | 31.9% | [23.0, 40.7] | - |
| Kimi K2 Thinking | 270 | 29.6% | [20.0, 40.0] | - |

**Read the intervals, not the ranking.** Episodes inside a task type share a
generator; the measured intraclass correlation is 0.40, so a naive binomial
interval is 2.9x too narrow. This release separates the top group from the
bottom two and **cannot** rank Grok, GPT and Claude against each other.

## How it works

**The answer key cannot be wrong.** Deterministic generators fabricate the data
and therefore know every answer, which puts label error near zero where every
other benchmark in the field carries 8 to 29 percent.

**Three conditions per task type, two of them byte-identical.**

- **Sound.** The reported concern is a false alarm; raising one is a failure.
- **Planted defect.** A real flaw that changes the answer, in a brief worded
  identically to the sound version.
- **Unanswerable.** The question cannot be answered as asked; a documented
  refusal with an explicit impossibility witness is the only correct outcome and
  silence scores zero.

**Anti-saturation is enforced.** An earlier version saturated at 94 to 100
percent because briefs printed method recipes and answer menus. That failure is
published in full, and the giveaway classes it identified are now rejected by
build gates.

## Layout

| Path | Contents |
|---|---|
| `crucible/lab/fam/` | The 30 task-type generators and verifiers, answer keys included |
| `crucible/lab/` | The frozen agent loop, the 11-tool belt, the campaign runner, the scorer |
| `runs/gate_families.py` | The gate that decides which task types may be scored |
| `runs/check_goal.py` | The 22 stop conditions for the release |
| `runs/_figures_house.py` | Every figure, regenerated from recomputed data |
| `docs/AUDIT.md` | Pre-release audit, including four defects found in our own claims |
| `docs/LIMITATIONS.md` | What these numbers cannot support |
| `CORRECTIONS.md` | Every material error in construction, scoring or conduct |
| `GOAL.md` | The stopping contract this release was built against |

Episode records live with the dataset on Hugging Face, not here.

## Reproducing

```bash
pip install -e .                  # Python >= 3.11
python runs/gate_families.py      # must read 30/30 before anything is scored
python -m crucible.lab.scorecard  # rebuild the scorecard from the episodes
python runs/check_goal.py         # 22/22 stop conditions
```

Running new episodes needs provider credentials and a free NVIDIA NIM key for
the structural-biology tools. `docs/REPLICATION.md` pins the versions.

## Read the audit first

[`docs/AUDIT.md`](docs/AUDIT.md) recomputes every published number with code
written for the audit rather than the code that produced it, and it leads with
what it found wrong with us: the card advertised six integrity gates where four
are mechanically enforced; the intraclass correlation was quoted as 0.26 and is
0.40; the hard-task band is selected on the episodes it then scores; and
reasoning effort was set high for Claude and GPT and left at each provider's
default for the other five. Grok still finished first without it.

Security note: the tool sandbox now runs model-authored code with an
allow-listed environment. It did not always, and models that printed
`os.environ` read the harness's provider keys. Found by this audit one command
before publication, fixed, tested, and written up as CORR-013. If you build an
agent harness, pass `env=` to your sandbox.

## CRUCIBLE-CHAIN

The sibling track in this repository, evaluating scientific reasoning under
attractive error as a chain of 5 to 8 judgment calls where every stage offers a
plausible wrong path. It keeps its own name, its own gates and its own
corrections; see `crucible/chain/` and the CORRECTIONS ledger.

Apache-2.0. The literature PDFs used in the design review are not redistributed;
the synthesis notes under `analysis/` are ours.
