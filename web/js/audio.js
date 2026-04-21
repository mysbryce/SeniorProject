import { els } from './dom.js'
import { createMouthAnimation } from './mouth-animation.js'
import { state } from './state.js'

export async function speakWithAvatar(speech, text) {
  const audioBuffer = await decodeAudio(speech.base64, speech.mime_type)

  if (!state.avatarReady || !state.head) {
    await playFallbackAudio(audioBuffer)
    return
  }

  await playTalkingHeadAudio(audioBuffer, text)
}

async function playTalkingHeadAudio(audioBuffer, text) {
  const speechAnim = createMouthAnimation(audioBuffer.duration, text)
  const result = state.head.speakAudio(
    {
      audio: audioBuffer,
      anim: speechAnim,
    },
    { isRaw: true },
  )

  if (result instanceof Promise) {
    await result
    return
  }

  await wait(audioBuffer.duration * 1000 + 250)
}

async function decodeAudio(base64, mimeType) {
  const response = await fetch(`data:${mimeType};base64,${base64}`)
  const arrayBuffer = await response.arrayBuffer()
  const context = getAudioContext()
  return context.decodeAudioData(arrayBuffer)
}

function getAudioContext() {
  if (!state.audioContext) {
    const AudioContextClass = window.AudioContext || window.webkitAudioContext
    state.audioContext = new AudioContextClass()
  }

  if (state.audioContext.state === 'suspended') {
    state.audioContext.resume()
  }

  return state.audioContext
}

async function playFallbackAudio(audioBuffer) {
  const context = getAudioContext()
  await context.resume()

  const source = context.createBufferSource()
  source.buffer = audioBuffer
  source.connect(context.destination)

  els.fallbackFace.classList.add('talking')
  source.start()
  await new Promise((resolve) => {
    source.onended = resolve
  })
  els.fallbackFace.classList.remove('talking')
}

function wait(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}
