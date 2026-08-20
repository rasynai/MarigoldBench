"""Model authoring of chain templates, with the hand-written exemplar in
context and a hostile cross-family review afterwards.

Two evidence-backed choices:
- a strong exemplar beats a bare specification for generated-artifact quality
  (Hong et al. 2026: extrinsic alignment 0.58 -> 0.70 with exemplars);
- the reviewer is always from the other model family, because same-family
  review inherits the author's blind spots along with its style preferences.
"""
from __future__ import annotations

import re

from ..llm import ModelClient, extract_json
from .exemplar import EXEMPLAR_GENERATOR

AUTHOR_SYSTEM = """You are a senior scientist who also builds measurement instruments.
You write ONE task generator for a public benchmark that must stay hard for
years and must never be embarrassed by a wrong answer key. You write exact,
deterministic Python and you check your own arithmetic. You never let the
machinery of the benchmark appear in anything the candidate reads."""

AUTHOR_TEMPLATE = """Write ONE chain-template generator for this slot.

- Science area: {area_desc}
- Workflow: {workflow_desc}
- Scenario seed idea (adapt freely, keep the science): {idea}

# What a chain template is

An instance is a realistic work order plus text artifacts. Behind it sits an
ORDERED CHAIN of {min_stages}-{max_stages} stages. Each stage is one judgment call whose
correct answer depends on getting the previous stages right. Every stage has an
ATTRACTIVE WRONG PATH - the value a competent but hurried analyst produces by
taking the obvious default (skipping a footnote, using the unweighted fit,
ignoring a confound, substituting for censored values). The candidate must get
EVERY stage right to score, so difficulty compounds.

# The contract

Emit exactly these sections with these delimiters on their own lines:

===TITLE===
One line naming the task. No meta-language.

===DESIGN_NOTES===
5-12 lines, never shown to candidates: the science, what varies by seed, each
fork and why its default is tempting, what the H1 defect is, what the F2
premise flaw is, and why C0 is genuinely clean.

===GENERATOR===
```python
def gen(seed, condition):
    # condition is 'C0', 'H1' or 'F2'. Deterministic. Standard library only
    # (random, math, json are fine). No file I/O, no imports beyond stdlib.
    ...
    return {{
        "prompt": prompt,          # >=500 chars, the full work order
        "artifacts": {{...}},        # 2-5 realistic text files
        "stages": [ ... ],         # the ordered chain, see below
        "decision": {{"correct": "TOKEN_A", "decoy": "TOKEN_B"}},
        "reference_answer": ...,   # a strong answer + final json block
        "weak_answer": ...,        # the careless answer + final json block
        # plus "defect": str on H1, "premise_flaw": str on F2
    }}
```

Each stage is:
```python
{{"key": "snake_case_field",        # the json field the candidate must emit
  "label": "what this quantity is",
  "correct": <number or token>,     # computed, never hardcoded
  "decoy": <number or token>,       # what the careless path yields
  "tol": <positive number>,         # numeric tolerance
  "fork": "the judgment call, >=15 chars",
  "fork_keywords": ["...", "..."]}}  # words a correct answer would use
```

# Hard rules (a template that breaks any of these is rejected automatically)

1. TRAP SEPARATION: for numeric stages |correct - decoy| >= 3*tol, AND the
   decoy must be PLAUSIBLE - same sign as the correct value and within a
   factor of 10 of it. A negative concentration or an answer 100x off is not
   a trap, it is noise.
2. NO LEAKAGE: no stage answer (to 4+ significant figures) may appear anywhere
   in the prompt or artifacts. The candidate must COMPUTE it. Counts under 100
   are exempt.
3. SYMMETRY: the C0 and H1 prompts must be byte-identical. Only artifact
   CONTENT differs. Nothing in candidate-visible text may hint that anything
   is wrong, or that conditions exist at all.
4. NO META-VOCABULARY anywhere the candidate reads: never write hazard,
   planted, decoy, trap, condition, benchmark, rubric, ground truth.
5. THE REFERENCE ANSWER MUST BE CORRECT: it must contain a final ```json
   block whose every field equals the stage 'correct' values and the correct
   decision token. Compute those values from the same variables; never retype
   a number by hand.
6. THE WEAK ANSWER must take the careless path: its json block uses the decoy
   values and the decoy decision, and it must read like a plausible,
   confident, competent-sounding report - not like an obviously bad one.
7. The prompt must name the exact json fields and the allowed decision tokens,
   and must ask for a confidence in [0,1] per field as conf_<field>.
8. Artifacts must be realistic and slightly messy: operator notes, footnotes,
   extra columns, inconsistent spacing. The critical detail (the footnote that
   invalidates a sample, the metadata column that encodes batch) must be
   present but not signposted.
9. EVERY stage needs correct != decoy. For a token stage the two tokens must
   be different strings. For a numeric stage they must differ by more than
   3*tol. Compute both from the data and assert the separation yourself before
   returning - templates are rejected automatically for this more than any
   other reason.
10. If a stage's correct answer is an abstention token ("cannot_determine"),
   its decoy must still be the NUMBER the careless path produces, and you must
   still supply a numeric 'tol' for that decoy.
11. THE H1 DEFECT MUST CHANGE THE ANSWER. If the planted problem leaves the
   final number and the decision unchanged, the task measures nothing. Verify
   in code that at least one stage value AND the decision token differ between
   C0 and H1 for the same seed.
12. Keep the science physically possible. Masses, concentrations, rate
   constants and instrument readings must be values a real instrument could
   produce; a reviewer will recompute them.
13. NEVER use printf-style %-formatting anywhere in the generator. Scientific
   text is full of literal percent signs ("50% w/w", "95% CI", "RSD 2%"), and
   a stray % makes "unsupported format character" or "not enough arguments"
   at runtime - this is the single most common reason templates are rejected.
   Use str.format(), f-strings, or plain concatenation, and format numbers
   with the two-argument builtin format(x, '.3f').
14. NEVER put `assert` in the generator, and never raise if a constraint is
   unmet. If your design needs a parameter search (to make a decoy land the
   right side of a limit, say), search a fixed deterministic list of
   candidates and take the first that works, with a plain fallback if none
   do. A generator that raises on some seed is rejected, and "no valid
   instance found" is the second most common rejection there is.
15. Keep the generator COMPACT - roughly 150-250 lines. Build long artifact
   text by appending short strings to a list and joining them, never as one
   enormous nested literal. Truncated and syntactically broken generators are
   a large share of rejections and both come from over-long files.
16. The work order must NOT tell the candidate what is wrong. Do not describe
   a record as "informal", "questionable", "provisional" or "to be confirmed",
   and do not instruct the candidate to "review X carefully" where X is the
   defect. State the job, supply the records, and let the analysis find it.
17. THE WORK ORDER STATES WHAT IS NEEDED, NEVER HOW. Never enumerate the
   method steps ("apply the X test, identify Y, select Z, calculate W..." is
   an automatic rejection: it converts every judgment into execution). Never
   warn against the wrong path ("a good r-squared does not by itself...").
   One sentence naming the deliverable and its units is the whole ask.
18. NO ANSWER MENUS. The JSON field list may name each field and its units,
   but for every judgment field it must say "in your own words" - it must
   NEVER print candidate values (an automatic rejection: printing both the
   correct token and the decoy token makes the stage multiple choice). The
   single exception is the terminal `decision` field, whose vocabulary is the
   output contract, plus naming the abstention string cannot_determine.
19. Every categorical stage (correct answer not a number, not an abstention
   token) MUST carry "correct_aliases" and "decoy_aliases": 3-7 natural
   phrasings a scientist might use for that side of the fork. They are matched
   on word boundaries after lowercasing, so they must be NEGATION-SAFE: no
   correct alias may occur inside a natural phrasing of the decoy side or
   vice versa ("quantifiable" vs "not quantifiable" is the canonical
   violation - use "above the lloq" / "below the lloq" style phrases instead).
20. Every NUMERIC stage MUST carry "wrong_paths": >=2 dicts
   {{"id": "<which wrong analysis>", "value": <number>}} enumerating what the
   plausible WRONG analyses produce for that stage (wrong eligible set, wrong
   rule choice, wrong unit convention, partial fix...). The generator must
   COMPUTE these, and every one must miss the correct value by more than 3x
   the stage tolerance - derive tol from the smallest wrong-path gap
   (tol ~ 0.3 * min_gap), never from a fixed percentage. If a wrong analysis
   lands inside tolerance the instance is invalid: search over the generated
   data (resample noise, move the operating point) until all paths separate.
21. If the answer key depends on a threshold, limit or critical value, the
   candidate must be able to DERIVE it from shipped data (a qualification
   table, replicate QC set, document register); list every such number in a
   payload key "rule_constants" - the gates reject the template if any of
   them is printed verbatim in the prompt or an artifact. A rule the SOP
   states in full prose (like an acceptance band in percent) is fine; a
   pre-computed critical value is not.

# The standard to match

This is a complete, accepted template. Match its rigour, its realism and its
structure; do NOT copy its science.

```python
{exemplar}
```

# Your slot again

Area: {area_desc}
Workflow: {workflow_desc}

Write the five sections now."""

SECTION_RE = re.compile(r"^===([A-Z_]+)===\s*$", re.M)


def parse_sections(text: str) -> dict:
    parts = SECTION_RE.split(text)
    if len(parts) < 3:
        preview = text[-400:] if text else "(empty reply)"
        raise ValueError(
            "author reply lacks ===SECTION=== delimiters (likely truncated);"
            f" tail was: {preview!r}")
    sections = {name.strip(): body.strip()
                for name, body in zip(parts[1::2], parts[2::2])}
    missing = {"TITLE", "DESIGN_NOTES", "GENERATOR"} - set(sections)
    if missing:
        raise ValueError(f"author reply missing sections: {sorted(missing)}")
    code = sections["GENERATOR"]
    # GREEDY to the LAST fence. The generator legitimately contains a nested
    # ```json block inside the prompt string it builds, so a non-greedy match
    # stops there and truncates the module mid-string - which presents as an
    # unterminated string literal and killed every early template.
    fence = re.search(r"```(?:python)?\s*\n(.*)\n\s*```", code, re.S)
    sections["GENERATOR"] = fence.group(1) if fence else code
    return sections


def author_chain(slot: dict, feedback: str | None = None) -> dict:
    from .spec import MAX_STAGES, MIN_STAGES

    # Thinking tokens share the output budget on claude-opus-5, and at high
    # effort a first attempt spent all 48k thinking and returned a truncated
    # document. Medium effort with a larger ceiling leaves room for the ~10k
    # tokens of generator + rubric this task actually has to emit.
    client = ModelClient(slot["author_family"], purpose="chain-author",
                         max_tokens=64000, effort="medium")
    user = AUTHOR_TEMPLATE.format(
        area_desc=slot["area_desc"], workflow_desc=slot["workflow_desc"],
        idea=slot.get("idea", "(choose a realistic scenario yourself)"),
        exemplar=EXEMPLAR_GENERATOR.strip(),
        min_stages=MIN_STAGES, max_stages=MAX_STAGES)
    if feedback:
        user += ("\n\n# A previous attempt was REJECTED\n"
                 "Fix every point below and re-emit ALL sections:\n" + feedback)
    return parse_sections(client.ask(AUTHOR_SYSTEM, user))


REVIEW_SYSTEM = """You are a hostile reviewer for a public science benchmark. Your job is
to find the reason this task would embarrass us after release: a wrong answer
key, an ambiguous question, a shortcut that reaches the answer without the
analysis, a trap no real scientist would fall for, a defect visible from the
prompt alone, or a valid alternative analysis the key would mark wrong.
Approve only what you would defend publicly. Respond in JSON only."""

REVIEW_TEMPLATE = """Review this rendered chain task. You see everything: what the candidate
reads, the hidden answer key, and both model answers.

{rendered}

Judge these, and be specific about WHERE the problem is:

1. KEY CORRECTNESS - is every 'correct' value actually right for the data
   shown? Recompute what you can. This matters more than anything else: a
   benchmark whose answers are wrong is worse than no benchmark.
2. ALTERNATIVE VALID PATHS - could a competent scientist reach a DIFFERENT
   defensible value for any stage? If so, tighten the key by making the DATA
   determine the method: an acceptance criterion the alternatives measurably
   fail (back-calculation limits, replicate CV bounds, a qualification table
   the alternative violates). NEVER by having the prompt or an artifact name
   the required method - a named method converts the judgment into execution,
   which is the exact defect that saturated campaign 3.0.0 at 94-100%. If no
   data-driven construction can single out one defensible value, the stage is
   unsalvageable: require its deletion.
3. SHORTCUTS - can the final answer be reached without doing the intended
   analysis? Look for the answer sitting in an artifact, derivable from a
   trivial operation, or guessable from domain priors alone.
4. TRAP QUALITY - is each decoy genuinely what a hurried expert would produce,
   and plausible enough to be reported?
5. LEAKAGE AND SYMMETRY - does anything the candidate reads reveal the defect,
   the premise flaw, or that variants exist?
6. AMBIGUITY - is the requested quantity, its units, and its rounding
   unambiguous from the prompt alone?
7. DIFFICULTY - would this take a competent PhD-level practitioner real work
   (20+ minutes of genuine analysis), or is it routine?

Respond with JSON:
{{"approve": true/false,
  "key_correctness_verified": true/false,
  "problems": ["..."],
  "required_fixes": ["..."],
  "estimated_expert_minutes": <int>,
  "severity": "none"|"minor"|"major"}}"""


def review_chain(slot: dict, rendered: str) -> dict:
    reviewer = "openai" if slot["author_family"] == "anthropic" else "anthropic"
    # Reviews were hitting the 20k ceiling exactly and truncating, which costs
    # an escalation retry every time. Thinking shares the output budget, so
    # trade a little depth for headroom to actually emit the verdict.
    client = ModelClient(reviewer, purpose="chain-review", max_tokens=32000,
                         effort="medium")
    verdict = client.ask_json(REVIEW_SYSTEM,
                              REVIEW_TEMPLATE.format(rendered=rendered[:70000]))
    verdict["reviewer_family"] = reviewer
    return verdict


def render_for_review(payloads: dict, seed: int, sections: dict) -> str:
    from .spec import answer_key

    blocks = [f"# TITLE\n{sections['TITLE']}\n\n# DESIGN NOTES (hidden)\n{sections['DESIGN_NOTES']}"]
    for condition in ("C0", "H1", "F2"):
        payload = payloads[seed][condition]
        key = answer_key(payload)
        artifacts = "\n".join(f"--- {name} ---\n{content[:2200]}"
                              for name, content in payload["artifacts"].items())
        stages = "\n".join(
            f"  {k}: correct={v['correct']!r} decoy={v['decoy']!r} tol={v['tol']}"
            f"  | fork: {v['fork']}" for k, v in key["stages"].items())
        blocks.append(
            f"\n## CONDITION {condition}\n### Work order (candidate-visible)\n"
            f"{payload['prompt'][:3000]}\n### Artifacts (candidate-visible)\n{artifacts}\n"
            f"### Hidden chain key\n{stages}\n  decision: {key['decision']}\n"
            f"### Reference answer (should be right)\n{payload['reference_answer'][:2600]}\n"
            f"### Weak answer (should be wrong)\n{payload['weak_answer'][:1600]}")
    return "\n".join(blocks)
