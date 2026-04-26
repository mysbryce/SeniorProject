from __future__ import annotations

import sys
from pathlib import Path

# AI generated comment: ไฟล์นี้ช่วยให้รันจาก root ได้เลย โดยไม่ต้องติดตั้งแพ็กเกจก่อน
src_path = Path(__file__).resolve().parent / "src"
if src_path.is_dir():
    sys.path.insert(0, str(src_path))

from rose_chat.app import main as app_main
from rose_chat.voice_cli import main as voice_cli_main

if __name__ == "__main__":
    try:
        app_main()
    except RuntimeError as exc:
        if "pywebview is not available" not in str(exc):
            raise
        print("GUI mode unavailable, switching to voice CLI mode.")
        voice_cli_main()
