#!/usr/bin/env python3
"""
tests/test_rag_runtime_integration.py - Verification Suite for Dynamic RAG Runtime Integration
Dubai AI Agents Championship 2026-2027 (Pillar 1: Authoritative Dynamic RAG Runtime)

Milestone: SPRINT-12 (M-12)
Founder & Principal Systems Architect: Mohamed Fathy, BPharm
Architectural Blueprint: docs/PHASE_1_ARCHITECTURE_AND_SCHEMAS.md

Validates:
- Test 1: `rag_search` tool execution via `bridge/openrouter_client.py`:
          - Argument schema validation and domain filtering (CLINICAL, CUSTOMS, CIVIC, ALL).
          - FTS5 BM25 ranked retrieval from corpus/rag_master.db.
          - Cryptographic SHA-256 verification on all returned chunks.
- Test 2: Taryaq clinical query returns `DRUG_MONOGRAPHS_SOVEREIGN_CATALOG:COLCHICINE_MONOGRAPH`
          with verified passage SHA-256 and Turn 2 citation in synthesis.
- Test 3: Qala customs query returns `DUBAI-CUSTOMS-TARIFF-2026:Article 1`
          and landed tax calculation (5% duty + 5% import VAT = 10.25% landed tax).
- Test 4: Nibras civic query returns `DLD-EJARI-DECREE-43-2013:Article 1`
          rent increase tiers (Tiers 1-5 under Decree 43/2013).
- Test 5: End-to-end SSE chat stream over HTTP POST `/api/chat` returns `rag_retrieval`
          events followed by streamed synthesis and final `data: [DONE]`.
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

from bridge.openrouter_client import (
    OpenRouterAgentEngine,
    AGENT_TOOLS,
    RAG_MASTER_DB_PATH,
    _execute_rag_tool,
    VALID_OVERRIDE_TOKEN,
    _consumed_override_tokens,
)
from bridge.server import ChampionshipRequestHandler, ThreadingHTTPServer, DEFAULT_HOST


class TestRAGRuntimeIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure test audit key for ledger signing
        cls._orig_audit_key = os.environ.get("TARYAQ_AUDIT_KEY")
        os.environ["TARYAQ_AUDIT_KEY"] = "test-key-32-bytes-minimum-phase2-rag-00"

        # Verify RAG Master DB exists; auto-ingest if running in clean/CI environment
        if not os.path.exists(RAG_MASTER_DB_PATH):
            from scripts.ingest_rag_corpus import ingest_corpus
            ingest_corpus(reingest=True)

        # Start ephemeral HTTP/SSE server on dedicated port for endpoint validation
        cls.port = 8833
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
    # TEST 1: rag_search Tool Execution via bridge/openrouter_client.py
    # -------------------------------------------------------------------------
    def test_01_rag_search_tool_execution(self):
        """Verify rag_search tool schema, domain filtering, limit enforcement, and SHA-256 verification."""
        # 1. Verify tool registration in AGENT_TOOLS
        tool_names = [t["function"]["name"] for t in AGENT_TOOLS]
        self.assertIn("rag_search", tool_names, "rag_search tool not registered in AGENT_TOOLS")

        rag_spec = next(t["function"] for t in AGENT_TOOLS if t["function"]["name"] == "rag_search")
        self.assertIn("query", rag_spec["parameters"]["required"])
        self.assertIn("domain", rag_spec["parameters"]["properties"])
        self.assertIn("limit", rag_spec["parameters"]["properties"])

        engine = OpenRouterAgentEngine(provider="deterministic")

        # 2. Clinical query with domain filter
        res_clin = engine._execute_rag_tool({
            "query": "Colchicine CYP3A4",
            "domain": "CLINICAL",
            "limit": 3
        })
        self.assertEqual(res_clin["status"], "SUCCESS")
        self.assertEqual(res_clin["domain"], "CLINICAL")
        self.assertGreater(res_clin["count"], 0)
        self.assertLessEqual(res_clin["count"], 3)
        self.assertTrue(all(c["domain"] == "CLINICAL" for c in res_clin["chunks"]))

        # Verify chunk structure and SHA-256 cryptographic digest
        chunk0 = res_clin["chunks"][0]
        for field in ("chunk_id", "doc_id", "domain", "section_code", "title", "passage", "passage_sha256", "token_count", "rank"):
            self.assertIn(field, chunk0)
        computed_sha = hashlib.sha256(chunk0["passage"].encode("utf-8")).hexdigest()
        self.assertEqual(chunk0["passage_sha256"], computed_sha)

        # 3. Customs domain query
        res_customs = engine._execute_rag_tool({
            "query": "customs duty rate CIF",
            "domain": "CUSTOMS",
            "limit": 2
        })
        self.assertEqual(res_customs["status"], "SUCCESS")
        self.assertEqual(res_customs["domain"], "CUSTOMS")
        self.assertGreater(res_customs["count"], 0)
        self.assertTrue(all(c["domain"] == "CUSTOMS" for c in res_customs["chunks"]))

        # 4. Civic domain query
        res_civic = engine._execute_rag_tool({
            "query": "Ejari rental index increase",
            "domain": "CIVIC",
            "limit": 2
        })
        self.assertEqual(res_civic["status"], "SUCCESS")
        self.assertEqual(res_civic["domain"], "CIVIC")
        self.assertGreater(res_civic["count"], 0)
        self.assertTrue(all(c["domain"] == "CIVIC" for c in res_civic["chunks"]))

        # 5. ALL / None domain query
        res_all = engine._execute_rag_tool({
            "query": "tariff or prescription or rent",
            "domain": "ALL",
            "limit": 5
        })
        self.assertEqual(res_all["status"], "SUCCESS")
        self.assertGreater(res_all["count"], 0)

        # 6. Limit parameter enforcement
        res_limit1 = engine._execute_rag_tool({
            "query": "Colchicine",
            "limit": 1
        })
        self.assertEqual(res_limit1["count"], 1)

        # 7. Empty query handling
        res_empty = engine._execute_rag_tool({"query": "   "})
        self.assertEqual(res_empty["status"], "EMPTY_QUERY")
        self.assertEqual(res_empty["count"], 0)

        # 8. Execution through _execute_c99_tool dispatcher
        res_disp = engine._execute_c99_tool("rag_search", {
            "query": "Colchicine",
            "domain": "CLINICAL",
            "limit": 1
        })
        self.assertEqual(res_disp["status"], "SUCCESS")
        self.assertEqual(res_disp["count"], 1)

    # -------------------------------------------------------------------------
    # TEST 2: Taryaq Clinical Query Returns Monograph with Passage SHA-256
    # -------------------------------------------------------------------------
    def test_02_taryaq_clinical_query_rag_retrieval(self):
        """Verify Taryaq clinical query returns COLCHICINE_MONOGRAPH with passage SHA-256 and Turn 2 citation."""
        engine = OpenRouterAgentEngine(provider="deterministic")
        engine.set_agent("taryaq")

        prompt = "Patient Ahmed presented with acute gout flare. Prescribed Colchicine and Clarithromycin, lab report shows eGFR 22 mL/min/1.73m²"
        events = list(engine.process_chat(prompt))

        event_types = [e["type"] for e in events]
        self.assertIn("rag_retrieval", event_types, "rag_retrieval event missing from Taryaq chat stream")

        rag_ev = next(e for e in events if e["type"] == "rag_retrieval")
        self.assertIn("chunks", rag_ev)
        chunks = rag_ev["chunks"]
        self.assertGreater(len(chunks), 0)

        # Verify COLCHICINE_MONOGRAPH was returned
        colch_chunk = next((c for c in chunks if "COLCHICINE" in c["section_code"]), None)
        self.assertIsNotNone(colch_chunk, "COLCHICINE_MONOGRAPH chunk not retrieved in RAG search")
        self.assertEqual(colch_chunk["doc_id"], "DRUG_MONOGRAPHS_SOVEREIGN_CATALOG")
        self.assertEqual(colch_chunk["section_code"], "COLCHICINE_MONOGRAPH")

        # Verify cryptographic SHA-256 of passage
        expected_sha = hashlib.sha256(colch_chunk["passage"].encode("utf-8")).hexdigest()
        self.assertEqual(colch_chunk["passage_sha256"], expected_sha)
        self.assertEqual(len(colch_chunk["passage_sha256"]), 64)

        # Verify Turn 2 synthesis streamed tokens explicitly cite document ID, section, and SHA-256
        synthesis_text = "".join(e["content"] for e in events if e["type"] == "token")
        self.assertIn("DRUG_MONOGRAPHS_SOVEREIGN_CATALOG:COLCHICINE_MONOGRAPH", synthesis_text)
        self.assertIn(f"sha256:{expected_sha[:16]}", synthesis_text)
        self.assertIn("CRITICAL CLINICAL CONTRAINDICATION", synthesis_text)
        self.assertIn("CYP3A4", synthesis_text)
        self.assertIn("P-glycoprotein", synthesis_text)
        self.assertIn("22.0 mL/min", synthesis_text)

    # -------------------------------------------------------------------------
    # TEST 3: Qala Customs Query Returns Tariff Article 1 & Landed Tax
    # -------------------------------------------------------------------------
    def test_03_qala_customs_query_rag_retrieval_and_landed_tax(self):
        """Verify Qala customs query returns DUBAI-CUSTOMS-TARIFF-2026:Article 1 and landed tax calculation."""
        engine = OpenRouterAgentEngine(provider="deterministic")
        engine.set_agent("qala")

        prompt = "Initiate automated customs settlement clearance for DP World Jebel Ali container shipment #DPW-DXB-88301 with transaction value AED 125,000.00 under Dubai Customs Tariff"
        events = list(engine.process_chat(prompt))

        event_types = [e["type"] for e in events]
        self.assertIn("rag_retrieval", event_types, "rag_retrieval event missing from Qala chat stream")

        rag_ev = next(e for e in events if e["type"] == "rag_retrieval")
        chunks = rag_ev["chunks"]
        self.assertGreater(len(chunks), 0)

        # Verify Article 1 of DUBAI-CUSTOMS-TARIFF-2026 was returned
        tariff_chunk = next((c for c in chunks if c["section_code"] == "Article 1" and c["doc_id"] == "DUBAI-CUSTOMS-TARIFF-2026"), None)
        self.assertIsNotNone(tariff_chunk, "DUBAI-CUSTOMS-TARIFF-2026:Article 1 not retrieved in RAG search")

        expected_sha = hashlib.sha256(tariff_chunk["passage"].encode("utf-8")).hexdigest()
        self.assertEqual(tariff_chunk["passage_sha256"], expected_sha)
        self.assertEqual(len(tariff_chunk["passage_sha256"]), 64)

        # Verify Turn 2 synthesis streamed tokens explicitly cite Article 1 with SHA-256 and landed tax
        synthesis_text = "".join(e["content"] for e in events if e["type"] == "token")
        self.assertIn("DUBAI-CUSTOMS-TARIFF-2026:Article 1", synthesis_text)
        self.assertIn(f"sha256:{expected_sha[:16]}", synthesis_text)

        # Landed Tax Math Verification:
        # CIF: AED 125,000.00
        # Customs Duty (5%): AED 6,250.00
        # VAT (5% on CIF+Duty): AED 6,562.50
        # Total Landed Tax: AED 12,812.50 (10.25% landed tax rate)
        # Total Landed Cost: AED 137,812.50
        self.assertIn("125,000.00", synthesis_text)
        self.assertIn("6,250.00", synthesis_text)
        self.assertIn("6,562.50", synthesis_text)
        self.assertIn("12,812.50", synthesis_text)
        self.assertIn("10.25%", synthesis_text)
        self.assertIn("137,812.50", synthesis_text)

    # -------------------------------------------------------------------------
    # TEST 4: Nibras Civic Query Returns Ejari Decree 43/2013 Rent Increase Tiers
    # -------------------------------------------------------------------------
    def test_04_nibras_civic_query_rag_retrieval_and_ejari_tiers(self):
        """Verify Nibras civic query returns DLD-EJARI-DECREE-43-2013:Article 1 and explains rent increase tiers."""
        engine = OpenRouterAgentEngine(provider="deterministic")
        engine.set_agent("nibras")

        prompt = "صاحب الشقة رفع عليا الايجار 20%، هل هذا قانوني وفق مرسوم إيجاري رقم 43 لسنة 2013 الصادر عن دائرة الأراضي والأملاك؟"
        events = list(engine.process_chat(prompt))

        event_types = [e["type"] for e in events]
        self.assertIn("rag_retrieval", event_types, "rag_retrieval event missing from Nibras chat stream")

        rag_ev = next(e for e in events if e["type"] == "rag_retrieval")
        chunks = rag_ev["chunks"]
        self.assertGreater(len(chunks), 0)

        # Verify DLD-EJARI-DECREE-43-2013 chunks were returned
        ejari_chunks = [c for c in chunks if c["doc_id"] == "DLD-EJARI-DECREE-43-2013"]
        self.assertGreater(len(ejari_chunks), 0, "DLD-EJARI-DECREE-43-2013 chunks missing from retrieval")

        # Verify passage SHA-256 integrity
        for c in ejari_chunks:
            expected_sha = hashlib.sha256(c["passage"].encode("utf-8")).hexdigest()
            self.assertEqual(c["passage_sha256"], expected_sha)

        # Verify Turn 2 synthesis streamed tokens explicitly cite Decree 43/2013 Article 1 with SHA-256
        synthesis_text = "".join(e["content"] for e in events if e["type"] == "token")
        self.assertIn("DLD-EJARI-DECREE-43-2013", synthesis_text)
        self.assertIn("Decree No. 43 of 2013", synthesis_text)
        self.assertIn("Article 1", synthesis_text)

        # Verify that all 5 statutory rent increase tiers are detailed:
        # Tier 1: 0% Increase (up to 10% below market)
        # Tier 2: 5% Increase (11% to 20% below market)
        # Tier 3: 10% Increase (21% to 30% below market)
        # Tier 4: 15% Increase (31% to 40% below market)
        # Tier 5: 20% Increase (> 40% below market)
        self.assertIn("Tier 1", synthesis_text)
        self.assertIn("Tier 2", synthesis_text)
        self.assertIn("Tier 3", synthesis_text)
        self.assertIn("Tier 4", synthesis_text)
        self.assertIn("Tier 5", synthesis_text)
        self.assertIn("0%", synthesis_text)
        self.assertIn("5%", synthesis_text)
        self.assertIn("10%", synthesis_text)
        self.assertIn("15%", synthesis_text)
        self.assertIn("20%", synthesis_text)

        # Verify notice requirement mention
        self.assertIn("90", synthesis_text)

    # -------------------------------------------------------------------------
    # TEST 5: End-to-End SSE Chat Stream over /api/chat Returns RAG Events
    # -------------------------------------------------------------------------
    def test_05_http_sse_chat_stream_rag_retrieval(self):
        """Verify HTTP POST /api/chat streams rag_retrieval events followed by streamed synthesis."""
        url = f"http://{DEFAULT_HOST}:{self.port}/api/chat"

        # 1. Clinical query over SSE
        payload = json.dumps({
            "message": "Patient Ahmed prescribed Colchicine 0.5mg and Clarithromycin 500mg, eGFR 22 mL/min",
            "agent": "taryaq"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")

        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/event-stream", resp.headers.get("Content-Type", ""))
            raw_data = resp.read().decode("utf-8")

        # Parse SSE lines
        sse_events = []
        for line in raw_data.split("\n"):
            line = line.strip()
            if line.startswith("data: "):
                event_data = line[len("data: "):]
                if event_data == "[DONE]":
                    sse_events.append({"type": "done"})
                else:
                    try:
                        sse_events.append(json.loads(event_data))
                    except Exception:
                        pass

        sse_types = [e.get("type") for e in sse_events]
        self.assertIn("rag_retrieval", sse_types, "rag_retrieval event missing from HTTP SSE stream")
        self.assertIn("token", sse_types, "token events missing from HTTP SSE stream")
        self.assertIn("done", sse_types, "[DONE] closing frame missing from HTTP SSE stream")

        # Verify rag_retrieval frame contents
        rag_frame = next(e for e in sse_events if e.get("type") == "rag_retrieval")
        self.assertIn("chunks", rag_frame)
        self.assertGreater(len(rag_frame["chunks"]), 0)
        c0 = rag_frame["chunks"][0]
        self.assertIn("chunk_id", c0)
        self.assertIn("passage_sha256", c0)
        self.assertEqual(len(c0["passage_sha256"]), 64)

        # Verify streamed synthesis text contains SHA-256 citation
        synthesis_streamed = "".join(e.get("content", "") for e in sse_events if e.get("type") == "token")
        self.assertIn("DRUG_MONOGRAPHS_SOVEREIGN_CATALOG:COLCHICINE_MONOGRAPH", synthesis_streamed)
        self.assertIn("sha256:", synthesis_streamed)


if __name__ == "__main__":
    unittest.main()
