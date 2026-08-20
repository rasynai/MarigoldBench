"""Redact live credentials that models dumped into episode transcripts.

CORR-013. The value is replaced with a marker of the same shape, so the record
still shows that the model read a key and what kind, but the key itself is
gone. Verdicts, checkpoints, costs and usage are untouched: the redaction only
rewrites characters inside `transcript` and `reasoning` text.
"""
import glob
import json
import re

PATS = {
    "ANTHROPIC": re.compile(r"sk-ant-api03-[A-Za-z0-9_\-]{20,}"),
    "OPENAI": re.compile(r"sk-proj-[A-Za-z0-9_\-]{20,}"),
    "OPENROUTER": re.compile(r"sk-or-v1-[A-Za-z0-9_\-]{20,}"),
    "NVIDIA": re.compile(r"nvapi-[A-Za-z0-9_\-]{20,}"),
    "XAI": re.compile(r"xai-[A-Za-z0-9]{20,}"),
    "HF": re.compile(r"hf_[A-Za-z0-9]{20,}"),
    "GOOGLE_TOKEN": re.compile(r"ya29\.[A-Za-z0-9_\-]{20,}"),
    # A partially-truncated key is still a partially-leaked key.
    "TRUNCATED": re.compile(r"sk-(?:ant-api03|proj|or-v1)-[A-Za-z0-9_\-]{8,19}"),
}


def redact(text: str) -> tuple[str, int]:
    total = 0
    for name, pat in PATS.items():
        text, n = pat.subn(f"[REDACTED-{name}-KEY-CORR-013]", text)
        total += n
    return text, total


def main() -> None:
    changed = 0
    replacements = 0
    for path in glob.glob("runs/**/*.json", recursive=True):
        try:
            with open(path, encoding="utf-8") as handle:
                raw = handle.read()
        except (OSError, UnicodeDecodeError):
            continue
        clean, n = redact(raw)
        if not n:
            continue
        try:
            json.loads(clean)          # never write a file we just broke
        except json.JSONDecodeError:
            print("SKIPPED (would corrupt):", path)
            continue
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(clean)
        changed += 1
        replacements += n
    print(json.dumps({"files_rewritten": changed,
                      "values_redacted": replacements}))


if __name__ == "__main__":
    main()
