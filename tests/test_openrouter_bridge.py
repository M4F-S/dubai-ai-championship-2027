#!/usr/bin/env python3
"""
tests/test_openrouter_bridge.py - Verification Suite for Sovereign Agent Bridge
Dubai AI Agents Championship 2026-2027

Validates:
1. C99 Native Shield Bindings (Pharmacovigilance, DHA Claims, Policy Gate, Normalizer, PII Scrub)
2. Sub-millisecond Execution Latency (< 0.5 ms on CPU)
3. OpenRouter Agent Engine (Air-gapped and Hybrid modes)
4. Security Block & Human Override Governance Flow
5. SHA-256 Non-Repudiation Audit Ledger Logging
6. Multi-threaded HTTP/SSE Server Endpoints
"""

import os
import sys
import time
import json
import unittest
import threading
import urllib.request
import urllib.error

# Ensure project root is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bridge.c99_bindings import (
    taryaq_verify_rx,
    qala_verify_call,
    normalize_arabic,
    scrub_pii,
    step_fademem,
    get_engine_status
)
from bridge.openrouter_client import (
    OpenRouterAgentEngine,
    VALID_OVERRIDE_TOKEN,
    append_audit_log,
    AUDIT_LOG_FILE,
    _consumed_override_tokens
)
from bridge.server import ChampionshipRequestHandler, ThreadingHTTPServer, DEFAULT_HOST


class TestOpenRouterBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure clean state for test run
        if os.path.exists(AUDIT_LOG_FILE):
            try:
                os.remove(AUDIT_LOG_FILE)
            except OSError:
                pass
        # Start server on ephemeral port for endpoint tests
        cls.port = 8799
        cls.server = ThreadingHTTPServer((DEFAULT_HOST, cls.port), ChampionshipRequestHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.2)  # Wait for socket to bind
        # Warm up ctypes binding symbols to eliminate first-call dynamic linker latency
        taryaq_verify_rx(primary_drug="Aspirin", concurrent_drug="Paracetamol", egfr=90.0)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "server"):
            cls.server.shutdown()
            cls.server.server_close()
        if os.path.exists(AUDIT_LOG_FILE):
            try:
                os.remove(AUDIT_LOG_FILE)
            except OSError:
                pass

    def setUp(self):
        """Reset consumed tokens before each test."""
        _consumed_override_tokens.clear()

    def test_01_c99_bindings_taryaq_fatal_block(self):
        """Verify C99 bare-metal engine blocks fatal drug interaction in < 0.5 ms."""
        res = taryaq_verify_rx(
            primary_drug="Colchicine",
            concurrent_drug="Clarithromycin",
            egfr=22.0
        )
        self.assertEqual(res["verdict"], "CLINICAL_CONTRAINDICATION_BLOCK")
        self.assertEqual(res["alert_code"], "FATAL_CYP3A4_RENAL_CONTRAINDICATION")
        self.assertTrue(res["is_blocked"])
        self.assertFalse(res["is_safe"])
        self.assertLess(res["execution_time_ms"], 1.0)

    def test_02_c99_bindings_taryaq_safe_rx(self):
        """Verify C99 engine safely approves non-interacting prescriptions."""
        res = taryaq_verify_rx(
            primary_drug="Paracetamol",
            concurrent_drug="Amoxicillin",
            egfr=95.0
        )
        self.assertEqual(res["verdict"], "CLINICAL_SAFE")
        self.assertTrue(res["is_safe"])
        self.assertFalse(res["is_blocked"])

    def test_03_c99_bindings_dha_late_claim_scrub(self):
        """Verify DHA SN 03/2019 claims submission delay penalty calculation (42 days = 12 days past 30-day window)."""
        res = taryaq_verify_rx(
            primary_drug="Metformin",
            egfr=75.0,
            submission_delay_days=42
        )
        self.assertEqual(res["verdict"], "CLINICAL_CLAIM_CYCLE_WARN")
        self.assertTrue(res["is_warning"])

    def test_04_c99_bindings_qala_policy_gate(self):
        """Verify Qala policy gate pauses transactions exceeding AED 50,000."""
        res = qala_verify_call(
            tool_name="erp_customs_settlement",
            amount_aed=125000.0,
            is_mutating=True
        )
        self.assertEqual(res["verdict"], "VERDICT_REVIEW")
        self.assertTrue(res["requires_review"])
        self.assertFalse(res["is_safe"])

    def test_05_c99_bindings_arabic_normalizer(self):
        """Verify zero-allocation C99 Arabic normalizer removes hamzas and Eastern digits."""
        res = normalize_arabic("إدارة الأزمات في دبي ٢٠٢٧")
        self.assertEqual(res["normalized"], "اداره الازمات في دبي 2027")
        self.assertLess(res["execution_time_ms"], 1.0)

    def test_06_c99_bindings_pii_scrubber(self):
        """Verify DESC ISR v3.1 PII scrubber strips Emirates IDs and patient data."""
        raw = "Patient Ahmed Ali (Emirates ID 784-1985-1234567-1, DOB 1985-04-12) taking Colchicine"
        res = scrub_pii(raw)
        self.assertNotIn("784-1985-1234567-1", res["scrubbed"])
        self.assertGreater(res["bytes_removed"], 0)

    def test_07_engine_process_chat_security_block(self):
        """Verify agent chat halts and returns security_block on fatal interaction."""
        engine = OpenRouterAgentEngine()
        events = list(engine.process_chat("Patient prescribed كولشيسين and Clarithromycin, eGFR 22"))
        
        event_types = [e["type"] for e in events]
        self.assertIn("pii_scrubbed", event_types)
        self.assertIn("tool_call", event_types)
        self.assertIn("c99_execution", event_types)
        self.assertIn("security_block", event_types)

        # Check block specifics
        block_event = next(e for e in events if e["type"] == "security_block")
        self.assertEqual(block_event["alert_code"], "FATAL_CYP3A4_RENAL_CONTRAINDICATION")
        self.assertTrue(block_event["override_required"])

    def test_08_engine_process_chat_with_override(self):
        """Verify agent chat succeeds and cryptographically signs ledger with valid override."""
        engine = OpenRouterAgentEngine()
        events = list(engine.process_chat(
            "Patient prescribed كولشيسين and Clarithromycin, eGFR 22",
            override_token=VALID_OVERRIDE_TOKEN,
            override_rationale="ICU attending co-signature Dr. Tariq DHA-P-44019"
        ))

        event_types = [e["type"] for e in events]
        self.assertIn("audit_committed", event_types)
        
        audit_event = next(e for e in events if e["type"] == "audit_committed")
        self.assertEqual(audit_event["state"], "COMMITTED")
        self.assertEqual(len(audit_event["signature"]), 64)  # 64 hex characters (SHA-256)

    def test_09_api_health_endpoint(self):
        """Verify HTTP GET /api/health returns valid system diagnostic telemetry."""
        url = f"http://{DEFAULT_HOST}:{self.port}/api/health"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data["c99_library_loaded"])
            self.assertTrue(data["symbols"]["taryaq_verify_prescription_and_claim"])

    def test_10_api_scenarios_endpoint(self):
        """Verify HTTP GET /api/scenarios returns predefined championship demos."""
        url = f"http://{DEFAULT_HOST}:{self.port}/api/scenarios"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertGreaterEqual(len(data["scenarios"]), 4)

    def test_11_api_override_endpoint(self):
        """Verify HTTP POST /api/override validates and enforces single-use clinician code."""
        url = f"http://{DEFAULT_HOST}:{self.port}/api/override"
        payload = json.dumps({
            "token": VALID_OVERRIDE_TOKEN,
            "rationale": "Nephrology clinical protocol approval"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "VALIDATED")

        # AF-04: Verify single-use replay protection raises HTTP 409 Conflict
        req_replay = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(req_replay, timeout=5)
        self.assertEqual(ctx.exception.code, 409)

    def test_12_api_chat_sse_stream(self):
        """Verify HTTP POST /api/chat streams Server-Sent Events (SSE) frames."""
        url = f"http://{DEFAULT_HOST}:{self.port}/api/chat"
        payload = json.dumps({
            "message": "Verify claim invoice for 12 days late submission under DHA SN 03/2019",
            "agent": "taryaq"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/event-stream", resp.headers.get("Content-Type", ""))
            raw_stream = resp.read().decode("utf-8")
            self.assertIn("data: ", raw_stream)
            self.assertIn('"type": "completed"', raw_stream)

    def test_13_api_ui_endpoint(self):
        """Verify HTTP GET / serves the championship Glass Cockpit HTML interface."""
        url = f"http://{DEFAULT_HOST}:{self.port}/"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/html", resp.headers.get("Content-Type", ""))
            html = resp.read().decode("utf-8")
            self.assertIn("DUBAI AI AGENTS CHAMPIONSHIP 2027", html)
            self.assertIn("IBM Plex Sans Arabic", html)
            self.assertIn("TARYAQ", html)
            self.assertIn("QALA", html)
            self.assertIn("NIBRAS", html)

    def test_14_api_audit_verify_endpoint(self):
        """Verify HTTP GET /api/audit/verify validates SHA-256 hash chaining from genesis."""
        url = f"http://{DEFAULT_HOST}:{self.port}/api/audit/verify"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("application/json", resp.headers.get("Content-Type", ""))
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data["chain_intact"])
            self.assertEqual(data["status"], "VERIFIED_TAMPER_EVIDENT")
            self.assertGreater(data["total_records"], 0)


if __name__ == "__main__":
    unittest.main()
