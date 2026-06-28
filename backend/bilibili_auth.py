"""
Bilibili authentication helper.
Reads SESSDATA cookie from environment variable or .env file.

Setup:
    1. Open bilibili.com in your browser (make sure you're logged in)
    2. Press F12 → Application → Cookies → bilibili.com
    3. Find SESSDATA, copy its value
    4. Paste into backend/.env:
       BILIBILI_SESSDATA=your_copied_value
"""
import os
import json
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

COOKIE_FILE = Path(__file__).parent / ".bilibili_cookies.json"


def get_saved_cookie() -> str:
    """Get SESSDATA from env var first, then from cookie file."""
    # Priority: env var > cookie file
    sessdata = os.environ.get("BILIBILI_SESSDATA", "")
    if sessdata:
        return sessdata

    if COOKIE_FILE.exists():
        try:
            data = json.loads(COOKIE_FILE.read_text("utf-8"))
            return data.get("SESSDATA", "")
        except Exception:
            pass
    return ""


def save_cookie(sessdata: str):
    """Save SESSDATA to file."""
    COOKIE_FILE.write_text(json.dumps({"SESSDATA": sessdata}), "utf-8")


def check_login() -> bool:
    """Check if the saved cookie is valid."""
    sessdata = get_saved_cookie()
    if not sessdata:
        print("❌ 未配置 BILIBILI_SESSDATA")
        print("请在 backend/.env 中添加: BILIBILI_SESSDATA=你的SESSDATA值")
        return False

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"SESSDATA={sessdata}",
    }

    try:
        req = urllib.request.Request(
            "https://api.bilibili.com/x/web-interface/nav", headers=headers
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            is_login = data.get("data", {}).get("isLogin", False)
            if is_login:
                uname = data.get("data", {}).get("uname", "Unknown")
                print(f"✅ 已登录 Bilibili: {uname}")
                return True
            else:
                print("❌ Cookie 已过期，请更新 SESSDATA")
                return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False


if __name__ == "__main__":
    check_login()
