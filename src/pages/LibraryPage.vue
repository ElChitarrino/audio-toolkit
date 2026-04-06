<template>
  <q-page class="library-page q-pa-md">
    <div class="page-inner q-mx-auto">

      <div class="row items-center q-mb-lg">
        <div class="text-h6 text-white">Downloaded Tracks</div>
        <q-space />
        <q-btn flat round icon="refresh" color="grey-4" @click="loadLibrary" />
      </div>

      <div v-if="isLoading" class="text-center q-py-xl">
        <q-spinner-audio color="primary" size="3rem" />
        <div class="text-grey-5 q-mt-md">Loading library…</div>
      </div>

      <div v-else-if="tracks.length === 0" class="empty-state text-center q-py-xl">
        <q-icon name="library_music" size="4rem" color="grey-7" />
        <div class="text-h6 text-grey-5 q-mt-md">Library is empty</div>
        <div class="text-caption text-grey-7 q-mb-lg">Search for a YouTube video and download it to add tracks here.</div>
        <q-btn color="primary" icon="search" label="Go to Search" no-caps to="/" />
      </div>

      <div v-else class="track-grid">
        <div
          v-for="track in tracks"
          :key="track.videoId"
          class="track-card"
        >
          <q-img
            :src="track.thumbnail"
            :ratio="16/9"
            class="track-thumb"
          >
            <template #error>
              <div class="absolute-full flex flex-center bg-grey-9">
                <q-icon name="music_note" size="2rem" color="grey-5" />
              </div>
            </template>
          </q-img>

          <div class="track-info q-pa-sm">
            <div class="track-title ellipsis-2-lines">{{ track.title }}</div>
            <div class="track-meta text-caption text-grey-6 q-mt-xs">
              {{ formatDate(track.downloadedAt) }}
              <span v-if="track.fileSize"> · {{ formatSize(track.fileSize) }}</span>
            </div>
          </div>

          <div class="track-actions row q-pa-sm q-pt-none q-gutter-xs">
            <q-btn
              size="sm" no-caps unelevated
              color="primary"
              icon="analytics"
              label="Analyze"
              class="col"
              @click="loadAndAnalyze(track)"
            />
            <q-btn
              size="sm" flat round
              color="negative"
              icon="delete"
              @click="confirmDelete(track)"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Delete confirm dialog -->
    <q-dialog v-model="deleteDialog">
      <q-card style="min-width: 280px" class="bg-dark">
        <q-card-section>
          <div class="text-subtitle1">Delete track?</div>
          <div class="text-caption text-grey-5 q-mt-xs ellipsis-2-lines">{{ deleteTarget?.title }}</div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="grey-4" v-close-popup />
          <q-btn flat label="Delete" color="negative" @click="doDelete" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAudioStore } from 'src/stores/audioStore'
import { getLibrary, deleteTrack } from 'src/boot/axios'

const router = useRouter()
const audioStore = useAudioStore()

const tracks = ref([])
const isLoading = ref(true)
const deleteDialog = ref(false)
const deleteTarget = ref(null)

async function loadLibrary() {
  isLoading.value = true
  try {
    tracks.value = await getLibrary()
  } catch {
    tracks.value = []
  } finally {
    isLoading.value = false
  }
}

function loadAndAnalyze(track) {
  audioStore.loadFromLibrary(track)
  router.push('/analyze')
}

function confirmDelete(track) {
  deleteTarget.value = track
  deleteDialog.value = true
}

async function doDelete() {
  if (!deleteTarget.value) return
  try {
    await deleteTrack(deleteTarget.value.videoId)
    tracks.value = tracks.value.filter(t => t.videoId !== deleteTarget.value.videoId)
  } catch {
    // silently ignore
  }
  deleteTarget.value = null
}

function formatDate(iso) {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
  } catch {
    return ''
  }
}

function formatSize(bytes) {
  if (!bytes) return ''
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(1)} MB`
}

onMounted(loadLibrary)
</script>

<style scoped>
.library-page { background: transparent; }
.page-inner { max-width: 900px; }

.track-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.track-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: background 0.2s, transform 0.15s;
}
.track-card:hover {
  background: rgba(255,255,255,0.07);
  transform: translateY(-2px);
}

.track-thumb { border-radius: 0; }

.track-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: #e2e2e2;
  line-height: 1.3;
}
.track-meta { font-size: 0.75rem; }
.track-actions { margin-top: auto; }

.ellipsis-2-lines {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.empty-state { padding-top: 60px; }
</style>
