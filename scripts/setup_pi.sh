#!/usr/bin/env bash
set -euo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but not found."
  exit 1
fi

if ! command -v apt >/dev/null 2>&1; then
  echo "This script is intended for Debian/Raspberry Pi OS (apt-based)."
  exit 1
fi

echo "Updating apt package index..."
sudo apt update

echo "Installing required system packages..."
sudo apt install -y \
  build-essential \
  pkg-config \
  python3-dev \
  python3.12-dev \
  libffi-dev \
  portaudio19-dev \
  libasound2-dev \
  libgtk-3-0 \
  libwebkit2gtk-4.1-0 \
  libsndfile1 \
  mpg123

echo "Creating virtual environment (.venv)..."
python3 -m venv .venv

echo "Installing Python dependencies for Raspberry Pi..."
".venv/bin/python" -m pip install --upgrade pip setuptools wheel
".venv/bin/python" -m pip install -r requirements.pi.txt

echo "Running readiness diagnostics..."
".venv/bin/python" -m rose_chat.doctor

cat <<'EOF'

Setup complete.

Next steps:
  source .venv/bin/activate
  cp env.example .env
  # Fill in GEMINI_API_KEY and ELEVENLABS_API_KEY in .env
  python main.py

EOF
