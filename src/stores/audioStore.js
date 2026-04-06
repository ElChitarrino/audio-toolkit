import { defineStore, acceptHMRUpdate } from 'pinia'
import { downloadVideo, getAudioUrl } from 'src/boot/axios'

export const useAudioStore = defineStore('audio', {
  state: () => ({
    currentVideo: null,
    audioUrl: null,
    audioBlob: null,      // present only for fresh downloads; null for library loads
    isDownloading: false,
    downloadError: null,
    isAnalyzing: false,
    bpm: null,
    chords: [],
    currentChord: null,
    currentChordConfidence: 0,
    metronome: {
      bpm: 120,
      isRunning: false,
      timeSignature: 4,
      currentBeat: 0,
    },
  }),

  getters: {
    hasAudio: (state) => !!state.audioUrl,
    hasVideo: (state) => !!state.currentVideo,
  },

  actions: {
    setVideo(video) {
      this.currentVideo = video
      this._clearAudio()
    },

    _clearAudio() {
      if (this.audioUrl && this.audioBlob) {
        // Only revoke object URLs we created (not /audiorequester/ paths)
        URL.revokeObjectURL(this.audioUrl)
      }
      this.audioUrl = null
      this.audioBlob = null
      this.bpm = null
      this.chords = []
      this.currentChord = null
      this.downloadError = null
    },

    /** Download from YouTube and store as blob */
    async loadAudio(videoId) {
      this.isDownloading = true
      this.downloadError = null
      try {
        const blob = await downloadVideo(videoId)
        if (this.audioBlob && this.audioUrl) URL.revokeObjectURL(this.audioUrl)
        this.audioBlob = blob
        this.audioUrl = URL.createObjectURL(blob)
      } catch (e) {
        this.downloadError = e.message || 'Download failed. Make sure the backend is running.'
      } finally {
        this.isDownloading = false
      }
    },

    /** Load a previously downloaded track from the library (no re-download) */
    loadFromLibrary(track) {
      if (this.audioBlob && this.audioUrl) URL.revokeObjectURL(this.audioUrl)
      this.audioBlob = null   // no blob — analysis will fetch on demand
      this.bpm = null
      this.chords = []
      this.currentChord = null
      this.downloadError = null
      this.currentVideo = {
        videoId: track.videoId,
        title: track.title,
        thumbnail: track.thumbnail,
      }
      this.audioUrl = getAudioUrl(track.videoId)
    },

    setBpm(bpm) {
      this.bpm = bpm
      this.metronome.bpm = bpm
    },

    setChords(chords) { this.chords = chords },

    setCurrentChord(chord, confidence) {
      this.currentChord = chord
      this.currentChordConfidence = confidence
    },

    setMetronomeBpm(bpm) {
      this.metronome.bpm = Math.max(40, Math.min(240, bpm))
    },

    setTimeSignature(ts) { this.metronome.timeSignature = ts },
    setMetronomeRunning(val) { this.metronome.isRunning = val },
    setCurrentBeat(beat) { this.metronome.currentBeat = beat },

    useDetectedBpm() {
      if (this.bpm) this.metronome.bpm = this.bpm
    },
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAudioStore, import.meta.hot))
}
