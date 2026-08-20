"""How far did the environment dump spread? Counts only - never prints a key.

CORR-013: models exploring their sandbox ran code that printed os.environ, and
the sandbox inherited the parent process environment, so live API keys were
written into episode transcripts - and sent back to every provider as
conversation context on the following turn.
"""
import collections
import glob
import json
import re

PATS = {
    "ANTHROPIC": re.compile(r"sk-ant-api03-[A-Za-z0-9_\-]{20,}"),
    "OPENAI": re.compile(r"sk-proj-[A-Za-z0-9_\-]{20,}"),
    "OPENROUTER": re.compile(r"sk-or-v1-[a-f0-9]{40,}"),
    "NVIDIA": re.compile(r"nvapi-[A-Za-z0-9_\-]{30,}"),
    "XAI": re.compile(r"xai-[A-Za-z0-9]{40,}"),
    "HF": re.compile(r"hf_[A-Za-z0-9]{30,}"),
    "GOOGLE_TOKEN": re.compile(r"ya29\.[A-Za-z0-9_\-]{40,}"),
}


def main() -> None:
    by_system = collections.Counter()
    which = collections.Counter()
    affected = []
    for path in glob.glob("runs/**/*.json", recursive=True):
        try:
            with open(path, encoding="utf-8", errors="ignore") as handle:
                text = handle.read()
        except OSError:
            continue
        found = [name for name, pat in PATS.items() if pat.search(text)]
        if not found:
            continue
        affected.append(path)
        for name in found:
            which[name] += 1
        parts = path.replace("\\", "/").split("/")
        system = (parts[parts.index("systems") + 1]
                  if "systems" in parts else parts[1])
        by_system[system] += 1
    print(json.dumps({"files_containing_a_live_key": len(affected),
                      "by_system": dict(by_system.most_common()),
                      "which_credentials": dict(which)}, indent=1))
    with open("runs/_leaked_files.txt", "w", encoding="utf-8") as handle:
        handle.write("\n".join(affected))


if __name__ == "__main__":
    main()
