#!/usr/bin/env python3
"""tests/test_audit_verify_endpoint.py - /api/audit/verify HTTP contract tests.

Asserts the bridge delegates to tools/verify_audit.py (the single definition of
"verified") and fails closed:

1. Genuine 2-record HMAC ledger  -> 200, chain_intact true, total_records 2, VERIFIED.
2. Tampered record              -> 400, chain_intact false, error names the tampering.
3. Missing/short key            -> 503, status AUDIT_KEY_MISSING (never "verified").
4. Empty ledger                 -> 200, EMPTY_LEDGER, total_records 0.

Regression guard for the bug where /api/audit/verify recomputed
sha256(json minus signature) and reported a genuine HMAC ledger as
"Signature mismatch at record 0" with total_records 1 of 2.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
AGENT_BIN = os.path.join(ROOT_DIR, "build", "taryaq_agent")
TEST_KEY = "test-key-32-bytes-minimum-000000"


def _build_agent_if_needed():
    if os.path.isfile(AGENT_BIN):
        return True
    try:
        subprocess.run(["make", "build/taryaq_agent"], cwd=ROOT_DIR, check=True,
                       capture_output=True, text=True)
    except Exception:
        return False
    return os.path.isfile(AGENT_BIN)


class TestAuditVerifyEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not _build_agent_if_needed():
            raise unittest.SkipTest("build/taryaq_agent unavailable; cannot generate ledger")
        if not os.path.isfile(os.path.join(ROOT_DIR, "tools", "verify_audit.py")):
            raise unittest.SkipTest("tools/verify_audit.py missing")

        from http.server import ThreadingHTTPServer
        import bridge.server as server_mod

        cls.server_mod = server_mod
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server_mod.ChampionshipRequestHandler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.httpd.shutdown()
            cls.httpd.server_close()
        except Exception:
            pass

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="audit_verify_")
        self.ledger = os.path.join(self.tmpdir, "ledger.jsonl")
        self._orig_ledger = self.server_mod.AUDIT_LOG_FILE
        self.server_mod.AUDIT_LOG_FILE = self.ledger
        self._orig_key = os.environ.get("TARYAQ_AUDIT_KEY")

    def tearDown(self):
        self.server_mod.AUDIT_LOG_FILE = self._orig_ledger
        if self._orig_key is None:
            os.environ.pop("TARYAQ_AUDIT_KEY", None)
        else:
            os.environ["TARYAQ_AUDIT_KEY"] = self._orig_key
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _generate(self, path=None):
        target = path or self.ledger
        env = dict(os.environ, TARYAQ_AUDIT_KEY=TEST_KEY)
        res = subprocess.run([AGENT_BIN, "--test", "--audit-file", target],
                             env=env, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"ledger generation failed: {res.stderr}")
        return target

    def _get(self):
        url = f"http://127.0.0.1:{self.port}/api/audit/verify"
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    def test_01_genuine_ledger_verifies(self):
        self._generate()
        os.environ["TARYAQ_AUDIT_KEY"] = TEST_KEY
        code, body = self._get()
        self.assertEqual(code, 200, body)
        self.assertTrue(body["chain_intact"], body)
        self.assertEqual(body["total_records"], 2, body)
        self.assertEqual(body["status"], "VERIFIED")

    def test_02_tampered_ledger_fails_closed(self):
        self._generate()
        with open(self.ledger, "r", encoding="utf-8") as f:
            recs = [json.loads(line) for line in f if line.strip()]
        recs[1]["patient_egfr"] = 90.0
        with open(self.ledger, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r) + "\n")

        os.environ["TARYAQ_AUDIT_KEY"] = TEST_KEY
        code, body = self._get()
        self.assertEqual(code, 400, body)
        self.assertFalse(body["chain_intact"], body)
        self.assertEqual(body["status"], "CHAIN_INTEGRITY_COMPROMISED")
        self.assertIn("tampering", (body["error"] or "").lower())
        self.assertEqual(body["total_records"], 2)

    def test_03_missing_key_returns_503(self):
        self._generate()
        os.environ.pop("TARYAQ_AUDIT_KEY", None)
        code, body = self._get()
        self.assertEqual(code, 503, body)
        self.assertFalse(body["chain_intact"], body)
        self.assertEqual(body["status"], "AUDIT_KEY_MISSING")

    def test_04_short_key_returns_503(self):
        self._generate()
        os.environ["TARYAQ_AUDIT_KEY"] = "too-short"
        code, body = self._get()
        self.assertEqual(code, 503, body)
        self.assertEqual(body["status"], "AUDIT_KEY_MISSING")

    def test_05_empty_ledger_is_not_an_error(self):
        open(self.ledger, "w", encoding="utf-8").close()
        os.environ["TARYAQ_AUDIT_KEY"] = TEST_KEY
        code, body = self._get()
        self.assertEqual(code, 200, body)
        self.assertTrue(body["chain_intact"], body)
        self.assertEqual(body["total_records"], 0)
        self.assertEqual(body["status"], "EMPTY_LEDGER")


if __name__ == "__main__":
    unittest.main()
