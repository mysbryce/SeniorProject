from __future__ import annotations

import os
import base64
import subprocess
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

import pygame
import speech_recognition as sr
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
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.generation_config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=GEMINI_TEMPERATURE,
            top_p=GEMINI_TOP_P,
        )
        self.rooms = RoomManager()
        self.recognizer = sr.Recognizer()
        self.tts_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE_ID)
        self._mixer_ready = False

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
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=18)

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
            pygame.mixer.music.load(str(temp_path))
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            return True
        finally:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
            except pygame.error:
                pass
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    def synthesize_speech(self, text: str) -> dict[str, str]:
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
        if os.name == "nt":
            os.startfile(url)
            return

        webbrowser.open_new_tab(url)

    def _ensure_mixer(self) -> None:
        if self._mixer_ready:
            return

        pygame.mixer.init()
        self._mixer_ready = True

    def _do_action(self, action: ActionCommand) -> str:
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
