# CORR-002 - Marigold runs voided for evaluation-infrastructure failure

- Date: 2026-08-16 (UTC). Scope: campaign release-0.3.0 (marigold stage,
  Track D/E marigold arm) and campaign release-1.0.0 (marigold shards).
- What happened: every Marigold run between ~01:00 and ~01:30 UTC failed at
  conversation creation with "MCP tool listing timed out after 120.0 seconds"
  (HTTP 500 from the agent server). No task was ever started, so these are
  failures of the evaluation infrastructure, not of the product under test.
- Root cause: an unrelated workload on the same GPU server
  (analyst/scripts/run_v4.py, 48 workers, started ~01:00 UTC by the sponsor's
  other project) drove the 15-min load average above 445, starving the agent
  server's MCP tool-listing subprocess past its 120 s timeout. Verified by
  process inspection (parent PID 3206989 spawning pyopenms jobs; uptime).
- Why voiding is allowed: the preregistrations count MODEL/product failures
  (API errors, no-submission) as failures. A create-time 500 from the harness
  host means the product received no work order; scoring it would measure the
  sponsor's server contention, not the product. Decision rule applied: any run
  whose only integrity problem is "conversation create failed: ... MCP tool
  listing timed out" is voided and re-run; no other run is touched; no
  outcome-dependent selection is possible because every affected run failed
  identically before task start.
- Affected and quarantined here:
  - release-1.0.0/marigold: 21 outcome files (all failures of this kind)
    + worker summary. Re-run from scratch after the host is idle.
  - release-0.3.0/marigold_outcomes.voided.json: all 5 rows failed this way.
    Stage re-runs after the host is idle; Track D/E marigold arm (None/0)
    re-asked the same way and is re-run marigold-only, other arms untouched.
- Prevention: before any future Marigold batch, the runner checks host load
  and refuses to start above load 24 (see release notes).
- Re-run environment: because the original host stayed saturated for hours,
  the sponsor authorized the second server (192.222.59.201, aarch64). The
  product was installed there from the same source and uv lockfile, same
  default_agent.json, same model routing (all model calls are API-side);
  verified healthy before use. Hardware differs (ARM vs x86) - irrelevant to
  the product's scientific behavior but disclosed here for completeness.
