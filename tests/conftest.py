from __future__ import annotations

import sys
from pathlib import Path
import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@pytest.fixture()
def example_files() -> dict[str, Path]:
    return {
        "dpl_demo_debug": PROJECT_ROOT
        / "example_files"
        / "dpl_demo_debug_linkinfo.xml",
        "enet_cli_debug": PROJECT_ROOT
        / "example_files"
        / "enet_cli_debug_linkinfo.xml",
    }
