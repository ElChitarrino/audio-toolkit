<template>
  <div class="search-wrap">
    <q-input
      v-model="query"
      rounded
      outlined
      dark
      placeholder="Search YouTube for a song or artist..."
      class="search-input"
      :loading="isLoading"
      clearable
      @update:model-value="onInput"
      @clear="suggestions = []"
    >
      <template #prepend>
        <q-icon name="search" color="grey-5" />
      </template>
    </q-input>

    <q-banner
      v-if="searchError"
      class="q-mt-sm bg-warning text-dark rounded-borders"
      dense rounded
    >
      <template #avatar><q-icon name="warning" /></template>
      Backend not reachable. Make sure the FastAPI server is running on port 8000.
    </q-banner>

    <ul v-if="suggestions.length" class="suggestions">
      <li
        v-for="video in suggestions"
        :key="video.id"
        @click="onSelect(video)"
      >
        <img :src="video.thumbnail" alt="Thumbnail" />
        <span>{{ video.title }}</span>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { searchVideos } from 'src/boot/axios'

const emit = defineEmits(['video-selected'])

const query = ref('')
const suggestions = ref([])
const isLoading = ref(false)
const searchError = ref(false)

let debounceTimer = null

function onInput(val) {
  clearTimeout(debounceTimer)
  searchError.value = false
  if (!val || val.length <= 2) {
    suggestions.value = []
    return
  }
  debounceTimer = setTimeout(async () => {
    isLoading.value = true
    try {
      const results = await searchVideos(val)
      suggestions.value = results || []
      searchError.value = false
    } catch {
      searchError.value = true
      suggestions.value = []
    } finally {
      isLoading.value = false
    }
  }, 400)
}

function onSelect(video) {
  emit('video-selected', video)
  query.value = video.title
  suggestions.value = []
}
</script>

<style scoped>
.search-wrap {
  position: relative;
  width: 100%;
}
.search-input {
  width: 100%;
}
</style>
