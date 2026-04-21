import { TalkingHead } from 'talkinghead'

import { AVATAR_URL } from './config.js'
import { els } from './dom.js'
import { state } from './state.js'
import { showFallbackAvatar, showTalkingHeadAvatar, updateAvatarProgress } from './ui.js'

export async function initTalkingHead() {
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
