#!/usr/bin/env python3
"""
tests/test_airlock_engine.py - Verification Suite for Curated Web Research Airlock Engine
Dubai AI Agents Championship 2026-2027 (Pillar 2: Curated Web Research Airlock)

Milestone: SPRINT-13 (M-13)
Founder & Principal Systems Architect: Mohamed Fathy, BPharm
Architectural Blueprint: docs/PHASE_1_ARCHITECTURE_AND_SCHEMAS.md

Test Coverage:
- Test 1: Whitelist security enforcement:
          - Validates that approved domains and paths are permitted.
          - Blocks non-whitelisted domains (google.com, bing.com, arbitrary IPs) with AirlockSecurityViolation.
          - Blocks unauthorized endpoints on whitelisted domains.
- Test 2: PubMed E-Utilities execution, SHA-256 digest computation, and database audit logging.
- Test 3: OpenFDA drug label query and automatic insertion into airlock_quarantine with STAGED status.
- Test 4: HITL review lifecycle (approve/reject quarantine item updates airlock_quarantine).
- Test 5: End-to-end SSE `/api/chat` returns `airlock_retrieval` followed by Stage 2 clinical synthesis
          citing PubMed/OpenFDA provenance and exact 16-character SHA-256 prefix.
- Test 6: Offline cable-pull fixture fallback resilience.
"""

import os
import sys
import time
import json
import hashlib
import unittest
import threading
import urllib.request
import urllib.error

# Ensure project root is in python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bridge.airlock import (
    validate_airlock_target,
    validate_airlock_url,
    AirlockSecurityViolation,
    query_pubmed,
    query_openfda,
    execute_airlock_research,
    list_quarantine_items,
    review_quarantine_item,
    WHITELIST_DOMAINS,
    AUTHORITY_MAP,
    AIRLOCK_LEDGER_DB_PATH
)
from bridge.openrouter_client import (
    OpenRouterAgentEngine,
    AGENT_TOOLS,
    _execute_airlock_tool,
    VALID_OVERRIDE_TOKEN,
    _consumed_override_tokens
)
from bridge.server import ChampionshipRequestHandler, ThreadingHTTPServer, DEFAULT_HOST


class TestAirlockEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure test audit key for ledger HMAC signing
        cls._orig_audit_key = os.environ.get("TARYAQ_AUDIT_KEY")
        os.environ["TARYAQ_AUDIT_KEY"] = "test-key-32-bytes-minimum-phase3-airlock-00"

        # Dedicated test database path to avoid polluting production airlock ledger
        cls.test_db_dir = os.path.join(PROJECT_ROOT, "build")
        os.makedirs(cls.test_db_dir, exist_ok=True)
        cls.test_db_path = os.path.join(cls.test_db_dir, "test_airlock_ledger.db")
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)

        # Initialize test airlock ledger schema
        from scripts.init_phase1_schemas import init_airlock_ledger
        init_airlock_ledger(cls.test_db_path, reset=True)

        # Start ephemeral HTTP/SSE server on dedicated port for endpoint validation
        cls.port = 8844
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
        """Reset state before each test."""
        _consumed_override_tokens.clear()

    # -------------------------------------------------------------------------
    # TEST 1: Whitelist Security Enforcement
    # -------------------------------------------------------------------------
    def test_01_whitelist_security_enforcement(self):
        """Verify that strictly whitelisted domains and paths are permitted and unauthorized hosts/endpoints are blocked."""
        # 1. Permitted targets must not raise
        permitted_cases = [
            ("ncbi.nlm.nih.gov", "/entrez/eutils/esearch.fcgi?db=pubmed&term=colchicine"),
            ("ncbi.nlm.nih.gov", "/entrez/eutils/efetch.fcgi?db=pubmed&id=21543424"),
            ("api.fda.gov", "/drug/label.json?search=colchicine"),
            ("api.fda.gov", "/drug/event.json?search=patient.drug"),
            ("api.fda.gov", "/drug/enforcement.json"),
            ("who.int", "/entity/medicines/safety_alerts/"),
            ("who.int", "/news/item/2026"),
            ("mohap.gov.ae", "/en/services/pharmacy-licensing"),
            ("mohap.gov.ae", "/ar/services/drugs"),
            ("dha.gov.ae", "/en/HealthRegulation/circulars"),
            ("dha.gov.ae", "/ar/HealthRegulation/circulars"),
            ("dubaicustoms.gov.ae", "/en/CustomsTariff/search"),
            ("dubaicustoms.gov.ae", "/ar/CustomsTariff/search"),
        ]
        for domain, path in permitted_cases:
            try:
                validate_airlock_target(domain, path)
            except AirlockSecurityViolation as e:
                self.fail(f"Legitimate target '{domain}{path}' was blocked by whitelist: {e}")

        # 2. Block unauthorized domains
        blocked_domains = [
            ("google.com", "/search?q=colchicine"),
            ("bing.com", "/search?q=clarithromycin"),
            ("malicious-exfiltration-c2.net", "/data"),
            ("192.168.1.100", "/admin"),
            ("api.openai.com", "/v1/chat/completions"),
            ("raw.githubusercontent.com", "/exploit"),
        ]
        for domain, path in blocked_domains:
            with self.assertRaises(AirlockSecurityViolation, msg=f"Domain '{domain}' should have been blocked!"):
                validate_airlock_target(domain, path)

        # 3. Block unauthorized paths on whitelisted domains
        blocked_paths = [
            ("ncbi.nlm.nih.gov", "/admin/system/dump"),
            ("ncbi.nlm.nih.gov", "/login"),
            ("api.fda.gov", "/food/enforcement.json"),
            ("api.fda.gov", "/device/recall.json"),
            ("api.fda.gov", "/private/admin"),
            ("dubaicustoms.gov.ae", "/internal/payment_keys"),
            ("who.int", "/secret/leaks"),
        ]
        for domain, path in blocked_paths:
            with self.assertRaises(AirlockSecurityViolation, msg=f"Path '{path}' on '{domain}' should have been blocked!"):
                validate_airlock_target(domain, path)

        # 4. execute_airlock_research with unknown authority
        with self.assertRaises(AirlockSecurityViolation):
            execute_airlock_research(authority="GOOGLE_SEARCH", query="colchicine", trigger_reason="TEST")

    # -------------------------------------------------------------------------
    # TEST 2: PubMed E-Utilities Execution & Cryptographic Audit
    # -------------------------------------------------------------------------
    def test_02_pubmed_eutilities_execution_and_audit(self):
        """Verify PubMed E-Utilities execution, cryptographic SHA-256 digest computation, and airlock ledger audit."""
        res = query_pubmed(
            term="Colchicine Clarithromycin renal failure fatal",
            max_results=3,
            agent_id="TARYAQ",
            trigger_reason="DDI_UNMODELED_CLARITHROMYCIN_VERIFICATION",
            offline_mode=True,
            db_path=self.test_db_path
        )

        # Validate response payload structure
        self.assertIn(res["status"], ("SUCCESS", "AIRGAP_FIXTURE_SUCCESS"))
        self.assertEqual(res["authority"], "PUBMED")
        self.assertEqual(res["target_domain"], "ncbi.nlm.nih.gov")
        self.assertEqual(res["endpoint_path"], "/entrez/eutils/esearch.fcgi")
        self.assertIn("21543424", res["pmids"])
        self.assertIn("Fatal colchicine toxicity", res["title"])
        self.assertEqual(len(res["payload_sha256"]), 64)

        # Verify audit records in SQLite ledger
        from scripts.init_phase1_schemas import get_db_connection
        conn = get_db_connection(self.test_db_path)
        try:
            # 1. Request audit check
            req_row = conn.execute(
                "SELECT * FROM airlock_requests WHERE request_id = ?",
                (res["request_id"],)
            ).fetchone()
            self.assertIsNotNone(req_row, "Request record missing from airlock_requests")
            self.assertEqual(req_row["agent_id"], "TARYAQ")
            self.assertEqual(req_row["target_domain"], "ncbi.nlm.nih.gov")
            self.assertEqual(req_row["trigger_reason"], "DDI_UNMODELED_CLARITHROMYCIN_VERIFICATION")

            # 2. Response audit check and SHA-256 verification
            resp_row = conn.execute(
                "SELECT * FROM airlock_responses WHERE response_id = ?",
                (res["response_id"],)
            ).fetchone()
            self.assertIsNotNone(resp_row, "Response record missing from airlock_responses")
            self.assertEqual(resp_row["http_status"], 200)

            # Cryptographically verify that stored payload_sha256 matches actual sha256 of payload_raw
            raw_blob = resp_row["payload_raw"]
            computed_sha = hashlib.sha256(raw_blob).hexdigest()
            self.assertEqual(computed_sha, resp_row["payload_sha256"])
            self.assertEqual(computed_sha, res["payload_sha256"])

            # 3. Quarantine staging check
            q_row = conn.execute(
                "SELECT * FROM airlock_quarantine WHERE quarantine_id = ?",
                (res["quarantine_id"],)
            ).fetchone()
            self.assertIsNotNone(q_row, "Quarantine entry missing from airlock_quarantine")
            self.assertEqual(q_row["status"], "STAGED")
            self.assertEqual(q_row["target_table"], "taryaq_clinical_evidence")
            self.assertEqual(q_row["reviewer_role"], "LICENSED_CLINICAL_PHARMACIST")
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # TEST 3: OpenFDA Drug Label Query & Quarantine Staging
    # -------------------------------------------------------------------------
    def test_03_openfda_drug_label_quarantine_staging(self):
        """Verify OpenFDA drug label query and automatic insertion into airlock_quarantine with STAGED status."""
        res = query_openfda(
            drug_name="Colchicine",
            agent_id="TARYAQ",
            trigger_reason="BOXED_WARNING_CYP3A4_CONTRAINDICATION",
            offline_mode=True,
            db_path=self.test_db_path
        )

        self.assertIn(res["status"], ("SUCCESS", "AIRGAP_FIXTURE_SUCCESS"))
        self.assertEqual(res["authority"], "OPENFDA")
        self.assertEqual(res["target_domain"], "api.fda.gov")
        self.assertEqual(res["endpoint_path"], "/drug/label.json")
        self.assertTrue(len(res["boxed_warning"]) > 0)
        self.assertIn("FATAL COLCHICINE TOXICITY", res["boxed_warning"])
        self.assertEqual(len(res["payload_sha256"]), 64)

        from scripts.init_phase1_schemas import get_db_connection
        conn = get_db_connection(self.test_db_path)
        try:
            q_row = conn.execute(
                "SELECT * FROM airlock_quarantine WHERE quarantine_id = ?",
                (res["quarantine_id"],)
            ).fetchone()
            self.assertIsNotNone(q_row)
            self.assertEqual(q_row["status"], "STAGED")
            self.assertEqual(q_row["target_table"], "taryaq_ddi_rules")
            self.assertEqual(q_row["reviewer_role"], "LICENSED_CLINICAL_PHARMACIST")

            extracted = json.loads(q_row["extracted_data_json"])
            self.assertEqual(extracted["generic_name"], "COLCHICINE")
            self.assertIn("FATAL COLCHICINE TOXICITY", extracted["boxed_warning"])
        finally:
            conn.close()

    # -------------------------------------------------------------------------
    # TEST 4: HITL Review Lifecycle (Approve / Reject via API)
    # -------------------------------------------------------------------------
    def test_04_hitl_review_lifecycle(self):
        """Verify GET /api/airlock/quarantine and POST /api/airlock/review lifecycle."""
        # 1. Fetch staged items from server
        req_url = f"http://{DEFAULT_HOST}:{self.port}/api/airlock/quarantine"
        with urllib.request.urlopen(req_url, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))

        self.assertEqual(data["status"], "SUCCESS")
        self.assertIsInstance(data["quarantine"], list)

        # Stage an item directly in the active DB used by the server
        stage_res = query_openfda(
            drug_name="Colchicine",
            agent_id="TARYAQ",
            trigger_reason="HITL_REVIEW_TEST"
        )
        target_qid = stage_res["quarantine_id"]

        # 2. Review candidate as APPROVED
        review_payload = {
            "quarantine_id": target_qid,
            "status": "APPROVED",
            "notes": "Verified against British National Formulary (BNF 84) monograph on Colchicine-Macrolide toxicity.",
            "reviewer_role": "LICENSED_CLINICAL_PHARMACIST"
        }
        review_req = urllib.request.Request(
            f"http://{DEFAULT_HOST}:{self.port}/api/airlock/review",
            data=json.dumps(review_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(review_req, timeout=5) as resp_rev:
            self.assertEqual(resp_rev.status, 200)
            rev_data = json.loads(resp_rev.read().decode("utf-8"))

        self.assertEqual(rev_data["status"], "SUCCESS")
        self.assertEqual(rev_data["review"]["quarantine_id"], target_qid)
        self.assertEqual(rev_data["review"]["status"], "APPROVED")
        self.assertIsNotNone(rev_data["review"]["reviewed_at"])

        # 3. Test REJECTED lifecycle on another item
        stage_res2 = query_pubmed(
            term="Unapproved Research Topic",
            agent_id="TARYAQ",
            trigger_reason="HITL_REJECT_TEST"
        )
        target_qid2 = stage_res2["quarantine_id"]
        reject_payload = {
            "quarantine_id": target_qid2,
            "status": "REJECTED",
            "notes": "Rejected by pharmacist: Insufficient evidence quality.",
            "reviewer_role": "LICENSED_CLINICAL_PHARMACIST"
        }
        reject_req = urllib.request.Request(
            f"http://{DEFAULT_HOST}:{self.port}/api/airlock/review",
            data=json.dumps(reject_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(reject_req, timeout=5) as resp_rej:
            self.assertEqual(resp_rej.status, 200)
            rej_data = json.loads(resp_rej.read().decode("utf-8"))

        self.assertEqual(rej_data["review"]["status"], "REJECTED")

        # 4. Test error handling (invalid status, missing ID)
        bad_req = urllib.request.Request(
            f"http://{DEFAULT_HOST}:{self.port}/api/airlock/review",
            data=json.dumps({"quarantine_id": target_qid, "status": "INVALID_STATUS"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(bad_req, timeout=5)
        self.assertEqual(ctx.exception.code, 400)

        missing_id_req = urllib.request.Request(
            f"http://{DEFAULT_HOST}:{self.port}/api/airlock/review",
            data=json.dumps({"status": "APPROVED"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx2:
            urllib.request.urlopen(missing_id_req, timeout=5)
        self.assertEqual(ctx2.exception.code, 400)

    # -------------------------------------------------------------------------
    # TEST 5: End-to-End SSE /api/chat with Airlock Retrieval & Provenance Synthesis
    # -------------------------------------------------------------------------
    def test_05_sse_chat_airlock_retrieval_and_provenance(self):
        """Verify SSE /api/chat returns airlock_retrieval event followed by Stage 2 clinical synthesis citing PubMed/OpenFDA."""
        chat_req_data = {
            "message": "Retrieve PubMed peer-reviewed literature evidence and OpenFDA boxed warning for Colchicine and Clarithromycin drug interaction in severe renal impairment.",
            "agent": "taryaq"
        }
        req = urllib.request.Request(
            f"http://{DEFAULT_HOST}:{self.port}/api/chat",
            data=json.dumps(chat_req_data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/event-stream", resp.headers.get("Content-Type", ""))

            events = []
            tokens = []
            done_received = False

            for raw_line in resp:
                line = raw_line.decode("utf-8").strip()
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    done_received = True
                    break
                try:
                    ev = json.loads(data_str)
                    events.append(ev)
                    if ev.get("type") == "token":
                        tokens.append(ev.get("content", ""))
                except Exception:
                    pass

        self.assertTrue(done_received, "Stream failed to emit closing data: [DONE]")

        event_types = [e.get("type") for e in events]
        self.assertIn("pii_scrubbed", event_types)
        self.assertIn("tool_call", event_types)
        self.assertIn("airlock_retrieval", event_types)
        self.assertIn("token", event_types)
        self.assertIn("completed", event_types)

        # Inspect airlock_retrieval event
        airlock_ev = next(e for e in events if e.get("type") == "airlock_retrieval")
        self.assertIn(airlock_ev.get("authority"), ("PUBMED", "OPENFDA"))
        self.assertEqual(len(airlock_ev.get("payload_sha256", "")), 64)
        self.assertTrue(len(airlock_ev.get("quarantine_id", "")) > 0)
        self.assertEqual(airlock_ev.get("status"), "STAGED")

        # Inspect Stage 2 clinical synthesis tokens for provenance citations
        full_text = "".join(tokens)
        self.assertTrue(len(full_text) > 50)
        # Verify statutory / airlock citation format: [AUTHORITY:... | sha256:PREFIX]
        self.assertIn("sha256:", full_text)
        expected_prefix = airlock_ev["payload_sha256"][:16]
        self.assertIn(expected_prefix, full_text, f"Expected 16-char SHA prefix {expected_prefix} in synthesis")
        self.assertIn(airlock_ev["quarantine_id"], full_text)

    # -------------------------------------------------------------------------
    # TEST 6: Offline Cable-Pull Fixture Fallback Resilience
    # -------------------------------------------------------------------------
    def test_06_offline_cable_pull_fixture_resilience(self):
        """Verify offline cable-pull resilience: deterministic fixtures served with valid cryptographic digests."""
        os.environ["AIRLOCK_OFFLINE"] = "1"
        try:
            # 1. PubMed in forced offline mode
            res_pm = query_pubmed(
                term="Colchicine Gout",
                agent_id="TARYAQ",
                trigger_reason="OFFLINE_TEST",
                offline_mode=True,
                db_path=self.test_db_path
            )
            self.assertEqual(res_pm["status"], "AIRGAP_FIXTURE_SUCCESS")
            self.assertTrue(res_pm["is_offline_fixture"])
            self.assertEqual(len(res_pm["payload_sha256"]), 64)
            self.assertIn("21543424", res_pm["pmids"])

            # 2. OpenFDA in forced offline mode
            res_fda = query_openfda(
                drug_name="Colchicine",
                agent_id="TARYAQ",
                trigger_reason="OFFLINE_TEST",
                offline_mode=True,
                db_path=self.test_db_path
            )
            self.assertEqual(res_fda["status"], "AIRGAP_FIXTURE_SUCCESS")
            self.assertTrue(res_fda["is_offline_fixture"])
            self.assertEqual(len(res_fda["payload_sha256"]), 64)
            self.assertIn("FATAL COLCHICINE TOXICITY", res_fda["boxed_warning"])

            # 3. Dubai Customs & WHO generic authorities in forced offline mode
            res_customs = execute_airlock_research(
                authority="DUBAI_CUSTOMS",
                query="HS 3004.90.00",
                trigger_reason="TARIFF_EXEMPTION_CHECK",
                db_path=self.test_db_path
            )
            self.assertEqual(res_customs["status"], "AIRGAP_FIXTURE_SUCCESS")
            self.assertEqual(len(res_customs["payload_sha256"]), 64)
            self.assertIn("3004.90.00", res_customs["extracted_data"].get("hs_code", ""))

            res_who = execute_airlock_research(
                authority="WHO",
                query="Counterfeit antibiotics",
                trigger_reason="WHO_MEDALERT_CHECK",
                db_path=self.test_db_path
            )
            self.assertEqual(res_who["status"], "AIRGAP_FIXTURE_SUCCESS")
            self.assertEqual(len(res_who["payload_sha256"]), 64)

        finally:
            os.environ.pop("AIRLOCK_OFFLINE", None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
