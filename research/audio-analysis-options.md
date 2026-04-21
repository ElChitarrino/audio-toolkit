# Audio Toolkit — Pulse, Chord & Metronome Research

**Research Date:** April 21, 2026
**Depth:** Quick (3 focus areas, 8 search queries, 4 detailed page fetches)
**Sources Consulted:** 12

---

## Executive Summary

The Audio Toolkit currently uses **hand-rolled DSP** for everything: a custom autocorrelation BPM detector, a chromagram + template chord matcher (running through Meyda.js), and a `setInterval`-based metronome scheduler driving raw `OscillatorNode` clicks. All three are silently struggling because audio analysis is one of the harder corners of the web platform — and there are now well-tested, off-the-shelf libraries that solve each problem properly.

For the **metronome**, the root cause of the silence is almost certainly the standard "AudioContext won't unsuspend" trap, compounded by the fact that scheduling on the JS main thread is fundamentally fragile. The community has converged on two robust patterns: Chris Wilson's lookahead scheduler (the de-facto standard, used by every major browser metronome demo) and Paul Adenot's **looping `AudioBufferSourceNode`** approach (sample-accurate, runs entirely on the audio thread, can't drift or fail). Both require an explicit "unlock" play of a silent buffer on the first user gesture to handle Chrome/Safari autoplay policy.

For **BPM detection**, `realtime-bpm-analyzer` (TypeScript, zero deps, actively maintained, 5.x release within the last week) is the clear winner for browser apps — it works on both live audio nodes and offline AudioBuffers, and its peak-detection algorithm beats hand-rolled autocorrelation on real songs. For maximum accuracy at the cost of bundle size, `essentia.js` exposes the same `RhythmExtractor2013` algorithm used in MIR research papers.

For **chord detection**, the current chromagram approach is the right idea but the wrong implementation. `essentia.js` provides a production-grade `HPCP` + `ChordsDetection` pipeline with proper key context, used in real ISMIR research. Lighter alternatives are `akkorder` (TypeScript port of Adam Stark's chord detector) or `myers/chord_detector` (WASM bindings to the same C++ library). All three will outperform raw chromagram template matching by a wide margin.

---

## Background

The current implementation has three pain points that compound each other:

1. **Metronome silence.** `MetronomePage.vue` creates an `AudioContext` and schedules oscillator clicks using `setInterval(scheduler, 25)`. After the recent fix that made `ensureAudioCtx` async and awaited `resume()`, the scheduling math is correct in isolation — but the metronome still reports no sound. This points to the **autoplay policy interaction inside the Replit preview iframe**, where `resume()` may not actually transition the context to running unless an audio buffer has been played first within the same gesture.

2. **Tempo guessing inaccurate.** `AudioPlayer.vue` runs an offline energy-envelope autocorrelation in `estimateBpm()`. This works on dance music with strong kick patterns but fails on most real songs (it misses the beat on rock, jazz, lo-fi, anything with heavy harmonic content, and any tempo near multiples like 60/120 or 80/160).

3. **Chord detection noisy.** A 12-bin chromagram + cosine similarity against 4 chord templates per root (`maj`, `min`, `7`, `maj7`) is the textbook starting point. It produces correct chords on isolated chord stabs but flickers wildly on real polyphonic mixes because (a) it has no temporal smoothing, (b) it doesn't model the bass note separately, and (c) the templates don't match real spectral profiles.

The web has a small but mature ecosystem of audio-analysis libraries that solve all three problems. The findings below cover the trade-offs.

---

## Key Findings

### Finding 1: Metronome — switch to a looping AudioBuffer, not a scheduler

The canonical reference for Web Audio metronomes is Chris Wilson's **"A Tale of Two Clocks"** (web.dev/audio-scheduling) [1] and the accompanying [cwilso/metronome](https://github.com/cwilso/metronome) repo [2]. It uses a 25ms `setInterval` lookahead loop that schedules notes 100ms ahead of the audio clock. Our current code follows this pattern correctly. So why no sound?

The answer is in the Chrome autoplay policy documentation [3, 4]: even when you call `audioContext.resume()` inside a click handler, the context may remain suspended in iframed contexts (the Replit preview is iframed) unless an actual audio buffer has been **played and finished** inside the same user gesture. The standard "unlock" pattern is to play a 1-sample silent `AudioBuffer` immediately on the first click — this proves to the browser that audio is wanted, and all subsequent scheduled audio plays normally. Most metronome demos that "work everywhere" include this trick; ours does not.

A more elegant solution comes from Paul Adenot, a Mozilla Web Audio engineer, in his post **"A robust metronome using the Web Audio API"** [5]. Instead of scheduling individual notes from JavaScript, he precomputes a single `AudioBuffer` containing one bar's worth of clicks (silence + click + silence + click + …) and plays it as a **looping `AudioBufferSourceNode`**. The audio thread loops the buffer with sample-accurate precision — zero JavaScript scheduling, zero jitter, zero `setTimeout` to throttle in background tabs. When the BPM changes, regenerate the buffer and swap. When the time signature changes, regenerate the buffer and swap.

> _"Don't use the main thread if you don't have to: you can't predict how much it is doing."_ — Paul Adenot [5]

This approach has three advantages for our app:

1. It is **immune to the suspended-AudioContext bug**, because `start()` on a source node forces the context to actually produce sound — there's no scheduling-window issue where the scheduler runs before the context is live.
2. It survives background-tab throttling, low-end devices, and CPU spikes from the chord analyzer running in parallel.
3. It is much simpler code: no `nextBeatTime`, no `lookahead`, no `scheduleAheadTime`, no `setInterval`.

The trade-off is that BPM/time-signature changes require regenerating the buffer (a few-millisecond cost) and re-`start()`ing — a one-frame audible gap. For practice metronomes this is acceptable.

**Recommended action:** Either (a) add the "silent unlock buffer" trick to the existing scheduler, or (b) rewrite `MetronomePage.vue` to use a looping `AudioBufferSourceNode`. Option (b) is more code change but eliminates an entire class of bugs.

### Finding 2: BPM detection — adopt `realtime-bpm-analyzer`

Three serious libraries are in the running [6, 7, 8]:

| Library | Approach | Realtime | Offline | Bundle | Maintenance |
|---|---|---|---|---|---|
| **realtime-bpm-analyzer** | Peak detection + interval analysis | ✅ | ✅ | ~15 KB | v5.0.7 published 7 days ago [6] |
| **web-audio-beat-detector** | Tempo estimation on AudioBuffer | ❌ | ✅ | ~10 KB | v8.2.35, regular updates |
| **essentia.js** (`RhythmExtractor2013`) | Multi-feature beat tracker (MIR paper) | ✅ | ✅ | ~7 MB WASM | v0.1.3 |

`realtime-bpm-analyzer` is the right default because it integrates directly with our existing audio graph: connect the existing `MediaElementAudioSourceNode` to its analyzer node, and BPM events arrive as the song plays. It works on the same `AudioBuffer` for offline analysis too, so we get one library covering both cases. Zero dependencies, MIT-style license, TypeScript, actively maintained.

```javascript
import { createRealtimeBpmAnalyzer } from 'realtime-bpm-analyzer'

const analyzer = await createRealtimeBpmAnalyzer(audioContext)
sourceNode.connect(analyzer.node)
analyzer.on('bpm', (data) => {
  audioStore.setBpm(data.bpm[0].tempo)
})
```

If the user wants research-grade accuracy and is willing to ship a 7 MB WebAssembly bundle (worth it only for a serious music app), `essentia.js`'s `RhythmExtractor2013` is the same algorithm used in academic MIR papers and produces near-ground-truth BPM on most popular music [9].

`web-audio-beat-detector` is a solid backup choice if we only need offline analysis and want minimum bundle size.

### Finding 3: Chord detection — adopt `essentia.js` or `akkorder`

The current chromagram + cosine similarity approach is the textbook starting point for chord recognition, but it's known to be noisy on real audio. The two principled improvements are (a) use a better chromagram (HPCP — harmonic pitch class profile, which down-weights non-harmonic energy) and (b) add temporal smoothing (don't accept a chord change unless it's been observed for ≥N consecutive frames). All the libraries below do both.

Three options [10, 11, 12]:

| Library | Approach | Browser size | Quality | Notes |
|---|---|---|---|---|
| **essentia.js** (`HPCP` + `ChordsDetection`) | HPCP + key-aware Viterbi | ~7 MB WASM | Production / MIR research | Same library cited in ISMIR papers [9] |
| **akkorder** | TypeScript port of Adam Stark's chord detector | ~30 KB | Good for major/minor + 7ths | Pure JS, drop-in |
| **myers/chord_detector** | WASM bindings to Adam Stark's C++ | ~200 KB WASM | Same as akkorder, faster | Used in Sonic Visualiser |

`essentia.js` is the strongest choice because (a) we're already considering it for BPM, so we'd amortize the WASM bundle cost, and (b) its `KeyExtractor` algorithm gives us the song's key, which lets the chord detector make musically-sensible choices (e.g., prefer chords that fit the key over outliers).

`akkorder` is the best choice if bundle size matters: it's pure TypeScript, ~30 KB, and Adam Stark's algorithm is well-respected — it's the same one that powers the `myers/chord_detector` WASM binding. It returns major/minor/7th/dim chords for each frame and we'd add our own temporal smoothing.

**Important pairing:** any chord detector should be paired with **`@tonaljs/chord-detect`** [12] for music-theory-aware naming. Tonal.js doesn't analyze audio; it takes detected note names ("D", "F#", "A", "C") and returns the proper chord name with inversions and extensions ("D7"). This complements (not replaces) the audio analysis.

---

## Analysis

The three problems are connected: they all stem from trying to solve research-grade audio problems with a few hundred lines of hand-written JavaScript. The research-quality libraries exist, are open-source, and are actively maintained.

The strongest end-state for this app is a **two-library bet**:

- **`realtime-bpm-analyzer`** for tempo (small, perfect-fit, zero deps)
- **`essentia.js`** for chord + key detection (heavy but the only browser library with research-grade music analysis)

This gives us the best BPM library AND the best chord library for the same total bundle cost as essentia.js alone. The metronome doesn't need a library at all — switching to the looping `AudioBufferSourceNode` pattern fixes it permanently and removes ~150 lines of scheduler code.

The minimum-viable alternative, if we want to avoid the 7 MB WASM bundle, is:

- **`realtime-bpm-analyzer`** for tempo
- **`akkorder`** + **`@tonaljs/chord-detect`** for chord (pure JS, ~50 KB total)
- Looping `AudioBufferSourceNode` for the metronome

This keeps the bundle under 100 KB extra and still beats the current implementation by a large margin.

---

## Limitations

This research focused on browser-native solutions because the existing app is client-side. Server-side options (ffmpeg + librosa, aubio, BTrack) would give better accuracy still, but require uploading the audio for analysis — which is a poor UX for a tool that already plays the audio in the browser. Given we already download audio to the backend (the new library feature), this is worth reconsidering: a Python-side `librosa.beat.beat_track` and `librosa.feature.chroma_cqt` pipeline would give the most accurate results with zero JS bundle overhead.

The metronome silence diagnosis is informed (the autoplay policy + iframe combination is the most common cause), but cannot be confirmed without browser DevTools console logs from the user's session. If the actual cause is a different bug (e.g., the `MediaElementAudioSourceNode` from `AudioPlayer.vue` is muting the metronome's `AudioContext`), the fix may be different. Adding a `console.log(audioCtx.state)` in `ensureAudioCtx` would confirm.

---

## Recommendations

**Recommended path (best balance, ~1 hour of work):**

1. **Fix the metronome immediately** by switching to a looping `AudioBufferSourceNode`. This is a single-file change to `MetronomePage.vue` and removes the entire scheduler. It also adds a silent-unlock buffer on the first click for iframe/Safari safety.
2. **Replace BPM detection** with `realtime-bpm-analyzer`. Single npm install, ~30 lines of code change in `AudioPlayer.vue`. Works in both real-time (during playback) and offline (button click) modes.
3. **Replace chord detection** with `essentia.js`. Larger lift: add the WASM bundle, swap Meyda.js for the essentia HPCP + ChordsDetection pipeline. Bundle grows by ~7 MB but chord quality jumps from "demo-quality" to "production-quality."

**If bundle size is a concern**, swap step 3 for `akkorder` + `@tonaljs/chord-detect` (~50 KB instead of 7 MB).

**If accuracy matters most and we accept a backend dependency**, do steps 1 and 2 above, then add a **Python-side analysis endpoint** to the backend using `librosa` — `librosa.beat.beat_track` for BPM, `librosa.feature.chroma_cqt` + a chord recognizer for chords. The backend already has the MP3 files (the new library); it's a natural extension.

I recommend we **start with step 1 (metronome fix)** since it's the visible bug, then ask which BPM/chord path you prefer before doing more work.

---

## Sources

1. Wilson, Chris. "A Tale of Two Clocks: Scheduling Web Audio with Precision." web.dev. https://web.dev/audio-scheduling/ — Tier 1 (browser team author)
2. cwilso/metronome (reference implementation). https://github.com/cwilso/metronome — Tier 1
3. Chrome Developers. "Autoplay policy in Chrome." https://developer.chrome.com/blog/autoplay — Tier 1
4. Chrome Developers. "Web Audio, Autoplay Policy and Games." https://developer.chrome.com/blog/web-audio-autoplay — Tier 1
5. Adenot, Paul (Mozilla). "A robust metronome using the Web Audio API." https://blog.paul.cx/post/metronome/ — Tier 1 (Mozilla Web Audio engineer)
6. realtime-bpm-analyzer (npm). https://www.npmjs.com/package/realtime-bpm-analyzer (Published April 14, 2026; v5.0.7) — Tier 2
7. chrisguttandin/web-audio-beat-detector. https://github.com/chrisguttandin/web-audio-beat-detector — Tier 2
8. killercrush/music-tempo. https://github.com/killercrush/music-tempo — Tier 3
9. Correya, Bogdanov, Joglar-Ongay, Serra. "Essentia.js: A JavaScript Library for Music and Audio Analysis on the Web." ISMIR 2020. https://program.ismir2020.net/static/final_papers/260.pdf — Tier 1 (peer-reviewed)
10. Essentia.js home + docs. https://mtg.github.io/essentia.js/ — Tier 1 (academic — Music Technology Group, UPF Barcelona)
11. Stark, Adam. "Chord-Detector-and-Chromagram." https://github.com/adamstark/Chord-Detector-and-Chromagram — Tier 2 (used in Sonic Visualiser)
12. Tonaljs chord-detect. https://github.com/tonaljs/tonal/tree/main/packages/chord-detect — Tier 2
