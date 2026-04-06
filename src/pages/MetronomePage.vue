<template>
  <q-page class="metronome-page flex flex-center q-pa-md">
    <div class="metronome-inner text-center">

      <div class="pendulum-container q-mb-xl">
        <div class="pendulum-track">
          <div
            class="pendulum-arm"
            :class="{ 'is-running': audioStore.metronome.isRunning }"
            :style="pendulumStyle"
          >
            <div class="pendulum-bob" :class="{ accent: audioStore.metronome.currentBeat === 0 }" />
          </div>
        </div>

        <div class="beat-lights row justify-center q-gutter-sm q-mt-md">
          <div
            v-for="n in audioStore.metronome.timeSignature"
            :key="n"
            class="beat-light"
            :class="{
              active: audioStore.metronome.isRunning && audioStore.metronome.currentBeat === n - 1,
              accent: n === 1
            }"
          />
        </div>
      </div>

      <div class="bpm-display q-mb-lg">
        <q-btn flat round dense icon="remove" color="grey-4" size="lg" @click="changeBpm(-1)" />
        <div class="bpm-number">{{ audioStore.metronome.bpm }}</div>
        <q-btn flat round dense icon="add" color="grey-4" size="lg" @click="changeBpm(1)" />
      </div>

      <div class="bpm-label text-caption text-grey-5 q-mb-md">BPM</div>

      <div class="q-mb-lg q-px-xl">
        <q-slider
          v-model="localBpm"
          :min="40"
          :max="240"
          :step="1"
          color="primary"
          track-color="grey-8"
          @update:model-value="onSliderChange"
        />
        <div class="row justify-between text-caption text-grey-7">
          <span>40</span><span>Slow</span><span>Medium</span><span>Fast</span><span>240</span>
        </div>
      </div>

      <div class="row justify-center q-gutter-md q-mb-lg">
        <q-btn-toggle
          v-model="audioStore.metronome.timeSignature"
          :options="[
            { label: '2/4', value: 2 },
            { label: '3/4', value: 3 },
            { label: '4/4', value: 4 },
            { label: '6/8', value: 6 },
          ]"
          toggle-color="primary"
          color="grey-9"
          text-color="grey-4"
          no-caps
          rounded
          @update:model-value="onTimeSigChange"
        />
      </div>

      <div class="row justify-center q-gutter-md q-mb-lg">
        <q-btn
          round size="xl"
          :color="audioStore.metronome.isRunning ? 'negative' : 'primary'"
          :icon="audioStore.metronome.isRunning ? 'stop' : 'play_arrow'"
          :loading="isStarting"
          @click="toggleMetronome"
        />
        <q-btn
          round size="xl"
          color="grey-9"
          icon="touch_app"
          @click="tapTempo"
        />
      </div>
      <div class="row justify-center q-gutter-lg text-caption text-grey-6 q-mb-lg">
        <span>{{ audioStore.metronome.isRunning ? 'Stop' : 'Start' }}</span>
        <span>Tap Tempo</span>
      </div>

      <div v-if="audioStore.bpm" class="q-mt-sm">
        <q-btn
          flat no-caps color="secondary"
          icon="music_note"
          :label="`Use detected BPM: ${audioStore.bpm}`"
          @click="useDetectedBpm"
        />
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import { useAudioStore } from 'src/stores/audioStore'

const audioStore = useAudioStore()

// Local BPM mirror — avoids v-model directly mutating the store from the slider
const localBpm = ref(audioStore.metronome.bpm)
watch(() => audioStore.metronome.bpm, (v) => { localBpm.value = v })

const isStarting = ref(false)

// ── AudioContext ────────────────────────────────────────────────────────────
let audioCtx = null
let schedulerTimer = null
let nextBeatTime = 0
let beatNumber = 0
const LOOKAHEAD_MS = 25      // scheduler interval
const SCHEDULE_AHEAD = 0.1   // seconds to schedule ahead

async function ensureAudioCtx() {
  if (!audioCtx) {
    audioCtx = new AudioContext()
  }
  // Must await resume — AudioContext starts suspended in modern browsers
  // until triggered by a user gesture AND explicitly resumed.
  if (audioCtx.state !== 'running') {
    await audioCtx.resume()
  }
}

// ── Scheduling ──────────────────────────────────────────────────────────────
function scheduleClick(beat, time) {
  const osc = audioCtx.createOscillator()
  const gain = audioCtx.createGain()
  osc.connect(gain)
  gain.connect(audioCtx.destination)

  // Beat 1 accent: higher pitch, louder
  osc.type = 'sine'
  osc.frequency.value = beat === 0 ? 1050 : 800
  gain.gain.setValueAtTime(0, audioCtx.currentTime)
  gain.gain.setValueAtTime(beat === 0 ? 0.9 : 0.6, time)
  gain.gain.exponentialRampToValueAtTime(0.001, time + 0.05)

  osc.start(time)
  osc.stop(time + 0.05)

  // Visual beat indicator — fire just before the click lands
  const delayMs = Math.max(0, (time - audioCtx.currentTime) * 1000 - 15)
  setTimeout(() => {
    audioStore.setCurrentBeat(beat)
  }, delayMs)
}

function scheduler() {
  if (!audioCtx) return
  while (nextBeatTime < audioCtx.currentTime + SCHEDULE_AHEAD) {
    scheduleClick(beatNumber, nextBeatTime)
    const secondsPerBeat = 60 / audioStore.metronome.bpm
    nextBeatTime += secondsPerBeat
    beatNumber = (beatNumber + 1) % audioStore.metronome.timeSignature
  }
}

async function startMetronome() {
  isStarting.value = true
  try {
    await ensureAudioCtx()
    beatNumber = 0
    // Set nextBeatTime AFTER context is running — currentTime is valid now
    nextBeatTime = audioCtx.currentTime + 0.05
    clearInterval(schedulerTimer)
    schedulerTimer = setInterval(scheduler, LOOKAHEAD_MS)
    audioStore.setMetronomeRunning(true)
  } finally {
    isStarting.value = false
  }
}

function stopMetronome() {
  clearInterval(schedulerTimer)
  schedulerTimer = null
  audioStore.setMetronomeRunning(false)
  audioStore.setCurrentBeat(0)
}

function restartIfRunning() {
  if (audioStore.metronome.isRunning) {
    stopMetronome()
    setTimeout(() => startMetronome(), 30)
  }
}

async function toggleMetronome() {
  if (audioStore.metronome.isRunning) {
    stopMetronome()
  } else {
    await startMetronome()
  }
}

// ── Controls ────────────────────────────────────────────────────────────────
function changeBpm(delta) {
  audioStore.setMetronomeBpm(audioStore.metronome.bpm + delta)
  localBpm.value = audioStore.metronome.bpm
  restartIfRunning()
}

function onSliderChange(val) {
  audioStore.setMetronomeBpm(val)
  restartIfRunning()
}

function onTimeSigChange() {
  restartIfRunning()
}

function useDetectedBpm() {
  audioStore.useDetectedBpm()
  localBpm.value = audioStore.metronome.bpm
  restartIfRunning()
}

const tapTimes_ = []
function tapTempo() {
  const now = performance.now()
  tapTimes_.push(now)
  if (tapTimes_.length > 8) tapTimes_.shift()

  if (tapTimes_.length >= 2) {
    const gaps = []
    for (let i = 1; i < tapTimes_.length; i++) {
      gaps.push(tapTimes_[i] - tapTimes_[i - 1])
    }
    const avgGap = gaps.reduce((a, b) => a + b, 0) / gaps.length
    const bpm = Math.round(60000 / avgGap)
    audioStore.setMetronomeBpm(bpm)
    localBpm.value = audioStore.metronome.bpm
    restartIfRunning()
  }

  // Auto-start on first tap
  if (!audioStore.metronome.isRunning) {
    startMetronome()
  }
}

// ── Pendulum ────────────────────────────────────────────────────────────────
const pendulumStyle = computed(() => {
  if (!audioStore.metronome.isRunning) return {}
  const period = (60 / audioStore.metronome.bpm) * 2
  return { animationDuration: `${period}s` }
})

onUnmounted(() => {
  stopMetronome()
  if (audioCtx) { audioCtx.close(); audioCtx = null }
})
</script>

<style scoped>
.metronome-page { background: transparent; }
.metronome-inner { width: 100%; max-width: 420px; }

.pendulum-container {
  height: 220px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.pendulum-track {
  position: relative;
  width: 200px;
  height: 160px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}
.pendulum-arm {
  position: absolute;
  top: 0;
  width: 3px;
  height: 130px;
  background: linear-gradient(to bottom, #7C3AED, #4C1D95);
  border-radius: 2px;
  transform-origin: top center;
  transform: rotate(0deg);
}
.pendulum-arm.is-running {
  animation: swing linear infinite alternate;
}
@keyframes swing {
  from { transform: rotate(-40deg); }
  to   { transform: rotate(40deg); }
}
.pendulum-bob {
  position: absolute;
  bottom: -14px;
  left: 50%;
  transform: translateX(-50%);
  width: 28px;
  height: 28px;
  background: #7C3AED;
  border-radius: 50%;
  box-shadow: 0 0 12px rgba(124,58,237,0.5);
  transition: background 0.08s, box-shadow 0.08s;
}
.pendulum-bob.accent {
  background: #06B6D4;
  box-shadow: 0 0 18px rgba(6,182,212,0.9);
}
.beat-lights { margin-top: auto; }
.beat-light {
  width: 14px; height: 14px;
  border-radius: 50%;
  background: #333;
  transition: background 0.06s, box-shadow 0.06s;
}
.beat-light.active {
  background: #7C3AED;
  box-shadow: 0 0 8px rgba(124,58,237,0.8);
}
.beat-light.active.accent {
  background: #06B6D4;
  box-shadow: 0 0 12px rgba(6,182,212,1);
}
.bpm-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
}
.bpm-number {
  font-size: 5rem;
  font-weight: 800;
  line-height: 1;
  color: white;
  min-width: 130px;
}
</style>
