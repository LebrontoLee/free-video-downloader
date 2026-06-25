"""
Free Video Downloader - Backend Server
FastAPI + yt-dlp integration
"""
import os
import re
import uuid
import json
import queue
import threading
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yt_dlp
import yt_dlp.utils

# Douyin helper — auto session cookies
from douyin_helper import get_douyin_cookiefile, extract_aweme_id, get_video_info_playwright, download_direct

# ─── App Setup ───────────────────────────────────────────────────────────────
app = FastAPI(title="Free Video Downloader", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOADS_DIR = Path(__file__).parent.parent / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

# ─── In-Memory Task Store ────────────────────────────────────────────────────
tasks: dict[str, "DownloadTask"] = {}


class DownloadTask:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.queue: queue.Queue = queue.Queue()
        self.thread: Optional[threading.Thread] = None
        self.status = "pending"
        self.filename: Optional[str] = None
        self.error: Optional[str] = None


# ─── Request Models ──────────────────────────────────────────────────────────
class ExtractRequest(BaseModel):
    url: str
    cookies_from_browser: Optional[str] = None  # e.g., "chrome", "edge", "firefox"


class DownloadRequest(BaseModel):
    url: str
    format_id: str = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
    cookies_from_browser: Optional[str] = None


# ─── Helper Functions ────────────────────────────────────────────────────────

def build_http_headers(url: str) -> dict:
    """Build HTTP headers based on the target URL domain to avoid 412/403 errors."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    # Set Referer based on domain to avoid 412 Precondition Failed
    if "bilibili.com" in url or "b23.tv" in url:
        headers["Referer"] = "https://www.bilibili.com/"
        headers["Origin"] = "https://www.bilibili.com"
    elif "youtube.com" in url or "youtu.be" in url:
        headers["Referer"] = "https://www.youtube.com/"
    elif "twitter.com" in url or "x.com" in url:
        headers["Referer"] = "https://twitter.com/"
    elif "douyin.com" in url:
        headers["Referer"] = "https://www.douyin.com/"
        headers["Origin"] = "https://www.douyin.com"

    return headers


def build_ydl_opts(extra_opts: dict, cookies_from_browser: Optional[str] = None, url: str = "") -> dict:
    """Build yt-dlp options dict with optional browser cookies + Douyin auto-cookie."""
    opts = dict(extra_opts)

    # Douyin: auto-generate cookies via system Chrome + Playwright
    if "douyin.com" in url:
        cookiefile = get_douyin_cookiefile(url)
        if cookiefile:
            opts["cookiefile"] = cookiefile

    # Browser cookies for other sites that require authentication
    if cookies_from_browser:
        opts["cookiesfrombrowser"] = (cookies_from_browser,)

    return opts


def format_filesize(size_bytes: Optional[int]) -> str:
    """Convert bytes to human-readable string."""
    if size_bytes is None:
        return "Unknown"
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def simplify_formats(raw_formats: list, video_id: str) -> list[dict]:
    """
    Simplify yt-dlp raw formats list into user-friendly options.
    Groups video+audio pairs by resolution, deduplicates.
    """
    if not raw_formats:
        return []

    # Separate video-only, audio-only, and combined formats
    video_formats = []
    audio_formats = []
    combined_formats = []

    for f in raw_formats:
        vcodec = f.get("vcodec", "none")
        acodec = f.get("acodec", "none")
        if vcodec != "none" and acodec == "none":
            video_formats.append(f)
        elif vcodec == "none" and acodec != "none":
            audio_formats.append(f)
        elif vcodec != "none" and acodec != "none":
            combined_formats.append(f)

    # Find best audio
    best_audio = max(audio_formats, key=lambda f: f.get("tbr", 0) or 0, default=None)

    # Group video formats by height
    seen_heights = set()
    simplified = []

    # Process combined formats first (they don't need audio merge)
    for f in combined_formats:
        height = f.get("height") or 0
        ext = f.get("ext", "mp4")
        key = (height, ext)
        if key in seen_heights:
            continue
        seen_heights.add(key)
        filesize = f.get("filesize") or f.get("filesize_approx")
        simplified.append({
            "format_id": f["format_id"],
            "resolution": f"{f.get('width', '?')}x{height}" if height else "Audio",
            "height": height,
            "ext": ext,
            "filesize": filesize if filesize else None,
            "filesize_str": format_filesize(filesize),
            "vcodec": f.get("vcodec", ""),
            "acodec": f.get("acodec", ""),
            "tbr": f.get("tbr", 0),
            "label": build_format_label(height, ext, filesize),
            "note": "combined" if height else "audio",
        })

    # Process video formats, pairing with best audio
    for f in sorted(video_formats, key=lambda x: x.get("height") or 0, reverse=True):
        height = f.get("height") or 0
        ext = f.get("ext", "mp4")
        key = (height, ext)
        if key in seen_heights:
            continue
        seen_heights.add(key)

        video_size = f.get("filesize") or f.get("filesize_approx") or 0
        audio_size = best_audio.get("filesize") or best_audio.get("filesize_approx") or 0 if best_audio else 0
        total_size = (video_size + audio_size) if (video_size and audio_size) else (video_size or None)

        format_id = f["format_id"]
        if best_audio:
            format_id = f"{f['format_id']}+{best_audio['format_id']}"

        simplified.append({
            "format_id": format_id,
            "resolution": f"{f.get('width', '?')}x{height}",
            "height": height,
            "ext": ext,
            "filesize": total_size,
            "filesize_str": format_filesize(total_size),
            "vcodec": f.get("vcodec", ""),
            "acodec": best_audio.get("acodec", "") if best_audio else "",
            "tbr": f.get("tbr", 0),
            "label": build_format_label(height, ext, total_size),
            "note": "merge",
        })

    # Add audio-only option
    if best_audio:
        audio_size = best_audio.get("filesize") or best_audio.get("filesize_approx")
        simplified.append({
            "format_id": "bestaudio/best",
            "resolution": "Audio",
            "height": 0,
            "ext": best_audio.get("ext", "m4a"),
            "filesize": audio_size if audio_size else None,
            "filesize_str": format_filesize(audio_size),
            "vcodec": "none",
            "acodec": best_audio.get("acodec", ""),
            "tbr": best_audio.get("tbr", 0),
            "label": f"Audio Only · {best_audio.get('ext', 'm4a')} · {format_filesize(audio_size)}",
            "note": "audio",
        })

    # Sort by quality descending, audio last
    simplified.sort(key=lambda x: (x["height"] if x["height"] > 0 else -1), reverse=True)

    return simplified


def build_format_label(height: int, ext: str, filesize: Optional[int]) -> str:
    """Build a human-readable format label."""
    parts = []
    if height:
        parts.append(f"{height}p")
    else:
        parts.append("Audio")
    parts.append(f"· {ext}")
    if filesize:
        parts.append(f"· {format_filesize(filesize)}")
    else:
        parts.append("· size unknown")
    return " ".join(parts)


def make_progress_hook(task_queue: queue.Queue):
    """Factory: creates a progress hook that pushes updates to the task's queue."""
    def hook(d):
        status = d.get("status")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            percent = (downloaded / total * 100) if total > 0 else 0
            task_queue.put({
                "event": "progress",
                "status": "downloading",
                "percent": round(percent, 1),
                "downloaded_bytes": downloaded,
                "total_bytes": total,
                "downloaded_str": format_filesize(downloaded),
                "total_str": format_filesize(total) if total else "Unknown",
                "speed_str": d.get("_speed_str", ""),
                "eta": d.get("eta", 0),
            })
        elif status == "finished":
            filename = os.path.basename(d.get("filename", ""))
            task_queue.put({
                "event": "processing",
                "status": "processing",
                "message": "Post-processing: merging streams...",
            })
    return hook


def make_postprocessor_hook(task_queue: queue.Queue):
    """Factory: creates a post-processor hook for merge/completion events."""
    def hook(d):
        if d.get("status") == "started":
            pp_name = d.get("postprocessor", "")
            task_queue.put({
                "event": "processing",
                "status": "processing",
                "message": f"Post-processing: {pp_name}",
            })
    return hook


def run_download(task: DownloadTask, url: str, format_id: str, cookies_from_browser: Optional[str] = None):
    """Run download in a background thread. Uses direct HTTP for Douyin, yt-dlp for others."""
    try:
        # Douyin: use direct HTTP download (yt-dlp can't handle JS challenge)
        if "douyin.com" in url:
            from douyin_helper import get_video_info_playwright, download_direct

            task.queue.put({
                "event": "progress",
                "status": "downloading",
                "percent": 0,
                "downloaded_str": "Fetching...",
                "total_str": "Unknown",
                "speed_str": "",
                "eta": 0,
            })

            # Get direct video URL via Playwright
            info = get_video_info_playwright(url)
            if not info or not info.get("_direct_url"):
                raise Exception("Failed to extract Douyin video URL")

            direct_url = info["_direct_url"]
            safe_title = re.sub(r'[\\/*?:"<>|]', '', info.get("title", "video"))
            output_path = DOWNLOADS_DIR / f"{safe_title[:100]}.mp4"

            task.queue.put({
                "event": "progress",
                "status": "downloading",
                "percent": 10,
                "downloaded_str": "Downloading...",
                "total_str": "Unknown",
                "speed_str": "",
                "eta": 0,
            })

            # Download directly
            import httpx
            headers = build_http_headers(url)
            with httpx.Client(timeout=120.0, follow_redirects=True) as client:
                with open(output_path, "wb") as f:
                    with client.stream("GET", direct_url, headers=headers) as resp:
                        total = int(resp.headers.get("content-length", 0))
                        downloaded = 0
                        for chunk in resp.iter_bytes(8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total > 0:
                                pct = min(99, 10 + int(downloaded / total * 89))
                                task.queue.put({
                                    "event": "progress",
                                    "status": "downloading",
                                    "percent": pct,
                                    "downloaded_bytes": downloaded,
                                    "total_bytes": total,
                                    "downloaded_str": format_filesize(downloaded),
                                    "total_str": format_filesize(total),
                                    "speed_str": "",
                                    "eta": 0,
                                })

            task.filename = output_path.name
            task.queue.put({
                "event": "complete",
                "status": "finished",
                "filename": output_path.name,
            })
            return

        # YouTube, Bilibili, etc.: use yt-dlp
        progress_hook = make_progress_hook(task.queue)
        pp_hook = make_postprocessor_hook(task.queue)

        ydl_opts = build_ydl_opts({
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "format": format_id,
            "outtmpl": str(DOWNLOADS_DIR / "%(title).100s.%(ext)s"),
            "merge_output_format": "mp4",
            "progress_hooks": [progress_hook],
            "postprocessor_hooks": [pp_hook],
            "ignoreerrors": False,
            "http_headers": build_http_headers(url),
        }, cookies_from_browser=cookies_from_browser, url=url)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                final_filename = os.path.basename(filename)
            else:
                base = os.path.splitext(filename)[0]
                for ext in (".mp4", ".mkv", ".webm", ".m4a"):
                    candidate = base + ext
                    if os.path.exists(candidate):
                        final_filename = os.path.basename(candidate)
                        break
                else:
                    final_filename = os.path.basename(filename)

            task.filename = final_filename
            task_queue = task.queue
            task_queue.put({
                "event": "complete",
                "status": "finished",
                "filename": final_filename,
            })

    except Exception as e:
        task.error = str(e)
        task.queue.put({
            "event": "error",
            "status": "error",
            "message": str(e),
        })


# ─── API Endpoints ───────────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/extract")
async def extract_video_info(req: ExtractRequest):
    """
    Extract video metadata without downloading.
    Returns title, thumbnail, duration, and available formats.
    """
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")

    # Douyin: use Playwright direct extraction (bypasses yt-dlp JS challenge)
    # Must run in a thread — Playwright sync API cannot run inside asyncio loop
    if "douyin.com" in req.url:
        import asyncio as _asyncio
        info = await _asyncio.to_thread(get_video_info_playwright, req.url)
        if info:
            return {"success": True, "data": info}

    try:
        ydl_opts = build_ydl_opts({
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "extract_flat": False,
            "http_headers": build_http_headers(req.url),
        }, cookies_from_browser=req.cookies_from_browser, url=req.url)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(req.url, download=False)

            # Handle playlists: take first entry
            if info.get("_type") == "playlist" and "entries" in info:
                entries = info["entries"]
                if not entries:
                    raise HTTPException(status_code=400, detail="Playlist is empty")
                info = entries[0]

            raw_formats = info.get("formats", [])
            video_id = info.get("id", "")

            return {
                "success": True,
                "data": {
                    "id": video_id,
                    "title": info.get("title", "Unknown"),
                    "description": (info.get("description", "") or "")[:500],
                    "thumbnail": info.get("thumbnail", ""),
                    "duration": info.get("duration", 0),
                    "duration_string": format_duration(info.get("duration", 0)),
                    "uploader": info.get("uploader", info.get("channel", "")),
                    "upload_date": info.get("upload_date", ""),
                    "extractor": info.get("extractor", ""),
                    "webpage_url": info.get("webpage_url", req.url),
                    "formats": simplify_formats(raw_formats, video_id),
                    "best_format_id": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                },
            }

    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(status_code=400, detail=f"Download error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract video info: {str(e)}")


@app.post("/api/download")
async def start_download(req: DownloadRequest):
    """Start a download task and return a task_id for progress tracking."""
    if not req.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")

    task_id = uuid.uuid4().hex[:12]
    task = DownloadTask(task_id)
    task.status = "running"

    task.thread = threading.Thread(
        target=run_download,
        args=(task, req.url, req.format_id, req.cookies_from_browser),
        daemon=True,
    )
    task.thread.start()

    tasks[task_id] = task

    return {
        "success": True,
        "task_id": task_id,
        "message": "Download started",
    }


@app.get("/api/thumbnail")
async def proxy_thumbnail(url: str):
    """Proxy thumbnail images to bypass hotlink protection (Referer check)."""
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    try:
        import httpx

        headers = build_http_headers(url)

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Upstream returned {resp.status_code}")

            content_type = resp.headers.get("content-type", "image/jpeg")
            return StreamingResponse(
                resp.aiter_bytes(),
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=3600"},
            )
    except ImportError:
        raise HTTPException(status_code=500, detail="httpx not installed. Run: pip install httpx")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch thumbnail: {str(e)}")


@app.get("/api/download/{task_id}/progress")
async def stream_progress(task_id: str, request: Request):
    """SSE endpoint that streams download progress events."""
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        """Yield SSE-formatted progress events."""
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            try:
                # Non-blocking poll with timeout
                data = await asyncio.to_thread(task.queue.get, timeout=1)
            except queue.Empty:
                # Send heartbeat to keep connection alive
                yield f": heartbeat\n\n"
                continue

            event_type = data.get("event", "message")
            yield f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

            if data.get("status") in ("finished", "error"):
                # Clean up task after a short delay
                task.status = "finished" if data.get("status") == "finished" else "error"
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/files")
async def list_files():
    """List all downloaded files."""
    files = []
    if DOWNLOADS_DIR.exists():
        for entry in sorted(
            DOWNLOADS_DIR.iterdir(),
            key=lambda e: e.stat().st_mtime,
            reverse=True,
        ):
            if entry.is_file():
                stat = entry.stat()
                files.append({
                    "filename": entry.name,
                    "size": stat.st_size,
                    "size_str": format_filesize(stat.st_size),
                    "downloaded_at": datetime.fromtimestamp(
                        stat.st_mtime, tz=timezone.utc
                    ).isoformat(),
                })
    return {"success": True, "files": files}


@app.get("/api/downloads/{filename:path}")
async def download_file(filename: str):
    """Serve a downloaded file for re-download."""
    # Sanitize filename to prevent path traversal
    safe_path = DOWNLOADS_DIR / os.path.basename(filename)
    if not safe_path.exists() or not safe_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        str(safe_path),
        media_type="application/octet-stream",
        filename=filename,
    )


# ─── Helpers ─────────────────────────────────────────────────────────────────

def format_duration(seconds: int) -> str:
    """Convert seconds to HH:MM:SS or MM:SS format."""
    if not seconds:
        return "Unknown"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


# ─── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    print("=" * 56)
    print("  Free Video Downloader - Backend Server")
    print("=" * 56)
    print(f"  Downloads directory: {DOWNLOADS_DIR}")
    print(f"  API docs: http://localhost:8000/docs")
    print(f"  Frontend: http://localhost:5173")
    print("=" * 56)

    uvicorn.run(app, host="0.0.0.0", port=8000)
