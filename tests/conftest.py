from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for path in [
    ROOT / ".vendor",
    ROOT / "apps",
    ROOT / "apps" / "shared" / "v1_0_0",
]:
    sys.path.insert(0, str(path))
