"""Assemble the public Hugging Face release. Nothing is copied by wildcard."""
import json, glob, os, shutil, sys
from pathlib import Path
sys.path.insert(0, '.')
from crucible.lab.campaign import USABLE

REPO = Path('.').resolve()
OUT = Path('A:/marigoldbench-release')
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

def copy(src, dst):
    d = OUT / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, d)

# --- code: the harness, the families, the verifiers, the tests -------------
n_code = 0
for path in glob.glob('crucible/**/*.py', recursive=True):
    if '__pycache__' in path:
        continue
    copy(path, path); n_code += 1
for path in glob.glob('tests/**/*.py', recursive=True):
    if '__pycache__' in path:
        continue
    copy(path, path); n_code += 1
copy('pyproject.toml', 'pyproject.toml')

# --- the scripts that gate, launch, score and audit ------------------------
for name in ('gate_families.py', 'validate_families.py', 'check_goal.py',
             'launch_lab.py', 'stop_workers.py', '_audit3.py', '_audit4.py',
             '_audit5.py', '_reverify_chunk.py'):
    src = Path('runs') / name
    if src.exists():
        copy(src, f'harness/{name}'); n_code += 1

# --- documents -------------------------------------------------------------
n_doc = 0
for path in ('docs/AUDIT.md', 'docs/BENCHMARK_CARD.md', 'docs/LIMITATIONS.md',
             'docs/REPLICATION.md', 'docs/SATURATION_POLICY.md',
             'GOAL.md', 'CORRECTIONS.md'):
    if Path(path).exists():
        copy(path, path); n_doc += 1
for path in sorted(glob.glob('runs/corrections/CORR-*/CORR-*.md')):
    copy(path, f'corrections/{Path(path).name}'); n_doc += 1
for path in ('analysis/collab/hardening__gpt.md',
             'analysis/collab/hardening__gemini.md',
             'analysis/literature/deep/SYNTHESIS.md',
             'analysis/literature2/SYNTHESIS.md'):
    if Path(path).exists():
        copy(path, f'analysis/{Path(path).parent.name}__{Path(path).name}'); n_doc += 1

# --- results ---------------------------------------------------------------
copy('runs/lab-1.0.0/scorecard.md', 'results/scorecard.md')
commit = sorted(glob.glob('commitments/*.json')) + sorted(glob.glob('runs/lab-1.0.0/*commit*.json'))
for path in commit:
    copy(path, f'results/{Path(path).name}')

# --- episodes: gated families and retired ones kept apart ------------------
scored = retired = 0
for path in glob.glob('runs/lab-1.0.0/systems/*/outcomes/*.json'):
    r = json.load(open(path, encoding='utf-8'))
    where = 'episodes' if r['family'] in USABLE else 'episodes_retired'
    copy(path, f"{where}/{r['system']}/{Path(path).name}")
    scored += r['family'] in USABLE
    retired += r['family'] not in USABLE
# voided episodes, so the corrections can be checked rather than believed
voided = 0
for path in glob.glob('runs/corrections/CORR-*/*__*.json'):
    copy(path, f'episodes_voided/{Path(path).parent.name}/{Path(path).name}')
    voided += 1

size = sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file())
files = sum(1 for f in OUT.rglob('*') if f.is_file())
print(json.dumps({"code_files": n_code, "doc_files": n_doc,
                  "episodes_scored": scored, "episodes_retired": retired,
                  "episodes_voided": voided, "commitments": len(commit),
                  "total_files": files, "total_mb": round(size / 1e6, 1),
                  "out": str(OUT)}, indent=1))
