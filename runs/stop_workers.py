"""End campaign workers and PROVE they are gone.

CORR-012: the previous stop was an inline PowerShell one-liner built inside a
`python -c` string. The quoting mangled `$_.TaskName` into `\$_.TaskName`, so
every schtasks call matched nothing, `Out-Null` hid the errors, and the script
printed success anyway - three workers ran on for four hours and spent $30 on a
route that had just been forbidden. This runs from a file, prints every return
code, and ends by listing what is still registered.

    python runs/stop_workers.py            # everything
    python runs/stop_workers.py grok-or    # only tasks matching a substring
"""
import subprocess, sys
sys.path.insert(0, 'A:/PERTURB-Bench')
from crucible.nowindow import hidden_kwargs

BACKSLASH = chr(92)

def tasks():
    out = subprocess.run(["schtasks", "/Query", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True, **hidden_kwargs()).stdout
    found = set()
    for line in out.splitlines():
        if "MarigoldBench" in line:
            name = line.split('","')[0].strip('"')
            found.add(name.lstrip(BACKSLASH))
    return sorted(found)

match = sys.argv[1] if len(sys.argv) > 1 else ""
present = tasks()
print("campaign tasks present:", present)
for name in present:
    if match in name:
        for args in (["schtasks", "/End", "/TN", name],
                     ["schtasks", "/Delete", "/TN", name, "/F"]):
            r = subprocess.run(args, capture_output=True, text=True, **hidden_kwargs())
            print(args[1], name, "rc=", r.returncode,
                  (r.stdout or r.stderr).strip()[:70])
remaining = [n for n in tasks() if match in n]
print("tasks remaining after stop:", remaining)
sys.exit(1 if remaining else 0)
