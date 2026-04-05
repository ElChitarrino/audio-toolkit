# Audio Toolkit SE

## Overview
A Vue 3 + Quasar Framework web application for music enthusiasts. Search YouTube videos, download them as MP3, detect BPM/tempo, analyze chords in real-time, and practice with a built-in metronome.

## Tech Stack
- **Frontend**: Vue 3 + Quasar Framework v2 (SPA, hash routing) — port 5000
- **Backend**: FastAPI (Python 3.11) + yt-dlp — port 8000
- **Build Tool**: Vite (via @quasar/app-vite)
- **State Management**: Pinia (`src/stores/audioStore.js`)
- **Routing**: Vue Router — routes: `/`, `/analyze`, `/metronome`
- **HTTP Client**: Axios → `http://127.0.0.1:8000/audiorequester`
- **Audio Analysis**: Meyda.js (chromagram for chord detection, energy for BPM)
- **Styling**: SCSS + Quasar components, dark music theme

## Workflows
- **"Start application"** — `npm run dev` → frontend on port 5000
- **"Backend API"** — `uvicorn backend.main:app --host 0.0.0.0 --port 8000`

## Features
- **YouTube Search** — via `GET /audiorequester/search?query=...` (yt-dlp `ytsearch10`)
- **Audio Download** — via `GET /audiorequester/download?video_id=...` (returns MP3 blob via yt-dlp + ffmpeg)
- **BPM / Tempo Detection** — client-side, Web Audio API + autocorrelation on energy envelope
- **Chord Detection** — real-time Meyda.js chromagram + offline full-file analysis
- **Metronome** — Web Audio API click track, visual pendulum, tap-tempo, time signatures

## Project Structure
```
backend/
  main.py            FastAPI app: /audiorequester/search, /audiorequester/download, /health
  requirements.txt   fastapi, uvicorn[standard], yt-dlp
src/
  stores/
    audioStore.js    Central Pinia store: video, audio, BPM, chords, metronome state
  pages/
    IndexPage.vue    Home: search, video select, download trigger
    AnalyzePage.vue  BPM display, AudioPlayer, ChordDisplay
    MetronomePage.vue Standalone metronome
  components/
    AudioPlayer.vue  HTML5 player + Meyda real-time analysis + offline BPM/chord detection
    SearchBar.vue    YouTube search with debounce, error handling
    ChordDisplay.vue Live chord + chord progression timeline
  layouts/
    MainLayout.vue   Header nav tabs (Home/Analyze/Metronome), live status sidebar
  boot/
    axios.js         API helpers: searchVideos, downloadVideo (blob)
```

## Backend API
- `GET /health` → `{"status": "ok"}`
- `GET /audiorequester/search?query=<str>` → JSON array of `{id, videoId, title, thumbnail}`
- `GET /audiorequester/download?video_id=<str>` → MP3 audio/mpeg binary (FileResponse)
- CORS: open (`allow_origins=["*"]`)
- Uses yt-dlp for search and download; ffmpeg for MP3 extraction

## Development
- **Frontend**: `npm run dev` (port 5000)
- **Backend**: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
- **Build**: `npm run build` → `dist/spa`
- **Deployment**: static site build, publicDir `dist/spa`

## Theme
Dark music theme: primary `#7C3AED` (purple), secondary `#06B6D4` (cyan), accent `#F59E0B` (amber), bg `#0a0a14`
