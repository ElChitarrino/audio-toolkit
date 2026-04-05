# Audio Toolkit SE

## Overview
A Vue 3 + Quasar Framework web application for music enthusiasts to analyze metadata and interact with audio tracks, potentially retrieved via the YouTube API.

## Tech Stack
- **Frontend**: Vue 3 + Quasar Framework v2 (SPA mode)
- **Build Tool**: Vite (via @quasar/app-vite)
- **State Management**: Pinia
- **Routing**: Vue Router (hash mode)
- **HTTP Client**: Axios
- **i18n**: Vue I18n
- **Styling**: SCSS + Quasar components
- **Package Manager**: npm

## Project Structure
- `src/` - Main source code
  - `boot/` - App initialization (axios, i18n)
  - `components/` - Reusable Vue components (SearchBar, VideoList)
  - `layouts/` - Layout wrappers (MainLayout)
  - `pages/` - Route views (IndexPage, ErrorNotFound)
  - `router/` - Route definitions
  - `stores/` - Pinia state stores
  - `css/` - Global styles
  - `i18n/` - Translation files
- `public/` - Static assets
- `quasar.config.js` - Quasar/Vite configuration

## Development
- **Run**: `npm run dev` (starts on port 5000)
- **Build**: `npm run build` → outputs to `dist/spa`
- **Lint**: `npm run lint`

## Replit Configuration
- Dev server: host `0.0.0.0`, port `5000`, `allowedHosts: 'all'`
- Deployment: static site, build command `npm run build`, public dir `dist/spa`
