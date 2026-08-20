"""Task registry with an enforced intake state machine (guide section 19.3).

No candidate may skip a gate: transitions must follow the pipeline order.
Every transition requires a named owner and a reason, and is written to the
hash-chained audit log.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .audit import AuditLog
from .paths import registry_dir
from .schemas import assert_valid, load_record

PIPELINE = [
    "NOMINATED",
    "TRIAGED",
    "RIGHTS_CLEARED",
    "SCIENCE_SCREENED",
    "DATA_VERIFIED",
    "TASK_FRAMED",
    "TRUTH_REGIME_ASSIGNED",
    "CONSTRUCT_REVIEWED",
    "BUILT",
    "INDEPENDENTLY_REVIEWED",
    "SHORTCUT_AUDITED",
    "PILOTED",
    "ADMITTED",
    "FROZEN",
]

TERMINAL = {"REJECTED", "DEFERRED", "REQUIRES_REDESIGN", "RETIRED", "RETRACTED"}

# From which statuses each terminal status is reachable.
TERMINAL_FROM = {
    "REJECTED": set(PIPELINE[:-2]),
    "DEFERRED": set(PIPELINE[:-2]),
    "REQUIRES_REDESIGN": set(PIPELINE[:-2]),
    "RETIRED": {"ADMITTED", "FROZEN"},
    "RETRACTED": {"ADMITTED", "FROZEN"},
}

# Re-entry: paused or redesigned candidates go back to triage, never forward.
REENTRY = {"DEFERRED": "TRIAGED", "REQUIRES_REDESIGN": "TRIAGED"}


class TransitionError(Exception):
    pass


def allowed_transitions(status: str) -> set[str]:
    allowed: set[str] = set()
    if status in PIPELINE:
        idx = PIPELINE.index(status)
        if idx + 1 < len(PIPELINE):
            allowed.add(PIPELINE[idx + 1])
    for terminal, sources in TERMINAL_FROM.items():
        if status in sources:
            allowed.add(terminal)
    if status in REENTRY:
        allowed.add(REENTRY[status])
    return allowed


class TaskRegistry:
    def __init__(self, root: Path | None = None):
        base = registry_dir(root)
        self.tasks_path = base / "tasks.json"
        self.audit = AuditLog(base / "audit.jsonl")

    def _load(self) -> dict:
        if self.tasks_path.exists():
            return json.loads(self.tasks_path.read_text(encoding="utf-8"))
        return {}

    def _save(self, tasks: dict) -> None:
        self.tasks_path.write_text(
            json.dumps(tasks, indent=2, sort_keys=True), encoding="utf-8"
        )

    def add_task(self, template_path: Path, actor: str) -> dict:
        record = load_record(template_path)
        assert_valid("task-template", record)
        template_id = record["template_id"]
        tasks = self._load()
        if template_id in tasks:
            raise TransitionError(f"Task {template_id} already registered.")
        entry = {
            "template_id": template_id,
            "version": record["version"],
            "status": record["status"],
            "primary_track": record["identity"]["primary_track"],
            "source_cluster_id": record["source"]["source_cluster_id"],
            "template_path": str(template_path),
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "history": [],
        }
        if record["status"] != "NOMINATED":
            raise TransitionError(
                f"New tasks must enter as NOMINATED, got {record['status']}. "
                "No candidate may skip a gate."
            )
        tasks[template_id] = entry
        self._save(tasks)
        self.audit.append(actor, "registry.add_task", {"template_id": template_id})
        return entry

    def transition(self, template_id: str, new_status: str, actor: str, reason: str) -> dict:
        if not actor.strip():
            raise TransitionError("Every transition requires a named owner.")
        if not reason.strip():
            raise TransitionError("Every transition requires a reason.")
        tasks = self._load()
        if template_id not in tasks:
            raise TransitionError(f"Unknown task {template_id}.")
        entry = tasks[template_id]
        current = entry["status"]
        allowed = allowed_transitions(current)
        if new_status not in allowed:
            raise TransitionError(
                f"Illegal transition {current} -> {new_status}. "
                f"Allowed from {current}: {sorted(allowed) or 'none (terminal)'}"
            )
        entry["history"].append(
            {
                "from": current,
                "to": new_status,
                "actor": actor,
                "reason": reason,
                "at": datetime.now(timezone.utc).isoformat(),
            }
        )
        entry["status"] = new_status
        self._save(tasks)
        self.audit.append(
            actor,
            "registry.transition",
            {"template_id": template_id, "from": current, "to": new_status, "reason": reason},
        )
        return entry

    def list_tasks(self) -> list[dict]:
        return sorted(self._load().values(), key=lambda entry: entry["template_id"])

    def get(self, template_id: str) -> dict | None:
        return self._load().get(template_id)
