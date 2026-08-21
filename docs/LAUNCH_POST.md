# Announcement copy

Written in the register of OpenAI's LifeSciBench announcement: third person,
present tense, one fact per sentence, numbers inline, no first-person narration
and no build-up. Works as a blog post or as a single long X post with the links
in the comments below it.

Post one needs a paid X account. Every number is recomputed from the published
episodes.

---

**Main post**

Introducing MarigoldBench, a benchmark for measuring how well AI can run a
computational drug discovery lab and produce a result that survives being
checked.

MarigoldBench includes 30 task generators, three conditions per task, a belt of
eleven scientific tools, and 4,935 recorded episodes across seven frontier
models. The generators fabricate their own data and therefore know every answer,
so the grader recomputes each physical and statistical claim from the artifact a
model submits rather than scoring what the model says it did.

The tools are structure prediction, protein design, docking, generative
chemistry, RDKit and a Python sandbox.

The best model, Grok 4.6, passed 63.2 percent of episodes. The full table is in
the chart.

Half of the 30 task types are harder than the other half. On the hard half,
scores drop to between 15.6 and 38.5 percent. Claude Opus 5 and Grok both get 88
percent on the easy half, and on the hard half Claude gets 27 percent and Grok
gets 39.

Each task ran three times. Counting only the tasks a model passed all three
times, Gemini 3.1 Pro drops from 48.9 to 32.6 percent and Grok from 63.2 to 52.2.

The hardest task type is spotting leakage between training and test data. The
best of the seven models gets 11 percent.

The benchmark has limits that bear on how these numbers should be read. It
carries 30 task types where the statistics call for 100, the confidence
intervals of the top five models overlap, and three of the seven models ran a
reduced plan for budget reasons. A pre-release audit found four problems in the
benchmark's own claims, including a reasoning-effort setting that favoured two
models in the lineup, and all four are published alongside the results.

MarigoldBench is available under Apache 2.0, including the 30 generators and
their verifiers, all 4,935 transcripts, the scorer and the audit. Links are in
the comments.

*(attach fig01_headline.png)*

---

**Comment 1**

Code, the generators and the audit: github.com/rasynai/MarigoldBench

All 4,935 episodes with full transcripts:
huggingface.co/datasets/rasynai/MarigoldBench

*(attach fig06_cost_accuracy.png)*

---

**Comment 2**

The three conditions are indistinguishable to the model. In the first, the
reported problem is a false alarm and raising it fails. In the second, a real
defect changes the answer. In the third, no answer exists and only a stated
refusal passes.

*(attach fig02_refusal.png)*

---

**Comment 3**

One finding concerned the benchmark rather than the models. The tool sandbox
passed the parent environment to model-authored code, so a model printing
os.environ could read the provider API keys. Caught before release, keys
rotated, sandbox restricted, tests added.

*(attach fig07_hardest.png)*

---

## Posting notes

- Answer every reply, in the thread, within the first hour.
  `reply_engaged_by_author` is its own scored label in X's ranking code,
  separate from `reply`. Details in `docs/X_ALGORITHM_NOTES.md`.
- The main post is what gets screenshotted. The results sit near the top so a
  crop still carries them.
- Do not attach two charts of the same shape in a row. Media is deduplicated by
  visual cluster.
- Credit the people who did the work in a final comment, by handle so they get
  the notification.
