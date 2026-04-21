<template>
  <q-page class="analyze-page q-pa-md">
    <div class="page-inner q-mx-auto">

      <div v-if="!audioStore.hasAudio" class="empty-state text-center q-py-xl">
        <q-icon name="music_off" size="4rem" color="grey-7" />
        <div class="text-h6 text-grey-5 q-mt-md">No audio loaded</div>
        <div class="text-caption text-grey-7 q-mb-lg">Go to Home, search for a YouTube video and download it first.</div>
        <q-btn color="primary" icon="search" label="Go to Search" no-caps to="/" />
      </div>

      <template v-else>
        <div class="video-header q-mb-lg row items-center q-gutter-md">
          <q-img
            v-if="audioStore.currentVideo"
            :src="audioStore.currentVideo.thumbnail"
            style="width: 80px; height: 60px; border-radius: 8px; flex-shrink: 0;"
          />
          <div>
            <div class="text-subtitle1 text-white ellipsis-2-lines">
              {{ audioStore.currentVideo?.title || 'Audio Track' }}
            </div>
            <div class="text-caption text-grey-5">Ready for analysis</div>
          </div>
        </div>

        <div class="row q-col-gutter-md">
          <div class="col-12">
            <AudioPlayer />
          </div>

          <div class="col-12 col-md-4">
            <div class="stat-card q-pa-lg text-center">
              <div class="text-caption text-grey-5 q-mb-sm">Detected BPM</div>
              <div class="bpm-value" :class="audioStore.bpm ? 'text-secondary' : 'text-grey-7'">
                {{ audioStore.bpm || '—' }}
              </div>
              <div v-if="audioStore.bpm" class="text-caption text-grey-5">beats per minute</div>
              <q-btn
                v-if="audioStore.bpm"
                flat dense no-caps
                color="secondary"
                icon="timer"
                label="Use in Metronome"
                class="q-mt-sm"
                to="/metronome"
                @click="audioStore.useDetectedBpm()"
              />
            </div>
          </div>

          <div class="col-12 col-md-8">
            <ChordDisplay />
          </div>

          <div class="col-12">
            <LyricsDisplay />
          </div>
        </div>
      </template>
    </div>
  </q-page>
</template>

<script setup>
import { useAudioStore } from 'src/stores/audioStore'
import AudioPlayer from 'src/components/AudioPlayer.vue'
import ChordDisplay from 'src/components/ChordDisplay.vue'
import LyricsDisplay from 'src/components/LyricsDisplay.vue'

const audioStore = useAudioStore()
</script>

<style scoped>
.analyze-page {
  background: transparent;
}
.page-inner {
  max-width: 900px;
}
.empty-state {
  padding-top: 80px;
}
.stat-card {
  background: rgba(255,255,255,0.03);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  height: 100%;
}
.bpm-value {
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1;
}
.ellipsis-2-lines {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
