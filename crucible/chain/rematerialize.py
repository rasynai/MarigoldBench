"""Re-materialize already-built templates at the current seed set.

Templates built before the seed count changed hold fewer instances than the
population now specifies. Their generators are stored, deterministic and
already gate-validated, so the extra instances cost nothing but CPU - no model
call is made here.

    python -m crucible.chain.rematerialize
"""
from __future__ import annotations

import json
import sys

from ..paths import find_repo_root
from .build import SEEDS, materialize, _w
from .validate import validate_chain_template


def main() -> int:
    repo = find_repo_root()
    index_path = repo / "registry" / "chain_task_index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else []
    known = {(r["template_id"], r["instance"]) for r in index}

    added = 0
    for template_json in sorted((repo / "tasks_chain").glob("*/template.json")):
        meta = json.loads(template_json.read_text(encoding="utf-8"))
        slot = meta["slot"]
        try:
            payloads = validate_chain_template(meta["generator_py"], SEEDS,
                                               determinism_reps=0)
        except Exception as exc:  # noqa: BLE001 - report and keep going
            print(json.dumps({"template_id": meta["template_id"],
                              "status": f"revalidation failed: {str(exc)[:200]}"}))
            continue
        sections = {"TITLE": meta.get("title", ""),
                    "DESIGN_NOTES": meta.get("design_notes", ""),
                    "GENERATOR": meta["generator_py"]}
        rows = materialize(repo, slot, sections, payloads)
        new = [r for r in rows if (r["template_id"], r["instance"]) not in known]
        index += new
        known |= {(r["template_id"], r["instance"]) for r in new}
        added += len(new)
        print(json.dumps({"template_id": meta["template_id"],
                          "instances_now": len(rows), "added": len(new)}))

    _w(index_path, json.dumps(index, indent=2))
    from collections import Counter
    print(json.dumps({"added": added, "total_instances": len(index),
                      "splits": dict(Counter(r["split"] for r in index))}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
