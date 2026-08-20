"""Does the H1 defect actually change the answer? Compare ALL scored fields."""
import json, sys
sys.path.insert(0, '.')
from crucible.lab.families import build, REGISTRY
from crucible.lab.campaign import USABLE

seed = int(sys.argv[1])
identical, differing = [], 0
for family in sorted(f for f in REGISTRY if f in USABLE):
    mod = REGISTRY[family]
    refs = {}
    for cond in ("C0", "H1"):
        ep = build(family, seed, cond)
        ref = mod["reference_submission"](ep)
        refs[cond] = {k: v for k, v in (ref or {}).items() if not k.startswith("conf_")}
    if refs["C0"] == refs["H1"]:
        identical.append(family)
    else:
        differing += 1
print(json.dumps({"seed": seed, "h1_identical_to_c0": identical,
                  "h1_differs": differing}))
