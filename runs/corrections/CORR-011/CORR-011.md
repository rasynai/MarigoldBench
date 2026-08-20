# CORR-011 - the host, not the family: random memory faults in CPython

**Date:** 2026-08-18
**Scope:** family gate (`runs/gate_families.py`); no recorded outcome changed.
**Status:** worked around in the gate, unresolved on the machine.

## What happened

After the three campaigns finished, `runs/gate_families.py` began failing
families that had passed it for days. The first was `ensemble_disagreement`,
whose child process died with no Python traceback. Direct runs of the same
build were worse than the gate suggested: in one measured block, 5 of 8
processes died with `access violation`, one with `STATUS_STACK_BUFFER_OVERRUN`
(0xC0000409), and two survived. Surviving processes sometimes raised
impossible errors instead - a `zip` object where a dict belonged, a
`list_iterator` multiplied by a float, `'<' not supported between instances of
'Parameter' and 'str'`.

## What it was not

Each hypothesis was tested and killed:

| Hypothesis | Test | Result |
|---|---|---|
| Defect in the family | run three other families 8x each | 8/8 clean each; only this family faulted |
| numpy / rdkit / torch | block `model_build`, the only family importing numpy at module scope | still faulted with no native library loaded |
| CPython 3.11 bug | same workload on CPython 3.14 | faults identically, same impossible `TypeError` |
| Deep Python recursion | `setrecursionlimit(120)` across a full build | limit held; no deep recursion exists |
| Heap corruption by an extension | `PYTHONMALLOC=debug -X dev` | 4/4 clean, and no guard-byte violation reported |
| Memory pressure | `GlobalMemoryStatusEx` during a fault window | 12.8 GiB free of 31.6 GiB, 59% load |
| Bytecode specialisation | `sys.setprofile` (disables quickening) | 4/8 clean vs 0/8 - no clean separation |

Two observations settle it. First, a **25-line pure-Python reproducer with no
repository code in it** - a hot loop over
`sorted(list_of_dicts, key=lambda q: abs(q["spread"] - row["spread"]))[:6]` -
segfaults on this host at a similar rate. Second, the rate **drifts with
time, not with the code**: an identical allocation-churn script measured 4/4
clean early in the session and 3/4 an hour later; the three mitigation arms
(plain / gc off / big stack) measured 9-3-4 out of 12 in that order, which is
the opposite ordering to the one measured an hour earlier. Nothing in the
repository or the interpreter explains a failure rate that moves on its own.

The conclusion is a host-level fault - most likely RAM - that hits
allocation-heavy CPython processes. It also retrospectively explains the
"intermittent RDKit/torch SIGSEGV" logged repeatedly during this project and
attributed to those libraries.

## Effect on the benchmark

**No recorded outcome is affected, and none was changed.** A process that dies
writes no file, so a fault destroys an episode rather than corrupting one; the
campaign records 0 censored and 0 lost episodes across 3,135 runs. A fault that
merely corrupts a live object surfaces as an exception, which the runner
records as `censored` and re-runs rather than scoring - the rule introduced in
CORR-008.

What it did break is the gate's ability to read a verdict. Fixed by three
changes:

1. **One seed per child process** instead of six. A shorter process allocates
   less and is far less likely to be hit; a hit now costs one seed.
2. **A failure must reproduce to count.** A seed is charged with a defect only
   when two attempts fail with the same first problem. A pass cannot be
   manufactured this way: the child must print a complete clean verdict for
   every condition of that seed.
3. **The entropy check moved to the parent**, where it can see every seed. In
   the per-seed child it flagged fields that vary across seeds but not within
   one, which is not the property that check exists to enforce.

With those in place the gate reads 30/30 and `runs/check_goal.py` reads 18/18.

## Standing risk, stated plainly

A host that can corrupt a live object can in principle corrupt one inside a
verifier without raising, producing a wrong verdict that looks ordinary. We
have no evidence of that happening - every observed corruption raised or
crashed - but we cannot exclude it, and on this machine it is the largest
unquantified threat to label accuracy. Anyone replicating these numbers should
run on hardware that passes a memory test; the owner of this machine has been
advised to run one.
