#!/usr/bin/env python3
"""
tests/test_multi_turn_bridge.py - Verification Suite for Multi-Turn Bridge & Script Sanitizer
Dubai AI Agents Championship 2026-2027 (Pillar 4: Multi-Turn Orchestration Engine)

Covers Milestone SPRINT-11-C (M-11-C):
- Test 1: Katakana sanitization fallback and Arabic INN normalization.
- Test 2: Casual greeting intent routing (no tools invoked).
- Test 3: Colchicine + Clarithromycin eGFR 22 scenario produces both c99_execution (is_blocked=True)
          AND streamed synthesis tokens explaining the CYP3A4/P-gp fatal contraindication.
- Test 4: Qala customs scenario produces landed tax breakdown synthesis.
- Test 5: Clinician override multi-turn execution and audit trail commitment.
- Test 6: Cyrillic/Hiragana script leak defense and C99 memory safety.
"""

import os
import sys
import time
import json
import unittest
import threading
import urllib.request
import urllib.error

# Ensure project root is in python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bridge.sanitizer import (
    has_unauthorized_script,
    detect_unauthorized_scripts,
    strip_unauthorized_scripts,
    validate_script,
    normalize_drug_name,
    sanitize_tool_arguments,
    is_casual_intent,
    get_casual_introduction
)
from bridge.openrouter_client import (
    OpenRouterAgentEngine,
    VALID_OVERRIDE_TOKEN,
    AUDIT_LOG_FILE,
    _consumed_override_tokens
)
from bridge.server import ChampionshipRequestHandler, ThreadingHTTPServer, DEFAULT_HOST


class TestMultiTurnBridgeAndSanitizer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure test audit key for ledger signing
        cls._orig_audit_key = os.environ.get("TARYAQ_AUDIT_KEY")
        os.environ["TARYAQ_AUDIT_KEY"] = "test-key-32-bytes-minimum-phase1c-00000"

        # Start ephemeral HTTP/SSE server for endpoint validation
        cls.port = 8822
        cls.server = ThreadingHTTPServer((DEFAULT_HOST, cls.port), ChampionshipRequestHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "server"):
            cls.server.shutdown()
            cls.server.server_close()
        if getattr(cls, "_orig_audit_key", None) is None:
            os.environ.pop("TARYAQ_AUDIT_KEY", None)
        else:
            os.environ["TARYAQ_AUDIT_KEY"] = cls._orig_audit_key

    def setUp(self):
        """Reset consumed tokens before each test."""
        _consumed_override_tokens.clear()

    # -------------------------------------------------------------------------
    # TEST 1: Katakana Sanitization Fallback and Arabic INN Normalization
    # -------------------------------------------------------------------------
    def test_01_script_detection_and_rejection(self):
        """Verify Katakana, Hiragana, and Cyrillic scripts are accurately detected and stripped."""
        # Katakana checks
        self.assertTrue(has_unauthorized_script("コルヒチン"))
        self.assertIn("Katakana", detect_unauthorized_scripts("コルヒチン"))
        is_clean, err = validate_script("Patient prescribed コルヒチン")
        self.assertFalse(is_clean)
        self.assertIn("Katakana", err)

        # Hiragana checks
        self.assertTrue(has_unauthorized_script("こんにちは"))
        self.assertIn("Hiragana", detect_unauthorized_scripts("こんにちは"))

        # Cyrillic checks
        self.assertTrue(has_unauthorized_script("колхицин"))
        self.assertIn("Cyrillic", detect_unauthorized_scripts("колхицин"))

        # Clean Arabic, English, and numeric inputs must pass
        self.assertFalse(has_unauthorized_script("Colchicine 0.5mg"))
        self.assertFalse(has_unauthorized_script("كولشيسين وكلاريثروميسين"))
        self.assertFalse(has_unauthorized_script("eGFR 22 mL/min/1.73m²"))
        self.assertTrue(validate_script("Colchicine 0.5mg BID")[0])

        # Stripping behavior
        stripped = strip_unauthorized_scripts("Drug: Colchicine (コルヒチン) [колхицин]")
        self.assertEqual(stripped, "Drug: Colchicine () []")

    def test_01b_arabic_inn_bidirectional_normalization(self):
        """Verify Arabic <-> English INN mappings for core pharmaceutical compounds."""
        # Arabic -> English Canonical INN
        self.assertEqual(normalize_drug_name("كولشيسين"), "Colchicine")
        self.assertEqual(normalize_drug_name("الكولشيسين"), "Colchicine")
        self.assertEqual(normalize_drug_name("كلاريثروميسين"), "Clarithromycin")
        self.assertEqual(normalize_drug_name("كلاريثرو"), "Clarithromycin")
        self.assertEqual(normalize_drug_name("ميتفورمين"), "Metformin")
        self.assertEqual(normalize_drug_name("سيمفاستاتين"), "Simvastatin")
        self.assertEqual(normalize_drug_name("وارفارين"), "Warfarin")
        self.assertEqual(normalize_drug_name("أميودارون"), "Amiodarone")
        self.assertEqual(normalize_drug_name("باراسيتامول"), "Paracetamol")
        self.assertEqual(normalize_drug_name("أموكسيسيلين"), "Amoxicillin")
        self.assertEqual(normalize_drug_name("ترامادول"), "Tramadol")

        # English -> Arabic Canonical INN
        self.assertEqual(normalize_drug_name("Colchicine", target_lang="ar"), "كولشيسين")
        self.assertEqual(normalize_drug_name("Clarithromycin", target_lang="ar"), "كلاريثروميسين")
        self.assertEqual(normalize_drug_name("Metformin", target_lang="ar"), "ميتفورمين")
        self.assertEqual(normalize_drug_name("Warfarin", target_lang="ar"), "وارفارين")

    def test_01c_katakana_fallback_and_argument_sanitization(self):
        """Verify Katakana drug names safely map or fall back without crashing C99 lookup."""
        # Known Katakana drug names resolve to English INN
        self.assertEqual(normalize_drug_name("コルヒチン"), "Colchicine")
        self.assertEqual(normalize_drug_name("クラリスロマイシン"), "Clarithromycin")

        # Mixed Katakana and English resolves cleanly
        self.assertEqual(normalize_drug_name("Colchicine コルヒチン"), "Colchicine")

        # Completely unmodeled Katakana string yields safe fallback
        self.assertEqual(normalize_drug_name("カタカナテスト"), "UNKNOWN_DRUG")

        # Sanitize tool arguments for interaction check
        raw_args = {
            "primary_drug": "كولشيسين",
            "concurrent_drug": "クラリスロマイシン",
            "patient_egfr": "22",
            "is_controlled": False
        }
        sanitized = sanitize_tool_arguments("interaction_check", raw_args)
        self.assertEqual(sanitized["primary_drug"], "Colchicine")
        self.assertEqual(sanitized["concurrent_drug"], "Clarithromycin")
        self.assertEqual(sanitized["patient_egfr"], 22.0)
        self.assertIsInstance(sanitized["patient_egfr"], float)

        # Sanitize tool arguments for med_lookup
        lookup_args = {"drug_name": "コルヒチン"}
        sanitized_lookup = sanitize_tool_arguments("med_lookup", lookup_args)
        self.assertEqual(sanitized_lookup["drug_name"], "Colchicine")

    # -------------------------------------------------------------------------
    # TEST 2: Casual Greeting Intent Routing (No Tools Invoked)
    # -------------------------------------------------------------------------
    def test_02_casual_greeting_intent_routing(self):
        """Verify casual greetings and identity inquiries stream direct introductions with zero tool invocations."""
        engine = OpenRouterAgentEngine(provider="deterministic")

        casual_prompts = [
            "hello",
            "Hello there!",
            "مرحبا",
            "السلام عليكم",
            "who are you",
            "صباح الخير"
        ]

        for prompt in casual_prompts:
            with self.subTest(prompt=prompt):
                self.assertTrue(is_casual_intent(prompt), f"Failed to identify casual intent: {prompt}")

                events = list(engine.process_chat(prompt))
                event_types = [e["type"] for e in events]

                # Critical assertion: ZERO tool invocations for casual pleasantries
                self.assertNotIn("tool_call", event_types, f"Tool called on casual prompt: {prompt}")
                self.assertNotIn("c99_execution", event_types, f"C99 executed on casual prompt: {prompt}")
                self.assertNotIn("security_block", event_types, f"Security block raised on casual prompt: {prompt}")

                # Must stream tokens and complete
                self.assertIn("token", event_types)
                self.assertIn("completed", event_types)

                completed_ev = next(e for e in events if e["type"] == "completed")
                self.assertEqual(completed_ev.get("intent"), "CASUAL_GREETING_ROUTED")

                # Accumulate streamed tokens and verify bilingual greeting content
                accumulated = "".join(e["content"] for e in events if e["type"] == "token")
                self.assertTrue(len(accumulated) > 50)
                self.assertTrue("ترياق" in accumulated or "Taryaq" in accumulated)
                self.assertTrue("Dubai" in accumulated or "دبي" in accumulated)

    # -------------------------------------------------------------------------
    # TEST 3: Colchicine + Clarithromycin eGFR 22 Scenario
    # -------------------------------------------------------------------------
    def test_03_colchicine_clarithromycin_fatal_synthesis(self):
        """Verify fatal interaction produces both c99_execution (is_blocked=True) AND streamed synthesis tokens."""
        engine = OpenRouterAgentEngine(provider="deterministic")
        engine.set_agent("taryaq")

        prompt = (
            "Patient Ahmed (Emirates ID 784-1985-1234567-1, DOB 1985-04-12) presented with acute gout flare. "
            "Prescribed كولشيسين 0.5mg BID and Clarithromycin 500mg BID for concurrent respiratory infection. "
            "Current laboratory report shows eGFR = 22 mL/min/1.73m²."
        )

        events = list(engine.process_chat(prompt))
        event_types = [e["type"] for e in events]

        # 1. Verification of Tool Proposal & Intercept
        self.assertIn("tool_call", event_types)
        self.assertIn("c99_execution", event_types)
        self.assertIn("security_block", event_types)

        # 2. Verification of C99 Shield Block
        c99_executions = [e for e in events if e["type"] == "c99_execution"]
        inter_exec = next((e for e in c99_executions if e["tool"] == "interaction_check"), None)
        self.assertIsNotNone(inter_exec)
        self.assertTrue(inter_exec["result"]["is_blocked"])
        self.assertEqual(inter_exec["result"]["alert_code"], "FATAL_CYP3A4_RENAL_CONTRAINDICATION")

        # 3. Verification of Security Block Event
        sec_block = next(e for e in events if e["type"] == "security_block")
        self.assertEqual(sec_block["alert_code"], "FATAL_CYP3A4_RENAL_CONTRAINDICATION")
        self.assertTrue(sec_block["override_required"])

        # 4. Critical 2nd-Turn Verification: Streamed Synthesis Tokens Present
        self.assertIn("token", event_types)
        token_events = [e for e in events if e["type"] == "token"]
        self.assertGreater(len(token_events), 5, "Expected streaming tokens in multiple chunks")

        synthesis_text = "".join(e["content"] for e in token_events)

        # 5. Semantic Clinical Validation of Synthesis Output
        self.assertIn("CYP3A4", synthesis_text)
        self.assertTrue("P-glycoprotein" in synthesis_text or "P-gp" in synthesis_text)
        self.assertTrue("Colchicine" in synthesis_text or "كولشيسين" in synthesis_text)
        self.assertTrue("Clarithromycin" in synthesis_text or "كلاريثروميسين" in synthesis_text)
        self.assertTrue("22" in synthesis_text or "eGFR" in synthesis_text)
        self.assertTrue("contraindication" in synthesis_text.lower() or "blocked" in synthesis_text.lower())
        self.assertIn("TARYAQ-OVERRIDE-8842-CLIN", synthesis_text)

        # 6. Lifecycle completion check
        self.assertIn("completed", event_types)

    # -------------------------------------------------------------------------
    # TEST 4: Qala Customs Landed Tax Breakdown Synthesis
    # -------------------------------------------------------------------------
    def test_04_qala_customs_landed_tax_breakdown(self):
        """Verify Qala customs scenario produces c99_execution AND landed tax breakdown synthesis."""
        engine = OpenRouterAgentEngine(provider="deterministic")
        engine.set_agent("qala")

        prompt = (
            "Initiate automated customs settlement clearance for DP World Jebel Ali container shipment "
            "#DPW-DXB-88301 with transaction value AED 125,000.00."
        )

        events = list(engine.process_chat(prompt))
        event_types = [e["type"] for e in events]

        # 1. Tool proposal and C99 policy gate execution
        self.assertIn("tool_call", event_types)
        self.assertIn("c99_execution", event_types)

        policy_exec = next(e for e in events if e["type"] == "c99_execution" and e["tool"] == "policy_verify_call")
        self.assertEqual(policy_exec["result"]["verdict"], "VERDICT_REVIEW")
        self.assertTrue(policy_exec["result"]["requires_review"])

        # 2. Stage 2 Conversational Synthesis Tokens Present
        self.assertIn("token", event_types)
        token_events = [e for e in events if e["type"] == "token"]
        self.assertGreater(len(token_events), 5, "Expected streaming tokens in multiple chunks")

        synthesis_text = "".join(e["content"] for e in token_events)

        # 3. Validation of Landed Tax & Tariff Breakdown
        # CIF: AED 125,000.00
        # Customs Duty (5%): AED 6,250.00
        # VAT (5% on CIF + Duty): AED 6,562.50
        # Total Landed Tax: AED 12,812.50 (10.25% landed tax)
        self.assertIn("125,000", synthesis_text)
        self.assertIn("6,250.00", synthesis_text)
        self.assertIn("6,562.50", synthesis_text)
        self.assertIn("12,812.50", synthesis_text)
        self.assertIn("10.25%", synthesis_text)

        # 4. Validation of Policy Threshold & Governance Notice
        self.assertIn("50,000", synthesis_text)
        self.assertTrue("DESC ISR v3.1" in synthesis_text or "Tau-3" in synthesis_text)
        self.assertIn("QALA-CONFIRM-50K", synthesis_text)

        self.assertIn("completed", event_types)

    # -------------------------------------------------------------------------
    # TEST 5: Clinician Override Multi-Turn Workflow
    # -------------------------------------------------------------------------
    def test_05_clinician_override_workflow(self):
        """Verify valid clinician override releases safety gate, scrub claim, and signs audit ledger."""
        engine = OpenRouterAgentEngine(provider="deterministic")
        engine.set_agent("taryaq")

        prompt = "Patient prescribed كولشيسين and Clarithromycin, eGFR 22"
        events = list(engine.process_chat(
            prompt,
            override_token=VALID_OVERRIDE_TOKEN,
            override_rationale="Emergency ICU renal dialysis protocol Dr. Tariq DHA-P-44019"
        ))

        event_types = [e["type"] for e in events]
        self.assertIn("audit_committed", event_types)

        audit_ev = next(e for e in events if e["type"] == "audit_committed")
        self.assertEqual(audit_ev["state"], "COMMITTED")
        self.assertEqual(len(audit_ev["signature"]), 64)

        # Verify streamed synthesis explains the approval
        synthesis_text = "".join(e["content"] for e in events if e["type"] == "token")
        self.assertIn("Approved with Clinician Override", synthesis_text)
        self.assertIn(VALID_OVERRIDE_TOKEN, synthesis_text)

    # -------------------------------------------------------------------------
    # TEST 6: Cyrillic/Hiragana Script Leak Defense
    # -------------------------------------------------------------------------
    def test_06_cyrillic_script_leak_defense(self):
        """Verify Cyrillic input leaks do not crash C99 and are safely handled."""
        engine = OpenRouterAgentEngine(provider="deterministic")
        engine.set_agent("taryaq")

        # Cyrillic drug name input
        cyrillic_prompt = "Пациент принимает колхицин 0.5мг и кларитромицин"
        self.assertTrue(has_unauthorized_script(cyrillic_prompt))
        self.assertIn("Cyrillic", detect_unauthorized_scripts(cyrillic_prompt))

        # Engine execution must not raise an unhandled exception
        events = list(engine.process_chat(cyrillic_prompt))
        self.assertTrue(len(events) > 0)
        self.assertEqual(events[-1]["type"], "completed")

    # -------------------------------------------------------------------------
    # TEST 7: HTTP SSE Streaming Endpoint Integration
    # -------------------------------------------------------------------------
    def test_07_http_sse_streaming_endpoint(self):
        """Verify HTTP POST /api/chat streams Server-Sent Events with multi-turn synthesis."""
        url = f"http://{DEFAULT_HOST}:{self.port}/api/chat"

        # 1. Casual stream test
        casual_payload = json.dumps({"message": "مرحبا", "agent": "taryaq"}).encode("utf-8")
        req_casual = urllib.request.Request(url, data=casual_payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req_casual, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            raw = resp.read().decode("utf-8")
            self.assertIn('"type": "token"', raw)
            self.assertIn('"intent": "CASUAL_GREETING_ROUTED"', raw)
            self.assertIn("data: [DONE]", raw)

        # 2. Fatal contraindication stream test
        fatal_payload = json.dumps({
            "message": "Patient prescribed كولشيسين and Clarithromycin, eGFR 22",
            "agent": "taryaq"
        }).encode("utf-8")
        req_fatal = urllib.request.Request(url, data=fatal_payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req_fatal, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            raw = resp.read().decode("utf-8")
            self.assertIn('"type": "c99_execution"', raw)
            self.assertIn('"type": "security_block"', raw)
            self.assertIn('"type": "token"', raw)
            self.assertIn("CYP3A4", raw)
            self.assertIn("data: [DONE]", raw)


if __name__ == "__main__":
    unittest.main()
