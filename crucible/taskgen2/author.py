"""Template authoring and cross-family review for CRUCIBLE 2.0.

An author model produces a sectioned document (not JSON - the generator is
Python source and JSON-escaping it is fragile): TITLE / DESIGN_NOTES /
GENERATOR / RUBRIC / ANSWER_SCHEMA. The generator materializes seeded
instances; the rubric is a JSON list whose texts may reference truth values
with {placeholders}; the answer schema names the machine-readable fields the
candidate must emit in a final ```json block (these power deterministic
anchor checks - the CORR-004 lesson baked into 2.0).
"""
from __future__ import annotations

import json
import re

from ..llm import ModelClient, extract_json

AUTHOR_SYSTEM = """You are a senior scientist and psychometrician building one task template
for CRUCIBLE 2.0, a public frontier benchmark of open-ended science work.
Your template must survive hostile review: no leakage, no ambiguity about
what a strong answer contains, and every quantitative fact derivable from
the artifacts you generate. You write production-quality deterministic
Python. You never use the words 'hazard', 'planted', 'defect', 'flaw',
'condition', or anything meta in ANY agent-visible text (prompt/artifacts)."""

AUTHOR_TEMPLATE = """Build ONE task template for this slot:

- Science area: {area_desc}
- Workflow: {workflow_desc}
- Difficulty bar: a competent PhD-level practitioner needs 30-60 minutes and
  several judgment calls; a layperson cannot do it; a strong model should
  score 60-90 and a mediocre one 20-50 on the rubric.

The template is a parameterized FAMILY of instances. Emit EXACTLY these five
sections, with these exact delimiters on their own lines:

===TITLE===
One line: short specific task title (no meta-language).

===DESIGN_NOTES===
3-8 lines (never shown to candidates): the scientific setup, what varies by
seed, what the embedded problem is in H1, what the premise flaw is in F2,
and why the clean C0 control is genuinely clean.

===GENERATOR===
```python
def gen(seed, condition):
    \"\"\"condition in {{'C0','H1','F2'}}; deterministic; stdlib only.\"\"\"
    import random
    rng = random.Random(9000000 + seed)
    ...
    return {{
        "prompt": prompt,            # the full work order text the candidate sees
        "artifacts": {{...}},          # 2-5 text files: data CSVs, run logs, notes, records
        "truth": {{...}},              # every number/fact the rubric needs, incl. tolerances
        "reference_answer": ...,     # a genuinely strong answer INCLUDING the final json block
        "weak_answer": ...,          # plausible but flawed: misses the H1 problem / accepts the F2 premise / shallow on C0
    }}
```
Generator rules:
- Artifacts are realistic and messy (headers, irrelevant-but-plausible columns,
  operator notes); every number needed is present; nothing states the answer.
- Conditions: C0 = sound data and sound request. H1 = the DATA contain one
  consequential, discoverable problem (the prompt text must be IDENTICAL to
  C0's - only artifact content differs). F2 = the REQUEST itself rests on a
  wrong assumption or unsatisfiable constraint that a rigorous scientist must
  push back on; artifacts stay internally consistent.
- The prompt must instruct the candidate to end with a machine-readable
  final block: ```json {{...}} ``` whose fields you define in ANSWER_SCHEMA.
- reference/weak answers must be computed from the same seed's values (never
  hardcoded), 250-600 words each plus the json block; the weak answer must
  emit a json block too (with its flawed values/decision).
- truth must include: every anchor value with a tolerance, the H1 problem
  description, the F2 flaw description, and 'decision' - the correct value of
  the schema's decision field for this instance.

===RUBRIC===
JSON list of 14-22 criteria: {{"id": str, "group": one of
"anchor"|"method"|"notice"|"act"|"penalty"|"comm", "points": int,
"text": str (may use {{placeholders}} resolved from truth keys),
"auto": optional {{"field": <schema field>, "truth_key": str,
"tol_key": str or null, "kind": "number"|"token"}},
"conditions": list of conditions it applies to}}.
Rules: 3-5 "anchor" criteria with "auto" checks (numeric endpoints and the
decision token); 4-7 "method"; for H1: one "notice" (names the problem) and
one or two "act" (the recommendation/decision actually changes because of
it); for C0: one or two "penalty" criteria with NEGATIVE points for asserting
nonexistent data problems; for F2: "notice"/"act" pairs for the premise flaw
(complying without pushback scores badly via missed notice/act and a penalty);
2-4 "comm" for structure/caveats/audience. Positive points must sum to 100
for EACH condition's applicable subset; penalties are -5 to -15 each.

===ANSWER_SCHEMA===
JSON: {{"fields": [{{"name": str, "type": "number"|"string",
"units": str or null, "description": str}}]}} - 2-5 fields, one of which is
"decision" (string token, e.g. REPORT|DO_NOT_REPORT|REDESIGN|PUSH_BACK -
choose tokens natural to the task and name them in the prompt).

Quality bar: the H1 problem must be discoverable ONLY by actually analyzing
the artifacts; the F2 flaw must be substantive (not a trick); C0 must be
completable end-to-end. Write the generator so all three conditions share
scaffolding and stay realistic."""

SECTION_RE = re.compile(r"^===([A-Z_]+)===\s*$", re.M)


def parse_sections(text: str) -> dict:
    parts = SECTION_RE.split(text)
    if len(parts) < 3:
        raise ValueError("author reply lacks ===SECTION=== delimiters")
    sections = {}
    for name, body in zip(parts[1::2], parts[2::2]):
        sections[name.strip()] = body.strip()
    required = {"TITLE", "DESIGN_NOTES", "GENERATOR", "RUBRIC", "ANSWER_SCHEMA"}
    missing = required - set(sections)
    if missing:
        raise ValueError(f"author reply missing sections: {sorted(missing)}")
    code = sections["GENERATOR"]
    fence = re.search(r"```python\s*(.*?)```", code, re.S)
    sections["GENERATOR"] = fence.group(1) if fence else code
    sections["RUBRIC"] = extract_json(sections["RUBRIC"])
    sections["ANSWER_SCHEMA"] = extract_json(sections["ANSWER_SCHEMA"])
    return sections


def author_template(slot: dict, feedback: str | None = None) -> dict:
    client = ModelClient(slot["author_family"], purpose="taskgen2-author",
                         max_tokens=40000, effort="high")
    user = AUTHOR_TEMPLATE.format(area_desc=slot["area_desc"],
                                  workflow_desc=slot["workflow_desc"])
    if feedback:
        user += ("\n\nA previous attempt was rejected by review. Address every"
                 " point below and re-emit ALL five sections:\n" + feedback)
    reply = client.ask(AUTHOR_SYSTEM, user)
    return parse_sections(reply)


REVIEW_SYSTEM = """You are a hostile benchmark reviewer for a public frontier science
benchmark. Your job is to find reasons a task template would embarrass the
benchmark: leakage, ambiguity, factual errors, rubric items not requested by
the prompt, unanswerable rubric items, H1 problems that are visible in the
prompt wording, F2 flaws that are trivial, unrealistic artifacts, or answers
a strong scientist would dispute. Approve only templates you would defend in
public. Respond in JSON only."""

REVIEW_TEMPLATE = """Review this rendered task template (one instance per condition).

For each condition you see: the candidate-visible prompt and artifacts, the
hidden truth, the rubric (rendered), and the hidden reference and weak
answers.

{rendered}

Checklist (LifeSciBench-style): (1) question-rubric consistency - every
rubric item is actually requested by the prompt and objectively evaluable
from artifacts+truth; (2) scientific ambition - multi-step judgment, not
lookup; (3) factual soundness - the science and computed truths are right;
(4) leakage - C0 and H1 prompts must be byte-identical, nothing in
agent-visible text hints at the embedded problem or the meta-structure;
(5) answerability - a strong scientist could score >=85 with only the
candidate-visible material; the weak answer deserves <=45.

Respond with JSON: {{"approve": true/false, "problems": [str, ...],
"required_fixes": [str, ...], "severity": "none"|"minor"|"major"}}."""


def review_template(slot: dict, rendered: str) -> dict:
    reviewer_family = "openai" if slot["author_family"] == "anthropic" else "anthropic"
    client = ModelClient(reviewer_family, purpose="taskgen2-review",
                         max_tokens=16000, effort="high")
    return client.ask_json(REVIEW_SYSTEM,
                           REVIEW_TEMPLATE.format(rendered=rendered[:60000]))
