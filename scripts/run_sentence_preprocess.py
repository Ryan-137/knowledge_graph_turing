from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["preprocess", "sentences", *sys.argv[1:]], repo_root=REPO_ROOT))
