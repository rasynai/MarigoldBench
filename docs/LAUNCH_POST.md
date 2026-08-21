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
eleven scientific tools, and 4,923 recorded episodes across seven frontier
models. The generators fabricate their own data and therefore know every answer,
so the grader recomputes each physical and statistical claim from the artifact a
model submits rather than scoring what the model says it did.

The tools are structure prediction, protein design, docking, generative
chemistry, RDKit and a Python sandbox.

The best model, Grok 4.6, passed 64.6 percent of episodes, then Claude Opus 5 on
61.0 and GPT-5.6 Sol on 58.9. The full table is in the chart.

Half of the 30 task types are harder than the other half. On the hard half,
scores drop to between 19.3 and 41.5 percent. Claude gets 92 percent on the easy
half, the highest of the seven, and 30.4 on the hard half, the fifth highest.

Each task ran three times. Counting only the tasks a model passed all three
times, Gemini 3.1 Pro drops from 49.9 to 33.1 percent and Grok from 64.6 to 54.0.

The hardest task type is spotting leakage between training and test data. The
best of the seven models gets 11 percent.

The benchmark has limits that bear on how these numbers should be read. It
carries 30 task types where the statistics call for 100, the confidence
intervals of the top five models overlap, and three of the seven models ran a
reduced plan for budget reasons.

Every number above is a corrected number. Reading the transcripts found three
defects in the benchmark and none in the models: the tool sandbox confined the
file tool and not the interpreter, so 371 episodes reached the network and one
read the grader for its own task; a checkpoint read a ruled-out explanation as a
claim, which failed 51 of 53 correct answers in one task type; and the submit
handler dropped 73 of Claude's answers and none of GPT's. All three are fixed,
everything is re-scored, 12 episodes are voided, and Claude moved from 57.9 to
61.0 percent, which changed second place. Seven problems in our own claims are
now published alongside the results.

MarigoldBench is available under Apache 2.0, including the 30 generators and
their verifiers, all 4,923 transcripts, the scorer and the audit. Links are in
the comments.

*(attach fig01_headline.png)*

---

**Comment 1**

Code, the generators and the audit: github.com/rasynai/MarigoldBench

All 4,923 episodes with full transcripts:
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

Every defect we found was ours. The sandbox passed our environment to model
code, so a model printing os.environ read our provider API keys, and it also
left the network open: 371 episodes called out, 42 used one of those keys. Keys
rotated, audit hook installed, tests added.

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
