"""Audit pass 4: does any brief hand the model its own answer?

The CORR-010 saturation was caused by briefs that printed the method recipe,
an answer menu, or a decoy hint. This checks the strongest form mechanically:
whether the values the verifier scores appear verbatim in the text the model
reads, and whether C0 and H1 answers differ (an H1 that shares C0's answer is
free marks).
"""
import json, sys
sys.path.insert(0, '.')
from crucible.lab.families import build, REGISTRY
from crucible.lab.campaign import USABLE

seed = int(sys.argv[1])
leaks, same_answer, checked = [], [], 0
for family in sorted(f for f in REGISTRY if f in USABLE):
    mod = REGISTRY[family]
    answers = {}
    for cond in ("C0", "H1", "F2"):
        ep = build(family, seed, cond)
        ref = mod["reference_submission"](ep) if "reference_submission" in mod else None
        if ref is None:
            continue
        checked += 1
        haystack = (ep.brief + "\n" + "\n".join(ep.files.values())).lower()
        scored = {k: v for k, v in ref.items()
                  if not k.startswith("conf_") and isinstance(v, (int, float))}
        answers[cond] = tuple(sorted(scored.items()))
        # A numeric answer that appears verbatim in the brief (not the data
        # files) is a giveaway; values legitimately appear in the CSVs.
        for field, value in scored.items():
            token = f"{value}"
            if len(token) >= 4 and token in ep.brief.lower():
                leaks.append(f"{family}/{cond}: {field}={value} appears in the brief")
    if "C0" in answers and "H1" in answers and answers["C0"] == answers["H1"]:
        same_answer.append(family)
print(json.dumps({"seed": seed, "checked": checked,
                  "brief_leaks": leaks[:10], "n_leaks": len(leaks),
                  "h1_same_as_c0": same_answer}))
