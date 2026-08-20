"""CRUCIBLE command-line interface (guide Appendix H, days 4-7).

Commands:
  crucible schema validate <kind> <file>
  crucible registry add-task <template.yaml>
  crucible registry transition <template_id> <new_status> --owner X --reason Y
  crucible registry list
  crucible audit verify-chain
  crucible task lint <task_dir>
  crucible task package <task_dir> <out_dir>
  crucible verify run <task_dir> <submission_dir> [--out results.json]
  crucible verify selftest <task_dir>

Every command emits machine-readable output and a nonzero exit code on failure.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .audit import AuditLog
from .lint import lint_task
from .packaging import build_agent_bundle, scan_for_truth
from .paths import registry_dir
from .registry import TaskRegistry, TransitionError
from .schemas import SCHEMA_KINDS, validate_file
from .selftest import run_selftests
from .verification import run_verification


def _emit(payload: dict, ok: bool) -> int:
    print(json.dumps(payload, indent=2, default=str))
    return 0 if ok else 1


def cmd_schema_validate(args: argparse.Namespace) -> int:
    errors = validate_file(args.kind, Path(args.file))
    return _emit({"command": "schema.validate", "kind": args.kind, "file": args.file,
                  "valid": not errors, "errors": errors}, not errors)


def cmd_registry_add(args: argparse.Namespace) -> int:
    registry = TaskRegistry()
    try:
        entry = registry.add_task(Path(args.template), actor=args.owner)
    except Exception as exc:  # noqa: BLE001
        return _emit({"command": "registry.add-task", "ok": False, "error": str(exc)}, False)
    return _emit({"command": "registry.add-task", "ok": True, "entry": entry}, True)


def cmd_registry_transition(args: argparse.Namespace) -> int:
    registry = TaskRegistry()
    try:
        entry = registry.transition(args.template_id, args.new_status,
                                    actor=args.owner, reason=args.reason)
    except TransitionError as exc:
        return _emit({"command": "registry.transition", "ok": False, "error": str(exc)}, False)
    return _emit({"command": "registry.transition", "ok": True, "entry": entry}, True)


def cmd_registry_list(args: argparse.Namespace) -> int:  # noqa: ARG001
    registry = TaskRegistry()
    tasks = registry.list_tasks()
    return _emit({"command": "registry.list", "count": len(tasks), "tasks": tasks}, True)


def cmd_audit_verify(args: argparse.Namespace) -> int:  # noqa: ARG001
    log = AuditLog(registry_dir() / "audit.jsonl")
    ok, problems = log.verify_chain()
    return _emit({"command": "audit.verify-chain", "ok": ok, "problems": problems}, ok)


def cmd_task_lint(args: argparse.Namespace) -> int:
    problems = lint_task(Path(args.task_dir))
    return _emit({"command": "task.lint", "task_dir": args.task_dir,
                  "ok": not problems, "problems": problems}, not problems)


def cmd_task_package(args: argparse.Namespace) -> int:
    task_dir = Path(args.task_dir)
    out_dir = Path(args.out_dir)
    try:
        copied = build_agent_bundle(task_dir, out_dir)
    except Exception as exc:  # noqa: BLE001
        return _emit({"command": "task.package", "ok": False, "error": str(exc)}, False)
    violations = scan_for_truth(out_dir, task_dir)
    ok = not violations
    return _emit({
        "command": "task.package",
        "ok": ok,
        "files_copied": len(copied),
        "truth_boundary_violations": violations,
    }, ok)


def cmd_verify_run(args: argparse.Namespace) -> int:
    outcome = run_verification(Path(args.task_dir), Path(args.submission_dir))
    if args.out:
        Path(args.out).write_text(json.dumps(outcome, indent=2, default=str), encoding="utf-8")
    return _emit(outcome, True)  # producing a verdict is success; the verdict itself may be negative


def cmd_verify_selftest(args: argparse.Namespace) -> int:
    report = run_selftests(Path(args.task_dir))
    return _emit(report, report["ok"])


def cmd_campaign_run(args: argparse.Namespace) -> int:
    from .campaign import run_campaign

    result = run_campaign(args.label)
    return _emit({"command": "campaign.run", "ok": True, **result}, True)


def cmd_usage(args: argparse.Namespace) -> int:  # noqa: ARG001
    from .llm import usage_summary

    return _emit({"command": "usage", "models": usage_summary()}, True)


def cmd_adjudicate(args: argparse.Namespace) -> int:
    from .adjudication import adjudicate

    report = adjudicate(Path(args.campaign_dir))
    return _emit({"command": "adjudicate", **report}, True)


def cmd_campaign_frontier(args: argparse.Namespace) -> int:
    from .frontier_campaign import run_frontier_campaign

    result = run_frontier_campaign(args.label)
    return _emit({"command": "campaign.frontier", "ok": True, **result}, True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="crucible",
                                     description="CRUCIBLE Phase 0 reference implementation")
    sub = parser.add_subparsers(dest="group", required=True)

    schema = sub.add_parser("schema", help="schema operations").add_subparsers(
        dest="action", required=True)
    validate = schema.add_parser("validate", help="validate a record against a schema")
    validate.add_argument("kind", choices=sorted(SCHEMA_KINDS))
    validate.add_argument("file")
    validate.set_defaults(func=cmd_schema_validate)

    registry = sub.add_parser("registry", help="task registry").add_subparsers(
        dest="action", required=True)
    add = registry.add_parser("add-task")
    add.add_argument("template")
    add.add_argument("--owner", required=True)
    add.set_defaults(func=cmd_registry_add)
    transition = registry.add_parser("transition")
    transition.add_argument("template_id")
    transition.add_argument("new_status")
    transition.add_argument("--owner", required=True)
    transition.add_argument("--reason", required=True)
    transition.set_defaults(func=cmd_registry_transition)
    listing = registry.add_parser("list")
    listing.set_defaults(func=cmd_registry_list)

    audit = sub.add_parser("audit", help="audit log").add_subparsers(dest="action", required=True)
    verify_chain = audit.add_parser("verify-chain")
    verify_chain.set_defaults(func=cmd_audit_verify)

    task = sub.add_parser("task", help="task operations").add_subparsers(dest="action", required=True)
    lint = task.add_parser("lint")
    lint.add_argument("task_dir")
    lint.set_defaults(func=cmd_task_lint)
    package = task.add_parser("package")
    package.add_argument("task_dir")
    package.add_argument("out_dir")
    package.set_defaults(func=cmd_task_package)

    campaign = sub.add_parser("campaign", help="evaluation campaigns").add_subparsers(
        dest="action", required=True)
    campaign_run = campaign.add_parser("run")
    campaign_run.add_argument("--label", default="release-0.2.0")
    campaign_run.set_defaults(func=cmd_campaign_run)
    campaign_frontier = campaign.add_parser("frontier")
    campaign_frontier.add_argument("--label", default="release-0.3.0")
    campaign_frontier.set_defaults(func=cmd_campaign_frontier)

    usage = sub.add_parser("usage", help="model usage totals")
    usage.set_defaults(func=cmd_usage)

    adjudicate = sub.add_parser("adjudicate", help="run the escalation adjudication queue")
    adjudicate.add_argument("campaign_dir")
    adjudicate.set_defaults(func=cmd_adjudicate)

    verify = sub.add_parser("verify", help="verification").add_subparsers(dest="action", required=True)
    run = verify.add_parser("run")
    run.add_argument("task_dir")
    run.add_argument("submission_dir")
    run.add_argument("--out")
    run.set_defaults(func=cmd_verify_run)
    selftest = verify.add_parser("selftest")
    selftest.add_argument("task_dir")
    selftest.set_defaults(func=cmd_verify_selftest)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
