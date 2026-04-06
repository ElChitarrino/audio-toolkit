import asyncio
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="Audio Toolkit Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LIBRARY_DIR = Path("backend/library")
LIBRARY_INDEX = LIBRARY_DIR / "index.json"
LIBRARY_DIR.mkdir(parents=True, exist_ok=True)


def _load_index() -> dict:
    if LIBRARY_INDEX.exists():
        try:
            return json.loads(LIBRARY_INDEX.read_text())
        except Exception:
            return {}
    return {}


def _save_index(data: dict) -> None:
    LIBRARY_INDEX.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _valid_video_id(video_id: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9_-]{1,20}$", video_id))


# ── Search ────────────────────────────────────────────────────────────────────

def _search_sync(query: str):
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": "in_playlist",
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        results = ydl.extract_info(f"ytsearch10:{query}", download=False)

    videos = []
    for entry in (results.get("entries") or []):
        if not entry:
            continue
        vid_id = entry.get("id") or ""
        videos.append({
            "id": vid_id,
            "videoId": vid_id,
            "title": entry.get("title") or "Unknown",
            "thumbnail": (
                entry.get("thumbnail")
                or f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg"
            ),
        })
    return videos


@app.get("/audiorequester/search")
async def search(query: str):
    if not query or len(query.strip()) < 2:
        return []
    try:
        return await asyncio.to_thread(_search_sync, query.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Download & Library ────────────────────────────────────────────────────────

def _download_sync(video_id: str) -> Path:
    dest = LIBRARY_DIR / f"{video_id}.mp3"
    if dest.exists():
        return dest

    tmpdir = tempfile.mkdtemp(prefix="audiotk_")
    output_template = os.path.join(tmpdir, "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
    }

    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = (info or {}).get("title", "Unknown")
        thumbnail = (info or {}).get("thumbnail", f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg")

    tmp_mp3 = Path(tmpdir) / f"{video_id}.mp3"
    if not tmp_mp3.exists():
        # yt-dlp sometimes uses a different filename; find the mp3
        for f in Path(tmpdir).glob("*.mp3"):
            tmp_mp3 = f
            break
        else:
            raise RuntimeError("MP3 file not found after download")

    shutil.move(str(tmp_mp3), str(dest))

    # Persist metadata
    index = _load_index()
    index[video_id] = {
        "videoId": video_id,
        "title": title,
        "thumbnail": thumbnail,
        "downloadedAt": datetime.now(timezone.utc).isoformat(),
    }
    _save_index(index)

    return dest


@app.get("/audiorequester/download")
async def download(video_id: str):
    if not video_id or not _valid_video_id(video_id):
        raise HTTPException(status_code=400, detail="Invalid video_id")
    try:
        filepath = await asyncio.to_thread(_download_sync, video_id)
        filename = filepath.name
        return FileResponse(
            str(filepath),
            media_type="audio/mpeg",
            filename=filename,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/audiorequester/library")
async def get_library():
    index = _load_index()
    tracks = []
    for entry in index.values():
        vid_id = entry.get("videoId", "")
        mp3_path = LIBRARY_DIR / f"{vid_id}.mp3"
        if mp3_path.exists():
            entry["fileSize"] = mp3_path.stat().st_size
            tracks.append(entry)
    tracks.sort(key=lambda t: t.get("downloadedAt", ""), reverse=True)
    return tracks


@app.get("/audiorequester/audio/{video_id}")
async def serve_audio(video_id: str):
    if not _valid_video_id(video_id):
        raise HTTPException(status_code=400, detail="Invalid video_id")
    filepath = LIBRARY_DIR / f"{video_id}.mp3"
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Track not found in library")
    return FileResponse(
        str(filepath),
        media_type="audio/mpeg",
        headers={"Accept-Ranges": "bytes"},
    )


@app.delete("/audiorequester/library/{video_id}")
async def delete_track(video_id: str):
    if not _valid_video_id(video_id):
        raise HTTPException(status_code=400, detail="Invalid video_id")
    filepath = LIBRARY_DIR / f"{video_id}.mp3"
    if filepath.exists():
        filepath.unlink()
    index = _load_index()
    index.pop(video_id, None)
    _save_index(index)
    return {"deleted": video_id}


@app.get("/health")
async def health():
    return {"status": "ok"}
