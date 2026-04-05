# Audio Toolkit SE

## Overview
A Vue 3 + Quasar Framework web application for music enthusiasts. Search YouTube videos, download them as MP3, detect BPM/tempo, analyze chords in real-time, and practice with a built-in metronome.

## Tech Stack
- **Frontend**: Vue 3 + Quasar Framework v2 (SPA, hash routing)
- **Build Tool**: Vite (via @quasar/app-vite)
- **State Management**: Pinia (`src/stores/audioStore.js`)
- **Routing**: Vue Router — routes: `/`, `/analyze`, `/metronome`
- **HTTP Client**: Axios (points to FastAPI backend at `localhost:8000`)
- **Audio Analysis**: Meyda.js (chromagram for chord detection, energy for BPM)
- **i18n**: Vue I18n
- **Styling**: SCSS + Quasar components, dark music theme

## Features
- **YouTube Search** — Search videos via the FastAPI backend (requires backend running)
- **BPM / Tempo Detection** — Offline analysis using Web Audio API + autocorrelation (client-side, no backend needed once MP3 is loaded)
- **Chord Detection** — Real-time chromagram analysis via Meyda.js during playback; full chord progression timeline via offline analysis
- **Metronome** — Standalone metronome with Web Audio API click track, visual pendulum, tap-tempo, time signature selector (2/4, 3/4, 4/4, 6/8), and "use detected BPM" shortcut

## Project Structure
- `src/stores/audioStore.js` — Central Pinia store: video, audio blob/URL, BPM, chords, metronome state
- `src/pages/IndexPage.vue` — Home: search, video selection, download trigger
- `src/pages/AnalyzePage.vue` — Analysis: audio player, BPM display, chord timeline
- `src/pages/MetronomePage.vue` — Standalone metronome
- `src/components/AudioPlayer.vue` — HTML5 player + Meyda real-time analysis + offline BPM/chord detection
- `src/components/SearchBar.vue` — YouTube search with debounce + backend error handling
- `src/components/ChordDisplay.vue` — Live chord + full chord progression display
- `src/layouts/MainLayout.vue` — Header nav tabs (Home/Analyze/Metronome), sidebar status
- `src/boot/axios.js` — API calls: searchVideos, downloadVideo (returns Blob)

## Backend (FastAPI — not in this repo)
The frontend expects a FastAPI server at `http://127.0.0.1:8000/audiorequester` with:
- `GET /search?query=...` → list of videos
- `GET /download?video_id=...` → MP3 audio blob

The metronome works without a backend. BPM and chord detection work once audio is downloaded.

## Development
- **Run**: `npm run dev` (port 5000)
- **Build**: `npm run build` → `dist/spa`
- **Deployment**: static site, publicDir `dist/spa`

## Theme
Dark music theme: primary `#7C3AED` (purple), secondary `#06B6D4` (cyan), accent `#F59E0B` (amber), background `#0a0a14`
