import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def lc_n0(repo_root: Path) -> Path:
    return repo_root / "tasks_public" / "CHEM-LC-CAL-001" / "instances" / "N0-s101"


@pytest.fixture
def lc_n1(repo_root: Path) -> Path:
    return repo_root / "tasks_public" / "CHEM-LC-CAL-001" / "instances" / "N1-s102"


@pytest.fixture
def ops_s1(repo_root: Path) -> Path:
    return repo_root / "tasks_public" / "OPS-AUTH-001" / "instances" / "S1-s201"
