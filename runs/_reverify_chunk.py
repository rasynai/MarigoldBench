"""Re-score recorded submissions with today's verifiers. One chunk per process."""
import json, sys, tempfile, glob, random
from pathlib import Path
sys.path.insert(0, 'A:/PERTURB-Bench')
from crucible.lab.families import build, verify
from crucible.lab.campaign import USABLE

chunk, total, sample = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
paths = sorted(glob.glob('runs/lab-1.0.0/systems/*/outcomes/*.json'))
rng = random.Random(4242)
rng.shuffle(paths)
paths = [p for p in paths if json.load(open(p, encoding='utf-8'))['family'] in USABLE][:sample]
mine = paths[chunk::total]

agree = disagree = errors = 0
bad = []
for p in mine:
    r = json.load(open(p, encoding='utf-8'))
    try:
        ep = build(r['family'], r['seed'], r['condition'])
        ws = Path(tempfile.mkdtemp())
        for name, text in ep.files.items():
            (ws / name).write_text(text, encoding='utf-8')
        v = verify(ep, r['submitted'], ws)
    except Exception as exc:
        errors += 1
        bad.append(f"{r['system']}/{r['run_id']}: {type(exc).__name__}")
        continue
    if bool(v.passed) == bool(r['vec']):
        agree += 1
    else:
        disagree += 1
        bad.append(f"{r['system']}/{r['run_id']}: recorded={r['vec']} now={v.passed} "
                   f"first_failed={v.first_failed}")
print(json.dumps({"agree": agree, "disagree": disagree, "errors": errors,
                  "detail": bad[:6]}))
