# What is NOT done

As of ship 1.0 (campaign `runs/release-1.0.0`), one item is pending and one
class of work is out of scope by sponsor decision.

## Pending

Nothing. The 26 runs voided under CORR-003 (kimi-k3 12 sealed; qwen3.8-max
11 sealed + 3 hidden) were dropped by sponsor decision with reduced
denominators reported everywhere they appear - a content-blind
preregistration deviation documented in that correction.

Post-release quality work completed the same day: CORR-004 (grader
brittleness found via Marigold forensics; verifier v1.0.3; all 792 stored
submissions rescored, 22 grader false-negatives corrected across 7 systems)
and the Marigold product prompt iterated v1->v2->v3 with a full 28-run
re-benchmark per version.

Every 1.0 item is done and exercised end to end: 30 templates / 10
archetypes / 104 instances (16 development, 66 hidden, 22 sealed), card-leak
symmetry test, 828-run preregistered campaign over 8 API systems + the
Marigold native product, cross-family judge sample, cluster bootstrap
intervals, hidden-vs-sealed probe, corrections CORR-001/002/003 published,
restart-proof supervisor, release build with truth-marker leak scan.

## Out of scope by standing sponsor decision (not unimplemented work)

Real human scientists, real laboratory partnerships, and externally sealed
task cohorts. Documented with their consequences in `docs/LIMITATIONS.md`;
every scorecard carries the matching claim boundaries.
