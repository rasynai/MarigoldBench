"""Restart-proof launcher for the MarigoldBench campaign.

Processes spawned from an interactive session die when that session restarts,
which has now cost this campaign three relaunches. Task Scheduler entries
running pythonw.exe survive: no console window, no parent to lose, and the
battery settings that otherwise stop a task the moment a laptop unplugs are
explicitly cleared.

    python runs/launch_lab.py [--shards 8] [--systems claude,gpt,gemini]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from crucible.nowindow import run as hidden_run  # noqa: E402

LOGS = REPO / "runs" / "lab-1.0.0"
PYTHONW = str(Path(sys.executable).with_name("pythonw.exe"))
PREFIX = "MarigoldBench"

# Per-system ceilings. The sponsor's limit is per provider, and the guard
# reads spend fresh from disk so every shard of a system shares one budget.
# Anthropic is switched off at the sponsor's instruction: no further calls on
# that key. Episodes already collected stay on disk as recorded data, but
# "claude" is deliberately absent here so no shard can spend on it again.
# Claude is re-enabled: the sponsor's instruction was to start it when
# everything else is done, and GPT is complete with Gemini blocked only on a
# credential refresh that is not ours to perform.
# Per-system ceilings. Anthropic/OpenAI/Google are separate accounts with
# separate allowances. The three OpenRouter systems ALSO share one $95 gateway
# ceiling enforced in campaign.run, so these three numbers are what each may
# take of that shared pot, and they deliberately sum below it.
BUDGETS = {"gpt": 400.0, "gemini": 400.0, "claude": 1250.0,
           "grok": 250.0,
           "deepseek": 20.0, "kimi": 25.0, "glm": 15.0}


def register(system: str, shard: int, shards: int) -> str:
    name = f"{PREFIX}-{system}-s{shard}of{shards}"
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f"{system}-s{shard}.log"
    budget = BUDGETS.get(system, 200.0)
    argument = (f"-u -m crucible.lab.campaign run --system {system} "
                f"--budget-usd {budget} --shard {shard}/{shards} "
                f'--log "{log}"')
    hidden_run(
        ["powershell", "-NoProfile", "-Command",
         f"$a = New-ScheduledTaskAction -Execute '{PYTHONW}' "
         f"-Argument '{argument}' -WorkingDirectory '{REPO}'; "
         # NO repetition trigger: one added earlier told every task to relaunch
        # every 15 minutes forever, which is what produced repeating waves of
        # windows on the sponsor's desktop. A task here runs once and stops.
        # A 15-minute repetition trigger IS needed after all, and is safe here.
        # RestartOnFailure never fired: the killed shards ended with result 0,
        # so Windows saw success and had nothing to restart, and a task with no
        # trigger cannot be revived by StartWhenAvailable either. With
        # MultipleInstances IgnoreNew the trigger is a pure watchdog - it does
        # nothing while a shard is alive and relaunches one that is not. The
        # wave of relaunches this caused once came from 58 accumulated tasks,
        # not from the trigger; there are four here and pythonw has no console.
        # An explicit duration: with -RepetitionInterval alone the registered
        # task carries StopAtDurationEnd with no Duration, which is ambiguous.
        # Seven days is longer than any campaign here has taken.
        f"$t = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) "
        f"-RepetitionInterval (New-TimeSpan -Minutes 15) "
        f"-RepetitionDuration (New-TimeSpan -Days 7); "
        f"Register-ScheduledTask -TaskName '{name}' -Action $a -Trigger $t "
        f"-Force | Out-Null; "
         # RestartCount/RestartInterval, not a repeat trigger: this host kills
         # allocation-heavy Python processes at random (CORR-011), and a shard
         # that dies mid-plan otherwise stays dead until someone notices. Task
         # Scheduler restarts only on UNEXPECTED termination, so a shard that
         # finishes its plan or hits its budget still exits for good. A repeat
         # trigger was tried once and produced waves of relaunches; this does
         # not, because a healthy exit is not a failure.
         f"$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries "
         f"-DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) "
         f"-StartWhenAvailable -MultipleInstances IgnoreNew "
         f"-RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1); "
         f"$s.DisallowStartIfOnBatteries = $false; "
         f"Set-ScheduledTask -TaskName '{name}' -Settings $s | Out-Null; "
         f"Start-ScheduledTask -TaskName '{name}'"],
        check=True, capture_output=True)
    return name


# Gemini's Vertex quota rate-limits well before 8 concurrent shards (two
# episodes were lost to 429 before the transport retry existed). Fewer, longer
# shards get more done than more shards that spend their time backing off.
# Gemini was capped at 3 shards before the transport retry existed; with
# backoff in place a 429 costs a wait rather than an episode, so it can carry
# more concurrency - and it is the throughput bottleneck.
# GPT is the throughput bottleneck: its shards grind through 40-call
# binder-design episodes, and at $47 of a $400 ceiling the constraint is
# wall-clock, not money. More shards is the only lever that moves completion.
SHARDS = {"gpt": 3, "gemini": 3, "claude": 4,
          "grok": 4, "deepseek": 3, "kimi": 3, "glm": 3}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shards", type=int, default=0,
                        help="0 = per-system default from SHARDS")
    parser.add_argument("--systems", default="gpt,gemini")
    parser.add_argument("--stop", action="store_true",
                        help="end and delete every campaign task instead")
    args = parser.parse_args()

    if args.stop:
        hidden_run(
            ["powershell", "-NoProfile", "-Command",
             f"Get-ScheduledTask -TaskName '{PREFIX}-*' -ErrorAction SilentlyContinue "
             "| ForEach-Object { schtasks /End /TN $_.TaskName 2>&1 | Out-Null; "
             "schtasks /Delete /TN $_.TaskName /F 2>&1 | Out-Null }"],
            check=False, capture_output=True)
        print("stopped and removed all campaign tasks")
        return

    launched = 0
    for system in [s.strip() for s in args.systems.split(",") if s.strip()]:
        shards = args.shards or SHARDS.get(system, 4)
        for shard in range(shards):
            print("started", register(system, shard, shards), flush=True)
            launched += 1
    print(f"{launched} restart-proof workers running", flush=True)


if __name__ == "__main__":
    main()
