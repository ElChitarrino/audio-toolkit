import asyncio
import os
import tempfile
import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI(title="Audio Toolkit Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        title = entry.get("title") or "Unknown"
        thumbnail = (
            entry.get("thumbnail")
            or f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg"
        )
        videos.append(
            {
                "id": vid_id,
                "videoId": vid_id,
                "title": title,
                "thumbnail": thumbnail,
            }
        )
    return videos


@app.get("/audiorequester/search")
async def search(query: str):
    if not query or len(query.strip()) < 2:
        return []
    try:
        results = await asyncio.to_thread(_search_sync, query.strip())
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _download_sync(video_id: str) -> str:
    tmpdir = tempfile.mkdtemp(prefix="audiotk_")
    output_template = os.path.join(tmpdir, "%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
    }

    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    for fname in os.listdir(tmpdir):
        if fname.endswith(".mp3"):
            return os.path.join(tmpdir, fname)

    raise RuntimeError("MP3 file not found after download")


@app.get("/audiorequester/download")
async def download(video_id: str):
    if not video_id:
        raise HTTPException(status_code=400, detail="video_id is required")
    try:
        filepath = await asyncio.to_thread(_download_sync, video_id)
        filename = os.path.basename(filepath)
        return FileResponse(
            filepath,
            media_type="audio/mpeg",
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Allow-Origin": "*",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}
