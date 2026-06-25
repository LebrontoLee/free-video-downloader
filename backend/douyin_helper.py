"""
Douyin (抖音) download helper.
Uses system Chrome via Playwright to:
 1. Execute Douyin's JS challenge (_$jsvmprt) -> get valid page content
 2. Extract video metadata from rendered RENDER_DATA JSON (app.videoDetail)
 3. Provide cookies for yt-dlp as fallback

No user action needed — the system browser handles everything.
"""
import re
import json
import sys
import tempfile
from typing import Optional
from urllib.parse import unquote


def extract_aweme_id(url: str) -> Optional[str]:
    """Extract the aweme_id / video_id from a Douyin URL or share link."""
    patterns = [
        r"/video/(\d+)",
        r"modal_id=(\d+)",
        r"/note/(\d+)",
    ]
    for pat in patterns:
        m = re.search(pat, url)
        if m:
            return m.group(1)
    return None


def _get_page_with_playwright(video_url: str) -> Optional[tuple]:
    """
    Use Playwright + system Chrome to visit a Douyin page.
    Returns (page_html, cookies_netscape_string) or None.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[DOUYIN] playwright not installed", flush=True)
        return None

    try:
        with sync_playwright() as p:
            browser = None
            for channel in ("chrome", "msedge", "chromium"):
                try:
                    if channel == "chromium":
                        browser = p.chromium.launch(headless=True)
                    else:
                        browser = p.chromium.launch(channel=channel, headless=True)
                    print(f"[DOUYIN] Browser launched: {channel}", flush=True)
                    break
                except Exception as e:
                    print(f"[DOUYIN] Channel {channel} failed: {e}", flush=True)
                    continue

            if not browser:
                print("[DOUYIN] No browser available", flush=True)
                return None

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/131.0.0.0 Safari/537.36"
                ),
                locale="zh-CN",
            )
            page = context.new_page()

            print("[DOUYIN] Visiting homepage...", flush=True)
            page.goto("https://www.douyin.com/", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

            print("[DOUYIN] Visiting video page...", flush=True)
            try:
                page.goto(video_url, wait_until="networkidle", timeout=15000)
            except Exception:
                pass  # Douyin has continuous requests that prevent networkidle
            page.wait_for_timeout(3000)

            html = page.content()
            cookies = context.cookies()
            browser.close()
            print(f"[DOUYIN] Got HTML: {len(html)} chars, {len(cookies)} cookies", flush=True)

        # Convert cookies to Netscape format
        lines = ["# Netscape HTTP Cookie File", f"# Auto-generated for: {video_url}"]
        for c in cookies:
            domain = c.get("domain", "").lstrip(".")
            flag = "TRUE" if domain.startswith(".") else "FALSE"
            path = c.get("path", "/")
            secure = "TRUE" if c.get("secure") else "FALSE"
            expiry = str(int(c.get("expires", 0))) if c.get("expires") and c["expires"] > 0 else "0"
            lines.append(
                f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{c['name']}\t{c['value']}"
            )

        return (html, "\n".join(lines))

    except Exception as e:
        import traceback
        print(f"[DOUYIN] Error: {e}", flush=True)
        traceback.print_exc(file=sys.stderr)
        return None


def get_video_info_playwright(url: str) -> Optional[dict]:
    """
    Main entry point: extract Douyin video info using Playwright.
    """
    video_id = extract_aweme_id(url)
    if not video_id:
        return None

    if "v.douyin.com" in url:
        page_url = url
    else:
        page_url = f"https://www.douyin.com/video/{video_id}"

    result = _get_page_with_playwright(page_url)
    if not result:
        return None

    html, cookie_content = result

    info = _extract_video_from_html(html, video_id, url)
    if info:
        info["_cookies"] = cookie_content
        return info

    print("[DOUYIN] Failed to extract video from HTML", flush=True)
    return None


def _extract_video_from_html(html: str, video_id: str, original_url: str) -> Optional[dict]:
    """Extract video metadata from fully-rendered Douyin page HTML."""

    # Pattern 1: RENDER_DATA script tag
    m = re.search(r'<script[^>]*id="RENDER_DATA"[^>]*>([^<]+)</script>', html)
    if m:
        try:
            raw = unquote(m.group(1))
            data = json.loads(raw)
            return _parse_render_data(data, video_id, original_url)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[DOUYIN] RENDER_DATA parse failed: {e}", flush=True)

    # Fallback: try other patterns
    for pattern_name, pattern in [
        ("RENDER_DATA window", r'window\.__RENDER_DATA__\s*=\s*({.+?});\s*\n'),
        ("__NEXT_DATA__", r'<script[^>]*id="__NEXT_DATA__"[^>]*type="application/json"[^>]*>([^<]+)</script>'),
    ]:
        m = re.search(pattern, html, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                result = _parse_render_data(data, video_id, original_url)
                if result:
                    return result
            except (json.JSONDecodeError, KeyError):
                pass

    return None


def _parse_render_data(data: dict, video_id: str, original_url: str) -> Optional[dict]:
    """Walk the RENDER_DATA structure to find the video object."""
    # Primary path: RENDER_DATA.app.videoDetail (current Douyin PC web structure)
    if "app" in data and isinstance(data["app"], dict):
        app = data["app"]
        if "videoDetail" in app and isinstance(app["videoDetail"], dict):
            return _parse_video_detail(app["videoDetail"], video_id, original_url)

    # If data itself looks like an aweme object
    if isinstance(data, dict) and "video" in data and "desc" in data:
        return _parse_aweme(data, video_id, original_url)

    return None


def _parse_video_detail(vd: dict, video_id: str, original_url: str) -> Optional[dict]:
    """Parse app.videoDetail structure from RENDER_DATA."""
    video_info = vd.get("video", {})
    if not video_info:
        return None

    # Get video URLs — playAddr is a list of {"src": "..."} dicts
    def _extract_url(addr_list):
        if not addr_list:
            return None
        first = addr_list[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            return first.get("src") or first.get("url") or first.get("Url")
        return None

    video_url = (
        _extract_url(video_info.get("playAddr"))
        or _extract_url(video_info.get("playAddrH265"))
    )
    if not video_url:
        bitrate_list = video_info.get("bitRateList", [])
        if bitrate_list:
            video_url = _extract_url(bitrate_list[0].get("playAddr"))

    if not video_url:
        return None

    # Remove watermark
    video_url = video_url.replace("playwm", "play")

    # Thumbnail
    def _extract_cover(val):
        if not val:
            return ""
        if isinstance(val, str):
            return val
        if isinstance(val, list) and val:
            item = val[0]
            if isinstance(item, str):
                return item
            if isinstance(item, dict):
                return item.get("src") or item.get("url_list", [""])[0] or ""
        if isinstance(val, dict):
            return val.get("url_list", [""])[0] or ""
        return ""

    cover = (
        _extract_cover(video_info.get("dynamicCover"))
        or _extract_cover(video_info.get("originCover"))
        or _extract_cover(video_info.get("cover"))
    )

    aweme_id = vd.get("awemeId", video_id)
    title = vd.get("itemTitle", "") or vd.get("desc", "") or "Douyin Video"
    duration_ms = video_info.get("duration", 0)
    author_info = vd.get("authorInfo", {})
    author_name = author_info.get("nickname", "") or author_info.get("uniqueId", "")
    width = video_info.get("width", 0)
    height = video_info.get("height", 0)

    return {
        "id": aweme_id,
        "title": title,
        "thumbnail": cover,
        "duration": duration_ms // 1000 if duration_ms else 0,
        "duration_string": _format_duration(duration_ms // 1000 if duration_ms else 0),
        "uploader": author_name,
        "upload_date": str(vd.get("createTime", ""))[:8] if vd.get("createTime") else "",
        "extractor": "douyin",
        "webpage_url": original_url,
        "description": title,
        "formats": [
            {
                "format_id": "direct",
                "resolution": f"{width}x{height}" if width else "Adaptive",
                "height": height,
                "ext": "mp4",
                "filesize": None,
                "filesize_str": "Unknown",
                "vcodec": "h264",
                "acodec": "aac",
                "tbr": 0,
                "label": f"{height}p · mp4 (无水印)" if height else "高清 · mp4 (无水印)",
                "note": "direct",
            }
        ],
        "best_format_id": "direct",
        "_direct_url": video_url,
    }


def _parse_aweme(aweme: dict, video_id: str, original_url: str) -> Optional[dict]:
    """Parse a single aweme object (API response format)."""
    video_info = aweme.get("video", {})
    if not video_info:
        return None

    play_addr = (
        video_info.get("play_addr_h264")
        or video_info.get("play_addr_265")
        or video_info.get("play_addr")
        or {}
    )

    url_list = play_addr.get("url_list", [])
    if not url_list:
        download_addr = video_info.get("download_addr", {})
        url_list = download_addr.get("url_list", [])

    if not url_list:
        return None

    video_url = url_list[0].replace("playwm", "play")

    cover = (
        (video_info.get("dynamic_cover", {}).get("url_list", [None])[0])
        or (video_info.get("cover", {}).get("url_list", [None])[0])
        or ""
    )

    author = aweme.get("author", {})
    author_name = author.get("nickname", "")
    duration_ms = aweme.get("duration", 0)
    width = play_addr.get("width", 0)
    height = play_addr.get("height", 0)
    aweme_id = aweme.get("aweme_id", video_id)

    return {
        "id": aweme_id,
        "title": aweme.get("desc", "") or "Douyin Video",
        "thumbnail": cover,
        "duration": duration_ms // 1000 if duration_ms else 0,
        "duration_string": _format_duration(duration_ms // 1000 if duration_ms else 0),
        "uploader": author_name,
        "upload_date": str(aweme.get("create_time", ""))[:8] if aweme.get("create_time") else "",
        "extractor": "douyin",
        "webpage_url": original_url,
        "description": aweme.get("desc", "") or "",
        "formats": [
            {
                "format_id": "direct",
                "resolution": f"{width}x{height}" if width else "Adaptive",
                "height": height,
                "ext": "mp4",
                "filesize": None,
                "filesize_str": "Unknown",
                "vcodec": "h264",
                "acodec": "aac",
                "tbr": 0,
                "label": f"{height}p · mp4 (无水印)" if height else "高清 · mp4 (无水印)",
                "note": "direct",
            }
        ],
        "best_format_id": "direct",
        "_direct_url": video_url,
    }


def _build_minimal_result(video_id: str, url: str, video_url: str) -> dict:
    """Build a minimal result when only a video URL was found."""
    return {
        "id": video_id,
        "title": "Douyin Video",
        "thumbnail": "",
        "duration": 0,
        "duration_string": "Unknown",
        "uploader": "",
        "upload_date": "",
        "extractor": "douyin",
        "webpage_url": url,
        "description": "",
        "formats": [
            {
                "format_id": "direct",
                "resolution": "Adaptive",
                "height": 0,
                "ext": "mp4",
                "filesize": None,
                "filesize_str": "Unknown",
                "vcodec": "h264",
                "acodec": "aac",
                "tbr": 0,
                "label": "高清 · mp4 (无水印)",
                "note": "direct",
            }
        ],
        "best_format_id": "direct",
        "_direct_url": video_url,
    }


def get_douyin_cookiefile(video_url: str) -> Optional[str]:
    """Generate cookies for yt-dlp using Playwright."""
    result = _get_page_with_playwright(video_url)
    if not result:
        return None

    _, cookie_content = result
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    tmp.write(cookie_content)
    tmp.close()
    return tmp.name


def download_direct(url: str, output_path: str) -> bool:
    """Download a Douyin video directly."""
    import httpx

    info = get_video_info_playwright(url)
    if not info or not info.get("_direct_url"):
        return False

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.douyin.com/",
    }

    try:
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            with open(output_path, "wb") as f:
                with client.stream("GET", info["_direct_url"], headers=headers) as resp:
                    if resp.status_code not in (200, 206):
                        return False
                    for chunk in resp.iter_bytes(8192):
                        f.write(chunk)
        return True
    except Exception:
        return False


def _format_duration(seconds: int) -> str:
    if not seconds:
        return "Unknown"
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
