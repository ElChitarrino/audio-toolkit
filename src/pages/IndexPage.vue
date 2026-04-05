<template>
  <q-page class="index-page q-pa-md">
    <div class="page-inner q-mx-auto">

      <div class="logo-row row justify-center q-mb-lg">
        <q-img
          alt="Audio Toolkit logo"
          src="../assets/logoLessBorders.png"
          style="width: 100px; height: 100px;"
        />
      </div>

      <div class="text-center q-mb-xl">
        <div class="text-h5 text-white q-mb-xs">Audio Toolkit SE</div>
        <div class="text-caption text-grey-5">Search YouTube · Detect BPM · Analyze Chords · Metronome</div>
      </div>

      <SearchBar @video-selected="onVideoSelected" />

      <div v-if="audioStore.currentVideo" class="selected-video q-mt-lg">
        <div class="text-caption text-grey-5 q-mb-sm">Selected Video</div>
        <div class="video-card row items-center q-gutter-md q-pa-md">
          <q-img
            :src="audioStore.currentVideo.thumbnail"
            style="width: 90px; height: 68px; border-radius: 8px; flex-shrink: 0;"
          />
          <div class="col ellipsis-2-lines text-white text-subtitle2">
            {{ audioStore.currentVideo.title }}
          </div>
        </div>

        <div class="q-mt-md row q-gutter-sm">
          <q-btn
            color="primary"
            icon="download"
            label="Download & Load"
            no-caps
            :loading="audioStore.isDownloading"
            :disable="audioStore.isDownloading"
            @click="downloadAudio"
          />
          <q-btn
            v-if="audioStore.hasAudio"
            color="secondary"
            icon="analytics"
            label="Analyze"
            no-caps
            to="/analyze"
          />
        </div>

        <q-banner
          v-if="audioStore.downloadError"
          class="q-mt-md bg-negative text-white rounded-borders"
          dense
          rounded
        >
          <template #avatar>
            <q-icon name="error" />
          </template>
          {{ audioStore.downloadError }}
          <template #action>
            <q-btn flat dense label="Dismiss" @click="audioStore.downloadError = null" />
          </template>
        </q-banner>

        <q-banner
          v-if="audioStore.hasAudio"
          class="q-mt-md bg-positive text-white rounded-borders"
          dense
          rounded
        >
          <template #avatar>
            <q-icon name="check_circle" />
          </template>
          Audio loaded! Go to Analyze to detect BPM and chords.
          <template #action>
            <q-btn flat dense label="Analyze" to="/analyze" />
          </template>
        </q-banner>
      </div>

      <div v-if="!audioStore.currentVideo" class="quick-access row q-gutter-md q-mt-xl justify-center">
        <q-card
          class="quick-card cursor-pointer"
          flat
          @click="$router.push('/metronome')"
        >
          <q-card-section class="text-center q-pa-lg">
            <q-icon name="timer" size="2.5rem" color="primary" />
            <div class="text-subtitle2 text-white q-mt-sm">Metronome</div>
            <div class="text-caption text-grey-6">Practice with the beat</div>
          </q-card-section>
        </q-card>

        <q-card
          v-if="audioStore.hasAudio"
          class="quick-card cursor-pointer"
          flat
          @click="$router.push('/analyze')"
        >
          <q-card-section class="text-center q-pa-lg">
            <q-icon name="analytics" size="2.5rem" color="secondary" />
            <div class="text-subtitle2 text-white q-mt-sm">Analyze</div>
            <div class="text-caption text-grey-6">BPM · Chords</div>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAudioStore } from 'src/stores/audioStore'
import SearchBar from 'src/components/SearchBar.vue'

const audioStore = useAudioStore()
const router = useRouter()

function onVideoSelected(video) {
  audioStore.setVideo(video)
}

async function downloadAudio() {
  await audioStore.loadAudio(audioStore.currentVideo.videoId)
  if (audioStore.hasAudio) {
    router.push('/analyze')
  }
}
</script>

<style scoped>
.index-page {
  background: transparent;
}
.page-inner {
  max-width: 680px;
}
.video-card {
  background: rgba(255,255,255,0.04);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
}
.quick-card {
  background: rgba(255,255,255,0.04);
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.08);
  min-width: 150px;
  transition: background 0.2s;
}
.quick-card:hover {
  background: rgba(255,255,255,0.08);
}
.ellipsis-2-lines {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
