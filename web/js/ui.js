import { STAGE_LABELS } from './config.js'
import { els } from './dom.js'
import { state } from './state.js'

export function setIdle() {
  // AI generated comment: idle คือสถานะพร้อมรับเสียงรอบใหม่
  setStage('idle')
  setStatus('พร้อมคุยแล้ว')
  els.voiceButton.disabled = false
  els.voiceButton.textContent = STAGE_LABELS.idle
}

export function setStage(stage) {
  document.body.dataset.stage = stage
  els.voiceButton.textContent = STAGE_LABELS[stage] ?? STAGE_LABELS.idle
}

export function setStatus(text) {
  els.status.textContent = text
}

export function setSubtitle(text) {
  els.subtitle.textContent = text
}

export function showTalkingHeadAvatar() {
  state.avatarReady = true
  els.loading.classList.add('hidden')
  els.fallbackFace.classList.add('hidden')
}

export function showFallbackAvatar() {
  // AI generated comment: ถ้า 3D avatar พัง ผู้ใช้ยังเห็นหน้าสำรองและใช้ voice chat ได้ต่อ
  state.avatarReady = false
  els.loading.textContent = 'โหลดหน้า 3D ไม่ได้ ใช้หน้าแบบสำรองแทน'
  els.fallbackFace.classList.remove('hidden')
}

export function updateAvatarProgress(event) {
  // AI generated comment: โชว์เปอร์เซ็นต์โหลดเฉพาะตอน browser รู้ขนาดไฟล์จริง
  if (!event.lengthComputable) {
    return
  }

  const percent = Math.min(100, Math.round((event.loaded / event.total) * 100))
  els.loading.textContent = `Loading avatar ${percent}%`
}
