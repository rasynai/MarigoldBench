"""Independent hostile review harness for the selectivity-panel family.

Deliberately does NOT reuse selftest_selectivity_panel.py.
"""
from __future__ import annotations

import json
import sys
import traceback
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crucible.lab.fam import selectivity_panel as SP

SEEDS = [11, 12, 13, 14, 15, 16]
CONDS = ["C0", "H1", "F2"]
WS = Path("runs/_hostile_selpanel").resolve()
WS.mkdir(parents=True, exist_ok=True)

blocking: list[str] = []
notes: list[str] = []


def hdr(t):
    print("\n" + "=" * 72)
    print(t)
    print("=" * 72)


# ------------------------------------------------------------------ 1. build
hdr("1. BUILD 18 EPISODES")
eps = {}
for s in SEEDS:
    for c in CONDS:
        try:
            eps[(s, c)] = SP.build(s, c)
        except Exception as exc:
            blocking.append(f"build({s},{c}) raised {type(exc).__name__}: {exc}")
            traceback.print_exc()
print(f"built {len(eps)}/18")
for (s, c), ep in sorted(eps.items()):
    print(f"  {s} {c}: files={sorted(ep.files)} budget={ep.budget} "
          f"bytes={sum(len(v) for v in ep.files.values())}")

# determinism
for (s, c), ep in sorted(eps.items()):
    again = SP.build(s, c)
    if again.files != ep.files or again.brief != ep.brief or again.key != ep.key:
        blocking.append(f"build({s},{c}) is not deterministic")

# ------------------------------------------------------- 2. brief identity
hdr("2. BRIEF BYTE-IDENTITY (C0 vs H1, and F2)")
for s in SEEDS:
    b0 = eps[(s, "C0")].brief.encode("utf-8")
    b1 = eps[(s, "H1")].brief.encode("utf-8")
    b2 = eps[(s, "F2")].brief.encode("utf-8")
    print(f"  seed {s}: C0==H1 {b0 == b1}   C0==F2 {b0 == b2}  len={len(b0)}")
    if b0 != b1:
        blocking.append(f"seed {s}: C0/H1 briefs differ")
    if b0 != b2:
        notes.append(f"seed {s}: C0/F2 briefs differ")

# file-name sets must also match between C0 and H1 (a structural tell)
for s in SEEDS:
    if sorted(eps[(s, "C0")].files) != sorted(eps[(s, "H1")].files):
        blocking.append(f"seed {s}: C0/H1 file name sets differ")

# row-count tell between C0 and H1
print("\n  row counts dose_response.csv (C0 / H1 / F2):")
for s in SEEDS:
    counts = [len(eps[(s, c)].files["dose_response.csv"].strip().splitlines())
              for c in CONDS]
    print(f"    seed {s}: {counts}   defect={eps[(s,'H1')].key['defect']['flavour']}")

# ------------------------------------------- 3. reference / degenerate / naive
hdr("3. REFERENCE, DEGENERATE, NAIVE")


def naive_facevalue(ep, scope_to_panel: bool):
    """Trust panel_summary.csv (no refit, no control check)."""
    primary, fold, mandated = SP._parse_criteria(ep.files["progression_criteria.txt"])
    rows = {}
    for line in ep.files["panel_summary.csv"].splitlines()[1:]:
        cells = line.split(",")
        if len(cells) >= 3:
            rows[cells[0]] = SP._as_float(cells[2])
    base = rows[primary]
    margins = {t: v / base for t, v in rows.items() if t != primary}
    if scope_to_panel:
        margins = {t: m for t, m in margins.items() if t in mandated}
    worst = min(margins, key=lambda t: margins[t])
    return {"decision": "progress" if margins[worst] >= fold else "hold",
            "limiting_target": worst,
            "limiting_margin_fold": round(margins[worst], 3),
            "primary_ic50_nM": round(base, 3),
            "conf_decision": 0.8, "conf_limiting_target": 0.8,
            "conf_limiting_margin_fold": 0.8, "conf_primary_ic50_nM": 0.8}


rows = []
for (s, c), ep in sorted(eps.items()):
    ref = SP.reference_submission(ep)
    vr = SP.verify(ep, ref, WS)
    ve = SP.verify(ep, {}, WS)
    vn = SP.verify(ep, None, WS)
    va = SP.verify(ep, naive_facevalue(ep, False), WS)
    vm = SP.verify(ep, naive_facevalue(ep, True), WS)
    rows.append((s, c, vr.passed, ve.passed, vn.passed, va.passed, vm.passed))
    if not vr.passed:
        blocking.append(f"{s}/{c}: reference_submission FAILED at {vr.first_failed} "
                        + json.dumps(vr.checkpoints) + " " + json.dumps(vr.detail, default=str)[:400])
    if ve.passed:
        blocking.append(f"{s}/{c}: empty submission {{}} PASSED")
    if vn.passed:
        blocking.append(f"{s}/{c}: None submission PASSED")
    if va.passed:
        blocking.append(f"{s}/{c}: naive panel-wide face-value PASSED")
    if c != "C0" and vm.passed:
        blocking.append(f"{s}/{c}: naive scoped face-value PASSED")

print(f"{'seed':>5} {'cond':>4} {'ref':>5} {'empty':>6} {'none':>5} "
      f"{'naiveAll':>9} {'naiveScoped':>12}")
for r in rows:
    print(f"{r[0]:>5} {r[1]:>4} {str(r[2]):>5} {str(r[3]):>6} {str(r[4]):>5} "
          f"{str(r[5]):>9} {str(r[6]):>12}")

# extra wrong paths: refit but ignore units / ignore controls
hdr("3b. REFIT-BUT-SLOPPY WRONG PATHS")


def refit(ep, honour_controls=True, honour_units=True, scope=True):
    primary, fold, mandated = SP._parse_criteria(ep.files["progression_criteria.txt"])
    ctl = SP._parse_controls(ep.files["plate_controls.csv"])
    pooled = defaultdict(list)
    for line in ep.files["dose_response.csv"].splitlines()[1:]:
        t, plate, conc, unit, pct = line.split(",")
        if honour_controls:
            pos, veh = ctl[plate]
            if pos < 80.0 or veh > 10.0:
                continue
        f = SP.UNIT_TO_NM[unit.lower()] if honour_units else 1.0
        pooled[t].append((float(conc) * f, float(pct)))
    fits = {t: SP._fit_ic50(p) for t, p in pooled.items()}
    base = fits[primary]
    pool = mandated if scope else list(fits)
    m = {t: fits[t] / base for t in pool if t in fits and t != primary}
    worst = min(m, key=lambda t: m[t])
    return {"decision": "progress" if m[worst] >= fold else "hold",
            "limiting_target": worst, "limiting_margin_fold": round(m[worst], 3),
            "primary_ic50_nM": round(base, 3), "conf_decision": 0.9,
            "conf_limiting_target": 0.9, "conf_limiting_margin_fold": 0.9,
            "conf_primary_ic50_nM": 0.9}


for name, kw in [("no-controls", {"honour_controls": False}),
                 ("no-units", {"honour_units": False}),
                 ("unscoped", {"scope": False})]:
    line = []
    for c in CONDS:
        n = 0
        for s in SEEDS:
            if SP.verify(eps[(s, c)], refit(eps[(s, c)], **kw), WS).passed:
                n += 1
        line.append(f"{c}={n}/6")
    print(f"  refit but {name:<12}: " + "  ".join(line))

# only the failed_control H1 instances are supposed to punish no-controls
for s in SEEDS:
    ep = eps[(s, "H1")]
    if ep.key["defect"]["flavour"] == "failed_control":
        if SP.verify(ep, refit(ep, honour_controls=False), WS).passed:
            blocking.append(f"{s}/H1: ignoring plate controls PASSED on a "
                            f"failed_control instance")

# ------------------------------------------------------------ 4. giveaways
hdr("4. BRIEF GIVEAWAY SCAN")
print(eps[(11, "C0")].brief)
print("-" * 72)
try:
    from crucible.chain.spec import giveaway_scan
    allhits = []
    for (s, c), ep in sorted(eps.items()):
        hits = giveaway_scan({"prompt": ep.brief, "artifacts": ep.files, "stages": []})
        allhits += [f"{s}/{c}: {h}" for h in hits]
    print(f"giveaway_scan findings: {len(allhits)}")
    for h in sorted(set(allhits))[:20]:
        print("  ", h)
    if allhits:
        blocking.append(f"giveaway_scan produced {len(allhits)} findings")
except Exception as exc:
    print("scan unavailable:", type(exc).__name__, exc)
    notes.append(f"giveaway_scan unavailable: {exc}")

# manual probes
brief = eps[(11, "C0")].brief.lower()
method_words = ["refit", "fit ", "curve fit", "hill", "four-parameter", "ic50 fit",
                "least squares", "regression", "control", "vehicle", "unit",
                "convert", "micromolar", "nanomolar", "scale", "drop", "exclude",
                "do not trust", "beware", "careful", "note that", "remember",
                "step 1", "first,", "then,", "panel_summary is", "may be wrong"]
found = [w for w in method_words if w in brief]
print("\nmethod/warning words present in brief:", found)

# ------------------------------------------------------------- 5. variety
hdr("5. ANSWER VARIETY ACROSS ALL 18")
fields = defaultdict(list)
for (s, c), ep in sorted(eps.items()):
    t = SP._recompute(ep.files)
    fields["decision"].append(t["decision"])
    fields["limiting_target"].append(t["limiting_target"])
    fields["limiting_margin_fold"].append(
        None if t["limiting_margin_fold"] is None else round(t["limiting_margin_fold"], 2))
    fields["primary_ic50_nM"].append(round(t.get("primary_ic50_nM") or 0, 2))
for f, vals in fields.items():
    ctr = Counter(map(str, vals))
    print(f"  {f:<22} distinct={len(ctr):<3} {dict(ctr)}")
    if len(ctr) == 1:
        blocking.append(f"scored field {f} is constant across all 18 instances")

print("\n  per-condition decision spread:")
for c in CONDS:
    ctr = Counter(SP._recompute(eps[(s, c)].files)["decision"] for s in SEEDS)
    print(f"    {c}: {dict(ctr)}")

print("\n  per-seed key (C0 | H1 | F2):")
for s in SEEDS:
    cells = []
    for c in CONDS:
        k = eps[(s, c)].key
        cells.append(f"{k['decision']}:{k['limiting_target']}")
    print(f"    seed {s}: " + " | ".join(cells))
    if (eps[(s, "C0")].key["decision"], eps[(s, "C0")].key["limiting_target"]) == \
       (eps[(s, "H1")].key["decision"], eps[(s, "H1")].key["limiting_target"]):
        blocking.append(f"seed {s}: H1 defect does not change the answer vs C0")

# -------------------------------------------------- 6. verifier recomputes
hdr("6. DOES THE VERIFIER RECOMPUTE?")
# Tamper with the key: if verify() still agrees with the DATA, it recomputes.
import copy
tampered_ok = 0
for (s, c), ep in sorted(eps.items()):
    ep2 = copy.deepcopy(ep)
    truth = SP._recompute(ep.files)
    # poison the key with a different decision + limiting target + numbers
    others = [t for t in ep.key["mandated"] if t != truth["limiting_target"]]
    ep2.key["decision"] = "progress" if truth["decision"] != "progress" else "hold"
    ep2.key["limiting_target"] = others[0]
    ep2.key["limiting_margin_fold"] = 999.0
    ep2.key["primary_ic50_nM"] = 12345.0
    v = SP.verify(ep2, SP.reference_submission(ep), WS)
    if v.passed:
        tampered_ok += 1
    else:
        blocking.append(f"{s}/{c}: verifier follows the poisoned key rather than "
                        f"the data (ref failed at {v.first_failed})")
print(f"  correct-from-data submission still passes with a poisoned key: "
      f"{tampered_ok}/18")

# And: a submission that matches the poisoned key must FAIL.
lied = 0
for (s, c), ep in sorted(eps.items()):
    truth = SP._recompute(ep.files)
    others = [t for t in ep.key["mandated"] if t != truth["limiting_target"]]
    bogus = {"decision": "progress" if truth["decision"] != "progress" else "hold",
             "limiting_target": others[0], "limiting_margin_fold": 999.0,
             "primary_ic50_nM": 12345.0}
    if SP.verify(ep, bogus, WS).passed:
        blocking.append(f"{s}/{c}: fabricated submission passed")
    else:
        lied += 1
print(f"  fabricated submissions rejected: {lied}/18")

# self-report honesty: right decision+target, wrong numbers must fail
selfrep = 0
for (s, c), ep in sorted(eps.items()):
    truth = SP._recompute(ep.files)
    sub = {"decision": truth["decision"], "limiting_target": truth["limiting_target"],
           "limiting_margin_fold": 777.0, "primary_ic50_nM": 4321.0}
    v = SP.verify(ep, sub, WS)
    if v.passed:
        blocking.append(f"{s}/{c}: right verdict + invented numbers passed")
    else:
        selfrep += 1
print(f"  right verdict but invented numbers rejected: {selfrep}/18")

# key vs recomputation agreement (a generator bug detector)
dis = []
for (s, c), ep in sorted(eps.items()):
    t = SP._recompute(ep.files)
    if t["decision"] != ep.key["decision"] or t["limiting_target"] != ep.key["limiting_target"]:
        dis.append(f"{s}/{c}: recomputed ({t['decision']},{t['limiting_target']}) "
                   f"!= key ({ep.key['decision']},{ep.key['limiting_target']})")
print(f"  key/recomputation disagreements: {len(dis)}")
for d in dis:
    print("   ", d)
    blocking.append(d)

# fit accuracy
err = []
for (s, c), ep in sorted(eps.items()):
    t = SP._recompute(ep.files)
    for tgt, fitted in t["fits_nM"].items():
        true = ep.key["true_ic50_nM"].get(tgt)
        if true:
            err.append(abs(fitted / true - 1.0))
print(f"  refit vs constructed IC50 worst relative error: {max(err)*100:.3f}%  (n={len(err)})")

# ------------------------------------------------------------ 7. solvability
hdr("7. SOLVABILITY WITHIN BUDGET WITH THE REAL TOOL BELT")
SOLUTION = r'''
import json, re
import numpy as np, pandas as pd
from scipy.optimize import curve_fit

crit = open("progression_criteria.txt").read()
primary = re.search(r"Primary target:\s*(\S+)", crit).group(1)
fold = float(re.search(r"at least ([0-9.]+)\s*-fold", crit).group(1))
panel, seen = [], False
for line in crit.splitlines():
    if line.strip().lower().startswith("mandated safety panel"):
        seen = True; continue
    if seen and line.strip():
        panel.append(line.split()[0].strip())

proto = open("assay_protocol.txt").read()
pos_min = float(re.search(r"at least ([0-9.]+)% inhibition", proto).group(1))
veh_max = float(re.search(r"below ([0-9.]+)% inhibition", proto).group(1))

ctl = pd.read_csv("plate_controls.csv")
good = set(ctl[(ctl.positive_control_pct_inhibition >= pos_min)
               & (ctl.vehicle_pct_inhibition <= veh_max)].plate_id)

dr = pd.read_csv("dose_response.csv")
dr["nm"] = dr.concentration * dr.conc_unit.str.lower().map({"nm":1.0,"um":1e3,"pm":1e-3})
dr = dr[dr.plate_id.isin(good)]

def hill(lx, li):
    return 100.0/(1.0+10.0**(li-lx))

fits = {}
for t, g in dr.groupby("target_id"):
    p,_ = curve_fit(hill, np.log10(g.nm.values), g.pct_inhibition.values,
                    p0=[2.0], maxfev=40000)
    fits[t] = float(10.0**p[0])

base = fits[primary]
missing = [t for t in panel if t not in fits]
if missing:
    out = {"decision":"cannot_determine","limiting_target":missing[0],
           "limiting_margin_fold":"cannot_determine","primary_ic50_nM":round(base,3)}
else:
    m = {t: fits[t]/base for t in panel}
    w = min(m, key=m.get)
    out = {"decision":"progress" if m[w]>=fold else "hold","limiting_target":w,
           "limiting_margin_fold":round(m[w],3),"primary_ic50_nM":round(base,3)}
out.update({"conf_decision":0.9,"conf_limiting_target":0.9,
            "conf_limiting_margin_fold":0.85,"conf_primary_ic50_nM":0.9})
print(json.dumps(out))
'''

from crucible.lab.tools import ToolBelt

for (s, c), ep in sorted(eps.items()):
    ws = WS / f"{s}{c}"
    ws.mkdir(parents=True, exist_ok=True)
    for n, txt in ep.files.items():
        (ws / n).write_text(txt, encoding="utf-8")
    belt = ToolBelt(workspace=ws, budget=ep.budget)
    try:
        belt.call("list_files")
        for n in sorted(ep.files):
            belt.call("read_file", path=n)
        r = belt.call("run_python", code=SOLUTION)
        if r["exit_code"] != 0:
            blocking.append(f"{s}/{c}: tool-belt solution crashed: {r['stderr'][-250:]}")
            print(f"  {s} {c}: CRASH {r['stderr'][-200:]}")
            continue
        sub = json.loads(r["stdout"].strip().splitlines()[-1])
        v = SP.verify(ep, sub, ws)
        used = belt.calls_used + 1        # +1 for the submit step
        print(f"  {s} {c}: calls={used}/{ep.budget} passed={v.passed} "
              + ("" if v.passed else json.dumps(v.checkpoints)))
        if not v.passed:
            blocking.append(f"{s}/{c}: honest tool-belt solution FAILED "
                            + json.dumps(v.checkpoints) + " "
                            + json.dumps(v.detail, default=str)[:400])
        if used > ep.budget:
            blocking.append(f"{s}/{c}: solution needs {used} > budget {ep.budget}")
    except Exception as exc:
        blocking.append(f"{s}/{c}: tool belt raised {type(exc).__name__}: {exc}")
        traceback.print_exc()

# ------------------------------------------------------- 8. robustness extras
hdr("8. FORMAT ROBUSTNESS + PARSER PROBES")
for (s, c), ep in sorted(eps.items()):
    ref = SP.reference_submission(ep)
    messy = {
        "Decision": str(ref["decision"]).replace("_", " ").title(),
        "limiting target": f"{ref['limiting_target']} (off-target)",
        "limiting_margin_fold": (f"{ref['limiting_margin_fold']:.1f}-fold"
                                 if isinstance(ref["limiting_margin_fold"], float)
                                 else "N/A"),
        "primary_ic50_nM": f"{ref['primary_ic50_nM']} nM",
        "conf_decision": 0.9,
    }
    v = SP.verify(ep, messy, WS)
    if not v.passed:
        notes.append(f"{s}/{c}: reformatted reference rejected "
                     + json.dumps(v.checkpoints))
print("  reformatted reference accepted on all 18:",
      not any("reformatted" in n for n in notes))

for t in ["does not clear the margin", "hold, cannot determine the margin",
          "", None, "progress but hold"]:
    print(f"    _decision_class({t!r}) -> {SP._decision_class(t)}")

hdr("SUMMARY")
print(f"blocking: {len(blocking)}")
for b in blocking:
    print("  X", b)
print(f"notes: {len(notes)}")
for n in notes:
    print("  -", n)
sys.exit(1 if blocking else 0)
