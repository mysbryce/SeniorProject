# SeniorProject
Main system
    - Python
    - Lv5 AI -> Chain of thought
    - Output sound model (using eleven lap)
    - Using api from processing
    - Face interface to rect with sound

System
     ____________________________________________________________________________________________________________________________    
    |                                                                                                                            |
    | TTS (Text to speech) -> input -> api (Brain system process) -> processing -> STT (Speech to text) -> output -> sound model |
    |____________________________________________________________________________________________________________________________|

    - Have chain of though
    - Can agressive 
    - Face interface to rect with sound

Make AI Responses More Smooth and Natural
Overview
    Enhance Rose's responses to sound more natural and conversational by updating the system instruction with specific conversational guidelines and adding generation configuration parameters.

Changes
1. - Enhanced System Instruction (MainSystem.py lines 19-25)
    - Add specific guidelines for natural conversation:
    - Use shorter, simpler sentences that flow naturally
    - Vary sentence length for natural rhythm
    - Use casual, friendly language appropriate for a Thai friend
    - Avoid overly formal or structured responses
    - Sound like you're speaking, not writing a document
    - Keep responses concise but warm
2. - Generation Configuration (MainSystem.py around line 17)
    - Add generation_config parameter to the GenerativeModel:
    - Set temperature to ~0.8-0.9 for more natural variation
    - Add max_output_tokens if needed to encourage concise responses
    - Configure top_p/top_k for natural sampling
3. - Response Handling (MainSystem.py in ask function)
    - Consider minimal post-processing if needed, but prioritize letting the model generate naturally

Files to Modify
    - MainSystem.py: Update system instruction and add generation config

Summary
    - Package the Python app under src/rose_chat with a root main.py launcher
    - Replace deprecated google.generativeai usage with google-genai
    - Add voice-first PyWebView frontend with TalkingHead avatar support
    - Split frontend code into web/js and web/css modules
    - Add action handling for YouTube, web URLs, and app launch commands
    - Add Thai voice/STT/TTS support and Noto Sans Thai font
    - Configure Python and web formatting/linting tooling
    - Update .gitignore to exclude local runtime, build, cache, and AI agent files
    - Add Thai AI generated comment notes across Python and web code

Verification
    - npm run lint:format:web
    - npm run lint:web
    - .venv/Scripts/python.exe -m black src main.py MainSystem.py

วิธีรันโปรเจกต์
ติดตั้ง dependency ก่อน:

    - python -m venv .venv
    - source .venv/bin/activate (Linux/Raspberry Pi) หรือ .venv/Scripts/activate (Windows)
    - python -m pip install --upgrade pip
    - python -m pip install -r requirements.txt

ถ้าต้องการโหมด GUI (PyWebView) ค่อยติดตั้งเพิ่ม:

    - python -m pip install ".[gui]"

ถ้าต้องการเปิดฟีเจอร์เสียง (mic + speaker) เพิ่มเติมค่อยติดตั้ง:

    - python -m pip install ".[audio]"

สร้างไฟล์ .env จาก env.example แล้วใส่ API key ที่จำเป็น เช่น GEMINI_API_KEY และ ELEVENLABS_API_KEY

รันแอป:

    - python main.py

หรือถ้าติดตั้ง package แบบ editable แล้ว:

    - python -m rose_chat

## Raspberry Pi 4 (Python 3.12.13) setup

สำหรับ Raspberry Pi OS ให้ติดตั้ง system package ก่อน (จำเป็นสำหรับ `pyaudio`, `pygame`, และ `pywebview`):

    - sudo apt update
    - sudo apt install -y python3-dev portaudio19-dev libasound2-dev libgtk-3-0 libwebkit2gtk-4.1-0 libsndfile1 mpg123

จากนั้นสร้าง virtualenv ด้วย Python 3.12.13 แล้วติดตั้งตามขั้นตอนด้านบนได้เลย

ก่อนรันจริง แนะนำให้เช็คความพร้อมของเครื่อง Pi:

    - npm run check:pi

ถ้าผลเป็น `PASS` ทั้งหมดค่อยรันแอป:

    - python main.py

### If `pygame` or `pyaudio` fails to install on Pi

ติดตั้ง system headers ให้ครบก่อน:

    - sudo apt update
    - sudo apt install -y build-essential python3-dev python3.12-dev portaudio19-dev libasound2-dev libsdl2-dev libsdl2-mixer-dev libsdl2-image-dev libsdl2-ttf-dev libfreetype6-dev libjpeg-dev libpng-dev

แล้วค่อยติดตั้งใน venv:

    - python -m pip install --upgrade pip setuptools wheel
    - python -m pip install pygame pyaudio

ถ้ายังไม่ผ่าน ให้ติดตั้ง package อื่นก่อน แล้วค่อยติดตั้ง 2 ตัวนี้แยก:

    - python -m pip install -r requirements.txt --no-deps
    - python -m pip install pygame pyaudio

หมายเหตุ: ถ้าไม่มี `pygame`/`pyaudio` แอปยังเปิดได้ แต่ฟีเจอร์ไมค์และเล่นเสียงจะไม่พร้อมใช้งาน

### Recommended voice setup on Pi4 (without pyaudio/pygame)

โปรเจกต์นี้รองรับ fallback สำหรับเสียง:

- ไมค์: `arecord` (จาก `alsa-utils`) + `SpeechRecognition`
- เล่นเสียงตอบกลับ: `mpg123` (หรือ `ffplay` / `aplay`)

ติดตั้งที่แนะนำ:

    - sudo apt update
    - sudo apt install -y build-essential pkg-config libffi-dev alsa-utils libasound2-dev libportaudio2 portaudio19-dev mpg123 ffmpeg
    - python -m pip install --upgrade pip
    - python -m pip install -r requirements.txt

เช็คว่าโหมดเสียงพร้อมใช้งาน:

    - npm run check:pi

ให้ดูส่วน `Voice mode readiness` ต้องมีทั้ง input และ output เป็น `PASS` อย่างน้อยอย่างละ 1 วิธี

หมายเหตุ: ถ้าไม่ได้ติดตั้ง `pywebview` ระบบจะ fallback ไปโหมด Voice CLI อัตโนมัติเมื่อรัน `python main.py`

## คำสั่ง NPM ทั้งหมด

- npm run format:py
  จัด format โค้ด Python ด้วย Black
- npm run lint:py
  ตรวจว่าโค้ด Python format ถูกต้องตาม Black หรือไม่ โดยไม่แก้ไฟล์
- npm run format:web
  จัด format ไฟล์ในโฟลเดอร์ web ด้วย Biome ตาม config เช่น single quote, ไม่มี semicolon, indent 2 spaces
- npm run lint:format:web
  ตรวจ format ของไฟล์ใน web ด้วย Biome โดยไม่แก้ไฟล์
- npm run lint:web
  ตรวจ lint ฝั่งเว็บด้วย Oxc
- npm run lint
  รัน lint ทั้ง Python และ web รวมกัน
- npm run format
  จัด format ทั้ง Python และ web รวมกัน
- npm run build:win
  build แอปเป็น .exe สำหรับ Windows ด้วย PyInstaller
- npm run build:pi
  build แอปสำหรับ Raspberry Pi/Linux ด้วย PyInstaller
- npm run build:linux
  alias ของ build:pi
