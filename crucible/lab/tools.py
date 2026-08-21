"""The tool belt MarigoldBench hands to a candidate model.

Design rules, each traceable to a bar in GOAL.md:

- **Real tools, real failures.** A tool that fails returns its actual error to
  the model. Recovering from a genuine service error is part of the science
  (B9), so errors are never smoothed away or retried behind the model's back.
- **Docstrings are candidate-visible, so they are gated.** A tool description
  that names the method to use, or warns which path is wrong, is a giveaway
  exactly like a prompt recipe (B3). `giveaway_scan` runs over these strings.
- **Record/replay.** Every live call is recorded; scoring and re-scoring replay
  from the record. A verifier that needs a live service is not deterministic,
  and the whole benchmark rests on recomputation (B2).
- **Free by construction.** Every hosted tool here is on NVIDIA's free NIM
  tier, so a >=100-family agentic benchmark costs only candidate tokens.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from ..paths import find_repo_root
from ..nowindow import hidden_kwargs

NIM_BASE = "https://health.api.nvidia.com/v1/biology"
TIMEOUT = 300


class ToolError(RuntimeError):
    """A tool failed. The message is shown to the candidate verbatim."""


def _key() -> str:
    from ..llm import load_keys
    load_keys()
    key = os.environ.get("NVIDIA_API_KEY")
    if not key:
        raise ToolError("no NVIDIA_API_KEY configured")
    return key


def _digest(name: str, payload: dict) -> str:
    blob = name + json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


@dataclass
class ToolBelt:
    """Dispatches tool calls, records every one, and enforces the step budget.

    `cache_dir` makes identical calls free and instant across re-scoring and
    across candidates - which also means two systems that make the same call
    get byte-identical tool output, removing a source of variance that has
    nothing to do with their judgment.
    """

    workspace: Path
    budget: int = 25
    cache_dir: Path | None = None
    transcript: list[dict] = field(default_factory=list)
    _calls: int = 0

    def __post_init__(self):
        self.workspace = Path(self.workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)
        if self.cache_dir is None:
            self.cache_dir = find_repo_root() / "runs" / "toolcache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ core

    @property
    def calls_used(self) -> int:
        return self._calls

    def _post(self, name: str, path: str, payload: dict) -> dict:
        cached = self.cache_dir / f"{_digest(name, payload)}.json"
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))
        request = urllib.request.Request(
            f"{NIM_BASE}/{path}", data=json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {_key()}",
                     "Content-Type": "application/json",
                     "Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                body = json.loads(response.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            detail = exc.read(600).decode("utf-8", "replace")
            raise ToolError(f"{name} failed with HTTP {exc.code}: {detail[:400]}") from None
        except Exception as exc:  # noqa: BLE001
            raise ToolError(f"{name} unavailable: {type(exc).__name__}: {exc}") from None
        cached.write_text(json.dumps(body), encoding="utf-8")
        return body

    @staticmethod
    def _coerce(handler: Callable, kwargs: dict) -> dict:
        """Coerce arguments to their annotated types.

        Tool arguments arrive as model-generated JSON, and models routinely
        emit `"6000"` where an int is declared. Letting that raise crashes the
        episode and scores a harness defect as a model failure - exactly the
        confound bar B10 exists to prevent. Genuinely un-coercible values are
        left alone so the tool raises a real, informative ToolError.
        """
        import inspect

        coerced = dict(kwargs)
        for param in list(inspect.signature(handler).parameters.values())[1:]:
            if param.name not in coerced:
                continue
            value = coerced[param.name]
            # `from __future__ import annotations` makes every annotation a
            # string, so compare by name rather than by identity.
            target = param.annotation
            name = target if isinstance(target, str) else getattr(target, "__name__", "")
            try:
                if name.startswith("int") and not isinstance(value, bool):
                    coerced[param.name] = int(float(value))
                elif name.startswith("float"):
                    coerced[param.name] = float(value)
                elif name.startswith("bool") and isinstance(value, str):
                    coerced[param.name] = value.strip().lower() in ("true", "1", "yes")
                elif name.startswith("str") and isinstance(value, (int, float)):
                    coerced[param.name] = str(value)
            except (TypeError, ValueError):
                pass
        return coerced

    def call(self, name: str, **kwargs) -> Any:
        """Run one tool. Budget and transcript are enforced here, once."""
        if self._calls >= self.budget:
            raise ToolError(
                f"step budget exhausted ({self.budget} tool calls). Submit your "
                "result with what you have, or state why you cannot.")
        self._calls += 1
        started = time.time()
        entry: dict = {"n": self._calls, "tool": name, "args": _summarise(kwargs)}
        try:
            handler = TOOLS.get(name)
            if handler is None:
                raise ToolError(f"unknown tool {name!r}; available: {sorted(TOOLS)}")
            result = handler(self, **self._coerce(handler, kwargs))
            entry["ok"] = True
            entry["result"] = _summarise(result)
            return result
        except ToolError as exc:
            entry["ok"] = False
            entry["error"] = str(exc)[:500]
            raise
        except Exception as exc:  # noqa: BLE001
            # A malformed argument is the model's problem to notice and fix,
            # not grounds for voiding the episode. Surface it as a tool error
            # so the loop continues and the recovery is what gets measured.
            entry["ok"] = False
            entry["error"] = f"{type(exc).__name__}: {str(exc)[:300]}"
            raise ToolError(
                f"{name} rejected your arguments: {type(exc).__name__}: "
                f"{str(exc)[:300]}") from None
        finally:
            entry["seconds"] = round(time.time() - started, 2)
            self.transcript.append(entry)


def _summarise(value: Any, limit: int = 300) -> Any:
    """Transcripts must stay readable: structures are kept, blobs are clipped."""
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + f"...<{len(value)} chars>"
    if isinstance(value, dict):
        return {k: _summarise(v, limit) for k, v in list(value.items())[:12]}
    if isinstance(value, (list, tuple)):
        head = [_summarise(v, limit) for v in value[:4]]
        return head + ([f"...<{len(value)} items>"] if len(value) > 4 else [])
    return value


# ------------------------------------------------------------------ the tools
# Docstrings are shown to the candidate. They state WHAT a tool does and what
# it returns - never which tool to use, in what order, or what to distrust.

def esmfold(belt: ToolBelt, sequence: str) -> str:
    """Predict a 3D structure from a single protein sequence. Returns PDB text."""
    body = belt._post("esmfold", "nvidia/esmfold", {"sequence": sequence})
    pdbs = body.get("pdbs") or []
    if not pdbs:
        raise ToolError(f"esmfold returned no structure: {str(body)[:200]}")
    return pdbs[0]


def boltz2(belt: ToolBelt, sequence: str, ligand_smiles: str | None = None,
           recycling_steps: int = 3, sampling_steps: int = 50) -> dict:
    """Co-fold a protein (optionally with a ligand) and return the predicted
    complex plus confidence metrics. Returns {'structure': mmCIF, 'confidence': ...}."""
    payload: dict = {
        "polymers": [{"id": "A", "molecule_type": "protein", "sequence": sequence}],
        "recycling_steps": recycling_steps, "sampling_steps": sampling_steps,
        "diffusion_samples": 1}
    if ligand_smiles:
        payload["ligands"] = [{"id": "L", "smiles": ligand_smiles}]
    body = belt._post("boltz2", "mit/boltz2/predict", payload)
    structures = body.get("structures") or []
    if not structures:
        raise ToolError(f"boltz2 returned no structure: {str(body)[:200]}")
    return {"structure": structures[0].get("structure", ""),
            "confidence": body.get("confidence_scores") or structures[0].get("confidence")}


def rfdiffusion(belt: ToolBelt, input_pdb: str, contigs: str,
                hotspot_res: list[str] | None = None,
                diffusion_steps: int = 15) -> str:
    """Generate a protein backbone conditioned on a template PDB and a contig
    specification. Returns PDB text of the designed backbone."""
    body = belt._post("rfdiffusion", "ipd/rfdiffusion/generate", {
        "input_pdb": input_pdb, "contigs": contigs,
        "hotspot_res": hotspot_res or [], "diffusion_steps": diffusion_steps})
    pdb = body.get("output_pdb") or body.get("pdb")
    if not pdb:
        raise ToolError(f"rfdiffusion returned no backbone: {str(body)[:200]}")
    return pdb


def proteinmpnn(belt: ToolBelt, input_pdb: str, num_seq_per_target: int = 4,
                sampling_temp: float = 0.1, ca_only: bool = False) -> str:
    """Design amino-acid sequences for a given backbone (inverse folding).
    Returns a FASTA string of candidate sequences with scores."""
    body = belt._post("proteinmpnn", "ipd/proteinmpnn/predict", {
        "input_pdb": input_pdb, "ca_only": ca_only, "use_soluble_model": False,
        "num_seq_per_target": num_seq_per_target, "sampling_temp": [sampling_temp]})
    fasta = body.get("mfasta")
    if not fasta:
        raise ToolError(f"proteinmpnn returned no sequences: {str(body)[:200]}")
    return fasta


def diffdock(belt: ToolBelt, protein_pdb: str, ligand: str,
             ligand_file_type: str = "sdf", num_poses: int = 5,
             steps: int = 18) -> dict:
    """Dock a ligand into a protein structure. Returns predicted poses and
    the model's own confidence for each."""
    body = belt._post("diffdock", "mit/diffdock", {
        "protein": protein_pdb, "ligand": ligand,
        "ligand_file_type": ligand_file_type, "num_poses": num_poses,
        "time_divisions": 20, "steps": steps})
    if "ligand_positions" not in body and "trajectory" not in body:
        raise ToolError(f"diffdock returned no poses: {str(body)[:200]}")
    return {"poses": body.get("ligand_positions"),
            "confidence": body.get("position_confidence")}


def molmim_optimize(belt: ToolBelt, smiles: str, property_name: str = "QED",
                    num_molecules: int = 10, min_similarity: float = 0.7,
                    iterations: int = 10) -> list[dict]:
    """Optimise a molecule against a scalar property while staying similar to
    the seed. Returns a list of {'sample': SMILES, 'score': float}."""
    body = belt._post("molmim", "nvidia/molmim/generate", {
        "smi": smiles, "num_molecules": num_molecules, "algorithm": "CMA-ES",
        "property_name": property_name, "min_similarity": min_similarity,
        "iterations": iterations})
    raw = body.get("molecules")
    if isinstance(raw, str):
        raw = json.loads(raw)
    if not raw:
        raise ToolError(f"molmim returned no molecules: {str(body)[:200]}")
    return raw


def genmol(belt: ToolBelt, smiles_fragment: str, num_molecules: int = 10,
           temperature: float = 1.0, scoring: str = "QED") -> list[dict]:
    """Generate molecules from a fragment/scaffold specification (SAFE syntax,
    e.g. '[*{25-25}]' for de novo). Returns generated SMILES with scores."""
    body = belt._post("genmol", "nvidia/genmol/generate", {
        "smiles": smiles_fragment, "num_molecules": num_molecules,
        "temperature": temperature, "noise": 0.0, "step_size": 1,
        "scoring": scoring})
    mols = body.get("molecules")
    if not mols:
        raise ToolError(f"genmol returned nothing: {str(body)[:200]}")
    return mols


# ------------------------------------------------------- local, free, instant

def rdkit_properties(belt: ToolBelt, smiles: str) -> dict:
    """Compute standard cheminformatics descriptors for a molecule."""
    from rdkit import Chem
    from rdkit.Chem import Crippen, Descriptors, QED, rdMolDescriptors
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ToolError(f"could not parse SMILES {smiles!r}")
    return {
        "mw": round(Descriptors.MolWt(mol), 2),
        "clogp": round(Crippen.MolLogP(mol), 3),
        "tpsa": round(rdMolDescriptors.CalcTPSA(mol), 2),
        "hbd": rdMolDescriptors.CalcNumHBD(mol),
        "hba": rdMolDescriptors.CalcNumHBA(mol),
        "rotatable_bonds": rdMolDescriptors.CalcNumRotatableBonds(mol),
        "rings": rdMolDescriptors.CalcNumRings(mol),
        "qed": round(QED.qed(mol), 4),
        "heavy_atoms": mol.GetNumHeavyAtoms(),
        "formula": rdMolDescriptors.CalcMolFormula(mol),
    }


# Environment variables the sandbox is allowed to see. CORR-013: the sandbox
# used to inherit the parent's environment, so a model that printed os.environ
# read every provider key on the machine - and the dump then went back to that
# provider as conversation context on the next turn. A model-run process needs
# a path, a temp directory and a locale; it never needs a credential.
SANDBOX_ENV_ALLOW = ("PATH", "SYSTEMROOT", "SystemRoot", "COMSPEC", "TEMP",
                     "TMP", "TMPDIR", "HOME", "USERPROFILE", "LANG", "LC_ALL",
                     "PYTHONIOENCODING", "NUMBER_OF_PROCESSORS", "OS",
                     "PROCESSOR_ARCHITECTURE", "WINDIR")

# Any variable whose name looks like a secret is denied even if some future
# edit adds it to the allow-list: an allow-list plus a deny-check fails safe.
SECRET_MARKERS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL", "AUTH",
                  "COOKIE", "SESSION", "PRIVATE")


# CORR-014: the sandbox confined the file TOOL and not the interpreter, so
# model-authored code could read anything the harness could: 371 episodes
# reached the network, 42 used one of our provider keys, 6 swept the operator's
# home directory, and one read the grader for the task it was being scored on.
# An audit hook cannot be unregistered once installed, so this prelude runs
# before the model's code and stays in force. Imports still need the Python
# installation, so reads are allowed there and denied under the repository.
SANDBOX_PRELUDE = '''
import sys as _sys, os as _os
_WORKSPACE = _os.path.realpath(r"{workspace}")
_ALLOWED_READ = tuple(_os.path.realpath(p) for p in
                      (_sys.prefix, _sys.base_prefix, _os.path.dirname(_os.__file__))
                      if p)
# ctypes.dlopen and winreg.OpenKey are NOT here: numpy, torch and rdkit load
# native libraries through them, and denying those turns the lockdown into an
# outage. The probe in runs/_probe_sandbox.py exists to catch that.
_DENY_EVENTS = ("socket.connect", "socket.getaddrinfo", "socket.gethostbyname",
                "urllib.Request", "http.client.connect", "ftplib.connect",
                "subprocess.Popen", "os.exec", "os.posix_spawn", "os.system",
                "os.fork")
# Listing a directory is not an "open" event, and reading the operator's home
# directory in six episodes was done with os.listdir.
_PATH_EVENTS = ("os.listdir", "os.scandir", "pathlib.Path.glob",
                "pathlib.Path.rglob", "glob.glob", "os.walk")


def _guard(event, args):
    if event in _DENY_EVENTS:
        raise PermissionError(
            "the sandbox has no network and cannot spawn processes; use the "
            "provided tools for folding, docking and design")
    if event in _PATH_EVENTS or event == "open":
        target = args[0] if args else None
        if hasattr(target, "__fspath__"):
            target = target.__fspath__()
        if isinstance(target, (str, bytes)):
            if isinstance(target, bytes):
                target = target.decode("utf-8", "replace")
            try:
                full = _os.path.realpath(target)
            except (OSError, ValueError):
                return
            if full.startswith(_WORKSPACE):
                return
            if any(full.startswith(root) for root in _ALLOWED_READ):
                return
            mode = args[1] if len(args) > 1 and isinstance(args[1], str) else "r"
            if event != "open":
                raise PermissionError(
                    "the sandbox can only list directories inside its own "
                    "workspace")
            if any(flag in mode for flag in "wax+"):
                raise PermissionError(
                    "the sandbox can only write inside its own workspace")
            raise PermissionError(
                "the sandbox can only read files inside its own workspace")


_sys.addaudithook(_guard)
del _guard
'''


def _sandbox_env() -> dict:
    """A minimal environment for model-authored code: no credentials in it."""
    import os
    env = {}
    for name in SANDBOX_ENV_ALLOW:
        value = os.environ.get(name)
        if value is None:
            continue
        if any(marker in name.upper() for marker in SECRET_MARKERS):
            continue
        env[name] = value
    env.setdefault("PYTHONIOENCODING", "utf-8")
    # Keep the interpreter's own import machinery working when the harness is
    # run from a source checkout rather than an installed package.
    env["PYTHONNOUSERSITE"] = "1"
    return env


def run_python(belt: ToolBelt, code: str, timeout: int = 240) -> dict:
    """Execute Python in the workspace directory. numpy, pandas, scipy,
    scikit-learn, torch, rdkit and networkx are importable. Returns stdout,
    stderr and the exit status. Files you write persist for later calls."""
    import os
    import subprocess
    import sys
    script = belt.workspace / "_step.py"
    # The workspace path goes into a raw string literal in the prelude, so the
    # backslashes are already safe; nothing to escape here.
    prelude = SANDBOX_PRELUDE.format(workspace=str(belt.workspace.resolve()))
    script.write_text(prelude + "\n" + code, encoding="utf-8")
    # CREATE_NO_WINDOW: without it, every sandbox call from a windowless
    # worker flashes a console window onto the desktop. With many workers each
    # running model-authored code, that is a constant interruption for whoever
    # is using the machine.
    try:
        proc = subprocess.run(
            [sys.executable, "-u", str(script)], cwd=str(belt.workspace),
            capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace", env=_sandbox_env(),
            **hidden_kwargs())
    except subprocess.TimeoutExpired:
        raise ToolError(f"python execution exceeded {timeout}s") from None
    return {"stdout": proc.stdout[-4000:], "stderr": proc.stderr[-2000:],
            "exit_code": proc.returncode}


def read_file(belt: ToolBelt, path: str, max_bytes: int = 6000) -> str:
    """Read a file from the workspace."""
    target = (belt.workspace / path).resolve()
    if not str(target).startswith(str(belt.workspace.resolve())):
        raise ToolError("path escapes the workspace")
    if not target.exists():
        raise ToolError(f"no such file: {path}")
    return target.read_text(encoding="utf-8", errors="replace")[:max_bytes]


def list_files(belt: ToolBelt) -> list[str]:
    """List the files available in the workspace."""
    return sorted(str(p.relative_to(belt.workspace)).replace("\\", "/")
                  for p in belt.workspace.rglob("*") if p.is_file())


TOOLS: dict[str, Callable] = {
    "esmfold": esmfold,
    "boltz2": boltz2,
    "rfdiffusion": rfdiffusion,
    "proteinmpnn": proteinmpnn,
    "diffdock": diffdock,
    "molmim_optimize": molmim_optimize,
    "genmol": genmol,
    "rdkit_properties": rdkit_properties,
    "run_python": run_python,
    "read_file": read_file,
    "list_files": list_files,
}


def tool_schemas() -> list[dict]:
    """OpenAI/Anthropic-style function schemas, generated from the signatures
    so the advertised interface cannot drift from the implementation."""
    import inspect
    schemas = []
    for name, fn in sorted(TOOLS.items()):
        signature = inspect.signature(fn)
        properties: dict = {}
        required: list[str] = []
        for param_name, param in list(signature.parameters.items())[1:]:  # skip belt
            annotation = param.annotation
            kind = "string"
            if annotation in (int,):
                kind = "integer"
            elif annotation in (float,):
                kind = "number"
            elif annotation in (bool,):
                kind = "boolean"
            elif annotation in (list, "list[str]") or "list" in str(annotation):
                kind = "array"
            entry: dict = {"type": kind}
            if kind == "array":
                entry["items"] = {"type": "string"}
            properties[param_name] = entry
            if param.default is inspect.Parameter.empty:
                required.append(param_name)
        schemas.append({
            "name": name,
            "description": (inspect.getdoc(fn) or "").strip(),
            "input_schema": {"type": "object", "properties": properties,
                             "required": required},
        })
    return schemas
