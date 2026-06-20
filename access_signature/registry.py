"""Persistent state for the access-signature gatekeeper (JSON-backed).

Tracks the owner, the protected repositories (``tuplenetwork`` and ``Bada``),
every access request from people who clone / push / pull, and the credentials
("digital-signature passwords") issued to approved people.
"""

from __future__ import annotations

import json
import os
import time

PROTECTED_REPOS = ["tuplenetwork", "Bada"]


def _now() -> int:
    return int(time.time())


class Registry:
    def __init__(self, path: str):
        self.path = path
        self.data: dict = {
            "owner": {"email": None, "public_key_pem": None,
                      "github_account": "masaaki-avnturle"},
            "repos": list(PROTECTED_REPOS),
            "requests": {},
            "credentials": {},
        }
        if os.path.exists(path):
            self.load()

    # -- io ----------------------------------------------------------------
    def load(self):
        with open(self.path) as f:
            self.data = json.load(f)

    def save(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.data, f, indent=2)
        os.replace(tmp, self.path)

    # -- owner -------------------------------------------------------------
    def set_owner(self, email: str, public_key_pem: str):
        self.data["owner"]["email"] = email
        self.data["owner"]["public_key_pem"] = public_key_pem

    @property
    def owner_email(self) -> str | None:
        return self.data["owner"]["email"]

    @property
    def owner_public_pem(self) -> str | None:
        return self.data["owner"]["public_key_pem"]

    def is_protected(self, repo: str) -> bool:
        return repo in self.data["repos"]

    # -- requests ----------------------------------------------------------
    def add_request(self, actor: str, actor_email: str, repo: str,
                    operation: str) -> dict:
        rid = f"req_{len(self.data['requests']) + 1:04d}_{_now()}"
        req = {
            "id": rid, "actor": actor, "actor_email": actor_email,
            "repo": repo, "operation": operation, "status": "pending",
            "created_at": _now(), "decided_at": None,
        }
        self.data["requests"][rid] = req
        return req

    def get_request(self, rid: str) -> dict | None:
        return self.data["requests"].get(rid)

    def set_status(self, rid: str, status: str):
        self.data["requests"][rid]["status"] = status
        self.data["requests"][rid]["decided_at"] = _now()

    def requests(self, status: str | None = None) -> list:
        return [r for r in self.data["requests"].values()
                if status is None or r["status"] == status]

    # -- credentials -------------------------------------------------------
    def add_credential(self, cred: dict):
        self.data["credentials"][cred["id"]] = cred

    def credentials_for(self, actor: str, repo: str) -> list:
        return [c for c in self.data["credentials"].values()
                if c["actor"] == actor and c["repo"] == repo]

    def mark_used(self, cred_id: str):
        self.data["credentials"][cred_id]["used"] = True
