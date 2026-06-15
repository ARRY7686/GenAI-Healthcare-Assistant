"""In-process session store.

Holds the canonical PatientCase + chat transcript per session. Survives a browser refresh,
lost on server restart. Mutating access goes through the `session(sid)` context manager,
which holds a per-session lock for the whole load -> mutate cycle so concurrent requests to
one session can't interleave.

A durable (SQLite) store is a follow-up; the in-memory store is enough for the MVP.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass, field

from ..domain import PatientCase

MAX_SESSIONS = 1000
SESSION_TTL_SECONDS = 2 * 60 * 60  # 2 hours


@dataclass
class Session:
    case: PatientCase
    transcript: list[dict] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)
    created_at: float = field(default_factory=time.monotonic)


class InMemorySessionStore:
    def __init__(self, max_sessions: int = MAX_SESSIONS, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        self._sessions: "OrderedDict[str, Session]" = OrderedDict()
        self._lock = threading.Lock()
        self._max = max_sessions
        self._ttl = ttl_seconds

    def _evict_locked(self) -> None:
        now = time.monotonic()
        for sid in [s for s, ss in self._sessions.items() if now - ss.created_at > self._ttl]:
            self._sessions.pop(sid, None)
        while len(self._sessions) > self._max:
            self._sessions.popitem(last=False)

    def create(self) -> Session:
        sid = uuid.uuid4().hex
        session = Session(case=PatientCase(session_id=sid))
        with self._lock:
            self._sessions[sid] = session
            self._evict_locked()
        return session

    def get(self, sid: str) -> Session | None:
        with self._lock:
            session = self._sessions.get(sid)
            if session is not None:
                self._sessions.move_to_end(sid)
            return session

    @contextmanager
    def session(self, sid: str):
        session = self.get(sid)
        if session is None:
            yield None
            return
        with session.lock:
            yield session  # live object — mutations are already persisted


def build_store(settings=None) -> InMemorySessionStore:
    return InMemorySessionStore()
