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
    - .venv/Scripts/python.exe -m pip install -r requirements.txt
    - npm install

สร้างไฟล์ .env จาก env.example แล้วใส่ API key ที่จำเป็น เช่น GEMINI_API_KEY และ ELEVENLABS_API_KEY

รันแอป:

    - .venv/Scripts/python.exe main.py

หรือถ้าติดตั้ง package แบบ editable แล้ว:

    - .venv/Scripts/python.exe -m rose_chat

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
