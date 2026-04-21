from __future__ import annotations

import sys
from pathlib import Path

src_path = Path(__file__).resolve().parent / "src"
if src_path.is_dir():
    sys.path.insert(0, str(src_path))

from rose_chat.app import main

if __name__ == "__main__":
    main()
