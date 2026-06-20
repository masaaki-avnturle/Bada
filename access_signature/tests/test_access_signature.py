import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from access_signature import ca
from access_signature.ed25519_pure import publickey, sign, verify
from access_signature.gatekeeper import Gatekeeper


class TestEd25519(unittest.TestCase):
    def test_sign_verify_roundtrip(self):
        import secrets
        seed = secrets.token_bytes(32)
        pub = publickey(seed)
        sig = sign(b"message", seed, pub)
        self.assertTrue(verify(sig, b"message", pub))

    def test_tampered_message_fails(self):
        import secrets
        seed = secrets.token_bytes(32)
        pub = publickey(seed)
        sig = sign(b"message", seed, pub)
        self.assertFalse(verify(sig, b"tampered", pub))

    def test_wrong_key_fails(self):
        import secrets
        seed1, seed2 = secrets.token_bytes(32), secrets.token_bytes(32)
        sig = sign(b"m", seed1, publickey(seed1))
        self.assertFalse(verify(sig, b"m", publickey(seed2)))


class TestCA(unittest.TestCase):
    def test_save_load_sign_verify(self):
        with tempfile.TemporaryDirectory() as d:
            auth = ca.SignatureAuthority.generate()
            path = os.path.join(d, "k.pem")
            auth.save(path)
            self.assertEqual(oct(os.stat(path).st_mode)[-3:], "600")
            loaded = ca.SignatureAuthority.load(path)
            sig = loaded.sign("hello")
            self.assertTrue(ca.verify(loaded.public_pem(), "hello", sig))
            self.assertFalse(ca.verify(loaded.public_pem(), "bye", sig))

    def test_passphrase_encryption(self):
        with tempfile.TemporaryDirectory() as d:
            os.environ["ACCESS_SIGNATURE_KEY_PASSPHRASE"] = "s3cret"
            try:
                auth = ca.SignatureAuthority.generate()
                path = os.path.join(d, "k.pem")
                auth.save(path)
                with open(path) as f:
                    self.assertTrue(f.read().startswith("enc:"))
                loaded = ca.SignatureAuthority.load(path)
                self.assertEqual(loaded.public_pem(), auth.public_pem())
            finally:
                del os.environ["ACCESS_SIGNATURE_KEY_PASSPHRASE"]


class TestGatekeeperFlow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gk = Gatekeeper(state_dir=self.tmp)
        self.gk.init_owner("masaaki.tabu4@gmail.com")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_unprotected_repo_ignored(self):
        res = self.gk.on_access("x", "some-other-repo", "push")
        self.assertEqual(res["status"], "ignored")

    def test_protected_repos(self):
        for repo in ("tuplenetwork", "Bada"):
            self.assertTrue(self.gk.registry.is_protected(repo))

    def test_access_creates_request_and_emails_owner(self):
        res = self.gk.on_access("dev", "Bada", "clone", "dev@example.com")
        self.assertEqual(res["status"], "pending")
        # owner approval email spooled
        sent = "\n".join(self.gk.mailer.log)
        self.assertIn("masaaki.tabu4@gmail.com", sent)

    def test_approve_issues_valid_password(self):
        req = self.gk.on_access("dev", "Bada", "push", "dev@x.com")["request"]
        result = self.gk.approve(req["id"])
        pw = result["password"]
        self.assertTrue(self.gk.verify("dev", "Bada", pw)["ok"])
        # password email went to the person
        self.assertTrue(any("dev@x.com" in l for l in self.gk.mailer.log))

    def test_wrong_password_rejected(self):
        req = self.gk.on_access("dev", "Bada", "push", "dev@x.com")["request"]
        self.gk.approve(req["id"])
        self.assertFalse(self.gk.verify("dev", "Bada", "not-the-password")["ok"])

    def test_deny_blocks_issuance(self):
        req = self.gk.on_access("dev", "tuplenetwork", "pull")["request"]
        self.gk.deny(req["id"])
        with self.assertRaises(ValueError):
            self.gk.approve(req["id"])

    def test_already_authorized_skips_new_request(self):
        req = self.gk.on_access("dev", "Bada", "push", "dev@x.com")["request"]
        self.gk.approve(req["id"])
        res = self.gk.on_access("dev", "Bada", "push", "dev@x.com")
        self.assertEqual(res["status"], "authorized")

    def test_stateless_token_verification(self):
        req = self.gk.on_access("dev", "Bada", "push", "dev@x.com")["request"]
        r = self.gk.approve(req["id"])
        pub = self.gk.owner_public_pem()
        self.assertTrue(self.gk.verify_token(
            "dev", "Bada", r["password"], r["signature"], r["expires_at"],
            public_pem=pub))
        self.assertFalse(self.gk.verify_token(
            "dev", "Bada", r["password"], r["signature"],
            int(time.time()) - 1, public_pem=pub))  # expired

    def test_expired_credential_not_valid(self):
        req = self.gk.on_access("dev", "Bada", "push", "dev@x.com")["request"]
        self.gk.approve(req["id"], ttl_days=0)
        time.sleep(0.01)
        self.assertFalse(self.gk.verify("dev", "Bada",
                                        "anything")["ok"])

    def test_persistence_across_instances(self):
        req = self.gk.on_access("dev", "Bada", "push", "dev@x.com")["request"]
        r = self.gk.approve(req["id"])
        gk2 = Gatekeeper(state_dir=self.tmp)
        self.assertTrue(gk2.verify("dev", "Bada", r["password"])["ok"])


class TestLockdown(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.gk = Gatekeeper(state_dir=self.tmp)
        self.gk.init_owner("masaaki.tabu4@gmail.com")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_lock_all_blocks_every_repo(self):
        self.gk.lock(scope="all", reason="temporary")
        self.assertTrue(self.gk.status()["locked"])
        self.assertEqual(self.gk.on_access("d", "Bada", "clone")["status"],
                         "blocked")
        # even a repo not in the protected list is blocked under 'all'
        self.assertEqual(self.gk.on_access("d", "anything", "push")["status"],
                         "blocked")

    def test_gate_denies_when_locked(self):
        self.gk.lock(scope="all")
        self.assertFalse(self.gk.gate("d", "Bada")["allow"])

    def test_approve_refused_during_lockdown(self):
        req = self.gk.on_access("d", "Bada", "push", "d@x")["request"]
        self.gk.lock(scope="all")
        with self.assertRaises(ValueError):
            self.gk.approve(req["id"])

    def test_unlock_restores_flow(self):
        self.gk.lock(scope="all")
        self.gk.unlock()
        self.assertFalse(self.gk.status()["locked"])
        self.assertEqual(self.gk.on_access("d", "Bada", "clone", "d@x")
                         ["status"], "pending")

    def test_scoped_lock_only_affects_listed_repos(self):
        self.gk.lock(scope=["Bada"])
        self.assertEqual(self.gk.on_access("d", "Bada", "push")["status"],
                         "blocked")
        # tuplenetwork is protected but not in the lock scope -> normal flow
        self.assertEqual(self.gk.on_access("d", "tuplenetwork", "pull", "d@x")
                         ["status"], "pending")

    def test_lockdown_persists_across_instances(self):
        self.gk.lock(scope="all", reason="maintenance")
        gk2 = Gatekeeper(state_dir=self.tmp)
        self.assertTrue(gk2.status()["locked"])
        self.assertEqual(gk2.status()["reason"], "maintenance")


if __name__ == "__main__":
    unittest.main()
