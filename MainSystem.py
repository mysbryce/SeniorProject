import os
import sys
import asyncio
import uuid
import webbrowser
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus
import speech_recognition as sr

import sound_tracker

# AI generated comment: ให้สคริปต์เก่ายังเรียก config กลางจาก src ได้เหมือนแอปใหม่
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from rose_chat.config import (
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
from google import genai
from google.genai import types
from dotenv import load_dotenv
from collections import deque
from elevenlabs.client import ElevenLabs

load_dotenv()

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
GENERATION_CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_INSTRUCTION,
    temperature=GEMINI_TEMPERATURE,
    top_p=GEMINI_TOP_P,
    # presence_penalty=0.3
)


@dataclass(frozen=True)
class ActionCommand:
    kind: str
    value: str


r = sr.Recognizer()
mic = sr.Microphone()
memory = deque(maxlen=6)

pygame.mixer.init()

# AI generated comment: เตรียมเสียงพูดของ Rose จาก ElevenLabs โดยให้เปลี่ยน voice ผ่าน .env ได้
tts_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_ELEVENLABS_VOICE_ID)


async def speak(text):
    if not text:
        return

    temp = f"tts_{uuid.uuid4().hex}.mp3"

    try:
        # AI generated comment: ElevenLabs ส่งเสียงกลับมาเป็นชิ้น ๆ เลยต้องเขียนรวมเป็นไฟล์ก่อนเล่น
        audio_stream = tts_client.text_to_speech.convert(
            text=text,
            voice_id=VOICE_ID,
            model_id=TTS_MODEL,
        )

        with open(temp, "wb") as f:
            for chunk in audio_stream:
                if chunk:
                    f.write(chunk)

        pygame.mixer.music.load(temp)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.05)

    except Exception as e:
        print(f"❌ Error Speak: {e}")

    finally:
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        if os.path.exists(temp):
            try:
                os.remove(temp)
            except:
                pass


def listen():
    with mic as s:
        r.adjust_for_ambient_noise(s)
        audio = r.listen(s)
    try:
        return r.recognize_google(audio, language=SPEECH_LANGUAGE)
    except:
        return None


def build_msgs():
    msgs = []
    for user, ai in memory:
        msgs.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user)],
            )
        )
        msgs.append(
            types.Content(
                role="model",
                parts=[types.Part.from_text(text=ai)],
            )
        )
    return msgs


def parse_action(reply: str):
    match = ACTION_PATTERN.search(reply)
    if not match:
        return None

    kind = match.group(1)
    value = match.group(2)
    return ActionCommand(kind=kind.strip().lower(), value=value.strip())


def open_url(url: str):
    opened = webbrowser.open_new_tab(url)
    if not opened and os.name == "nt":
        os.startfile(url)
    elif not opened:
        opener = shutil.which("xdg-open")
        if opener:
            subprocess.Popen([opener, url])


def do_action(action: ActionCommand):
    if not action.value:
        return "Action failed: missing target."

    if action.kind == "youtube":
        url = "https://www.youtube.com/results?search_query=" + quote_plus(action.value)
        open_url(url)
        return f"Opened YouTube search for: {action.value}"

    if action.kind == "web":
        open_url(action.value)
        return f"Opened web page: {action.value}"

    if action.kind == "app":
        subprocess.Popen(action.value, shell=True)
        return f"Opened app: {action.value}"

    return f"Action failed: unknown action '{action.kind}'."


def ask(text):
    msgs = build_msgs()
    msgs.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=text)],
        )
    )

    resp = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=msgs,
        config=GENERATION_CONFIG,
    )
    reply = (resp.text or "").strip()

    memory.append((text, reply))

    # AI generated comment: ถ้าโมเดลตอบเป็น action tag ให้ทำงานนั้นแทนการพูดข้อความดิบ
    action = parse_action(reply)
    if action:
        return do_action(action)

    return reply


async def main():
    print("ready")

    sound_tracker.start()

    while True:
        text = listen()
        if not text:
            continue

        print("You:", text)

        if text in ["หยุด", "ออก", "เลิก", "พอ"]:
            await speak("ไว้คุยกันใหม่นะ")
            break

        reply = ask(text)

        if reply:
            print("AI:", reply)
            await speak(reply)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:

        sound_tracker.stop()
        # AI generated comment: กด Ctrl+C แล้วปิดแบบนุ่ม ๆ ไม่ต้องโชว์ traceback ยาว ๆ
        print("\nกำลังปิดโปรแกรมนะ แล้วเจอกันใหม่นะะะ 😊")
