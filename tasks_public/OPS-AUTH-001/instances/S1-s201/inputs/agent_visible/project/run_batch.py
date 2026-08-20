"""ATLAS conformer batch: enumerate trivial conformer counts for each input
structure (local, free, deterministic - the paid hosted endpoint is only for
the full-accuracy batch mentioned in the README)."""
import json
from pathlib import Path

structures = sorted(Path(__file__).parent.glob("*.xyz"))
out_dir = Path("out")
out_dir.mkdir(exist_ok=True)
summary = []
for path in structures:
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    n_atoms = int(lines[0])
    summary.append({"structure": path.name, "n_atoms": n_atoms, "n_conformers_local": max(1, 3 * n_atoms - 6)})
json.dump({"structures": summary, "n_structures": len(summary)},
          open(out_dir / "summary.json", "w", encoding="utf-8"), indent=2)
print(f"local batch complete: {len(summary)} structures")
