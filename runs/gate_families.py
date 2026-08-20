"""Per-family gate, each family in its own process.

`validate_families.py` runs every family in one interpreter, and a native
crash inside RDKit or torch (SIGSEGV, not a Python exception) takes the whole
run down and reports nothing - which made the gate look like it had zero
usable families. Isolating each family means a crash is attributed to the
family that caused it and the rest of the report survives.

    python runs/gate_families.py            # summary
    python runs/gate_families.py --json     # machine-readable
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from crucible.nowindow import hidden_kwargs  # noqa: E402

CHILD = r'''
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, r"{repo}")
import importlib
m = importlib.import_module("crucible.lab.fam.{module}")
problems, b8, b1 = [], 0, 0
briefs = {{}}
answers = {{}}
for seed in {seeds}:
    per = {{}}
    for cond in ("C0", "H1", "F2"):
        ep = m.build(seed, cond)
        per[cond] = ep.brief
        ws = Path(tempfile.mkdtemp())
        for name, text in ep.files.items():
            (ws / name).write_text(text, encoding="utf-8")
        ref = m.reference_submission(ep)
        v = m.verify(ep, ref, ws)
        b8 += bool(v.passed)
        if not v.passed:
            problems.append(f"B8 fails s{{seed}}/{{cond}}: {{v.first_failed}}")
        e = m.verify(ep, {{}}, Path(tempfile.mkdtemp()))
        b1 += not e.passed
        if e.passed:
            problems.append(f"B1 empty passes s{{seed}}/{{cond}}")
        for field, value in (ref or {{}}).items():
            if not field.startswith("conf_") and isinstance(value, (str, int, float, bool)):
                answers.setdefault(field, set()).add(str(value))
    if per.get("C0") != per.get("H1"):
        problems.append(f"C0/H1 briefs differ at seed {{seed}}")
print(json.dumps({{"b8": b8, "b1": b1, "problems": problems[:8],
                  "answers": {{f: sorted(v) for f, v in answers.items()}},
                  "usable": not problems and b8 == 3 * len({seeds})
                            and b1 == 3 * len({seeds})}}))
'''


def check(module: str, attempts: int = 4) -> dict:
    """Gate one family, one seed per child process, retrying a crash.

    This host faults: allocation-heavy CPython processes segfault at a rate
    that drifts between roughly 5% and 90% over hours, and a 25-line pure
    Python `sorted(..., key=lambda ...)` loop with no repository code in it
    reproduces the crash. So a native death here is evidence about the
    machine, not about the family. Two consequences for this gate:

      * one seed per child, not six. A shorter, smaller process is far less
        likely to be hit, and a hit costs one seed rather than the family.
      * a crash is retried; only a reproducible Python-level verdict counts.

    Recorded outcomes are unaffected either way - a process that dies writes
    no file - but a gate that cannot get a clean read cannot certify a family
    that is sound. See CORRECTIONS.md CORR-011.
    """
    seeds = (11, 12, 13, 14, 15, 16)
    total = {"b8": 0, "b1": 0, "problems": [], "usable": True}
    answers: dict[str, set] = {}
    for seed in seeds:
        last, seen = {}, []
        for attempt in range(attempts):
            last = _check_once(module, (seed,))
            if last["usable"]:
                break
            first = (last["problems"] or [""])[0]
            # This host also corrupts live objects, not only kills processes:
            # the same seed has failed with "list indices must be ... not list"
            # and "'<' not supported between 'Parameter' and 'str'" on one run
            # and passed on the next. A defect in a deterministic generator
            # reproduces; only a repeated identical failure is charged to the
            # family. A pass cannot be manufactured this way - the child has to
            # print a full clean verdict for every condition to claim one.
            if first in seen:
                break
            seen.append(first)
        total["b8"] += last["b8"]
        total["b1"] += last["b1"]
        total["problems"].extend(last["problems"])
        total["usable"] &= bool(last["usable"])
        for field, values in (last.get("answers") or {}).items():
            answers.setdefault(field, set()).update(values)
    # Entropy is a property of the family across seeds, not of one instance:
    # judged here rather than in the child, which sees a single seed and would
    # call every field constant.
    constant = sorted(f for f, v in answers.items() if len(v) < 2)
    if constant:
        total["problems"].append("constant scored fields: "
                                 + ",".join(constant[:5]))
        total["usable"] = False
    total["problems"] = total["problems"][:8]
    return total


def _check_once(module: str, seeds: tuple = (11, 12, 13, 14, 15, 16)) -> dict:
    # Written to a file rather than passed with -c: a multi-kilobyte script on
    # the Windows command line silently mangles, which made four healthy
    # families report native crashes.
    import tempfile
    code = CHILD.format(repo=str(REPO), module=module, seeds=seeds)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                     encoding="utf-8") as handle:
        handle.write(code)
        script = handle.name
    proc = subprocess.run([sys.executable, script], cwd=str(REPO),
                          capture_output=True, text=True, timeout=1800,
                          **hidden_kwargs())
    os.unlink(script)
    line = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        detail = (proc.stderr.strip().splitlines() or ["no output"])[-1]
        if proc.returncode < 0 or proc.returncode == 139:
            detail = f"native crash (exit {proc.returncode}): {detail}"
        return {"b8": 0, "b1": 0, "problems": [detail[:200]], "usable": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    modules = sorted(os.path.basename(p)[:-3]
                     for p in glob.glob(str(REPO / "crucible" / "lab" / "fam" / "*.py"))
                     if not os.path.basename(p).startswith("_"))
    report = {}
    for module in modules:
        report[module] = check(module)
        if not args.json:
            r = report[module]
            mark = "PASS" if r["usable"] else "FAIL"
            print(f"  [{mark}] {module:28s} b8={r['b8']}/18 b1={r['b1']}/18"
                  + ("" if r["usable"] else "  " + "; ".join(r["problems"][:2])[:150]))
    usable = [m for m, r in report.items() if r["usable"]]
    if args.json:
        print(json.dumps({"usable": usable, "report": report}, indent=1))
    else:
        print(f"\nUSABLE FAMILIES: {len(usable)}/{len(report)}")
    return 0 if len(usable) == len(report) else 1


if __name__ == "__main__":
    sys.exit(main())
