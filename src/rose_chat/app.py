from __future__ import annotations

from pathlib import Path

import webview

from .api import Api
from .config import APP_TITLE, WINDOW_HEIGHT, WINDOW_MIN_SIZE, WINDOW_WIDTH


def project_root() -> Path:
    # AI generated comment: app.py อยู่ใน src/rose_chat เลยย้อนกลับไปหา root ของโปรเจกต์
    return Path(__file__).resolve().parents[2]


def main() -> None:
    index_file = project_root() / "web" / "index.html"

    # AI generated comment: PyWebView เปิดหน้าเว็บ local แล้วผูก Api ให้ JavaScript เรียก Python ได้
    webview.create_window(
        APP_TITLE,
        index_file.as_uri(),
        js_api=Api(),
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=WINDOW_MIN_SIZE,
    )
    webview.start(debug=False)
