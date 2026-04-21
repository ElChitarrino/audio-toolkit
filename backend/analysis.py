"""
Audio analysis utilities — chord detection and lyrics extraction.

Chord detection uses librosa's constant-Q chromagram (CQT) on the harmonic
component (after HPSS), then matches against major/minor templates with a
Viterbi-style smoothing pass to avoid the typical "chord flicker" of naive
template matching.

Lyrics extraction uses yt-dlp to fetch YouTube auto-generated subtitles
(VTT) — fast, free, and accurate when present.
"""
from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import List, Optional

import librosa
import numpy as np
import yt_dlp

# ──────────────────────────────────────────────────────────────────────────────
# Chord detection
# ──────────────────────────────────────────────────────────────────────────────

PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# 12 major + 12 minor binary templates, normalized.
# Index 0..11 = major C, C#, D, ...   Index 12..23 = minor C, C#, D, ...
_MAJOR = np.array([1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0], dtype=np.float32)
_MINOR = np.array([1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0], dtype=np.float32)


def _build_templates() -> tuple[np.ndarray, list[str]]:
    templates = []
    names = []
    for root in range(12):
        templates.append(np.roll(_MAJOR, root))
        names.append(PITCH_NAMES[root])
    for root in range(12):
        templates.append(np.roll(_MINOR, root))
        names.append(f"{PITCH_NAMES[root]}m")
    T = np.stack(templates, axis=0).astype(np.float32)
    # Bass-weight the root note slightly — the root tends to be stronger in real audio
    for i, t in enumerate(T):
        root_idx = int(np.argmax(t))
        T[i, root_idx] *= 1.4
    # L2-normalize each template for cosine similarity
    T /= np.linalg.norm(T, axis=1, keepdims=True) + 1e-9
    return T, names


_TEMPLATES, _CHORD_NAMES = _build_templates()


def _viterbi_smooth(emit: np.ndarray, self_loop: float = 0.92) -> np.ndarray:
    """
    Hidden-Markov-Model-style smoothing.

    `emit[t, k]` is the per-frame likelihood that frame t is chord k. We find
    the most likely chord sequence with a cheap Viterbi pass that prefers
    staying on the same chord (high `self_loop` probability) over jumping.
    This is what kills the "chord flicker" the user is seeing.
    """
    n_frames, n_states = emit.shape
    # Use log-probabilities to avoid underflow
    log_emit = np.log(emit + 1e-9)
    log_self = np.log(self_loop)
    log_switch = np.log((1.0 - self_loop) / max(n_states - 1, 1))

    dp = np.full((n_frames, n_states), -np.inf, dtype=np.float32)
    back = np.zeros((n_frames, n_states), dtype=np.int32)
    dp[0] = log_emit[0]

    for t in range(1, n_frames):
        # Transition: stay on same state (log_self) or jump (log_switch)
        # For each target state j, prev_score = max_i (dp[t-1, i] + trans(i, j))
        # Since trans is uniform-jump, we can compute it cheaply:
        prev = dp[t - 1]
        best_jump_idx = int(np.argmax(prev))
        best_jump_val = prev[best_jump_idx] + log_switch
        # For each j, the option of staying is prev[j] + log_self
        stay_vals = prev + log_self
        # Choose, for each j, max(stay_vals[j], best_jump_val)
        choose_jump = best_jump_val > stay_vals
        dp[t] = np.where(choose_jump, best_jump_val, stay_vals) + log_emit[t]
        back[t] = np.where(choose_jump, best_jump_idx, np.arange(n_states))

    # Backtrace
    path = np.zeros(n_frames, dtype=np.int32)
    path[-1] = int(np.argmax(dp[-1]))
    for t in range(n_frames - 2, -1, -1):
        path[t] = back[t + 1, path[t + 1]]
    return path


def detect_chords(mp3_path: Path, *, min_chord_duration: float = 0.4) -> dict:
    """
    Detect chords in an audio file.

    Returns dict with:
      - "chords": [{chord, start, end, confidence}, ...]
      - "duration": total audio duration in seconds
      - "key": estimated key (e.g. "C" or "Am")
    """
    # Load mono at 22050 Hz — plenty for chroma analysis, much faster than 44100
    y, sr = librosa.load(str(mp3_path), sr=22050, mono=True)
    duration = len(y) / sr

    # Harmonic-percussive separation: drop the percussive part, it confuses chroma
    y_harm = librosa.effects.harmonic(y, margin=4.0)

    # Constant-Q chromagram — far more pitch-accurate than STFT chroma at low freqs
    hop = 2048
    chroma = librosa.feature.chroma_cqt(y=y_harm, sr=sr, hop_length=hop, bins_per_octave=36)

    # Pre-smooth the chromagram itself (median filter across time)
    from scipy.ndimage import median_filter
    chroma = median_filter(chroma, size=(1, 9))

    # Normalize each frame
    chroma_n = chroma / (np.linalg.norm(chroma, axis=0, keepdims=True) + 1e-9)
    # Per-frame likelihood = cosine similarity with each template, mapped to [0,1]
    sims = _TEMPLATES @ chroma_n          # (24, n_frames)
    sims = np.clip(sims.T, 0.0, 1.0)      # (n_frames, 24)

    # Soften into a probability distribution (softmax with low temperature)
    temp = 0.08
    exp_s = np.exp(sims / temp)
    emit = exp_s / exp_s.sum(axis=1, keepdims=True)

    # Viterbi smoothing — biggest single quality win
    path = _viterbi_smooth(emit, self_loop=0.94)

    # Convert frame indices to time
    times = librosa.frames_to_time(np.arange(len(path)), sr=sr, hop_length=hop)

    # Group consecutive same-chord frames into segments
    segments = []
    cur_idx = path[0]
    seg_start = float(times[0])
    for i in range(1, len(path)):
        if path[i] != cur_idx:
            seg_end = float(times[i])
            seg_conf = float(np.mean(sims[i - 1:i, cur_idx]))
            segments.append({
                "chord": _CHORD_NAMES[cur_idx],
                "start": round(seg_start, 2),
                "end":   round(seg_end, 2),
                "confidence": round(seg_conf * 100, 1),
            })
            cur_idx = path[i]
            seg_start = float(times[i])
    # Final segment
    segments.append({
        "chord": _CHORD_NAMES[cur_idx],
        "start": round(seg_start, 2),
        "end":   round(float(duration), 2),
        "confidence": round(float(np.mean(sims[-5:, cur_idx])) * 100, 1),
    })

    # Merge segments shorter than min_chord_duration into the longer neighbour
    segments = _merge_short(segments, min_dur=min_chord_duration)

    # Estimate the song's key from the global chroma profile (Krumhansl-Schmuckler)
    key = _estimate_key(chroma)

    return {
        "duration": round(float(duration), 2),
        "key": key,
        "chords": segments,
    }


def _merge_short(segments: list[dict], *, min_dur: float) -> list[dict]:
    if not segments:
        return segments
    out = [segments[0]]
    for seg in segments[1:]:
        if seg["end"] - seg["start"] < min_dur and out:
            # Absorb into previous segment
            out[-1]["end"] = seg["end"]
        elif out and seg["chord"] == out[-1]["chord"]:
            out[-1]["end"] = seg["end"]
        else:
            out.append(seg)
    # Re-merge consecutive duplicates after the absorptions
    merged = [out[0]]
    for seg in out[1:]:
        if seg["chord"] == merged[-1]["chord"]:
            merged[-1]["end"] = seg["end"]
        else:
            merged.append(seg)
    return merged


# Krumhansl key profiles (major and minor)
_KEY_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
_KEY_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def _estimate_key(chroma: np.ndarray) -> str:
    profile = chroma.mean(axis=1)
    profile = profile / (np.linalg.norm(profile) + 1e-9)
    best = ("C", -np.inf)
    for root in range(12):
        for mode, prof in [("maj", _KEY_MAJOR), ("min", _KEY_MINOR)]:
            shifted = np.roll(prof, root)
            shifted = shifted / (np.linalg.norm(shifted) + 1e-9)
            score = float(np.dot(profile, shifted))
            if score > best[1]:
                name = PITCH_NAMES[root] + ("m" if mode == "min" else "")
                best = (name, score)
    return best[0]


# ──────────────────────────────────────────────────────────────────────────────
# Lyrics extraction (YouTube subtitles)
# ──────────────────────────────────────────────────────────────────────────────

def fetch_youtube_lyrics(video_id: str) -> Optional[List[dict]]:
    """
    Fetch time-synced lyrics from YouTube subtitles.

    Tries human-uploaded English subs first (most accurate for music videos
    that actually have them), then falls back to YouTube's auto-generated
    captions (decent on cleanly-mixed vocals).

    Returns list of {text, start, end} dicts, or None if no captions exist.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"

    with tempfile.TemporaryDirectory() as tmp:
        outtmpl = str(Path(tmp) / "%(id)s")
        opts = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en", "en-US", "en-GB", "en.*"],
            "subtitlesformat": "vtt",
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=False)
                ydl.process_info(ydl.extract_info(url, download=False))
        except Exception:
            pass

        # Find any .vtt file written by yt-dlp
        vtt_files = sorted(Path(tmp).glob("*.vtt"))
        if not vtt_files:
            return None
        # Prefer non-auto if both exist (auto captions have ".en.vtt" usually)
        manual = [f for f in vtt_files if ".en." in f.name and "automatic" not in f.name]
        chosen = manual[0] if manual else vtt_files[0]
        return _parse_vtt(chosen.read_text(encoding="utf-8", errors="ignore"))


_TS_RE = re.compile(r"(\d+):(\d{2}):(\d{2})\.(\d{3})\s+-->\s+(\d+):(\d{2}):(\d{2})\.(\d{3})")


def _ts_to_sec(h: str, m: str, s: str, ms: str) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def _parse_vtt(text: str) -> List[dict]:
    """Parse a WebVTT file into [{text, start, end}, ...] de-duplicated cues."""
    lines = text.splitlines()
    cues: List[dict] = []
    i = 0
    while i < len(lines):
        m = _TS_RE.search(lines[i])
        if not m:
            i += 1
            continue
        start = _ts_to_sec(*m.group(1, 2, 3, 4))
        end = _ts_to_sec(*m.group(5, 6, 7, 8))
        i += 1
        # Collect text lines until blank or next timestamp
        text_lines: List[str] = []
        while i < len(lines) and lines[i].strip() and not _TS_RE.search(lines[i]):
            cleaned = re.sub(r"<[^>]+>", "", lines[i])      # strip <c> tags
            cleaned = re.sub(r"&nbsp;", " ", cleaned)
            cleaned = cleaned.strip()
            if cleaned:
                text_lines.append(cleaned)
            i += 1
        cue_text = " ".join(text_lines).strip()
        if cue_text:
            cues.append({"text": cue_text, "start": round(start, 2), "end": round(end, 2)})

    # YouTube auto-captions repeat each phrase across rolling cues — dedupe by
    # keeping only cues whose text differs from the previous one.
    deduped: List[dict] = []
    for cue in cues:
        if not deduped or cue["text"] != deduped[-1]["text"]:
            deduped.append(cue)
        else:
            # Same text — extend the end time
            deduped[-1]["end"] = cue["end"]
    return deduped
