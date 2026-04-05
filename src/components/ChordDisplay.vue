<template>
  <div class="chord-display">
    <div class="current-chord-box q-pa-lg text-center">
      <div class="text-caption text-grey-5 q-mb-xs">Current Chord</div>
      <div class="chord-name" :class="chordColorClass">
        {{ audioStore.currentChord || '—' }}
      </div>
      <div v-if="audioStore.currentChordConfidence > 0" class="text-caption text-grey-5 q-mt-xs">
        {{ audioStore.currentChordConfidence }}% confidence
      </div>
    </div>

    <div v-if="audioStore.chords.length > 0" class="chord-timeline q-pa-md">
      <div class="text-caption text-grey-5 q-mb-sm">Chord Progression</div>
      <div class="timeline-scroll">
        <div
          v-for="(entry, idx) in audioStore.chords"
          :key="idx"
          class="chord-chip q-mr-sm q-mb-sm"
          :class="getChordType(entry.chord)"
        >
          <div class="chord-chip-name">{{ entry.chord }}</div>
          <div class="chord-chip-time">{{ formatTime(entry.time) }}</div>
        </div>
      </div>
    </div>

    <div v-else-if="audioStore.chords.length === 0 && !audioStore.isAnalyzing" class="text-center text-grey-6 q-pa-md text-caption">
      Press "Analyze Chords" to detect chord progression
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAudioStore } from 'src/stores/audioStore'

const audioStore = useAudioStore()

const chordColorClass = computed(() => {
  const chord = audioStore.currentChord
  if (!chord || chord === '—') return 'text-grey-5'
  if (chord.includes('m') && !chord.includes('maj')) return 'chord-minor'
  if (chord.includes('7')) return 'chord-seventh'
  return 'chord-major'
})

function getChordType(chord) {
  if (!chord) return ''
  if (chord.includes('m') && !chord.includes('maj')) return 'type-minor'
  if (chord.includes('7')) return 'type-seventh'
  return 'type-major'
}

function formatTime(secs) {
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
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
  transition: color 0.2s;
}
.chord-major   { color: #7C3AED; }
.chord-minor   { color: #06B6D4; }
.chord-seventh { color: #F59E0B; }

.timeline-scroll {
  display: flex;
  flex-wrap: wrap;
  max-height: 160px;
  overflow-y: auto;
}

.chord-chip {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 12px;
  border-radius: 8px;
  cursor: default;
  min-width: 52px;
}
.chord-chip-name { font-size: 0.95rem; font-weight: 600; }
.chord-chip-time { font-size: 0.65rem; opacity: 0.7; margin-top: 2px; }

.type-major   { background: rgba(124,58,237,0.2); color: #a78bfa; }
.type-minor   { background: rgba(6,182,212,0.2);  color: #67e8f9; }
.type-seventh { background: rgba(245,158,11,0.2); color: #fcd34d; }
</style>
