# Reproducing MarigoldBench

One command runs the development split end to end. Everything a sceptic needs
to disagree with us is here, including how to find a wrong key and what happens
when you do.

## Requirements

- Python 3.11+ with `rdkit`, `numpy`, `scipy`, `scikit-learn`, `torch`,
  `pandas`, `openai`, `anthropic`, `google-auth`
- Credentials in `.secrets/keys.env` (never committed):
  - `NVIDIA_API_KEY` — the hosted structural-biology tools (free tier)
  - `OPENAI_API_KEY` and/or Google ADC for the candidate you want to run
  - `GOOGLE_CLOUD_PROJECT` if using Vertex

## 1. Verify the instrument before trusting any score

```bash
python runs/validate_families.py
```

Re-derives the whole baseline ladder for every family × seed × condition:
the family's own reference submission must complete it (B8), an empty
submission must fail every instance (B1), C0/H1 briefs must be byte-identical,
and no scored field may be constant across the population. A family that fails
any rung is reported unusable and is excluded from the campaign allow-list —
which is generated from this output, so it cannot drift from what passed.

Expect `USABLE FAMILIES: n/n`. Anything less is a bug in the release.

## 2. Confirm the tools are reachable

```bash
python runs/probe_bio_nims.py     # hosted tools, live probe
python runs/probe_gemini.py       # Gemini credentials, if using it
```

A tool is only in the belt if a live call succeeded. Tool responses are cached
under `runs/toolcache/`, so a rerun replays identical bytes and scoring never
depends on a live service.

## 3. Run the development split

```bash
python -m crucible.lab.campaign run --system gpt --budget-usd 5 --limit 10
```

`--budget-usd` is enforced from recorded per-call usage, re-read from disk
before every episode so parallel shards share one ceiling. `--limit` caps the
episode count. Restart-proof: an existing outcome file is never re-run, so a
killed worker loses nothing.

For the full sharded campaign:

```bash
python runs/launch_lab.py --shards 8 --systems gpt,gemini
python runs/launch_lab.py --stop        # end everything
```

## 4. Score

```bash
python -m crucible.lab.scorecard
```

Writes `runs/lab-1.0.0/scorecard.md` and `summary.json`. Read the
family-clustered interval, not the naive Wilson one: episodes inside a family
share a generator and are not independent evidence.

## 5. Verify the sealed-split commitment

```bash
python -m crucible.commitment verify --label <campaign-label>
```

Before each campaign, every sealed file is hashed with a private salt and only
the manifest digest is published. Releasing the salt afterwards proves the
sealed instances scored are byte-identical to those committed to before any
candidate ran — no post-hoc swaps, no quiet regeneration.

## 6. How to find a wrong key, and what we owe you if you do

The dominant failure mode of a constructed-truth benchmark is a generator and
verifier that share one wrong scientific assumption: they agree perfectly and
are both wrong. Three of ours have already been found this way.

The cheapest detector, which you can run yourself:

```bash
python -m crucible.lab.scorecard      # then read the by-family table
```

Any family where two different frontier systems converge on the same non-key
answer, or where one frontier system scores near zero while another scores
well, is evidence about **our key** until proven otherwise. Inspect the stored
detail:

```python
import json, glob
for f in glob.glob('runs/lab-1.0.0/systems/*/outcomes/<family>*.json'):
    d = json.load(open(f, encoding='utf-8'))
    print(d['run_id'], d['checkpoints'], d['detail'])
```

Every outcome carries the recomputed values the verdict was based on, the full
tool transcript, and the model's own reasoning. If the recomputation is wrong,
it is visible there.

Report it and we publish it in `CORRECTIONS.md` with the fix and the affected
episode count — that is the standing commitment, and the ledger already
contains the errors that cost us money.
