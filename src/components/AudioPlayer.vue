<template>
  <div class="audio-player">
    <audio
      ref="audioEl"
      :src="audioStore.audioUrl"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoaded"
      @ended="onEnded"
      @play="onPlay"
      @pause="onPause"
      preload="auto"
    />

    <div class="player-controls q-pa-md">
      <div class="row items-center q-gutter-md">
        <q-btn
          round
          :icon="isPlaying ? 'pause' : 'play_arrow'"
          color="primary"
          size="lg"
          :disable="!audioStore.audioUrl"
          @click="togglePlay"
        />

        <div class="col">
          <q-slider
            v-model="currentTime"
            :min="0"
            :max="duration || 100"
            :step="0.1"
            color="primary"
            track-color="grey-8"
            @change="seek"
          />
          <div class="row justify-between text-caption text-grey-5">
            <span>{{ formatTime(currentTime) }}</span>
            <span>{{ formatTime(duration) }}</span>
          </div>
        </div>

        <q-btn
          round flat
          :icon="isMuted ? 'volume_off' : 'volume_up'"
          color="grey-4"
          @click="toggleMute"
        />
        <q-slider
          v-model="volume"
          :min="0"
          :max="1"
          :step="0.01"
          color="grey-4"
          track-color="grey-8"
          style="width: 80px"
          @update:model-value="setVolume"
        />
      </div>
    </div>

    <div class="row q-px-md q-pb-md q-gutter-sm">
      <q-btn
        color="secondary"
        icon="query_stats"
        label="Detect BPM"
        :loading="isDetectingBpm"
        :disable="!audioStore.audioUrl || isDetectingBpm"
        no-caps
        @click="detectBpm"
      />
      <q-btn
        color="accent"
        icon="piano"
        label="Analyze Chords"
        :loading="isAnalyzingChords"
        :disable="!audioStore.audioUrl || isAnalyzingChords"
        no-caps
        @click="startChordAnalysis"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { useAudioStore } from 'src/stores/audioStore'
import Meyda from 'meyda'

const audioStore = useAudioStore()
const audioEl = ref(null)

const isPlaying = ref(false)
const isMuted = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(0.8)
const isDetectingBpm = ref(false)
const isAnalyzingChords = ref(false)

let audioCtx = null
let meydaAnalyzer = null
let sourceNode = null
let sourceConnected = false

function formatTime(secs) {
  if (!secs || isNaN(secs)) return '0:00'
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function togglePlay() {
  if (!audioEl.value) return
  if (isPlaying.value) {
    audioEl.value.pause()
  } else {
    audioEl.value.play()
  }
}

function seek(val) {
  if (audioEl.value) audioEl.value.currentTime = val
}

function toggleMute() {
  isMuted.value = !isMuted.value
  if (audioEl.value) audioEl.value.muted = isMuted.value
}

function setVolume(val) {
  if (audioEl.value) audioEl.value.volume = val
}

function onPlay() {
  isPlaying.value = true
  ensureAudioContext()
  startMeydaAnalysis()
}

function onPause() {
  isPlaying.value = false
  stopMeydaAnalysis()
}

function onEnded() {
  isPlaying.value = false
  currentTime.value = 0
  stopMeydaAnalysis()
}

function onTimeUpdate() {
  if (audioEl.value) currentTime.value = audioEl.value.currentTime
}

function onLoaded() {
  if (audioEl.value) duration.value = audioEl.value.duration
}

function ensureAudioContext() {
  if (!audioCtx) {
    audioCtx = new AudioContext()
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume()
  }
  if (!sourceConnected && audioEl.value) {
    sourceNode = audioCtx.createMediaElementSource(audioEl.value)
    sourceNode.connect(audioCtx.destination)
    sourceConnected = true
  }
}

const CHORD_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

const MAJOR_TEMPLATE = [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0]
const MINOR_TEMPLATE = [1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0]
const DOM7_TEMPLATE  = [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0]
const MAJ7_TEMPLATE  = [1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1]

function buildTemplates() {
  const templates = []
  for (let root = 0; root < 12; root++) {
    const shift = (arr) => {
      const shifted = [...arr]
      for (let i = 0; i < root; i++) shifted.unshift(shifted.pop())
      return shifted
    }
    templates.push({ name: `${CHORD_NAMES[root]}`,     tpl: shift(MAJOR_TEMPLATE), suffix: '' })
    templates.push({ name: `${CHORD_NAMES[root]}m`,    tpl: shift(MINOR_TEMPLATE), suffix: 'm' })
    templates.push({ name: `${CHORD_NAMES[root]}7`,    tpl: shift(DOM7_TEMPLATE),  suffix: '7' })
    templates.push({ name: `${CHORD_NAMES[root]}maj7`, tpl: shift(MAJ7_TEMPLATE),  suffix: 'maj7' })
  }
  return templates
}

const CHORD_TEMPLATES = buildTemplates()

function cosineSimilarity(a, b) {
  let dot = 0, normA = 0, normB = 0
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i]
    normA += a[i] * a[i]
    normB += b[i] * b[i]
  }
  if (normA === 0 || normB === 0) return 0
  return dot / (Math.sqrt(normA) * Math.sqrt(normB))
}

function chromaToChord(chroma) {
  let best = { name: 'N/A', confidence: 0 }
  for (const { name, tpl } of CHORD_TEMPLATES) {
    const score = cosineSimilarity(Array.from(chroma), tpl)
    if (score > best.confidence) {
      best = { name, confidence: score }
    }
  }
  return best
}

let lastChordTime = 0

function startMeydaAnalysis() {
  if (!sourceNode || !audioCtx) return
  stopMeydaAnalysis()

  meydaAnalyzer = Meyda.createMeydaAnalyzer({
    audioContext: audioCtx,
    source: sourceNode,
    bufferSize: 4096,
    featureExtractors: ['chroma', 'rms'],
    callback: (features) => {
      if (!features || !features.chroma) return
      if (features.rms < 0.01) {
        audioStore.setCurrentChord('—', 0)
        return
      }
      const now = Date.now()
      if (now - lastChordTime < 300) return
      lastChordTime = now
      const { name, confidence } = chromaToChord(features.chroma)
      audioStore.setCurrentChord(name, Math.round(confidence * 100))
    },
  })
  meydaAnalyzer.start()
}

function stopMeydaAnalysis() {
  if (meydaAnalyzer) {
    meydaAnalyzer.stop()
    meydaAnalyzer = null
  }
}

/** Returns the audio blob, fetching it from the server if not already in store */
async function getAudioBlob() {
  if (audioStore.audioBlob) return audioStore.audioBlob
  if (!audioStore.audioUrl) return null
  const res = await fetch(audioStore.audioUrl)
  if (!res.ok) throw new Error(`Failed to fetch audio (${res.status})`)
  return await res.blob()
}

async function detectBpm() {
  isDetectingBpm.value = true
  try {
    const blob = await getAudioBlob()
    if (!blob) return
    const arrayBuffer = await blob.arrayBuffer()
    const offlineCtx = new OfflineAudioContext(1, 44100 * 60, 44100)
    const decoded = await offlineCtx.decodeAudioData(arrayBuffer)
    const bpm = estimateBpm(decoded)
    audioStore.setBpm(bpm)
  } catch (e) {
    console.error('BPM detection error:', e)
  } finally {
    isDetectingBpm.value = false
  }
}

function estimateBpm(audioBuffer) {
  const channelData = audioBuffer.getChannelData(0)
  const sampleRate = audioBuffer.sampleRate
  const frameSize = 1024
  const hopSize = 512

  const energies = []
  for (let i = 0; i + frameSize < channelData.length; i += hopSize) {
    let e = 0
    for (let j = 0; j < frameSize; j++) e += channelData[i + j] ** 2
    energies.push(e / frameSize)
  }

  const odf = []
  for (let i = 1; i < energies.length; i++) {
    odf.push(Math.max(0, energies[i] - energies[i - 1]))
  }

  const fps = sampleRate / hopSize
  const minLag = Math.round(fps * (60 / 220))
  const maxLag = Math.round(fps * (60 / 50))

  let bestLag = minLag
  let bestCorr = -Infinity

  for (let lag = minLag; lag <= Math.min(maxLag, odf.length - 1); lag++) {
    let corr = 0
    const limit = Math.min(odf.length - lag, 1500)
    for (let i = 0; i < limit; i++) corr += odf[i] * odf[i + lag]
    if (corr > bestCorr) {
      bestCorr = corr
      bestLag = lag
    }
  }

  const periodSec = bestLag / fps
  let bpm = Math.round(60 / periodSec)
  while (bpm < 60) bpm *= 2
  while (bpm > 200) bpm /= 2
  return bpm
}

async function startChordAnalysis() {
  isAnalyzingChords.value = true
  audioStore.setChords([])
  try {
    const blob = await getAudioBlob()
    if (!blob) { isAnalyzingChords.value = false; return }
    const arrayBuffer = await blob.arrayBuffer()
    const offCtx = new OfflineAudioContext(1, 44100 * 300, 44100)
    const decoded = await offCtx.decodeAudioData(arrayBuffer)
    const chords = analyzeChordsFull(decoded)
    audioStore.setChords(chords)
  } catch (e) {
    console.error('Chord analysis error:', e)
  } finally {
    isAnalyzingChords.value = false
  }
}

function analyzeChordsFull(audioBuffer) {
  const channelData = audioBuffer.getChannelData(0)
  const sampleRate = audioBuffer.sampleRate
  const frameSize = 8192
  const hopSize = 4096
  const results = []
  let prevChord = null

  for (let i = 0; i + frameSize < channelData.length; i += hopSize) {
    const frame = channelData.slice(i, i + frameSize)
    const chroma = computeChroma(frame, sampleRate)
    const { name, confidence } = chromaToChord(chroma)
    const timeStamp = parseFloat((i / sampleRate).toFixed(2))

    if (name !== prevChord && confidence > 0.6) {
      results.push({ chord: name, time: timeStamp, confidence: Math.round(confidence * 100) })
      prevChord = name
    }
  }
  return results
}

function computeChroma(frame, sampleRate) {
  const n = frame.length
  const re = new Float32Array(n)
  const im = new Float32Array(n)
  frame.forEach((v, i) => { re[i] = v })

  for (let len = 2; len <= n; len <<= 1) {
    const halfLen = len >> 1
    for (let i = 0; i < n; i += len) {
      for (let j = 0; j < halfLen; j++) {
        const angle = (-2 * Math.PI * j) / len
        const cos = Math.cos(angle)
        const sin = Math.sin(angle)
        const tr = cos * re[i + j + halfLen] - sin * im[i + j + halfLen]
        const ti = sin * re[i + j + halfLen] + cos * im[i + j + halfLen]
        re[i + j + halfLen] = re[i + j] - tr
        im[i + j + halfLen] = im[i + j] - ti
        re[i + j] += tr
        im[i + j] += ti
      }
    }
  }

  const chroma = new Float32Array(12)
  const fRef = 261.63
  for (let k = 1; k < n / 2; k++) {
    const freq = (k * sampleRate) / n
    const mag = Math.sqrt(re[k] ** 2 + im[k] ** 2)
    const pitchClass = Math.round(12 * Math.log2(freq / fRef)) % 12
    const pc = ((pitchClass % 12) + 12) % 12
    chroma[pc] += mag
  }

  const maxVal = Math.max(...chroma)
  if (maxVal > 0) for (let i = 0; i < 12; i++) chroma[i] /= maxVal
  return chroma
}

watch(() => audioStore.audioUrl, (url) => {
  if (!url) {
    isPlaying.value = false
    currentTime.value = 0
    duration.value = 0
    sourceConnected = false
    if (sourceNode) { sourceNode.disconnect(); sourceNode = null }
    if (audioCtx) { audioCtx.close(); audioCtx = null }
    stopMeydaAnalysis()
  }
})

onUnmounted(() => {
  stopMeydaAnalysis()
  if (audioCtx) audioCtx.close()
})
</script>

<style scoped>
.audio-player {
  background: rgba(255,255,255,0.03);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
}
</style>
