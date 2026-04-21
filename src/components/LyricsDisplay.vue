<template>
  <div class="lyrics-display q-pa-md">
    <div class="row items-center justify-between q-mb-sm">
      <div class="text-caption text-grey-5">Lyrics</div>
      <div v-if="audioStore.lyricsAvailable" class="text-caption text-grey-7">
        synced from YouTube captions
      </div>
    </div>

    <div v-if="audioStore.isFetchingLyrics" class="text-center text-grey-6 q-py-lg">
      <q-spinner color="primary" size="2em" />
      <div class="text-caption q-mt-sm">Fetching lyrics...</div>
    </div>

    <div
      v-else-if="audioStore.lyricsAvailable === false"
      class="text-center text-grey-6 q-py-lg text-caption"
    >
      No lyrics available — this video has no captions on YouTube.
    </div>

    <div
      v-else-if="audioStore.lyricsAvailable === null"
      class="text-center text-grey-6 q-py-md text-caption"
    >
      Press "Get Lyrics" to fetch synced lyrics
    </div>

    <div v-else ref="scrollEl" class="lyrics-scroll">
      <div
        v-for="(line, idx) in audioStore.lyrics"
        :key="idx"
        class="lyric-line"
        :class="{
          'is-active': idx === activeIdx,
          'is-past':   idx < activeIdx,
        }"
        :data-idx="idx"
        @click="seekTo(line.start)"
      >
        {{ line.text }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { useAudioStore } from 'src/stores/audioStore'

const audioStore = useAudioStore()
const scrollEl = ref(null)

const activeIdx = computed(() => {
  const t = audioStore.playbackTime
  const arr = audioStore.lyrics
  if (!arr.length) return -1
  for (let i = arr.length - 1; i >= 0; i--) {
    if (t >= arr[i].start) return i
  }
  return -1
})

function seekTo(time) {
  const audio = document.querySelector('.audio-player audio')
  if (audio) {
    audio.currentTime = time
    if (audio.paused) audio.play()
  }
}

watch(activeIdx, async (idx) => {
  if (idx < 0 || !scrollEl.value) return
  await nextTick()
  const el = scrollEl.value.querySelector(`[data-idx="${idx}"]`)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
})
</script>

<style scoped>
.lyrics-display {
  background: rgba(255,255,255,0.03);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  height: 100%;
  min-height: 240px;
}
.lyrics-scroll {
  max-height: 320px;
  overflow-y: auto;
  padding-right: 8px;
}
.lyric-line {
  font-size: 1rem;
  line-height: 1.6;
  padding: 6px 10px;
  border-radius: 6px;
  color: #6b7280;
  cursor: pointer;
  transition: color 0.2s, background 0.2s, transform 0.2s;
}
.lyric-line:hover { background: rgba(255,255,255,0.04); }
.lyric-line.is-past { color: #4b5563; }
.lyric-line.is-active {
  color: #fff;
  background: rgba(124,58,237,0.18);
  font-weight: 600;
  font-size: 1.1rem;
  transform: translateX(4px);
}
</style>
