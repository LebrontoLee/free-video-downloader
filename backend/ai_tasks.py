"""
In-memory state management for AI tasks.
Caches transcripts, summaries, mind maps, and chat sessions.
Follows the same pattern as the existing `tasks` dict in server.py.
"""
import asyncio
import time
from datetime import datetime, timezone
from typing import Optional


# ─── Caches ────────────────────────────────────────────────────────────────────

# Keyed by URL (str)
transcript_cache: dict[str, dict] = {}
summary_cache: dict[str, str] = {}
mindmap_cache: dict[str, dict] = {}

# Keyed by session_id (str)
chat_sessions: dict[str, dict] = {}

# Per-URL locks to prevent concurrent subtitle extractions
_url_locks: dict[str, asyncio.Lock] = {}

# Timestamps for cache entries
_cache_timestamps: dict[str, float] = {}

# Max cache entries
MAX_CACHE_SIZE = 50
MAX_SESSION_AGE_HOURS = 2


# ─── Cache Helpers ─────────────────────────────────────────────────────────────

def cache_transcript(url: str, data: dict):
    """Store transcript data in cache."""
    transcript_cache[url] = data
    _touch(url)


def get_cached_transcript(url: str) -> Optional[dict]:
    """Get cached transcript if available."""
    return transcript_cache.get(url)


def cache_summary(url: str, text: str):
    """Store summary in cache."""
    summary_cache[url] = text
    _touch(url)


def get_cached_summary(url: str) -> Optional[str]:
    """Get cached summary if available."""
    return summary_cache.get(url)


def cache_mindmap(url: str, data: dict):
    """Store mind map in cache."""
    mindmap_cache[url] = data
    _touch(url)


def get_cached_mindmap(url: str) -> Optional[dict]:
    """Get cached mind map if available."""
    return mindmap_cache.get(url)


def clear_caches_for_url(url: str):
    """Remove all cached data for a URL."""
    transcript_cache.pop(url, None)
    summary_cache.pop(url, None)
    mindmap_cache.pop(url, None)
    _cache_timestamps.pop(url, None)


def _touch(url: str):
    """Update last-access timestamp and enforce cache size limit."""
    _cache_timestamps[url] = time.time()
    _evict_if_needed()


def _evict_if_needed():
    """Remove oldest entries if cache exceeds max size."""
    while len(_cache_timestamps) > MAX_CACHE_SIZE:
        oldest_url = min(_cache_timestamps, key=_cache_timestamps.get)
        clear_caches_for_url(oldest_url)


# ─── URL Lock Helpers ──────────────────────────────────────────────────────────

def get_url_lock(url: str) -> asyncio.Lock:
    """Get or create an asyncio.Lock for a URL to prevent concurrent operations."""
    if url not in _url_locks:
        _url_locks[url] = asyncio.Lock()
    return _url_locks[url]


# ─── Chat Session Helpers ──────────────────────────────────────────────────────

def create_chat_session(url: str) -> str:
    """Create a new chat session and return its ID."""
    import uuid
    _cleanup_old_sessions()

    session_id = uuid.uuid4().hex[:12]
    chat_sessions[session_id] = {
        "url": url,
        "history": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_activity": time.time(),
    }
    return session_id


def get_chat_session(session_id: str) -> Optional[dict]:
    """Get chat session data. Returns None if not found."""
    session = chat_sessions.get(session_id)
    if session:
        session["last_activity"] = time.time()
    return session


def append_to_history(session_id: str, role: str, content: str):
    """Append a message to a chat session's history."""
    session = chat_sessions.get(session_id)
    if session:
        session["history"].append({"role": role, "content": content})
        session["last_activity"] = time.time()


def get_chat_history(session_id: str) -> list[dict]:
    """Get the chat history for a session."""
    session = chat_sessions.get(session_id)
    if session:
        return session["history"]
    return []


def _cleanup_old_sessions():
    """Remove sessions older than MAX_SESSION_AGE_HOURS."""
    now = time.time()
    expired = [
        sid for sid, session in chat_sessions.items()
        if now - session.get("last_activity", 0) > MAX_SESSION_AGE_HOURS * 3600
    ]
    for sid in expired:
        del chat_sessions[sid]
