"""
PRO feature gating and usage tracking.

Free tier limits:
  - AI analysis: 3 per day total (across summary, mindmap, chat, subtitles)
  - 4K+ downloads: PRO only (height > 1080)
  - Everything else: unlimited

PRO tier:
  - All features, no limits
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException

from auth import get_current_user
from db import get_db

# ─── Constants ────────────────────────────────────────────────────────────────

FREE_AI_LIMIT_PER_DAY = 3  # Max AI analyses per day for free users
AI_ACTION_TYPES = ("ai_summary", "ai_mindmap", "ai_chat", "ai_subtitles")


# ─── Usage Checker ─────────────────────────────────────────────────────────────


def check_and_record_usage(
    user: Optional[dict], action_type: str, db, url: str = ""
) -> "tuple[bool, str]":
    """Check if the user can perform the action and record usage if allowed.

    Args:
        user: The authenticated user dict (or None for anonymous).
        action_type: One of 'ai_summary', 'ai_mindmap', 'ai_chat', 'ai_subtitles',
                     'download_4k', 'download_8k'.
        db: Database connection.
        url: Optional video URL for logging.

    Returns:
        (allowed, reason) — allowed is True if the user can proceed.
        reason is an empty string if allowed, or an explanation if denied.
    """
    # PRO users can do everything
    if user and user.get("is_pro"):
        return True, ""

    # ── Download quality checks ──────────────────────────────────────────
    if action_type in ("download_4k", "download_8k"):
        return False, "PRO subscription required for 4K/8K quality. Free users are limited to 1080p."

    # ── AI usage checks ──────────────────────────────────────────────────
    if action_type in AI_ACTION_TYPES:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        user_id = user["id"] if user else None

        cursor = db.execute(
            """SELECT COUNT(*) as cnt FROM usage_logs
               WHERE user_id = ? AND action_type LIKE 'ai_%' AND created_at >= ?""",
            (user_id, today),
        )
        row = cursor.fetchone()
        count = row["cnt"] if row else 0

        if count >= FREE_AI_LIMIT_PER_DAY:
            return (
                False,
                f"Free tier limit: {FREE_AI_LIMIT_PER_DAY} AI analyses per day. "
                "Upgrade to PRO for unlimited access.",
            )

        # Record this usage
        db.execute(
            """INSERT INTO usage_logs (user_id, action_type, url, created_at)
               VALUES (?, ?, ?, ?)""",
            (user_id, action_type, url, datetime.now(timezone.utc).isoformat()),
        )
        db.commit()

        return True, ""

    # Unknown action type — allow by default
    return True, ""


# ─── FastAPI Dependencies ──────────────────────────────────────────────────────


async def require_pro(user: Optional[dict] = Depends(get_current_user)) -> dict:
    """FastAPI dependency: require the user to be a PRO member.

    Raises HTTP 402 Payment Required if the user is not PRO.
    """
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in to access this feature.",
        )
    if not user.get("is_pro"):
        raise HTTPException(
            status_code=402,
            detail="PRO subscription required for this feature. Upgrade to unlock.",
        )
    return user


def is_pro_format(format_id: str) -> bool:
    """Check if a format_id requires PRO access (4K or 8K quality).

    Returns True if the format has height > 1080 or is explicitly 4K/8K.
    """
    if not format_id:
        return False

    fid_lower = format_id.lower()

    # Check for 4K/8K markers in the format string
    if "2160" in fid_lower or "4k" in fid_lower:
        return True
    if "4320" in fid_lower or "8k" in fid_lower:
        return True

    return False
