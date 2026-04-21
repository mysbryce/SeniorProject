import { STAGE_LABELS } from './config.js'
import { els } from './dom.js'
import { state } from './state.js'

export function setIdle() {
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
  state.avatarReady = false
  els.loading.textContent = 'โหลดหน้า 3D ไม่ได้ ใช้หน้าแบบสำรองแทน'
  els.fallbackFace.classList.remove('hidden')
}

export function updateAvatarProgress(event) {
  if (!event.lengthComputable) {
    return
  }

  const percent = Math.min(100, Math.round((event.loaded / event.total) * 100))
  els.loading.textContent = `Loading avatar ${percent}%`
}
