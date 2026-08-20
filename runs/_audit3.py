"""Audit pass 3: fairness, contamination, refusal behaviour, budget binding."""
import json, glob, collections, sys
sys.path.insert(0, '.')
from crucible.lab.campaign import USABLE
from crucible.lab.episode import SYSTEMS

rows = [json.load(open(p, encoding='utf-8'))
        for p in glob.glob('runs/lab-1.0.0/systems/*/outcomes/*.json')]
rows = [r for r in rows if r['family'] in USABLE]
systems = sorted({r['system'] for r in rows})
hidden = [r for r in rows if r['split'] == 'hidden_test']
sealed = [r for r in rows if r['split'] == 'sealed']

print("=== 1. per-system settings (fairness of the frozen loop) ===")
for s in systems:
    print(f"  {s:9s} {SYSTEMS[s]['provider']:11s} {SYSTEMS[s]['model']:26s} "
          f"effort={SYSTEMS[s]['effort'] or '(none)'!r}")

print("\n=== 2. sealed vs hidden (contamination signal: sealed should NOT be worse) ===")
for s in systems:
    h = [r for r in hidden if r['system'] == s]
    q = [r for r in sealed if r['system'] == s]
    if not q:
        print(f"  {s:9s} hidden {100*sum(r['vec'] for r in h)/len(h):5.1f}%  sealed n=0 (reduced plan)")
        continue
    ph = 100*sum(r['vec'] for r in h)/len(h)
    pq = 100*sum(r['vec'] for r in q)/len(q)
    print(f"  {s:9s} hidden {ph:5.1f}% (n={len(h)})  sealed {pq:5.1f}% (n={len(q)})  gap {ph-pq:+5.1f}")

print("\n=== 3. stop reasons: is the score bound by capability or by the step budget? ===")
for s in systems:
    c = collections.Counter(r['stop_reason'] for r in rows if r['system'] == s)
    tot = sum(c.values())
    print(f"  {s:9s} " + "  ".join(f"{k}={100*v/tot:.0f}%" for k, v in c.most_common(4)))

print("\n=== 4. refusal discipline: F2 needs a refusal, C0 must NOT get one ===")
for s in systems:
    out = []
    for cond in ('C0', 'H1', 'F2'):
        sub = [r for r in hidden if r['system'] == s and r['condition'] == cond]
        out.append(f"{cond} {100*sum(r['vec'] for r in sub)/max(1,len(sub)):5.1f}%")
    # a system that just refuses everywhere would ace F2 and fail C0
    print(f"  {s:9s} " + "  ".join(out))

print("\n=== 5. first-failed checkpoints: one dominating everywhere smells of a verifier bug ===")
overall = collections.Counter()
for r in hidden:
    if not r['vec'] and r.get('first_failed'):
        overall[(r['family'], r['first_failed'])] += 1
tot_fail = sum(overall.values())
for (fam, cp), n in overall.most_common(8):
    who = collections.Counter(r['system'] for r in hidden
                              if not r['vec'] and r['family'] == fam
                              and r.get('first_failed') == cp)
    print(f"  {fam}/{cp}: {n} ({100*n/tot_fail:.1f}% of failures) systems={len(who)}")

print("\n=== 6. tool-call usage against the per-episode budget ===")
for s in systems:
    sub = [r for r in rows if r['system'] == s]
    calls = sorted(r['tool_calls'] for r in sub)
    med = calls[len(calls)//2]
    print(f"  {s:9s} median calls={med:3d}  max={max(calls):3d}  "
          f"episodes at max_turns={sum(1 for r in sub if r['stop_reason']=='max_turns')}")
