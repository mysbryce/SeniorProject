import { speakWithAvatar } from './audio.js'
import { els } from './dom.js'
import { state } from './state.js'
import { setIdle, setStage, setStatus, setSubtitle } from './ui.js'

export async function runVoiceTurn() {
  // AI generated comment: หนึ่ง voice turn คือฟังเสียง ส่งให้ AI แล้วพูดคำตอบกลับ
  if (!canStartVoiceTurn()) {
    return
  }

  startVoiceTurn()

  try {
    const transcript = await listenForTranscript()
    if (!transcript) {
      setSubtitle('โรสยังได้ยินไม่ชัดเลยนะ')
      return
    }

    const reply = await askAi(transcript)
    await speakReply(reply)
  } catch (error) {
    setStage('idle')
    setStatus('มีปัญหาเรื่องเสียง')
    setSubtitle(String(error))
  } finally {
    finishVoiceTurn()
  }
}

function canStartVoiceTurn() {
  return !state.busy && Boolean(state.activeRoomId)
}

function startVoiceTurn() {
  state.busy = true
  els.voiceButton.disabled = true
  setStage('listening')
  setStatus('กำลังฟัง...')
  setSubtitle('พูดได้เลยนะ')
}

function finishVoiceTurn() {
  state.busy = false
  setIdle()
}

async function listenForTranscript() {
  // AI generated comment: transcript ที่ได้จะแสดงเป็น subtitle ให้รู้ว่า Rose ได้ยินอะไร
  const transcript = (await window.pywebview.api.listen_once()).trim()
  if (transcript) {
    setStage('thinking')
    setStatus('กำลังคิด...')
    setSubtitle(transcript)
  }
  return transcript
}

async function askAi(transcript) {
  return window.pywebview.api.send_message(state.activeRoomId, transcript)
}

async function speakReply(reply) {
  // AI generated comment: ให้ backend สร้างเสียงก่อน แล้วค่อยเล่นพร้อม avatar ในหน้าเว็บ
  const speech = await window.pywebview.api.synthesize_speech(reply)
  setStage('speaking')
  setStatus('กำลังพูด...')
  setSubtitle(reply)
  await speakWithAvatar(speech, reply)
}
