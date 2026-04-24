import { initTalkingHead } from './avatar.js'
import { VOICE_ROOM_NAME } from './config.js'
import { els } from './dom.js'
import { state } from './state.js'
import { setIdle, setStatus, setSubtitle } from './ui.js'
import { runVoiceTurn } from './voice.js'

// AI generated comment: รอ PyWebView พร้อมก่อน เพราะ API ฝั่ง Python จะถูก inject หลัง event นี้
window.addEventListener('pywebviewready', init)

async function init() {
  bindEvents()

  try {
    await createVoiceRoom()
    await initTalkingHead()
    setIdle()
  } catch (error) {
    setStatus(`เกิดข้อผิดพลาด: ${error}`)
    setSubtitle('ลองปิดแล้วเปิดแอปใหม่อีกครั้งนะ')
  }
}

function bindEvents() {
  // AI generated comment: ปุ่มเดียวคุมทั้งรอบ ฟัง คิด และพูดกลับ
  els.voiceButton.addEventListener('click', runVoiceTurn)
}

async function createVoiceRoom() {
  const room = await window.pywebview.api.create_room(VOICE_ROOM_NAME)
  state.activeRoomId = room.id
}
