# access_signature — digital-signature access approval

For the GitHub repos **`masaaki-avnturle/tuplenetwork`** and
**`masaaki-avnturle/Bada`**.

When someone **clones / pushes / pulls**, a request is recorded and an
**approval email is sent to the owner** (`masaaki.tabu4@gmail.com`).  When the
owner approves a person, a **digital-signature password** — a one-time password
signed with the owner's **Ed25519** key — is **emailed to that person**.  The
password proves the owner authorised them and can be verified by anyone with
the owner's public key.

```
clone/push/pull ─▶ on-access ─▶ request recorded ─▶ EMAIL owner (approve/deny)
                                                          │ owner approves
                              EMAIL person ◀─ sign(password) with owner key
                                   │
                 verify(actor, repo, password) ─▶ Ed25519 verify with public key
```

Pure **Python 3, stdlib only** — Ed25519 is implemented from scratch in
`ed25519_pure.py` (RFC 8032), so there are no third-party dependencies.

## Honest scope (important)
GitHub.com **cannot run custom code on clone / pull / fetch** — only **push**
can be gated. So:

| operation | how it's covered here |
|:--|:--|
| **push** | real enforcement: the **GitHub Action** (`workflows/access-signature.yml`) verifies a signed token in the head-commit trailer, and/or a self-hosted **`pre-receive`** hook (`hooks/pre-receive.sample`). |
| **clone / pull / push (client)** | installable client-side git hooks (`post-checkout`, `post-merge`, `pre-push`) that record the request and email the owner. Client hooks are advisory (a user can skip them); server-side / the Action is authoritative. |
| **clone / pull (authoritative)** | only possible on a server you control (self-hosted mirror / GitHub Enterprise), where the same hooks/CLI run. |

## Workflow (CLI)
```bash
# one-time: create the owner key pair + approver email
python3 -m access_signature.cli init --email masaaki.tabu4@gmail.com

# someone clones/pushes/pulls -> request + email to owner
python3 -m access_signature.cli on-access --actor dev_taro --repo Bada \
        --op clone --email taro@example.com

python3 -m access_signature.cli list --status pending        # see requests
python3 -m access_signature.cli outbox                       # see spooled emails

# owner approves -> a signed password is issued and emailed to the person
python3 -m access_signature.cli approve req_0001_... --ttl 7

# the person proves authorisation
python3 -m access_signature.cli verify --actor dev_taro --repo Bada \
        --password <issued-password>

# deny instead
python3 -m access_signature.cli deny req_0001_...
```

## Temporary lockdown (封鎖)
Blockade the repositories so **all** clone/push/pull is denied — even holders
of valid passwords — until lifted.  Fully reversible.
```bash
python3 -m access_signature.cli lock all --reason "temporary blockade"
python3 -m access_signature.cli status        # locked : True
python3 -m access_signature.cli lock Bada tuplenetwork   # scope to repos
python3 -m access_signature.cli unlock        # lift the blockade
```
While locked: `on-access` returns **blocked**, `approve` is refused, and the
`gate` decision (used by the `pre-push` hook) returns **DENY (locked-down)**,
so pushes are refused. The owner is emailed on lock and unlock. The lock state
persists in the registry, so it survives restarts until you `unlock`.

> Note: this is the access-control layer's blockade. It does not change
> GitHub's own settings — to lock the repos on github.com itself, archive or
> make them private (see below).

## Locking the repos on github.com (real settings)
The MCP tools here can't change repo settings, so do it with the `gh` CLI or
the web UI. To **archive** (read-only) or make **private** every repo:
```bash
# archive every repo owned by the account (reversible: `--archived=false`)
gh repo list masaaki-avnturle --no-archived --json nameWithOwner -q '.[].nameWithOwner' \
  | xargs -I{} gh repo archive {} --yes

# or make every repo private
gh repo list masaaki-avnturle --json nameWithOwner -q '.[].nameWithOwner' \
  | xargs -I{} gh repo edit {} --visibility private --accept-visibility-change-consequences
```
To reverse: `gh repo unarchive <repo>` / `gh repo edit <repo> --visibility public`.

## Email
Sends real mail when SMTP env vars are set, otherwise **spools** each message
to `state/outbox/*.eml` and prints the path (nothing is sent without
credentials).  To send for real:
```bash
export SMTP_HOST=smtp.gmail.com SMTP_PORT=587 \
       SMTP_USER=you@gmail.com SMTP_PASS=app-password \
       SMTP_FROM=you@gmail.com
```

## The digital signature
* Owner key: Ed25519 private seed in `state/owner_key.pem` (mode `600`;
  optionally encrypted at rest with `ACCESS_SIGNATURE_KEY_PASSPHRASE`).
* Issued password is random; the **signature** is over the canonical message
  `sig-v1|actor|repo|password|expires`. Only the owner's private key can make
  it; `verify` / `verify-token` check it with the public key.
* Only the password **hash** is stored — the plaintext exists only in the
  email to the approved person.

## Git hooks
```bash
# client side, in a working copy of tuplenetwork or Bada:
access_signature/hooks/install-hooks.sh .
# server side (self-hosted): copy hooks/pre-receive.sample -> hooks/pre-receive
# github.com push checks: copy workflows/access-signature.yml -> .github/workflows/
#   and commit the owner public key:
python3 -m access_signature.cli pubkey > access_signature/owner_pubkey.txt
```

## Tests
```bash
python3 -m unittest discover -s tests -v       # 15 tests
```

## Security notes
- Never commit `state/` (private key, registry, spooled mail) — see
  `.gitignore`.
- Client-side git hooks are advisory; use the Action or a server-side hook for
  real enforcement.
- Rotating the key invalidates all outstanding passwords (re-publish pubkey).
