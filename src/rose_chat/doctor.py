from __future__ import annotations

import importlib
import os
import shutil
import sys


def _check_python() -> tuple[bool, str]:
    version = sys.version_info
    ok = (version.major, version.minor) == (3, 12)
    details = f"{version.major}.{version.minor}.{version.micro}"
    if ok:
        return True, f"Python version OK: {details}"
    return False, f"Expected Python 3.12.x but got {details}"


def _check_env_keys() -> tuple[bool, str]:
    required = ["GEMINI_API_KEY", "ELEVENLABS_API_KEY"]
    missing = [key for key in required if not os.getenv(key)]
    if not missing:
        return True, "Required API keys are present"
    return False, f"Missing environment variables: {', '.join(missing)}"


def _check_linux_runtime() -> tuple[bool, str]:
    if os.name != "posix":
        return True, "Non-Linux host, Linux runtime checks skipped"

    if not os.getenv("DISPLAY") and not os.getenv("WAYLAND_DISPLAY"):
        return False, "No GUI session detected (DISPLAY/WAYLAND_DISPLAY not set)"

    if shutil.which("xdg-open") is None:
        return False, "xdg-open not found (install xdg-utils)"

    return True, "Linux desktop runtime looks ready"


def _check_import(module_name: str, package_name: str | None = None) -> tuple[bool, str]:
    try:
        importlib.import_module(module_name)
        return True, f"Import OK: {module_name}"
    except Exception as exc:
        install_name = package_name or module_name
        return False, f"Cannot import {module_name}: {exc} (install/repair '{install_name}')"


def _check_audio_devices() -> tuple[bool, str]:
    try:
        import speech_recognition as sr
    except Exception as exc:
        return False, f"speech_recognition unavailable: {exc}"

    try:
        microphones = sr.Microphone.list_microphone_names()
    except Exception as exc:
        return False, f"Cannot list microphones: {exc}"

    if not microphones:
        return False, "No microphone devices detected"

    return True, f"Detected {len(microphones)} microphone device(s)"


def _check_pygame_mixer() -> tuple[bool, str]:
    try:
        import pygame

        pygame.mixer.init()
        pygame.mixer.quit()
        return True, "pygame mixer initialized successfully"
    except Exception as exc:
        return False, f"pygame mixer initialization failed: {exc}"


def run_checks() -> int:
    checks = [
        _check_python,
        _check_env_keys,
        _check_linux_runtime,
        lambda: _check_import("google.genai", "google-genai"),
        lambda: _check_import("elevenlabs", "elevenlabs"),
        lambda: _check_import("webview", "pywebview"),
        lambda: _check_import("pyaudio", "pyaudio"),
        _check_audio_devices,
        _check_pygame_mixer,
    ]

    failures = 0
    print("Rose Chat Pi diagnostics")
    print("========================")
    for check in checks:
        ok, message = check()
        label = "PASS" if ok else "FAIL"
        print(f"[{label}] {message}")
        if not ok:
            failures += 1

    if failures:
        print(f"\nDiagnostics completed with {failures} failure(s).")
        return 1

    print("\nDiagnostics completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_checks())
