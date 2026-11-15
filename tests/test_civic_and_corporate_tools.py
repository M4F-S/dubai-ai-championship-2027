#!/usr/bin/env python3
"""
tests/test_civic_and_corporate_tools.py - Verification Battery for Civic & Corporate Bridge Tools
Dubai AI Agents Championship 2026-2027 (Dubai Future Foundation / DCDE)

Milestone: SPRINT-17 (M-17)
Founder & Principal Systems Architect: Mohamed Fathy, BPharm
Architectural Blueprint: docs/PHASE_1_ARCHITECTURE_AND_SCHEMAS.md

Validates:
1. `test_dewa_progressive_slab_calculation`:
   Verifies exact mathematical bill for 4,500 kWh electricity and 8,000 IG water.
2. `test_golden_visa_real_estate_boundary`:
   Verifies qualification at AED 2,000,000 and rejection at AED 1,999,999.
3. `test_golden_visa_skilled_professional`:
   Verifies qualification at AED 30,000/mo with Bachelor's degree and rejection below AED 30,000.
4. `test_article_51_gratuity_calculation`:
   Verifies gratuity for 3-year tenure and 7-year tenure with statutory 2-year cap.
5. `test_qala_mandate_decomposition`:
   Verifies mandate routing to appropriate corporate specialist agents.
6. `test_rag_dewa_statutory_retrieval`:
   Verifies FTS5 BM25 retrieval of DEWA tariff slabs with SHA-256 citation.
7. `test_rag_golden_visa_resolution_retrieval`:
   Verifies retrieval of Cabinet Resolution 65/2022 with SHA-256 citation.
8. `test_c99_sub_millisecond_tool_execution`:
   Verifies tool execution latency remains strictly < 0.1 ms.
9. `test_rag_corporate_tax_decree_retrieval`:
   Verifies FTS5 BM25 retrieval of Corporate Tax Decree-Law 47/2022 and Small Business Relief.
10. `test_tools_schema_conformance`:
   Verifies JSON schema validity and registration in TOOLS definition.
"""

import hashlib
import os
import sys
import time
import unittest

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bridge.openrouter_client import (
    AGENT_TOOLS,
    TOOLS,
    OpenRouterAgentEngine,
    _execute_rag_tool,
    dewa_calculate_bill,
    golden_visa_evaluate,
    qala_route_department,
    uae_labor_gratuity,
)
from scripts.init_phase1_schemas import (
    DEFAULT_CORPUS_DIR,
    RAG_MASTER_FILENAME,
    get_db_connection,
    ingest_statutory_knowledge,
    search_rag,
)


class TestCivicAndCorporateTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensure statutory knowledge is seeded in corpus/rag_master.db."""
        cls.db_path = os.path.join(DEFAULT_CORPUS_DIR, RAG_MASTER_FILENAME)
        if os.path.exists(cls.db_path):
            conn = get_db_connection(cls.db_path)
            try:
                ingest_statutory_knowledge(conn, verbose=False)
            finally:
                conn.close()
        cls.engine = OpenRouterAgentEngine(provider="deterministic")

    # -------------------------------------------------------------------------
    # TEST 1: DEWA Progressive Slab Calculation
    # -------------------------------------------------------------------------
    def test_dewa_progressive_slab_calculation(self):
        """Verifies exact mathematical bill for 4,500 kWh electricity and 8,000 IG water."""
        # Baseline consumption: 4,500 kWh electricity and 8,000 IG water
        input_args = {
            "electricity_kwh": 4500.0,
            "water_gallons": 8000.0,
            "housing_fee_aed": 0.0,
        }
        res = dewa_calculate_bill(input_args)

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["electricity_kwh"], 4500.0)
        self.assertEqual(res["water_gallons"], 8000.0)

        # Electricity breakdown:
        # Slab 1 (0-2000 kWh): 2000 * 0.23 = 460.00 AED
        # Slab 2 (2001-4000 kWh): 2000 * 0.28 = 560.00 AED
        # Slab 3 (4001-6000 kWh): 500 * 0.32 = 160.00 AED
        # Total electricity tariff = 1180.00 AED
        self.assertAlmostEqual(res["electricity_tariff_aed"], 1180.00, places=2)

        # Electricity fuel surcharge: 4500 * 0.05 = 225.00 AED
        self.assertAlmostEqual(res["electricity_fuel_surcharge_aed"], 225.00, places=2)

        # Electricity total: 1180.00 + 225.00 = 1405.00 AED
        self.assertAlmostEqual(res["electricity_total_aed"], 1405.00, places=2)

        # Water breakdown:
        # Slab 1 (0-6000 IG): 6000 * 0.035 = 210.00 AED
        # Slab 2 (6001-12000 IG): 2000 * 0.040 = 80.00 AED
        # Total water tariff = 290.00 AED
        self.assertAlmostEqual(res["water_tariff_aed"], 290.00, places=2)

        # Water fuel surcharge: 8000 * 0.006 = 48.00 AED
        self.assertAlmostEqual(res["water_fuel_surcharge_aed"], 48.00, places=2)

        # Water total: 290.00 + 48.00 = 338.00 AED
        self.assertAlmostEqual(res["water_total_aed"], 338.00, places=2)

        # Total bill = 1405.00 + 338.00 = 1743.00 AED
        self.assertAlmostEqual(res["total_bill_aed"], 1743.00, places=2)

        # Verify execution through engine dispatch
        engine_res = self.engine._execute_c99_tool("dewa_calculate_bill", input_args)
        self.assertAlmostEqual(engine_res["total_bill_aed"], 1743.00, places=2)

        # Verify Housing fee inclusion
        with_housing = dewa_calculate_bill({
            "electricity_kwh": 4500.0,
            "water_gallons": 8000.0,
            "housing_fee_aed": 500.0,
        })
        self.assertAlmostEqual(with_housing["total_bill_aed"], 2243.00, places=2)

    # -------------------------------------------------------------------------
    # TEST 2: Golden Visa Real Estate Boundary
    # -------------------------------------------------------------------------
    def test_golden_visa_real_estate_boundary(self):
        """Verifies qualification at AED 2,000,000 and rejection at AED 1,999,999."""
        # Exact qualification threshold
        pass_res = golden_visa_evaluate({
            "category": "REAL_ESTATE",
            "real_estate_value_aed": 2000000.0,
        })
        self.assertTrue(pass_res["is_eligible"], "Qualification failed at exactly AED 2,000,000")
        self.assertEqual(pass_res["verdict"], "QUALIFIED")
        self.assertIn("Cabinet Resolution No. 65 of 2022", pass_res["statutory_reference"])

        # Boundary rejection at AED 1,999,999
        fail_res = golden_visa_evaluate({
            "category": "REAL_ESTATE",
            "real_estate_value_aed": 1999999.0,
        })
        self.assertFalse(fail_res["is_eligible"], "Rejection failed at AED 1,999,999")
        self.assertEqual(fail_res["verdict"], "REJECTED")

        # Engine dispatch verification
        engine_pass = self.engine._execute_c99_tool("golden_visa_evaluate", {
            "category": "REAL_ESTATE",
            "real_estate_value_aed": 2500000.0,
        })
        self.assertTrue(engine_pass["is_eligible"])

    # -------------------------------------------------------------------------
    # TEST 3: Golden Visa Skilled Professional
    # -------------------------------------------------------------------------
    def test_golden_visa_skilled_professional(self):
        """Verifies qualification at AED 30,000/mo with Bachelor's degree and rejection below AED 30,000."""
        # Qualified case: AED 30,000 + Bachelor's degree
        pass_res = golden_visa_evaluate({
            "category": "SKILLED_PROFESSIONAL",
            "monthly_salary_aed": 30000.0,
            "has_bachelor_degree": True,
        })
        self.assertTrue(pass_res["is_eligible"])
        self.assertEqual(pass_res["verdict"], "QUALIFIED")
        self.assertIn("Cabinet Resolution No. 65 of 2022", pass_res["statutory_reference"])

        # Salary below threshold: AED 29,999 with degree
        fail_salary = golden_visa_evaluate({
            "category": "SKILLED_PROFESSIONAL",
            "monthly_salary_aed": 29999.0,
            "has_bachelor_degree": True,
        })
        self.assertFalse(fail_salary["is_eligible"])
        self.assertEqual(fail_salary["verdict"], "REJECTED")

        # Degree missing: AED 35,000 without degree
        fail_degree = golden_visa_evaluate({
            "category": "SKILLED_PROFESSIONAL",
            "monthly_salary_aed": 35000.0,
            "has_bachelor_degree": False,
        })
        self.assertFalse(fail_degree["is_eligible"])
        self.assertEqual(fail_degree["verdict"], "REJECTED")

    # -------------------------------------------------------------------------
    # TEST 4: Article 51 Gratuity Calculation
    # -------------------------------------------------------------------------
    def test_article_51_gratuity_calculation(self):
        """Verifies gratuity for 3-year tenure and 7-year tenure with statutory 2-year cap."""
        basic_salary = 10000.0

        # Case A: 3-year tenure (3 * 21 days = 63 days)
        # Daily wage = 10000 / 30 = 333.333 AED
        # Gratuity = 63 * (10000 / 30) = 21,000.00 AED
        res_3yr = uae_labor_gratuity({
            "basic_salary_aed": basic_salary,
            "tenure_years": 3.0,
            "is_limited_contract": True,
        })
        self.assertEqual(res_3yr["entitlement_days"], 63.0)
        self.assertAlmostEqual(res_3yr["final_gratuity_aed"], 21000.00, places=2)
        self.assertFalse(res_3yr["is_capped"])

        # Case B: 7-year tenure
        # First 5 years: 5 * 21 = 105 days
        # Additional 2 years: 2 * 30 = 60 days
        # Total days = 165 days
        # Gratuity = 165 * (10000 / 30) = 55,000.00 AED
        res_7yr = uae_labor_gratuity({
            "basic_salary_aed": basic_salary,
            "tenure_years": 7.0,
            "is_limited_contract": True,
        })
        self.assertEqual(res_7yr["entitlement_days"], 165.0)
        self.assertAlmostEqual(res_7yr["final_gratuity_aed"], 55000.00, places=2)
        self.assertFalse(res_7yr["is_capped"])

        # Case C: Statutory 2-Year Cap verification (tenure = 30 years)
        # Uncapped entitlement = (105 + 25 * 30) = 855 days -> 285,000.00 AED
        # Statutory 2-year cap = 10,000 * 24 months = 240,000.00 AED
        res_cap = uae_labor_gratuity({
            "basic_salary_aed": basic_salary,
            "tenure_years": 30.0,
            "is_limited_contract": True,
        })
        self.assertAlmostEqual(res_cap["statutory_cap_aed"], 240000.00, places=2)
        self.assertAlmostEqual(res_cap["uncapped_gratuity_aed"], 285000.00, places=2)
        self.assertAlmostEqual(res_cap["final_gratuity_aed"], 240000.00, places=2)
        self.assertTrue(res_cap["is_capped"])

        # Case D: Less than 1 year continuous service = 0 payout
        res_sub1 = uae_labor_gratuity({
            "basic_salary_aed": basic_salary,
            "tenure_years": 0.8,
            "is_limited_contract": True,
        })
        self.assertEqual(res_sub1["final_gratuity_aed"], 0.0)

    # -------------------------------------------------------------------------
    # TEST 5: Qala Mandate Decomposition
    # -------------------------------------------------------------------------
    def test_qala_mandate_decomposition(self):
        """Verifies mandate routing to appropriate corporate specialist agents."""
        mandate = (
            "Clear shipment container at Jebel Ali port, review vendor procurement contract, "
            "audit VAT invoice and corporate tax filing, and calculate end-of-service gratuity for departing staff."
        )
        res = qala_route_department({"mandate_text": mandate})

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["routing_verdict"], "DECOMPOSED_SUCCESS")

        depts = res["target_departments"]
        self.assertIn("TRADE", depts, "Missing TRADE routing for container shipment")
        self.assertIn("PROCUREMENT", depts, "Missing PROCUREMENT routing for vendor contract")
        self.assertIn("FINANCE", depts, "Missing FINANCE routing for VAT invoice & corporate tax")
        self.assertIn("HR", depts, "Missing HR routing for gratuity and staff")
        self.assertIn("LEGAL", depts, "Missing LEGAL routing for contract review")

        tasks = res["decomposed_tasks"]
        self.assertGreaterEqual(len(tasks), 4)
        for task in tasks:
            self.assertIn("task_id", task)
            self.assertIn("department", task)
            self.assertIn("action", task)
            self.assertIn("description", task)
            self.assertIn("priority", task)

    # -------------------------------------------------------------------------
    # TEST 6: RAG DEWA Statutory Retrieval
    # -------------------------------------------------------------------------
    def test_rag_dewa_statutory_retrieval(self):
        """Verifies FTS5 BM25 retrieval of DEWA tariff slabs with SHA-256 citation."""
        query_res = _execute_rag_tool({
            "query": "DEWA residential electricity tariff slabs fuel surcharge",
            "domain": "CIVIC",
            "limit": 3,
        })

        self.assertEqual(query_res["status"], "SUCCESS")
        self.assertGreater(query_res["count"], 0, "No chunks retrieved for DEWA query")

        top_chunk = query_res["chunks"][0]
        self.assertIn(top_chunk["doc_id"], ("DEWA-TARIFF-SLABS-2026", "DEWA-SLAB-TARIFFS-2026"))
        self.assertTrue(top_chunk["passage_sha256"])
        self.assertEqual(len(top_chunk["passage_sha256"]), 64)

        # Cryptographic verification of retrieved passage
        computed_sha = hashlib.sha256(top_chunk["passage"].encode("utf-8")).hexdigest()
        self.assertEqual(computed_sha, top_chunk["passage_sha256"])
        self.assertIn("23 fils", top_chunk["passage"])

    # -------------------------------------------------------------------------
    # TEST 7: RAG Golden Visa Resolution Retrieval
    # -------------------------------------------------------------------------
    def test_rag_golden_visa_resolution_retrieval(self):
        """Verifies retrieval of Cabinet Resolution 65/2022."""
        query_res = _execute_rag_tool({
            "query": "Cabinet Resolution No. 65 of 2022 Real Estate Investor Golden Visa AED 2,000,000",
            "limit": 3,
        })

        self.assertEqual(query_res["status"], "SUCCESS")
        self.assertGreater(query_res["count"], 0, "No chunks retrieved for Golden Visa query")

        top_chunk = query_res["chunks"][0]
        self.assertEqual(top_chunk["doc_id"], "GDRFA-GOLDEN-VISA-RESOLUTION-65-2022")
        self.assertEqual(len(top_chunk["passage_sha256"]), 64)

        # Cryptographic verification
        computed_sha = hashlib.sha256(top_chunk["passage"].encode("utf-8")).hexdigest()
        self.assertEqual(computed_sha, top_chunk["passage_sha256"])
        self.assertIn("2,000,000", top_chunk["passage"])

    # -------------------------------------------------------------------------
    # TEST 8: Sub-Millisecond Tool Execution Latency
    # -------------------------------------------------------------------------
    def test_c99_sub_millisecond_tool_execution(self):
        """Verifies tool execution latency remains strictly < 0.1 ms."""
        # 1. Warm-up
        dewa_calculate_bill({"electricity_kwh": 4500, "water_gallons": 8000})
        golden_visa_evaluate({"category": "REAL_ESTATE", "real_estate_value_aed": 2000000})
        uae_labor_gratuity({"basic_salary_aed": 10000, "tenure_years": 5, "is_limited_contract": True})
        qala_route_department({"mandate_text": "Audit customs tariff clearance and vendor payment"})

        # 2. Benchmark 500 iterations of DEWA calculation
        t0 = time.perf_counter()
        iterations = 500
        for _ in range(iterations):
            dewa_calculate_bill({"electricity_kwh": 4500, "water_gallons": 8000})
        dt_dewa_ms = ((time.perf_counter() - t0) / iterations) * 1000.0

        # Benchmark 500 iterations of Golden Visa evaluation
        t0 = time.perf_counter()
        for _ in range(iterations):
            golden_visa_evaluate({"category": "REAL_ESTATE", "real_estate_value_aed": 2000000})
        dt_gv_ms = ((time.perf_counter() - t0) / iterations) * 1000.0

        # Benchmark 500 iterations of Labor Gratuity
        t0 = time.perf_counter()
        for _ in range(iterations):
            uae_labor_gratuity({"basic_salary_aed": 10000, "tenure_years": 7, "is_limited_contract": True})
        dt_grat_ms = ((time.perf_counter() - t0) / iterations) * 1000.0

        # Benchmark 500 iterations of Qala routing
        t0 = time.perf_counter()
        for _ in range(iterations):
            qala_route_department({"mandate_text": "Audit customs and tax"})
        dt_route_ms = ((time.perf_counter() - t0) / iterations) * 1000.0

        # All tool latencies must remain strictly < 0.1 ms (100 microseconds)
        self.assertLess(dt_dewa_ms, 0.1, f"DEWA latency {dt_dewa_ms:.4f} ms exceeds 0.1 ms threshold")
        self.assertLess(dt_gv_ms, 0.1, f"Golden Visa latency {dt_gv_ms:.4f} ms exceeds 0.1 ms threshold")
        self.assertLess(dt_grat_ms, 0.1, f"Gratuity latency {dt_grat_ms:.4f} ms exceeds 0.1 ms threshold")
        self.assertLess(dt_route_ms, 0.1, f"Routing latency {dt_route_ms:.4f} ms exceeds 0.1 ms threshold")

    # -------------------------------------------------------------------------
    # TEST 9: Corporate Tax Decree-Law 47/2022 Statutory Retrieval
    # -------------------------------------------------------------------------
    def test_rag_corporate_tax_decree_retrieval(self):
        """Verifies FTS5 BM25 retrieval of Corporate Tax Decree-Law 47/2022 and Small Business Relief."""
        query_res = _execute_rag_tool({
            "query": "Federal Decree-Law No. 47 of 2022 Corporate Tax 9 percent 375000",
            "limit": 3,
        })

        self.assertEqual(query_res["status"], "SUCCESS")
        self.assertGreater(query_res["count"], 0)

        top_chunk = query_res["chunks"][0]
        self.assertEqual(top_chunk["doc_id"], "UAE-CORPORATE-TAX-DECREE-47-2022")
        self.assertEqual(len(top_chunk["passage_sha256"]), 64)

        computed_sha = hashlib.sha256(top_chunk["passage"].encode("utf-8")).hexdigest()
        self.assertEqual(computed_sha, top_chunk["passage_sha256"])
        self.assertIn("375,000", top_chunk["passage"])

        # Test Small Business Relief query
        sbr_res = _execute_rag_tool({
            "query": "Small Business Relief Ministerial Decision No. 73 of 2023 3000000",
            "limit": 3,
        })
        self.assertEqual(sbr_res["status"], "SUCCESS")
        self.assertGreater(sbr_res["count"], 0)
        self.assertIn("3,000,000", sbr_res["chunks"][0]["passage"])

    # -------------------------------------------------------------------------
    # TEST 10: Bridge Tools Schema Conformance
    # -------------------------------------------------------------------------
    def test_tools_schema_conformance(self):
        """Verifies that new civic and corporate tools conform to JSON Schema and are in TOOLS."""
        tool_names = [t["function"]["name"] for t in TOOLS]
        self.assertIn("dewa_calculate_bill", tool_names)
        self.assertIn("golden_visa_evaluate", tool_names)
        self.assertIn("uae_labor_gratuity", tool_names)
        self.assertIn("qala_route_department", tool_names)

        # Confirm identity of AGENT_TOOLS and TOOLS
        self.assertEqual(TOOLS, AGENT_TOOLS)

        # Check required fields
        dewa_spec = next(t["function"] for t in TOOLS if t["function"]["name"] == "dewa_calculate_bill")
        self.assertIn("electricity_kwh", dewa_spec["parameters"]["required"])
        self.assertIn("water_gallons", dewa_spec["parameters"]["required"])

        gv_spec = next(t["function"] for t in TOOLS if t["function"]["name"] == "golden_visa_evaluate")
        self.assertIn("category", gv_spec["parameters"]["required"])

        grat_spec = next(t["function"] for t in TOOLS if t["function"]["name"] == "uae_labor_gratuity")
        self.assertIn("basic_salary_aed", grat_spec["parameters"]["required"])
        self.assertIn("tenure_years", grat_spec["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()
