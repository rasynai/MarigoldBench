"""Native-product adapter for Marigold (guide section 23).

Marigold runs on the user's GPU server as an agent-server product (48 tools,
its own model routing, tier policy, condenser, critic). This adapter follows
the minimal-adapter principle (23.5): it only

  1. creates a per-run working directory on the server and uploads the
     agent-visible bundle (task card + inputs) into it,
  2. submits the task text through Marigold's ordinary conversation API
     (POST /api/conversations -> /run -> poll -> agent_final_response) with NO
     agent override, so the product's pinned native spec applies (mode N1,
     autonomous work order, NeverConfirm),
  3. exports the submission files the product wrote, verifies them locally,
  4. records the final response and cleans up the conversation.

It never edits the product's outputs, never adds tools, and never retries a
scientific failure. The session API key stays on the server: every HTTP call
executes remotely over SSH with marigold.env sourced there.
"""
from __future__ import annotations

import base64
import json
import os
import shlex
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path

from .packaging import build_agent_bundle, scan_for_truth
from .verification import run_verification

HOST = os.environ.get("CRUCIBLE_MARIGOLD_HOST", "ubuntu@129.213.93.18")
# Cores 8012..8019 run the same product config; CRUCIBLE_MARIGOLD_PORT lets
# parallel campaign workers shard runs across cores without code changes.
CORE_URL = f"http://127.0.0.1:{os.environ.get('CRUCIBLE_MARIGOLD_PORT', '8012')}"
REMOTE_ROOT = "/home/ubuntu/crucible_bench"
SSH_BASE = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", HOST]
TERMINAL = {"finished", "error", "stuck", "idle"}

SUBMISSION_INSTRUCTIONS = """
You are working in {workdir}. The task inputs are in {workdir}/inputs/.

Write your COMPLETE submission into {workdir}/final_submission/ :
- status.json: {{"status": "COMPLETED"|"ABSTAINED"|"FAILED_SCIENTIFIC"|"STOPPED_FOR_SAFETY", "note": "..."}}
- report.md: your scientific report.
- claims.json: {{"claims": [{{"claim_id", "statement", "claim_type",
  "confidence" (0-1), "value" (number for numeric claims / short token for
  decisions), "units" (optional),
  "artifact_pointers": ["artifacts/x.json#field=y", ...], "source_pointers": [],
  "limitations": [...]}}],
  "hazards": [{{"hazard_id", "description", "probability", "severity"
  ("low"|"medium"|"high"|"critical"), "evidence": [...], "recommended_action"}}]}}
  (hazards = data/method problems you found; [] if none)
- every artifact, script, or log the work order requires, with the same
  relative layout the work order names (artifacts/, reproduction/, approvals/).
Reproduction scripts must run with the submission directory as the working
directory and read inputs from the RELATIVE path ./inputs/ (the grader places
a copy of the task inputs there - never use absolute paths), use only the
Python standard library, and be deterministic. For numeric claims, "value" must equal the number stored in the
artifact it points to. Decision claims use claim_type "reportability_decision".
When you are done, ensure final_submission/ contains everything; then finish.
"""


def _ssh(command: str, timeout: int = 120, attempts: int = 3) -> str:
    """One transient dropped connection must not kill a 15-minute run: with
    several workers polling concurrently, sshd occasionally refuses a burst
    (MaxStartups), so retry with backoff before declaring failure."""
    last = ""
    for attempt in range(attempts):
        try:
            result = subprocess.run(
                SSH_BASE + [command], capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            last = "local ssh timeout"
            time.sleep(5 * (attempt + 1))
            continue
        if result.returncode == 0:
            return result.stdout or ""
        last = f"({result.returncode}): {(result.stderr or '')[:400]}"
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"ssh failed after {attempts} attempts {last}")


def _remote_api(method: str, path: str, body: dict | None = None, timeout: int = 120) -> dict:
    """Run a curl against the core FROM the server with marigold.env sourced,
    so the session key never leaves the machine."""
    body_part = ""
    if body is not None:
        encoded = base64.b64encode(json.dumps(body).encode()).decode()
        body_part = f"-H 'Content-Type: application/json' --data-binary @<(echo {encoded} | base64 -d) "
    command = (
        "set -a; . /home/ubuntu/marigold.env >/dev/null 2>&1; set +a; "
        f"curl -s -m {timeout - 10} -X {method} "
        "-H \"X-Session-API-Key: $OPENHANDS_SESSION_API_KEY\" "
        + body_part
        + shlex.quote(CORE_URL + path)
    )
    out = _ssh(f"bash -c {shlex.quote(command)}", timeout=timeout)
    try:
        return json.loads(out) if out.strip() else {}
    except json.JSONDecodeError:
        return {"_raw": out[:500]}


def _wait_for_host(max_load: int = 24, max_wait_s: int = 5400) -> None:
    """CORR-002 prevention: never start a Marigold run on a saturated host.
    An overloaded box times out MCP tool listing at conversation create, which
    measures server contention instead of the product. Waits (not fails) so a
    campaign worker rides out a co-tenant burst; raises only after max_wait_s."""
    deadline = time.time() + max_wait_s
    while True:
        try:
            load = float(_ssh("cut -d' ' -f1 /proc/loadavg", timeout=30).strip())
        except Exception:  # noqa: BLE001 - transient ssh failure: retry below
            load = None
        if load is not None and load < max_load:
            return
        if time.time() > deadline:
            raise RuntimeError(
                f"host overloaded (load {load}) for {max_wait_s}s - refusing to start")
        time.sleep(120)


def _upload_bundle(task_dir: Path, workdir: str) -> None:
    with tempfile.TemporaryDirectory(prefix="crucible-mg-") as tmp:
        bundle = Path(tmp) / "bundle"
        build_agent_bundle(task_dir, bundle)
        violations = scan_for_truth(bundle, task_dir)
        if violations:
            raise RuntimeError(f"truth boundary violation: {violations}")
        tar_path = Path(tmp) / "bundle.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(bundle / "inputs", arcname="inputs")
            tar.add(bundle / "task_card", arcname="task_card")
        for attempt in range(3):
            try:
                with tar_path.open("rb") as fh:
                    result = subprocess.run(
                        SSH_BASE + [f"mkdir -p {workdir} && tar -xzf - -C {workdir}"],
                        stdin=fh, capture_output=True, timeout=180,
                    )
                if result.returncode == 0:
                    break
            except subprocess.TimeoutExpired:
                pass
            time.sleep(5 * (attempt + 1))
        else:
            raise RuntimeError("bundle upload failed after retries")


def _download_submission(workdir: str, out_dir: Path) -> bool:
    result = None
    for attempt in range(3):
        try:
            result = subprocess.run(
                SSH_BASE + [f"cd {workdir} 2>/dev/null && tar -czf - final_submission 2>/dev/null || echo __EMPTY__"],
                capture_output=True, timeout=180,
            )
            if result.returncode == 0:
                break
        except subprocess.TimeoutExpired:
            result = None
        time.sleep(5 * (attempt + 1))
    if result is None:
        raise RuntimeError("submission download failed after retries")
    if b"__EMPTY__" in result.stdout[:200]:
        return False
    with tempfile.TemporaryDirectory(prefix="crucible-mg-dl-") as tmp:
        tar_path = Path(tmp) / "sub.tar.gz"
        tar_path.write_bytes(result.stdout)
        out_dir.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tar_path, "r:gz") as tar:
            members = [m for m in tar.getmembers()
                       if m.name.startswith("final_submission/") and not m.name.startswith("/")
                       and ".." not in m.name]
            tar.extractall(Path(tmp) / "x", members=members)  # noqa: S202 - filtered members
        source = Path(tmp) / "x" / "final_submission"
        if not source.exists():
            return False
        import shutil

        for item in source.rglob("*"):
            if item.is_file():
                target = out_dir / item.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
    return True


def run_marigold(task_dir: Path, out_dir: Path, budget_minutes: int = 25) -> dict:
    task_dir = Path(task_dir).resolve()
    _wait_for_host()
    run_id = f"{task_dir.name}-{int(time.time())}"
    workdir = f"{REMOTE_ROOT}/{run_id}"
    _upload_bundle(task_dir, workdir)

    card = (task_dir / "task_card" / "card.md").read_text(encoding="utf-8")
    task_text = card + "\n" + SUBMISSION_INSTRUCTIONS.format(workdir=workdir)
    body = {
        "workspace": {"kind": "LocalWorkspace", "working_dir": workdir},
        "confirmation_policy": {"kind": "NeverConfirm"},
        "initial_message": {"role": "user", "content": [{"type": "text", "text": task_text}],
                            "run": False},
        "tags": {"suite": "crucible", "task": task_dir.name.lower()},
    }
    created = _remote_api("POST", "/api/conversations", body, timeout=300)
    cid = created.get("id") or created.get("conversation_id")
    if not cid:
        raise RuntimeError(f"conversation create failed: {str(created)[:300]}")

    _remote_api("POST", f"/api/conversations/{cid}/run", {}, timeout=60)  # 409 tolerated
    deadline = time.time() + budget_minutes * 60
    status = "timeout"
    while time.time() < deadline:
        time.sleep(25)
        try:  # a core busy for minutes must not kill the run - just poll again
            info = _remote_api("GET", f"/api/conversations/{cid}", timeout=60)
        except RuntimeError:
            continue
        status = str(info.get("execution_status") or "")
        if status in TERMINAL:
            break

    # Generous local timeouts: the remote curl needs its full window PLUS ssh
    # handshake overhead, which stacks up when several workers poll one box.
    try:
        final = _remote_api("GET", f"/api/conversations/{cid}/agent_final_response", timeout=150)
    except RuntimeError:
        final = {}
    got_files = _download_submission(workdir, Path(out_dir))
    # Cleanup: interrupt if still running, then delete the conversation.
    # Cleanup failures never fail the run - the submission is already local.
    try:
        if status not in TERMINAL:
            _remote_api("POST", f"/api/conversations/{cid}/interrupt", {}, timeout=60)
        _remote_api("DELETE", f"/api/conversations/{cid}", timeout=90)
        _ssh(f"rm -rf {shlex.quote(workdir)}")
    except RuntimeError:
        pass

    if got_files:
        outcome = run_verification(task_dir, Path(out_dir))
    else:
        outcome = {
            "schema_version": "crucible.reliable_completion.v1",
            "instance_id": task_dir.name,
            "reliable_completion": False, "abstained": False,
            "endpoint_acceptable": False, "artifacts_reproduce": False,
            "material_claims_grounded": False,
            "critical_scientific_failures": [], "critical_operational_failures": [],
            "failed_gate_claim_ids": [],
            "integrity_problems": [f"product produced no final_submission (status {status})"],
            "human_escalations": [], "adjudication_status": "FINAL",
            "diagnostic_profiles": {}, "leaf_results": [],
        }
    outcome["agent"] = {
        "provider": "marigold", "model": "marigold-native (base gpt-5.6-sol, 48 tools)",
        "conversation_id": cid, "execution_status": status,
        "final_response_excerpt": str(final)[:2000],
        "verification_gate": False, "attempts": 1,
    }
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / "run_summary.json").write_text(
        json.dumps(outcome["agent"], indent=2), encoding="utf-8"
    )
    return outcome


def oneshot(prompt: str, budget_minutes: int = 10) -> str:
    """Single-question native run (for Tracks D/E): returns the final response text."""
    _wait_for_host()
    workdir = f"{REMOTE_ROOT}/oneshot-{int(time.time())}"
    _ssh(f"mkdir -p {workdir}")
    body = {
        "workspace": {"kind": "LocalWorkspace", "working_dir": workdir},
        "confirmation_policy": {"kind": "NeverConfirm"},
        "initial_message": {"role": "user", "content": [{"type": "text", "text": prompt}],
                            "run": False},
        "tags": {"suite": "crucible", "task": "oneshot"},
    }
    created = _remote_api("POST", "/api/conversations", body, timeout=300)
    cid = created.get("id") or created.get("conversation_id")
    if not cid:
        raise RuntimeError(f"oneshot create failed: {str(created)[:300]}")
    _remote_api("POST", f"/api/conversations/{cid}/run", {}, timeout=60)
    deadline = time.time() + budget_minutes * 60
    while time.time() < deadline:
        time.sleep(20)
        try:
            info = _remote_api("GET", f"/api/conversations/{cid}", timeout=60)
        except RuntimeError:
            continue
        if str(info.get("execution_status") or "") in TERMINAL:
            break
    final = _remote_api("GET", f"/api/conversations/{cid}/agent_final_response", timeout=60)
    _remote_api("DELETE", f"/api/conversations/{cid}", timeout=60)
    if isinstance(final, dict):
        return str(final.get("content") or final.get("text") or final.get("response") or final)
    return str(final)
