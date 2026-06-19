"""In-process session store.

Holds the canonical PatientCase + chat transcript per session. Survives a browser refresh,
lost on server restart. Mutating access goes through the `session(sid)` context manager,
which holds a per-session lock for the whole load -> mutate cycle so concurrent requests to
one session can't interleave.

A durable (SQLite) store is a follow-up; the in-memory store is enough for the MVP.
"""

from __future__ import annotations

import json
import os
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


class RedisSessionStore:
    """Durable session store backed by Upstash Redis (REST) — required on serverless (Vercel),
    where the in-memory store would lose sessions between function invocations. Reads the Upstash
    REST credentials that Vercel's marketplace integration injects.
    """

    def __init__(self, ttl_seconds: int = SESSION_TTL_SECONDS) -> None:
        url = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL")
        token = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN")
        if not url or not token:
            raise RuntimeError(
                "TRIAGE_SESSION_STORE=redis but no Upstash REST credentials found "
                "(expected KV_REST_API_URL/KV_REST_API_TOKEN or UPSTASH_REDIS_REST_URL/TOKEN)."
            )
        from upstash_redis import Redis

        self._redis = Redis(url=url, token=token)
        self._ttl = ttl_seconds

    @staticmethod
    def _key(sid: str) -> str:
        return f"triage:sess:{sid}"

    def _save(self, session: Session) -> None:
        payload = json.dumps(
            {"case": session.case.model_dump_json(), "transcript": session.transcript}
        )
        self._redis.set(self._key(session.case.session_id), payload, ex=self._ttl)

    def create(self) -> Session:
        session = Session(case=PatientCase(session_id=uuid.uuid4().hex))
        self._save(session)
        return session

    def get(self, sid: str) -> Session | None:
        raw = self._redis.get(self._key(sid))
        if not raw:
            return None
        data = json.loads(raw)
        return Session(
            case=PatientCase.model_validate_json(data["case"]),
            transcript=data["transcript"],
        )

    @contextmanager
    def session(self, sid: str):
        # Load -> mutate -> save. Redis is the source of truth across serverless invocations;
        # no distributed lock (per-session triage concurrency is effectively single-user).
        session = self.get(sid)
        if session is None:
            yield None
            return
        yield session
        self._save(session)


def build_store(settings=None):
    if settings is not None and getattr(settings, "session_store", "memory") == "redis":
        return RedisSessionStore()
    return InMemorySessionStore()
