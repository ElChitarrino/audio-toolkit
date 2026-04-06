<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated class="bg-dark-header">
      <q-toolbar>
        <q-btn
          flat dense round
          icon="menu"
          aria-label="Menu"
          @click="toggleDrawer"
        />
        <q-avatar size="32px" class="q-mr-sm">
          <img src="../assets/logoLessBorders.png" />
        </q-avatar>
        <q-toolbar-title class="text-weight-bold">
          Audio Toolkit
        </q-toolbar-title>

        <q-tabs
          v-model="activeTab"
          dense
          no-caps
          indicator-color="primary"
          class="gt-xs"
        >
          <q-route-tab name="home"      to="/"          icon="home"      label="Home" />
          <q-route-tab name="analyze"   to="/analyze"   icon="analytics" label="Analyze" />
          <q-route-tab name="metronome" to="/metronome" icon="timer"         label="Metronome" />
          <q-route-tab name="library"   to="/library"   icon="library_music" label="Library" />
        </q-tabs>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="drawerOpen"
      show-if-above
      bordered
      :width="220"
      class="bg-dark-drawer"
    >
      <q-list padding>
        <q-item-label header class="text-grey-5 text-caption">Navigation</q-item-label>

        <q-item clickable v-ripple to="/" exact active-class="drawer-active">
          <q-item-section avatar><q-icon name="home" /></q-item-section>
          <q-item-section>Home</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/analyze" active-class="drawer-active">
          <q-item-section avatar><q-icon name="analytics" /></q-item-section>
          <q-item-section>Analyze</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/metronome" active-class="drawer-active">
          <q-item-section avatar><q-icon name="timer" /></q-item-section>
          <q-item-section>Metronome</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/library" active-class="drawer-active">
          <q-item-section avatar><q-icon name="library_music" /></q-item-section>
          <q-item-section>Library</q-item-section>
        </q-item>

        <q-separator class="q-my-md" />

        <q-item-label header class="text-grey-5 text-caption">Status</q-item-label>

        <q-item dense>
          <q-item-section avatar>
            <q-icon
              :name="audioStore.hasAudio ? 'music_note' : 'music_off'"
              :color="audioStore.hasAudio ? 'positive' : 'grey-7'"
            />
          </q-item-section>
          <q-item-section>
            <q-item-label caption :class="audioStore.hasAudio ? 'text-positive' : 'text-grey-6'">
              {{ audioStore.hasAudio ? 'Audio loaded' : 'No audio' }}
            </q-item-label>
          </q-item-section>
        </q-item>

        <q-item dense v-if="audioStore.bpm">
          <q-item-section avatar>
            <q-icon name="speed" color="secondary" />
          </q-item-section>
          <q-item-section>
            <q-item-label caption class="text-secondary">
              {{ audioStore.bpm }} BPM detected
            </q-item-label>
          </q-item-section>
        </q-item>

        <q-item dense v-if="audioStore.currentChord && audioStore.currentChord !== '—'">
          <q-item-section avatar>
            <q-icon name="piano" color="accent" />
          </q-item-section>
          <q-item-section>
            <q-item-label caption class="text-accent">
              Playing: {{ audioStore.currentChord }}
            </q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useAudioStore } from 'src/stores/audioStore'

const drawerOpen = ref(false)
const activeTab = ref('home')
const audioStore = useAudioStore()

function toggleDrawer() {
  drawerOpen.value = !drawerOpen.value
}
</script>

<style scoped>
.bg-dark-header {
  background: #0d0d1a;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.bg-dark-drawer {
  background: #0f0f1e;
  border-right: 1px solid rgba(255,255,255,0.06);
}
.drawer-active {
  color: #7C3AED;
  background: rgba(124,58,237,0.1);
}
</style>
