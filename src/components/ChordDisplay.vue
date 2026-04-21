<template>
  <div class="chord-display q-pa-md">
    <div class="row items-baseline justify-between q-mb-sm">
      <div class="text-caption text-grey-5">Current Chord</div>
      <div v-if="audioStore.songKey" class="text-caption text-grey-5">
        Key: <span class="text-white">{{ audioStore.songKey }}</span>
      </div>
    </div>

    <div class="current-chord-box text-center q-py-md">
      <div class="chord-name" :class="chordColorClass">
        {{ currentChord || '—' }}
      </div>
    </div>

    <div v-if="audioStore.chords.length > 0" class="q-mt-md">
      <div class="text-caption text-grey-5 q-mb-sm">
        Chord Progression
        <span class="text-grey-7">({{ audioStore.chords.length }} segments)</span>
      </div>
      <div class="timeline-scroll" ref="scrollEl">
        <div
          v-for="(entry, idx) in audioStore.chords"
          :key="idx"
          class="chord-chip"
          :class="[getChordType(entry.chord), { 'is-active': idx === activeIdx }]"
          :data-idx="idx"
          @click="seekTo(entry.start)"
        >
          <div class="chord-chip-name">{{ entry.chord }}</div>
          <div class="chord-chip-time">{{ formatTime(entry.start) }}</div>
        </div>
      </div>
    </div>

    <div
      v-else-if="!audioStore.isAnalyzing"
      class="text-center text-grey-6 q-py-md text-caption"
    >
      Press "Analyze Chords" to detect the progression
    </div>
    <div v-else class="text-center text-grey-6 q-py-md text-caption">
      Analyzing... this can take 5–15 seconds
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { useAudioStore } from 'src/stores/audioStore'

const audioStore = useAudioStore()
const scrollEl = ref(null)

// Find the chord segment that contains the current playback time
const activeIdx = computed(() => {
  const t = audioStore.playbackTime
  const arr = audioStore.chords
  if (!arr.length) return -1
  // Binary search would be nicer; linear is fine for typical sizes
  for (let i = 0; i < arr.length; i++) {
    if (t >= arr[i].start && t < arr[i].end) return i
  }
  return -1
})

const currentChord = computed(() => {
  const idx = activeIdx.value
  return idx >= 0 ? audioStore.chords[idx].chord : null
})

const chordColorClass = computed(() => {
  const c = currentChord.value
  if (!c) return 'text-grey-5'
  if (c.endsWith('m')) return 'chord-minor'
  return 'chord-major'
})

function getChordType(chord) {
  if (chord && chord.endsWith('m')) return 'type-minor'
  return 'type-major'
}

function formatTime(secs) {
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function seekTo(time) {
  // Find the audio element on the page and seek
  const audio = document.querySelector('.audio-player audio')
  if (audio) {
    audio.currentTime = time
    if (audio.paused) audio.play()
  }
}

// Auto-scroll to keep the active chord in view
watch(activeIdx, async (idx) => {
  if (idx < 0 || !scrollEl.value) return
  await nextTick()
  const chip = scrollEl.value.querySelector(`[data-idx="${idx}"]`)
  if (chip) chip.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' })
})
</script>

<style scoped>
.chord-display {
  background: rgba(255,255,255,0.03);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
}
.chord-name {
  font-size: 3rem;
  font-weight: 700;
  letter-spacing: -1px;
  line-height: 1;
  transition: color 0.15s;
}
.chord-major { color: #7C3AED; }
.chord-minor { color: #06B6D4; }

.timeline-scroll {
  display: flex;
  flex-wrap: wrap;
  max-height: 180px;
  overflow-y: auto;
  gap: 6px;
}
.chord-chip {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  min-width: 52px;
  transition: transform 0.1s, box-shadow 0.1s;
  user-select: none;
}
.chord-chip:hover { transform: translateY(-1px); }
.chord-chip.is-active {
  box-shadow: 0 0 0 2px #fff inset;
  transform: scale(1.05);
}
.chord-chip-name { font-size: 0.95rem; font-weight: 600; }
.chord-chip-time { font-size: 0.65rem; opacity: 0.7; margin-top: 2px; }

.type-major { background: rgba(124,58,237,0.2); color: #a78bfa; }
.type-minor { background: rgba(6,182,212,0.2);  color: #67e8f9; }
</style>
