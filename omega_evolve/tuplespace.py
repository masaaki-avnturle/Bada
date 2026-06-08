"""TupleSpace -- write-once, content-addressed memory.

Faithful to the report's constraint that the dictionary cannot be rewritten and
no datum is ever overwritten, so "前後の記憶が無駄なコードが作用されない"
(prior memory is never clobbered). Every datum is keyed by the sha256 of its
canonical content; writing the same content twice is a no-op. Lineage (which
parents and which variation operator produced a datum) is recorded so the whole
evolutionary history is reconstructable.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, Iterable, List, Optional


def _canonical(content: Any) -> str:
    return json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def content_hash(content: Any) -> str:
    return hashlib.sha256(_canonical(content).encode("utf-8")).hexdigest()[:16]


class TupleSpace:
    """Append-only, content-addressed store.

    A `put` returns the key (content hash). Re-putting identical content does
    not create a new record (memory is not overwritten) -- it just returns the
    existing key. Tags and lineage are attached to the *first* write.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}
        self._order: List[str] = []

    def put(
        self,
        content: Any,
        *,
        tags: Optional[Iterable[str]] = None,
        parents: Optional[Iterable[str]] = None,
        op: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        key = content_hash(content)
        if key in self._store:               # write-once: never overwrite
            return key
        self._store[key] = {
            "key": key,
            "content": content,
            "tags": sorted(set(tags or ())),
            "parents": list(parents or ()),
            "op": op,
            "meta": meta or {},
            "t": round(time.time(), 6),
            "seq": len(self._order),
        }
        self._order.append(key)
        return key

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        return self._store.get(key)

    def __contains__(self, key: str) -> bool:
        return key in self._store

    def __len__(self) -> int:
        return len(self._store)

    def select(self, tag: str) -> List[Dict[str, Any]]:
        """cognitive_system.scan: pull every record carrying a tag, in order."""
        return [self._store[k] for k in self._order if tag in self._store[k]["tags"]]

    def lineage(self, key: str) -> List[Dict[str, Any]]:
        """Walk parents back to the roots (the manifold's ancestry)."""
        chain: List[Dict[str, Any]] = []
        seen = set()
        frontier = [key]
        while frontier:
            k = frontier.pop()
            rec = self._store.get(k)
            if not rec or k in seen:
                continue
            seen.add(k)
            chain.append(rec)
            frontier.extend(rec["parents"])
        return chain

    def to_json(self) -> str:
        return json.dumps(
            {"version": 1, "records": [self._store[k] for k in self._order]},
            ensure_ascii=False,
            indent=2,
        )

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.to_json())
