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
        :loading="audioStore.isAnalyzing"
        :disable="!audioStore.audioUrl || audioStore.isAnalyzing"
        no-caps
        @click="audioStore.runChordAnalysis()"
      />
      <q-btn
        color="primary"
        icon="lyrics"
        label="Get Lyrics"
        :loading="audioStore.isFetchingLyrics"
        :disable="!audioStore.audioUrl || audioStore.isFetchingLyrics"
        no-caps
        @click="audioStore.loadLyrics()"
      />
    </div>

    <div v-if="audioStore.analyzeError" class="q-px-md q-pb-md text-caption text-negative">
      {{ audioStore.analyzeError }}
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { useAudioStore } from 'src/stores/audioStore'

const audioStore = useAudioStore()
const audioEl = ref(null)

const isPlaying = ref(false)
const isMuted = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(0.8)
const isDetectingBpm = ref(false)

function formatTime(secs) {
  if (!secs || isNaN(secs)) return '0:00'
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function togglePlay() {
  if (!audioEl.value) return
  if (isPlaying.value) audioEl.value.pause()
  else audioEl.value.play()
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

function onPlay()  { isPlaying.value = true }
function onPause() { isPlaying.value = false }
function onEnded() {
  isPlaying.value = false
  currentTime.value = 0
  audioStore.setPlaybackTime(0)
}

function onTimeUpdate() {
  if (audioEl.value) {
    currentTime.value = audioEl.value.currentTime
    audioStore.setPlaybackTime(audioEl.value.currentTime)
  }
}

function onLoaded() {
  if (audioEl.value) duration.value = audioEl.value.duration
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
    if (corr > bestCorr) { bestCorr = corr; bestLag = lag }
  }

  const periodSec = bestLag / fps
  let bpm = Math.round(60 / periodSec)
  while (bpm < 60) bpm *= 2
  while (bpm > 200) bpm /= 2
  return bpm
}

watch(() => audioStore.audioUrl, (url) => {
  if (!url) {
    isPlaying.value = false
    currentTime.value = 0
    duration.value = 0
  }
})

onUnmounted(() => {
  audioStore.setPlaybackTime(0)
})
</script>

<style scoped>
.audio-player {
  background: rgba(255,255,255,0.03);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
}
</style>
