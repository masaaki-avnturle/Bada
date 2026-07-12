"""Gatekeeper — the access-approval + digital-signature workflow.

Flow for the repos ``tuplenetwork`` and ``Bada`` (owner: masaaki-avnturle):

  1. Someone clones / pushes / pulls  ->  :meth:`on_access` records a request
     and **emails the owner** (masaaki.tabu4@gmail.com) to approve or deny.
  2. The owner approves  ->  :meth:`approve` issues a **digital-signature
     password** (a one-time password signed with the owner's Ed25519 key) and
     **emails it to the approved person**.
  3. The person proves authorisation with that password  ->  :meth:`verify`
     checks the signature against the owner's public key.

Only the owner's private key can mint a valid password; anyone can verify one.
"""

from __future__ import annotations

import hashlib
import os
import secrets
import time

from . import ca
from .mailer import Mailer
from .registry import Registry

_SIG_VERSION = "sig-v1"


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _canonical(actor: str, repo: str, password: str, expires_at: int) -> str:
    return f"{_SIG_VERSION}|{actor}|{repo}|{password}|{expires_at}"


class Gatekeeper:
    def __init__(self, state_dir: str | None = None):
        self.state_dir = state_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "state")
        os.makedirs(self.state_dir, exist_ok=True)
        self.registry = Registry(os.path.join(self.state_dir,
                                              "registry.json"))
        self.key_path = os.path.join(self.state_dir, "owner_key.pem")
        self.mailer = Mailer(os.path.join(self.state_dir, "outbox"))

    # -- setup -------------------------------------------------------------
    def init_owner(self, email: str) -> "Gatekeeper":
        authority = ca.SignatureAuthority.generate()
        authority.save(self.key_path)
        self.registry.set_owner(email, authority.public_pem())
        self.registry.save()
        return self

    def _authority(self) -> ca.SignatureAuthority:
        return ca.SignatureAuthority.load(self.key_path)

    # -- lockdown: temporarily blockade the repositories ------------------
    def lock(self, scope="all", reason: str | None = None,
             by: str | None = None) -> dict:
        self.registry.set_lockdown(True, scope=scope, reason=reason,
                                   by=by or self.registry.owner_email)
        self.registry.save()
        if self.registry.owner_email:
            tgt = "ALL repositories" if scope == "all" else ", ".join(scope)
            self.mailer.send(
                self.registry.owner_email,
                "[access-signature] repositories LOCKED DOWN",
                f"A temporary blockade is now ACTIVE for {tgt}.\n"
                f"reason: {reason or '(none)'}\n"
                f"All clone/push/pull access is denied until 'unlock'.\n")
        return self.status()

    def unlock(self) -> dict:
        self.registry.set_lockdown(False)
        self.registry.save()
        if self.registry.owner_email:
            self.mailer.send(
                self.registry.owner_email,
                "[access-signature] repositories UNLOCKED",
                "The temporary blockade has been lifted; normal "
                "approval flow resumes.\n")
        return self.status()

    def status(self) -> dict:
        lk = self.registry.lockdown
        return {
            "locked": bool(lk.get("active")),
            "scope": lk.get("scope"),
            "reason": lk.get("reason"),
            "since": lk.get("since"),
            "repos": self.registry.data["repos"],
        }

    # -- 1. access attempt -> request + email owner -----------------------
    def on_access(self, actor: str, repo: str, operation: str,
                  actor_email: str | None = None) -> dict:
        # lockdown overrides everything — even valid credentials are blocked.
        if self.registry.is_locked(repo):
            return {"status": "blocked", "repo": repo,
                    "reason": "repository temporarily locked down"}

        if not self.registry.is_protected(repo):
            return {"status": "ignored", "reason": f"{repo} not protected"}

        # already authorised? then no new request is needed.
        if self.has_valid_credential(actor, repo):
            return {"status": "authorized", "actor": actor, "repo": repo}

        actor_email = actor_email or actor
        req = self.registry.add_request(actor, actor_email, repo, operation)
        self.registry.save()
        self._email_owner(req)
        return {"status": "pending", "request": req}

    def _email_owner(self, req: dict):
        owner = self.registry.owner_email
        if not owner:
            return
        body = (
            f"A digital-signature access request needs your approval.\n\n"
            f"  repository : masaaki-avnturle/{req['repo']}\n"
            f"  operation  : {req['operation']} (clone/push/pull)\n"
            f"  person     : {req['actor']}  <{req['actor_email']}>\n"
            f"  request id : {req['id']}\n"
            f"  at         : {time.ctime(req['created_at'])}\n\n"
            f"Approve  ->  access-signature approve {req['id']}\n"
            f"Deny     ->  access-signature deny {req['id']}\n\n"
            f"On approval, a one-time digital-signature password will be "
            f"signed with your key and emailed to the person.\n")
        self.mailer.send(owner,
                         f"[access-signature] approve access to "
                         f"{req['repo']} for {req['actor']}", body)

    # -- 2. approve -> issue signed password + email person ----------------
    def approve(self, request_id: str, ttl_days: int = 7) -> dict:
        req = self.registry.get_request(request_id)
        if not req:
            raise KeyError(f"no such request {request_id}")
        if req["status"] != "pending":
            raise ValueError(f"request {request_id} is {req['status']}")
        if self.registry.is_locked(req["repo"]):
            raise ValueError(
                f"cannot approve while {req['repo']} is locked down — "
                f"run 'unlock' first")

        password = secrets.token_urlsafe(18)
        expires_at = int(time.time()) + ttl_days * 86400
        message = _canonical(req["actor"], req["repo"], password, expires_at)
        signature = self._authority().sign(message)

        cred = {
            "id": f"cred_{request_id}",
            "actor": req["actor"], "actor_email": req["actor_email"],
            "repo": req["repo"], "password_hash": _sha256(password),
            "signature": signature, "expires_at": expires_at,
            "used": False, "request_id": request_id,
        }
        self.registry.add_credential(cred)
        self.registry.set_status(request_id, "approved")
        self.registry.save()
        self._email_password(req, password, signature, expires_at)
        # password is returned once for the caller; only its hash is stored.
        return {"status": "approved", "actor": req["actor"],
                "repo": req["repo"], "password": password,
                "signature": signature, "expires_at": expires_at}

    def _email_password(self, req: dict, password: str, signature: str,
                        expires_at: int):
        body = (
            f"You are approved to {req['operation']} "
            f"masaaki-avnturle/{req['repo']}.\n\n"
            f"Your one-time digital-signature password (keep it secret):\n\n"
            f"  password  : {password}\n"
            f"  signature : {signature}\n"
            f"  expires   : {time.ctime(expires_at)}\n\n"
            f"Verify with:\n"
            f"  access-signature verify --actor {req['actor']} "
            f"--repo {req['repo']} --password {password}\n\n"
            f"This password was signed with the repository owner's private "
            f"key; it proves the owner authorised you.\n")
        self.mailer.send(req["actor_email"],
                         f"[access-signature] your access password for "
                         f"{req['repo']}", body)

    def deny(self, request_id: str) -> dict:
        req = self.registry.get_request(request_id)
        if not req:
            raise KeyError(f"no such request {request_id}")
        self.registry.set_status(request_id, "denied")
        self.registry.save()
        if req["actor_email"]:
            self.mailer.send(
                req["actor_email"],
                f"[access-signature] access to {req['repo']} denied",
                f"Your request {request_id} to {req['operation']} "
                f"{req['repo']} was denied.\n")
        return {"status": "denied", "request": req}

    # -- 3. verify a password ---------------------------------------------
    def verify(self, actor: str, repo: str, password: str,
               consume: bool = False) -> dict:
        owner_pub = self.registry.owner_public_pem
        now = int(time.time())
        for cred in self.registry.credentials_for(actor, repo):
            if cred["used"] or cred["expires_at"] < now:
                continue
            if _sha256(password) != cred["password_hash"]:
                continue
            message = _canonical(actor, repo, password, cred["expires_at"])
            if ca.verify(owner_pub, message, cred["signature"]):
                if consume:
                    self.registry.mark_used(cred["id"])
                    self.registry.save()
                return {"ok": True, "credential": cred["id"],
                        "expires_at": cred["expires_at"]}
        return {"ok": False}

    def verify_token(self, actor: str, repo: str, password: str,
                     signature: str, expires_at: int,
                     public_pem: str | None = None) -> bool:
        """Stateless verification: check a signed token purely with the
        owner's public key (no registry needed) — for git hooks / CI."""
        if expires_at < int(time.time()):
            return False
        pub = public_pem or self.registry.owner_public_pem
        return ca.verify(pub, _canonical(actor, repo, password, expires_at),
                         signature)

    def owner_public_pem(self) -> str | None:
        return self.registry.owner_public_pem

    def gate(self, actor: str, repo: str, password: str | None = None,
             operation: str = "push") -> dict:
        """Single allow/deny decision for git hooks.
        Lockdown denies unconditionally; otherwise a valid password allows."""
        if self.registry.is_locked(repo):
            return {"allow": False, "reason": "locked-down"}
        if password and self.verify(actor, repo, password)["ok"]:
            return {"allow": True, "reason": "authorized"}
        self.on_access(actor, repo, operation, actor)
        return {"allow": False, "reason": "access-requested"}

    def has_valid_credential(self, actor: str, repo: str) -> bool:
        now = int(time.time())
        return any(not c["used"] and c["expires_at"] >= now
                   for c in self.registry.credentials_for(actor, repo))
