import { TalkingHead } from 'talkinghead'

import { AVATAR_URL } from './config.js'
import { els } from './dom.js'
import { state } from './state.js'
import { showFallbackAvatar, showTalkingHeadAvatar, updateAvatarProgress } from './ui.js'

export async function initTalkingHead() {
  // AI generated comment: ถ้าโหลดหน้า 3D ไม่ได้ แอปยังใช้ fallback face ต่อได้
  try {
    state.head = new TalkingHead(els.avatar, getTalkingHeadOptions())
    await state.head.showAvatar(getAvatarOptions(), updateAvatarProgress)
    showTalkingHeadAvatar()
  } catch (error) {
    showFallbackAvatar()
    console.error(error)
  }
}

function getTalkingHeadOptions() {
  // AI generated comment: ล็อกกล้องไว้ให้ avatar อยู่กลางฉาก ไม่ให้ผู้ใช้เลื่อนหลุดเฟรม
  return {
    lipsyncModules: ['en'],
    cameraView: 'head',
    cameraRotateEnable: false,
    cameraPanEnable: false,
    cameraZoomEnable: false,
    avatarIdleEyeContact: 0.35,
    avatarSpeakingEyeContact: 0.65,
    avatarSpeakingHeadMove: 0.42,
    lightAmbientIntensity: 2.4,
    lightDirectIntensity: 28,
  }
}

function getAvatarOptions() {
  // AI generated comment: baseline blink ช่วยให้หน้าไม่แข็งเกินไปตอนยังไม่ได้พูด
  return {
    url: AVATAR_URL,
    body: 'F',
    avatarMood: 'neutral',
    lipsyncLang: 'en',
    baseline: {
      eyeBlinkLeft: 0.08,
      eyeBlinkRight: 0.08,
    },
  }
}
