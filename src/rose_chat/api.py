from __future__ import annotations

import os
import base64
import subprocess
import shutil
import tempfile
import time
import uuid
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from .config import (
    ACTION_PATTERN,
    DEFAULT_ELEVENLABS_VOICE_ID,
    GEMINI_MODEL,
    GEMINI_TEMPERATURE,
    GEMINI_TOP_P,
    PYGAME_HIDE_SUPPORT_PROMPT,
    SPEECH_LANGUAGE,
    SYSTEM_INSTRUCTION,
    TTS_MODEL,
)

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", PYGAME_HIDE_SUPPORT_PROMPT)

try:
    import pygame
except Exception:
    pygame = None  # type: ignore[assignment]

try:
    import speech_recognition as sr
except Exception:
    sr = None  # type: ignore[assignment]
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from google import genai
from google.genai import types

from .rooms import RoomManager


@dataclass(frozen=True)
class ActionCommand:
    kind: str
    value: str


class Api:
    def __init__(self) -> None:
        # AI generated comment: คลาสนี้คือสะพานหลักระหว่างหน้าเว็บกับระบบเสียง/AI ฝั่ง Python
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.generation_config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=GEMINI_TEMPERATURE,
            top_p=GEMINI_TOP_P,
        )
        self.rooms = RoomManager()
        self.recognizer = sr.Recognizer() if sr is not None else None
        self.tts_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE_ID)
        self._mixer_ready = False
        self.sample_rate = 16000

    def get_rooms(self) -> list[dict[str, object]]:
        return self.rooms.get_rooms()

    def create_room(self, name: str = "New Chat") -> dict[str, object]:
        return self.rooms.create_room(name)

    def delete_room(self, room_id: str) -> bool:
        return self.rooms.delete_room(room_id)

    def rename_room(self, room_id: str, new_name: str) -> dict[str, object]:
        return self.rooms.rename_room(room_id, new_name)

    def get_messages(self, room_id: str) -> list[dict[str, str]]:
        return self.rooms.get_messages(room_id)

    def clear_room(self, room_id: str) -> bool:
        return self.rooms.clear_room(room_id)

    def listen_once(self) -> str:
        # AI generated comment: ฟังเสียงหนึ่งรอบแล้วแปลงเป็นข้อความไทยด้วย Google speech recognition
        if sr is None or self.recognizer is None:
            raise RuntimeError("SpeechRecognition is not installed.")

        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=18)
                return self.recognizer.recognize_google(audio, language=SPEECH_LANGUAGE)
        except Exception:
            audio = self._record_audio_with_arecord(duration_seconds=8)
            return self.recognizer.recognize_google(audio, language=SPEECH_LANGUAGE)

    def speak_text(self, text: str) -> bool:
        speech = text.strip()
        if not speech:
            return False

        temp_path = Path(f"tts_{uuid.uuid4().hex}.mp3")
        try:
            audio_stream = self.tts_client.text_to_speech.convert(
                text=speech,
                voice_id=self.voice_id,
                model_id=TTS_MODEL,
            )

            with temp_path.open("wb") as audio_file:
                for chunk in audio_stream:
                    if chunk:
                        audio_file.write(chunk)

            self._ensure_mixer()
            if pygame is not None:
                pygame.mixer.music.load(str(temp_path))
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
            else:
                self._play_audio_file(temp_path)
            return True
        finally:
            try:
                if pygame is not None:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
            except Exception:
                pass
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    def synthesize_speech(self, text: str) -> dict[str, str]:
        # AI generated comment: ส่งเสียงกลับเป็น base64 เพื่อให้เว็บเล่นเสียงและขยับปาก avatar พร้อมกัน
        speech = text.strip()
        if not speech:
            raise ValueError("Speech text cannot be empty")

        audio = bytearray()
        audio_stream = self.tts_client.text_to_speech.convert(
            text=speech,
            voice_id=self.voice_id,
            model_id=TTS_MODEL,
        )
        for chunk in audio_stream:
            if chunk:
                audio.extend(chunk)

        return {
            "mime_type": "audio/mpeg",
            "base64": base64.b64encode(audio).decode("ascii"),
        }

    def send_message(self, room_id: str, user_message: str) -> str:
        # AI generated comment: flow หลักคือบันทึกเสียงผู้ใช้ ส่งเข้า AI แล้วจัดการ action ถ้ามี
        text = user_message.strip()
        if not text:
            raise ValueError("Message cannot be empty")

        try:
            self.rooms.add_message(room_id, "user", text)
            reply = self._generate_reply(room_id)

            action = self._parse_action(reply)
            if action:
                spoken_reply = self._do_action(action)
                self.rooms.add_message(room_id, "assistant", reply)
                return spoken_reply

            self.rooms.add_message(room_id, "assistant", reply)
            return reply
        except Exception as exc:
            error_text = f"Sorry, I could not get a response: {exc}"
            try:
                self.rooms.add_message(room_id, "assistant", error_text)
            except Exception:
                pass
            return error_text

    def _generate_reply(self, room_id: str) -> str:
        contents = self._build_contents(room_id)
        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=self.generation_config,
        )
        return (response.text or "").strip()

    def _build_contents(self, room_id: str) -> list[types.Content]:
        contents = []
        for message in self.rooms.get_messages(room_id):
            contents.append(
                types.Content(
                    role="user" if message["role"] == "user" else "model",
                    parts=[types.Part.from_text(text=message["content"])],
                )
            )
        return contents

    def _parse_action(self, reply: str) -> ActionCommand | None:
        match = ACTION_PATTERN.search(reply)
        if not match:
            return None

        kind = match.group(1)
        value = match.group(2)
        return ActionCommand(kind=kind.strip().lower(), value=value.strip())

    def _open_url(self, url: str) -> None:
        # AI generated comment: รองรับทั้ง Windows/Linux โดย fallback ไป xdg-open เมื่อจำเป็น
        if os.name == "nt":
            os.startfile(url)
            return

        if webbrowser.open_new_tab(url):
            return

        opener = shutil.which("xdg-open")
        if opener:
            subprocess.Popen([opener, url])

    def _ensure_mixer(self) -> None:
        if self._mixer_ready:
            return

        if pygame is None:
            self._mixer_ready = True
            return

        pygame.mixer.init()
        self._mixer_ready = True

    def _record_audio_with_arecord(self, duration_seconds: int) -> "sr.AudioData":
        if sr is None:
            raise RuntimeError("SpeechRecognition is not installed.")
        if shutil.which("arecord") is None:
            raise RuntimeError("arecord not found. Install alsa-utils for microphone fallback.")

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = Path(temp_file.name)
        temp_file.close()

        try:
            subprocess.run(
                [
                    "arecord",
                    "-q",
                    "-f",
                    "S16_LE",
                    "-r",
                    str(self.sample_rate),
                    "-c",
                    "1",
                    "-d",
                    str(duration_seconds),
                    str(temp_path),
                ],
                check=True,
            )
            with sr.AudioFile(str(temp_path)) as source:
                return self.recognizer.record(source)
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def _play_audio_file(self, path: Path) -> None:
        commands = [
            ["mpg123", str(path)],
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(path)],
            ["aplay", str(path)],
        ]

        for command in commands:
            if shutil.which(command[0]):
                subprocess.run(command, check=True)
                return

        raise RuntimeError(
            "No audio player found for fallback playback. Install mpg123 or ffmpeg on Raspberry Pi."
        )

    def _do_action(self, action: ActionCommand) -> str:
        # AI generated comment: ข้อความที่ return ตรงนี้จะถูกเอาไปพูดเป็นภาษาไทยแทน action tag
        if not action.value:
            return "โรสยังไม่เห็นสิ่งที่จะให้เปิดเลยนะ"

        if action.kind == "youtube":
            url = "https://www.youtube.com/results?search_query=" + quote_plus(action.value)
            self._open_url(url)
            return f"โรสเปิด YouTube ค้นหา {action.value} ให้แล้วนะ"

        if action.kind == "web":
            self._open_url(action.value)
            return "โรสเปิดเว็บให้แล้วนะ"

        if action.kind == "app":
            subprocess.Popen(action.value, shell=True)
            return "โรสเปิดแอปให้แล้วนะ"

        return "โรสยังเปิดสิ่งนี้ให้ไม่ได้นะ"
