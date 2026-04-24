import { MOUTH } from './config.js'

export function createMouthAnimation(durationSeconds, text) {
  // AI generated comment: animation นี้ตั้งใจให้ดูมีชีวิตพอประมาณ โดยไม่ต้องทำ phoneme จริง
  const durationMs = Math.max(MOUTH.minDurationMs, Math.round(durationSeconds * 1000))
  const frames = Math.ceil(durationMs / MOUTH.frameMs)
  const energy = getMouthEnergy(text)
  const durations = []
  const values = []

  for (let index = 0; index < frames; index += 1) {
    durations.push(getFrameDuration(index, frames, durationMs))
    values.push(getMouthOpenValue(index, energy))
  }

  durations.push(MOUTH.closeFrameMs)
  values.push(0)

  return {
    name: 'generated-mouth',
    dt: durations,
    vs: createVisemes(values),
  }
}

function getMouthEnergy(text) {
  return Math.min(1, Math.max(0.45, text.length / 160))
}

function getFrameDuration(index, frames, durationMs) {
  if (index !== frames - 1) {
    return MOUTH.frameMs
  }

  return Math.max(33, durationMs - MOUTH.frameMs * (frames - 1))
}

function getMouthOpenValue(index, energy) {
  // AI generated comment: ใช้คลื่นสั้น ๆ ให้ปากเปิดปิดเหมือนจังหวะพูด ไม่ใช่เปิดค้าง
  const wave = Math.abs(Math.sin(index * 1.7))
  const consonantBreak = index % 5 === 0 ? 0.18 : 1
  return Number((0.08 + wave * 0.72 * energy * consonantBreak).toFixed(3))
}

function createVisemes(values) {
  return {
    jawOpen: values,
    mouthClose: values.map((value) => Number((0.18 * (1 - value)).toFixed(3))),
    mouthFunnel: values.map((value, index) =>
      Number((index % 4 === 0 ? value * 0.22 : value * 0.06).toFixed(3)),
    ),
  }
}
