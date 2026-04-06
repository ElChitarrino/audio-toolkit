# Audio Toolkit SE

## Overview
A Vue 3 + Quasar Framework web application for music enthusiasts. Search YouTube videos, download them as MP3, detect BPM/tempo, analyze chords in real-time, practice with a built-in metronome, and manage a persistent track library.

## Tech Stack
- **Frontend**: Vue 3 + Quasar Framework v2 (SPA, hash routing) — port 5000
- **Backend**: FastAPI (Python 3.11) + yt-dlp — port 8000
- **Build Tool**: Vite (via @quasar/app-vite)
- **State Management**: Pinia (`src/stores/audioStore.js`)
- **Routing**: Vue Router — routes: `/`, `/analyze`, `/metronome`, `/library`
- **HTTP Client**: Axios — relative path `/audiorequester` (proxied by Vite dev server)
- **Audio Analysis**: Meyda.js (chromagram for chord detection), Web Audio API for BPM
- **Styling**: SCSS + Quasar components, dark music theme

## Workflows
- **"Start application"** — `npm run dev` → frontend on port 5000
- **"Backend API"** — `uvicorn backend.main:app --host 0.0.0.0 --port 8000`

## Features
- **YouTube Search** — `GET /audiorequester/search?query=...` (yt-dlp `ytsearch10`)
- **Audio Download** — `GET /audiorequester/download?video_id=...` — saves MP3 to `backend/library/` and returns the file. If already downloaded, serves immediately.
- **BPM / Tempo Detection** — client-side autocorrelation on energy envelope (offline)
- **Chord Detection** — real-time Meyda.js chromagram + offline full-file analysis
- **Metronome** — Web Audio API click track (async AudioContext resume), visual pendulum, tap-tempo, time signatures
- **Track Library** — persisted downloads: `backend/library/{video_id}.mp3` + `index.json`. Tracks load directly from library without re-downloading.

## Project Structure
```
backend/
  main.py            FastAPI: search, download, library list/serve/delete, health
  library/           MP3 files + index.json (gitignored)
src/
  stores/
    audioStore.js    Pinia store: video, audio, BPM, chords, metronome, loadFromLibrary
  pages/
    IndexPage.vue    Home: search, video select, download trigger
    AnalyzePage.vue  BPM display, AudioPlayer, ChordDisplay
    MetronomePage.vue Standalone metronome (async AudioContext)
    LibraryPage.vue  Grid of downloaded tracks, Analyze / Delete actions
  components/
    AudioPlayer.vue  HTML5 player + Meyda real-time analysis + offline BPM/chord (lazy blob fetch)
    SearchBar.vue    YouTube search with debounce, error handling
    ChordDisplay.vue Live chord + chord progression timeline
  layouts/
    MainLayout.vue   Header nav tabs (Home/Analyze/Metronome/Library), live status sidebar
  boot/
    axios.js         API helpers: searchVideos, downloadVideo, getLibrary, deleteTrack, getAudioUrl
```

## Backend API
- `GET /health` → `{"status": "ok"}`
- `GET /audiorequester/search?query=<str>` → `[{id, videoId, title, thumbnail}]`
- `GET /audiorequester/download?video_id=<str>` → MP3 FileResponse (persists to library)
- `GET /audiorequester/library` → `[{videoId, title, thumbnail, downloadedAt, fileSize}]`
- `GET /audiorequester/audio/<video_id>` → MP3 FileResponse (from library)
- `DELETE /audiorequester/library/<video_id>` → `{deleted: videoId}`
- CORS: open (`allow_origins=["*"]`)
- yt-dlp for search/download; ffmpeg for MP3 extraction

## Proxy
Vite dev server proxies `/audiorequester/*` → `http://127.0.0.1:8000`. All API calls use relative paths.

## Metronome (AudioContext)
`ensureAudioCtx()` is async and `await`s `audioCtx.resume()` before the scheduler starts. This ensures `currentTime` is valid when `nextBeatTime` is set, so scheduled beats always land in the future.

## Theme
Dark music theme: primary `#7C3AED` (purple), secondary `#06B6D4` (cyan), accent `#F59E0B` (amber), bg `#0a0a14`
