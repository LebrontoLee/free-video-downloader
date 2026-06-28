"""
Subtitle extraction via yt-dlp.
Downloads manual + auto-generated subtitles, parses VTT/SRT into JSON.
"""
import os
import re
import json
import tempfile
import shutil
import subprocess
from typing import Optional


class SubtitleNotFoundError(Exception):
    """Raised when no subtitles are available for a video."""
    pass


def extract_subtitles(url: str, lang: Optional[str] = None,
                      cookies_from_browser: Optional[str] = None) -> dict:
    """
    Extract subtitles for a video URL using yt-dlp.

    Tries in order:
    1. Manual subtitles (writesubtitles)
    2. Auto-generated subtitles (writeautomaticsub)
    3. Embedded subtitles via FFmpeg (if a video stream is downloaded)
    """
    import yt_dlp

    tmpdir = tempfile.mkdtemp(prefix="subs_")
    lang_list = _language_list(lang)

    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": lang_list,
            "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
            "ignoreerrors": True,
            "http_headers": _build_headers(url),
        }
        if cookies_from_browser:
            ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)
            ydl_opts["ignoreerrors"] = True

        video_id = None
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception:
                # Cookie loading may fail — retry without cookies
                if cookies_from_browser:
                    ydl_opts.pop("cookiesfrombrowser", None)
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                        info = ydl2.extract_info(url, download=False)
                    ydl = ydl2
                else:
                    raise

            video_id = info.get("id", "")
            if info.get("_type") == "playlist" and "entries" in info:
                entries = info["entries"]
                if entries:
                    info = entries[0]
                    video_id = info.get("id", video_id)
            try:
                ydl.download([url])
            except Exception:
                pass  # partial success is OK

        # Collect downloaded subtitle files
        subtitle_files = []
        for root, _dirs, files in os.walk(tmpdir):
            for f in files:
                if f.endswith(('.vtt', '.srt')):
                    subtitle_files.append(os.path.join(root, f))

        if subtitle_files:
            chosen = _pick_best_file(subtitle_files, lang)
            parsed = _parse_file(chosen)
            filename = os.path.basename(chosen)
            detected_lang = _lang_from_filename(filename)
            is_auto = 'auto' in filename.lower()
            full_text = " ".join(p["text"] for p in parsed)
            return _make_result(video_id, parsed, detected_lang, is_auto, full_text)

        # yt-dlp found no subtitles — try Bilibili CC API with saved cookie
        if "bilibili.com" in url or "b23.tv" in url:
            bili_result = _try_bilibili_with_cookie(url, lang)
            if bili_result and bili_result.get("available"):
                return bili_result

        # Try FFmpeg embedded subtitle extraction
        embedded = _extract_embedded_subtitles(url, tmpdir, video_id, lang)
        if embedded:
            return embedded

        return _empty_result(video_id)

    except Exception as e:
        raise SubtitleNotFoundError(f"Failed to extract subtitles: {str(e)}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def get_video_metadata_context(url: str) -> dict:
    """Fallback: extract video metadata as AI context."""
    import yt_dlp

    ydl_opts = {
        "quiet": True, "no_warnings": True, "noplaylist": True,
        "skip_download": True, "http_headers": _build_headers(url),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info.get("_type") == "playlist" and "entries" in info:
                entries = info["entries"]
                if entries:
                    info = entries[0]

            title = info.get("title", "")
            desc = (info.get("description") or "")[:2000]
            uploader = info.get("uploader") or info.get("channel") or ""
            duration = info.get("duration", 0)
            tags = info.get("tags") or []
            cats = info.get("categories") or []

            parts = [f"Title: {title}"]
            if uploader:
                parts.append(f"Creator: {uploader}")
            if duration:
                m, s = divmod(duration, 60)
                h, m = divmod(m, 60)
                parts.append(f"Duration: {h}h{m}m{s}s" if h else f"Duration: {m}m{s}s")
            if tags:
                parts.append(f"Tags: {', '.join(tags[:10])}")
            if desc:
                parts.append(f"\nDescription:\n{desc}")

            return _make_result(info.get("id", ""), [], "metadata", False,
                                "\n".join(parts), source="metadata",
                                title=title, uploader=uploader, duration=duration)

    except Exception:
        return _empty_result("")


# ─── VTT / SRT Parsers ──────────────────────────────────────────────────────

def parse_vtt(content: str) -> list[dict]:
    """Parse WebVTT content into [{text, start, end}, ...]."""
    if os.path.exists(content):
        with open(content, 'r', encoding='utf-8') as f:
            content = f.read()

    lines = content.strip().split('\n')
    result = []
    cue = None
    i = 1 if lines and lines[0].strip().startswith('WEBVTT') else 0

    for line in lines[i:]:
        line = line.strip()
        if not line:
            if cue and cue.get("text"):
                text = _clean_text(cue["text"].strip())
                if text:
                    cue["text"] = text
                    result.append(cue)
            cue = None
            continue

        m = re.match(r'(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})', line)
        if m:
            cue = {"start": _ts(m.group(1)), "end": _ts(m.group(2)), "text": ""}
            continue
        if cue is None:
            continue
        cue["text"] = (cue["text"] + " " + line) if cue["text"] else line

    if cue and cue.get("text"):
        text = _clean_text(cue["text"].strip())
        if text:
            cue["text"] = text
            result.append(cue)
    return result


def parse_srt(content: str) -> list[dict]:
    """Parse SRT content into [{text, start, end}, ...]."""
    if os.path.exists(content):
        with open(content, 'r', encoding='utf-8') as f:
            content = f.read()

    content = content.replace('\r\n', '\n').replace('\r', '\n')
    result = []

    for block in content.strip().split('\n\n'):
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue
        ts_idx = next((i for i, l in enumerate(lines) if '-->' in l), -1)
        if ts_idx < 0:
            continue
        m = re.match(r'(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})',
                     lines[ts_idx])
        if not m:
            continue
        text = " ".join(lines[ts_idx + 1:]).strip()
        text = _clean_text(text)
        if text:
            result.append({"text": text, "start": _ts(m.group(1)), "end": _ts(m.group(2))})
    return result


# ─── Embedded Subtitle Extraction via FFmpeg ─────────────────────────────────

def _try_bilibili_with_cookie(url: str, lang: Optional[str]) -> Optional[dict]:
    """Try Bilibili CC subtitle API with saved login cookie."""
    from bilibili_auth import get_saved_cookie
    import urllib.request

    sessdata = get_saved_cookie()
    if not sessdata:
        return None

    bvid = None
    for pat in [r"/video/(BV[a-zA-Z0-9]+)", r"bvid=(BV[a-zA-Z0-9]+)"]:
        m = re.search(pat, url)
        if m:
            bvid = m.group(1)
            break
    if not bvid:
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com/",
        "Cookie": f"SESSDATA={sessdata}",
    }

    try:
        # Get cid
        api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") != 0:
                return None
            cid = data["data"]["cid"]

        # Get subtitles via player API (with cookie)
        params = f"bvid={bvid}&cid={cid}"
        player_url = f"https://api.bilibili.com/x/player/wbi/v2?{params}"
        req2 = urllib.request.Request(player_url, headers=headers)
        with urllib.request.urlopen(req2, timeout=15) as resp2:
            pdata = json.loads(resp2.read().decode("utf-8"))

        subs_list = pdata.get("data", {}).get("subtitle", {}).get("subtitles", [])
        if not subs_list:
            return None

        # Pick language
        priorities = [lang] if lang else ["zh-Hans", "zh-CN", "zh", "en"]
        chosen = None
        for lang_code in priorities:
            if not lang_code:
                continue
            for s in subs_list:
                if lang_code.lower() in s.get("lan", "").lower():
                    chosen = s
                    break
            if chosen:
                break
        if not chosen:
            chosen = subs_list[0]

        sub_url = chosen.get("subtitle_url", "")
        if not sub_url:
            return None
        if sub_url.startswith("//"):
            sub_url = "https:" + sub_url

        # Download subtitle JSON
        req3 = urllib.request.Request(sub_url, headers={"User-Agent": headers["User-Agent"], "Referer": headers["Referer"]})
        with urllib.request.urlopen(req3, timeout=15) as resp3:
            sub_data = json.loads(resp3.read().decode("utf-8"))

        body = sub_data.get("body", [])
        subtitles = []
        for item in body:
            subtitles.append({
                "text": item.get("content", ""),
                "start": item.get("from", 0.0),
                "end": item.get("to", 0.0),
            })

        full_text = " ".join(s["text"] for s in subtitles)
        detected_lang = chosen.get("lan_doc", chosen.get("lan", "unknown"))

        return _make_result(bvid, subtitles, detected_lang, False, full_text,
                            source="bilibili_cc")

    except Exception:
        return None


def _extract_embedded_subtitles(url: str, tmpdir: str, video_id: str,
                                lang: Optional[str]) -> Optional[dict]:
    """Download a small video clip and check for embedded subtitle streams."""
    import yt_dlp

    try:
        # Download smallest audio stream instead of video (faster, fewer blocks)
        ydl_opts = {
            "quiet": True, "no_warnings": True, "noplaylist": True,
            "format": "worstaudio/worst",
            "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
            "http_headers": _build_headers(url),
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info.get("_type") == "playlist" and "entries" in info:
                info = info["entries"][0]
            filename = ydl.prepare_filename(info)

        # Find the actual downloaded file
        video_file = None
        for ext in ('.mp4', '.mkv', '.webm', '.flv', '.m3u8', '.mp3', '.m4a'):
            candidate = os.path.splitext(filename)[0] + ext
            if os.path.exists(candidate):
                video_file = candidate
                break
        if not video_file:
            for f in os.listdir(tmpdir):
                fp = os.path.join(tmpdir, f)
                if os.path.isfile(fp) and os.path.getsize(fp) > 1000:
                    video_file = fp
                    break
        if not video_file:
            return None

        # Check for subtitle streams with FFmpeg
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", "-select_streams", "s", video_file],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return None

        streams = json.loads(result.stdout).get("streams", [])
        if not streams:
            return None

        # Extract first subtitle track
        sub_ext = ".srt"
        sub_file = os.path.join(tmpdir, f"embedded{sub_ext}")
        sub_result = subprocess.run(
            ["ffmpeg", "-y", "-i", video_file, "-map", "0:s:0",
             "-c:s", "srt", sub_file],
            capture_output=True, text=True, timeout=60
        )

        if os.path.exists(sub_file) and os.path.getsize(sub_file) > 50:
            parsed = parse_srt(sub_file)
            if parsed:
                full_text = " ".join(p["text"] for p in parsed)
                return _make_result(video_id, parsed, "unknown", False, full_text,
                                    source="embedded")

        return None
    except Exception:
        return None


# ─── Internal Helpers ──────────────────────────────────────────────────────────

def _build_headers(url: str) -> dict:
    """Build HTTP headers for yt-dlp based on URL domain."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if "bilibili.com" in url or "b23.tv" in url:
        headers["Referer"] = "https://www.bilibili.com/"
        headers["Origin"] = "https://www.bilibili.com"
    elif "youtube.com" in url or "youtu.be" in url:
        headers["Referer"] = "https://www.youtube.com/"
    return headers


def _language_list(preferred: Optional[str]) -> list:
    if preferred:
        return [preferred]
    return ["en", "zh-Hans", "zh-Hant", "zh"]


def _pick_best_file(files: list[str], preferred_lang: Optional[str]) -> str:
    priorities = [preferred_lang] if preferred_lang else ["zh-Hans", "zh", "en"]
    for lang in priorities:
        if lang:
            for f in files:
                if lang.lower().replace('-', '') in os.path.basename(f).lower().replace('-', ''):
                    return f
    return files[0]


def _parse_file(path: str) -> list[dict]:
    return parse_vtt(path) if path.endswith('.vtt') else parse_srt(path)


def _lang_from_filename(filename: str) -> str:
    f = filename.lower()
    for code in ['zh-hans', 'zh-hant', 'zh', 'ja', 'ko', 'en']:
        if code in f:
            return code
    return "unknown"


def _ts(ts: str) -> float:
    ts = ts.replace(',', '.')
    h, m, s = ts.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


def _clean_text(text: str) -> str:
    text = re.sub(r'<\d{2}:\d{2}:\d{2}[.,]\d{3}>', '', text)
    text = re.sub(r'</?[a-zA-Z][^>]*>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _make_result(video_id: str, subtitles: list, language: str,
                 is_auto: bool, full_text: str, **extra) -> dict:
    return {
        "video_id": video_id,
        "subtitles": subtitles,
        "language": language,
        "is_auto_generated": is_auto,
        "full_text": full_text,
        "subtitle_count": len(subtitles),
        "available": bool(full_text.strip()),
        **extra,
    }


def _empty_result(video_id: str = "") -> dict:
    return _make_result(video_id, [], None, False, "", available=False)
