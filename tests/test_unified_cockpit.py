#!/usr/bin/env python3
"""
tests/test_unified_cockpit.py - Triple-Agent Track Switcher & Unified Cockpit HUD Verification Battery
Sprint: SPRINT-16 (M-16)
Championship Arena: Dubai AI Agents Championship 2026-2027 (Dubai Future Foundation / DCDE)
Architectural Reference: Dubai Sovereign Statutory & Clinical Architecture (Taryaq, Qala, Nibras)

Deterministic Verification Suite (6 Authoritative Tests):
1. test_server_agent_active_default:
   Verifies default active agent returned by GET /api/agent/active is 'taryaq'.
2. test_server_agent_switching:
   Verifies switching across 'taryaq', 'qala', and 'nibras' via POST /api/agent/switch and error handling on invalid agents.
3. test_scenarios_categorization_and_filtering:
   Verifies GET /api/scenarios with ?agent=qala filters Qala-specific scenarios and categorizes all tracks when unfiltered.
4. test_cockpit_html_contains_all_three_dashboards:
   Verifies bridge/cockpit.html contains the persistent Primary Agent Switcher and dedicated markup for Taryaq, Qala Agency Mesh, and Nibras Civic Navigator.
5. test_qala_mesh_department_definitions:
   Verifies all 6 departmental specialists, the Managing Director orchestrator, Tau-3 FinOps Circuit Breaker, and Landed Tax Calculator are defined.
6. test_nibras_fademem_gauge_markup:
   Verifies FadeMem token reduction (>85%), Ebbinghaus decay curve (R = e^{-t/S}), Cognitive Friction Index, AES-256-GCM vault, and Ejari/DEWA calculators are defined.
"""

import os
import sys
import time
import json
import unittest
import threading
import urllib.request
import urllib.error

# Ensure project root is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bridge.server import (
    ThreadingHTTPServer,
    ChampionshipRequestHandler,
    DEFAULT_HOST
)
from bridge.openrouter_client import OpenRouterAgentEngine


class TestUnifiedCockpit(unittest.TestCase):
    """Authoritative test battery for Sprint-16 Triple-Agent Track Switcher & Unified Cockpit HUD."""

    @classmethod
    def setUpClass(cls):
        """Initialize test environment and start ephemeral test HTTP server."""
        cls.port = 8866
        ChampionshipRequestHandler.engine = OpenRouterAgentEngine(provider="deterministic")
        cls.server = ThreadingHTTPServer((DEFAULT_HOST, cls.port), ChampionshipRequestHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        """Shutdown test HTTP server cleanly."""
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=2.0)

    def setUp(self):
        """Reset active agent to default 'taryaq' before each test."""
        ChampionshipRequestHandler.engine.set_agent("taryaq")

    # -------------------------------------------------------------------------
    # Test 1: Default Active Agent
    # -------------------------------------------------------------------------
    def test_server_agent_active_default(self):
        """Verify GET /api/agent/active defaults to 'taryaq' societal track."""
        url = f"http://{DEFAULT_HOST}:{self.port}/api/agent/active"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("active_agent", data)
            self.assertEqual(data["active_agent"], "taryaq")

    # -------------------------------------------------------------------------
    # Test 2: Agent Switching REST Endpoints
    # -------------------------------------------------------------------------
    def test_server_agent_switching(self):
        """Verify POST /api/agent/switch across taryaq, qala, and nibras with state persistence."""
        base_url = f"http://{DEFAULT_HOST}:{self.port}"

        # 1. Switch to Qala (Business)
        switch_qala = urllib.request.Request(
            f"{base_url}/api/agent/switch",
            data=json.dumps({"agent": "qala"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(switch_qala, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["active_agent"], "qala")

        # Verify active agent query reflects Qala
        with urllib.request.urlopen(f"{base_url}/api/agent/active", timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(json.loads(resp.read().decode("utf-8"))["active_agent"], "qala")

        # 2. Switch to Nibras (Personal)
        switch_nibras = urllib.request.Request(
            f"{base_url}/api/agent/switch",
            data=json.dumps({"agent": "nibras"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(switch_nibras, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["active_agent"], "nibras")

        # Verify active agent query reflects Nibras
        with urllib.request.urlopen(f"{base_url}/api/agent/active", timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(json.loads(resp.read().decode("utf-8"))["active_agent"], "nibras")

        # 3. Switch back to Taryaq (Societal)
        switch_taryaq = urllib.request.Request(
            f"{base_url}/api/agent/switch",
            data=json.dumps({"agent": "taryaq"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(switch_taryaq, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["active_agent"], "taryaq")

        # Verify active agent query reflects Taryaq
        with urllib.request.urlopen(f"{base_url}/api/agent/active", timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(json.loads(resp.read().decode("utf-8"))["active_agent"], "taryaq")

        # 4. Error Handling: Invalid Agent should return 400 Bad Request
        bad_req = urllib.request.Request(
            f"{base_url}/api/agent/switch",
            data=json.dumps({"agent": "unsupported_unknown_agent"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(bad_req, timeout=5.0)
        self.assertEqual(ctx.exception.code, 400)

    # -------------------------------------------------------------------------
    # Test 3: Demonstration Scenarios Categorization & Filtering
    # -------------------------------------------------------------------------
    def test_scenarios_categorization_and_filtering(self):
        """Verify GET /api/scenarios?agent=qala filters Qala-specific scenarios and categorizes properly."""
        base_url = f"http://{DEFAULT_HOST}:{self.port}"

        # 1. Filtered by Qala
        req_qala = urllib.request.Request(f"{base_url}/api/scenarios?agent=qala")
        with urllib.request.urlopen(req_qala, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("scenarios", data)
            scenarios = data["scenarios"]
            self.assertGreaterEqual(len(scenarios), 1)
            for s in scenarios:
                self.assertEqual(s.get("agent"), "qala")

        # 2. Filtered by Taryaq
        req_taryaq = urllib.request.Request(f"{base_url}/api/scenarios?agent=taryaq")
        with urllib.request.urlopen(req_taryaq, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            scenarios = data["scenarios"]
            self.assertGreaterEqual(len(scenarios), 1)
            for s in scenarios:
                self.assertEqual(s.get("agent"), "taryaq")

        # 3. Filtered by Nibras
        req_nibras = urllib.request.Request(f"{base_url}/api/scenarios?agent=nibras")
        with urllib.request.urlopen(req_nibras, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            scenarios = data["scenarios"]
            self.assertGreaterEqual(len(scenarios), 1)
            for s in scenarios:
                self.assertEqual(s.get("agent"), "nibras")

        # 4. Unfiltered Master Scenario Query
        req_all = urllib.request.Request(f"{base_url}/api/scenarios")
        with urllib.request.urlopen(req_all, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("scenarios", data)
            self.assertIn("categorized", data)
            self.assertGreaterEqual(len(data["scenarios"]), 5)
            cat = data["categorized"]
            self.assertIn("taryaq", cat)
            self.assertIn("qala", cat)
            self.assertIn("nibras", cat)
            self.assertGreaterEqual(len(cat["taryaq"]), 2)
            self.assertGreaterEqual(len(cat["qala"]), 1)
            self.assertGreaterEqual(len(cat["nibras"]), 2)

    # -------------------------------------------------------------------------
    # Test 4: Cockpit HTML Contains All Three Dashboards
    # -------------------------------------------------------------------------
    def test_cockpit_html_contains_all_three_dashboards(self):
        """Verify bridge/cockpit.html contains persistent Primary Agent Switcher and markup for all 3 dashboards."""
        cockpit_path = os.path.join(PROJECT_ROOT, "bridge", "cockpit.html")
        self.assertTrue(os.path.exists(cockpit_path), f"File not found: {cockpit_path}")

        with open(cockpit_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Primary Switcher Bar
        self.assertIn("tab-taryaq", html)
        self.assertIn("tab-qala", html)
        self.assertIn("tab-nibras", html)
        self.assertIn("TARYAQ (Societal)", html)
        self.assertIn("QALA (Business)", html)
        self.assertIn("NIBRAS (Personal)", html)

        # Dashboard 1: TARYAQ
        self.assertIn('id="dashboard-taryaq"', html)
        self.assertIn("view-clinician", html)
        self.assertIn("view-pharmacist", html)
        self.assertIn("view-patient", html)

        # Dashboard 2: QALA
        self.assertIn('id="dashboard-qala"', html)
        self.assertIn("Corporate Agency Mesh", html)
        self.assertIn("Managing Director", html)

        # Dashboard 3: NIBRAS
        self.assertIn('id="dashboard-nibras"', html)
        self.assertIn("Dubai Civic Navigator", html)
        self.assertIn("FadeMem", html)

    # -------------------------------------------------------------------------
    # Test 5: Qala Agency Mesh Department Definitions
    # -------------------------------------------------------------------------
    def test_qala_mesh_department_definitions(self):
        """Verify all 6 departmental specialists, Tau-3 circuit breaker, and landed tax calculator are defined."""
        cockpit_path = os.path.join(PROJECT_ROOT, "bridge", "cockpit.html")
        with open(cockpit_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Managing Director (Head Executive Agent)
        self.assertIn("Managing Director", html)
        self.assertIn("Head Executive Agent", html)

        # 6 Departmental Specialists:
        # 1. Finance & FinOps
        self.assertIn("Finance &amp; FinOps", html)
        self.assertIn("UAE Corporate Tax 9%", html)
        self.assertIn("VAT 5%", html)
        self.assertIn("three-way invoice matching", html)

        # 2. Legal & Compliance
        self.assertIn("Legal &amp; Compliance", html)
        self.assertIn("DESC ISR v3.1 Path Sandbox", html)
        self.assertIn("contract compliance", html)

        # 3. Trade & Customs
        self.assertIn("Trade &amp; Customs", html)
        self.assertIn("Mirsal II 10.25% landed tax", html)
        self.assertIn("DP World container clearance status", html)

        # 4. HR & People Ops
        self.assertIn("HR &amp; People Ops", html)
        self.assertIn("UAE Labor Law Article 51 gratuity", html)
        self.assertIn("WPS tracking", html)

        # 5. Procure & Vendor
        self.assertIn("Procure &amp; Vendor", html)
        self.assertIn("Supplier vetting", html)
        self.assertIn("PO approval", html)

        # 6. Operations & Facilities
        self.assertIn("Operations &amp; Facilities", html)
        self.assertIn("Corporate SOP retrieval", html)

        # Tau-3 FinOps Circuit Breaker Card
        self.assertIn("Tau-3 FinOps Circuit Breaker Card", html)
        self.assertIn("50,000", html)
        self.assertIn("autonomous approval", html)
        self.assertIn("QALA-CONFIRM-50K", html)

        # Landed Tax Calculator Widget
        self.assertIn("Landed Tax Calculator Widget", html)
        self.assertIn("CIF", html)
        self.assertIn("5% Customs Duty", html)
        self.assertIn("5% VAT", html)
        self.assertIn("10.25%", html)

    # -------------------------------------------------------------------------
    # Test 6: Nibras FadeMem & Civic Navigator Markup
    # -------------------------------------------------------------------------
    def test_nibras_fademem_gauge_markup(self):
        """Verify FadeMem token reduction (>85%), Ebbinghaus decay curve, AES-256-GCM vault, and Ejari/DEWA calculators."""
        cockpit_path = os.path.join(PROJECT_ROOT, "bridge", "cockpit.html")
        with open(cockpit_path, "r", encoding="utf-8") as f:
            html = f.read()

        # FadeMem Cognitive Shield
        self.assertIn("FadeMem", html)
        self.assertIn("Token Reduction Efficiency", html)
        self.assertIn("85%", html)
        self.assertIn("Ebbinghaus", html)
        self.assertIn("R = e^{-t/S}", html)
        self.assertIn("ephemeral chatter decay", html)
        self.assertIn("pinned statutory rules", html)
        self.assertIn("Cognitive Friction Index", html)

        # Sovereign Family Office Vault
        self.assertIn("Sovereign Family Office Vault", html)
        self.assertIn("AES-256-GCM", html)

        # Dubai Civic Navigator Card
        self.assertIn("DEWA progressive tariff calculator", html)
        self.assertIn("23-44 fils/kWh", html)
        self.assertIn("3.5-4.6 fils/IG", html)
        self.assertIn("DLD Ejari Decree 43/2013 rent dispute verification calculator", html)
        self.assertIn("GDRFA Golden Visa eligibility boundary checker", html)
        self.assertIn("Real Estate AED 2M", html)
        self.assertIn("Skilled Professional AED 30k/mo", html)


if __name__ == "__main__":
    unittest.main()
