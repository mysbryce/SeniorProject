# วิธี setup และ build บน Raspberry Pi 4

คู่มือนี้สำหรับ Raspberry Pi 4 ที่ใช้ Raspberry Pi OS แบบ 64-bit นะ แนะนำให้ใช้ 64-bit เพราะ Tauri, Rust และ dependency ฝั่ง desktop จะตรงและง่ายกว่า

## 1. เตรียมระบบ

เปิด Terminal แล้วอัปเดตแพ็กเกจก่อน

```bash
sudo apt update
sudo apt upgrade -y
```

ติดตั้ง dependency ที่ Tauri ต้องใช้ รวมถึง `flac` สำหรับระบบฟังเสียงของ backend

```bash
sudo apt install -y \
  build-essential \
  curl \
  wget \
  file \
  libssl-dev \
  libgtk-3-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev \
  libwebkit2gtk-4.1-dev \
  flac
```

เช็กว่า `flac` ใช้ได้แล้ว

```bash
flac --version
```

## 2. ติดตั้ง Rust

ถ้ายังไม่มี Rust ให้ติดตั้งด้วยคำสั่งนี้

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

หลังติดตั้งเสร็จ ให้โหลด path ของ Rust เข้ามาใน Terminal ปัจจุบัน

```bash
source "$HOME/.cargo/env"
```

เช็กว่า Rust พร้อมใช้

```bash
rustc --version
cargo --version
```

## 3. ติดตั้ง Node.js

แนะนำให้ใช้ Node.js เวอร์ชัน LTS หรือเวอร์ชันใหม่ที่ npm ใช้งานได้ปกติ

ตัวอย่างติดตั้งผ่าน NodeSource

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
```

เช็กเวอร์ชัน

```bash
node --version
npm --version
```

## 4. เตรียมไฟล์ `.env`

ในโฟลเดอร์โปรเจกต์ ให้สร้างไฟล์ `.env`

```bash
cp env.example .env
```

แล้วแก้ค่าในไฟล์ `.env`

```env
GEMINI_API_KEY=ใส่คีย์ของคุณตรงนี้
ELEVENLABS_API_KEY=ใส่คีย์ของคุณตรงนี้
ELEVENLABS_VOICE_ID=ใส่ถ้าต้องการเปลี่ยนเสียง
```

ค่าที่จำเป็นจริง ๆ คือ

```env
GEMINI_API_KEY
ELEVENLABS_API_KEY
```

`GOOGLE_SPEECH_API_KEY` ไม่จำเป็นในตอนนี้ ถ้าไม่ใส่ ระบบจะใช้ endpoint แบบเดียวกับที่ Python `SpeechRecognition` ใช้ แต่ถ้าต้องการความนิ่งสำหรับ production ควรเปลี่ยนไปใช้ STT แบบ official ภายหลัง

## 5. ติดตั้ง dependency ของโปรเจกต์

อยู่ใน root ของโปรเจกต์ แล้วรัน

```bash
npm install
```

## 6. รันแบบ dev

ใช้คำสั่งนี้เพื่อเปิดแอปแบบ development

```bash
npm run dev
```

ถ้าระบบถาม permission เรื่อง microphone ให้กดยอมรับ

## 7. Build แอปจริง

ใช้คำสั่งนี้

```bash
npm run build
```

ไฟล์ binary หลักจะอยู่ที่

```bash
src-tauri/target/release/rose-chat
```

ลองรันโดยตรงได้แบบนี้

```bash
./src-tauri/target/release/rose-chat
```

## 8. ถ้าเสียงพูดไม่เข้า

เช็กว่า Raspberry Pi เห็น microphone หรือยัง

```bash
arecord -l
```

ถ้าไม่มี device แสดงขึ้นมา ให้เช็ก USB microphone หรือ sound card ก่อน

ลองอัดเสียงสั้น ๆ

```bash
arecord -d 3 test.wav
aplay test.wav
```

ถ้าอัดแล้วเล่นกลับได้ แปลว่าฝั่งระบบเสียงของ Raspberry Pi พร้อมแล้ว

## 9. ปัญหาที่เจอบ่อย

ถ้า build แล้วหา `webkit2gtk` ไม่เจอ ให้ติดตั้ง dependency ข้อ 1 ให้ครบ โดยเฉพาะ

```bash
sudo apt install -y libwebkit2gtk-4.1-dev
```

ถ้าระบบบอกว่าใช้ `flac` ไม่ได้ ให้ติดตั้งใหม่

```bash
sudo apt install -y flac
```

ถ้าเปิดแอปแล้วตอบไม่ได้ ให้เช็ก `.env` ว่าใส่ `GEMINI_API_KEY` และ `ELEVENLABS_API_KEY` ถูกต้องแล้ว

ถ้า build ช้ามาก เป็นเรื่องปกติบน Raspberry Pi 4 โดยเฉพาะครั้งแรก เพราะ Rust ต้อง compile dependency เยอะ ครั้งต่อไปจะเร็วขึ้น
