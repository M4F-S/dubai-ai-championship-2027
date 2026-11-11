#!/usr/bin/env python3
"""
tests/test_clinical_scribe.py - Ambient Clinical Scribing & Tri-Modal Copilot Verification Battery
Sprint: SPRINT-15 (M-15)
Championship Arena: Dubai AI Agents Championship 2026-2027 (Dubai Future Foundation / DCDE)
Architectural Reference: docs/PHASE_5_ARCHITECTURE_AND_PLAN.md

Deterministic Verification Suite (7 Authoritative Tests):
1. test_ambient_dialogue_to_soap_parsing:
   Parses bilingual multi-turn transcript (Doctor/Patient in EN, MSA, and Gulf/Egyptian Arabic)
   with acute gout flare, CKD Stage 4, and concurrent clarithromycin into distinct S, O, A, P components.
2. test_icd10_coding_accuracy:
   Validates automated diagnostic coding of M10.9 (Gout, unspecified) and N18.4 (CKD Stage 4, severe).
3. test_dha_sn_03_2019_claim_mapping:
   Validates assignment of E&M CPT 99214, Lab CPT 80053 (CMP), and 84550 (Uric Acid),
   alongside DHA SN 03/2019 Section 3.7.1 14-calendar-day initial submission deadline calculation.
4. test_uae_pdpl_sha256_pseudonymization:
   Enforces UAE Federal Decree-Law No. 45 of 2021 (PDPL) Art 5 & 13 by proving Emirates ID
   is strictly stored as 64-character SHA-256 hex digest and narrative civilian PII is redacted.
5. test_soap_database_commit_and_retrieval:
   Validates sovereign SQLite persistence in data/clinical_records.db (clinical_soap_notes),
   retrieval by ID and patient hash, and clinician digital sign-off record locking.
6. test_tri_modal_mode_switching:
   Verifies state management across Clinician Scribe, Pharmacist Gate, and Patient Companion modes.
7. test_rest_api_soap_endpoints:
   Executes HTTP client calls against bridge/server.py endpoints:
   - POST /api/clinical/soap/generate (and /api/clinical/soap/parse)
   - POST /api/clinical/soap/commit
   - GET  /api/clinical/soap/notes (and /api/clinical/soap/list)
   - GET  /api/clinical/soap/{note_id}
   - POST /api/clinical/soap/signoff
"""

import os
import sys
import time
import json
import uuid
import hashlib
import sqlite3
import datetime
import tempfile
import unittest
import threading
import urllib.request
import urllib.error

# Ensure project root is in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bridge.clinical_scribe import (
    ClinicalScribeEngine,
    DEFAULT_CLINICAL_DB,
    DEFAULT_AUDIT_LOG
)
from bridge.server import (
    ThreadingHTTPServer,
    ChampionshipRequestHandler,
    DEFAULT_HOST,
    get_clinical_mode,
    set_clinical_mode
)
from bridge.openrouter_client import OpenRouterAgentEngine


class TestClinicalScribeEngine(unittest.TestCase):
    """Authoritative test battery for Sprint-15 Tri-Modal Ambient Clinical Scribing."""

    @classmethod
    def setUpClass(cls):
        """Initialize test environment and start test HTTP server."""
        cls._orig_audit_key = os.environ.get("TARYAQ_AUDIT_KEY")
        os.environ["TARYAQ_AUDIT_KEY"] = "test-key-32-bytes-minimum-scribe-sprint15"

        cls.engine = ClinicalScribeEngine()

        # Ephemeral SQLite database for isolated test persistence
        cls.temp_db_fd, cls.temp_db_path = tempfile.mkstemp(suffix="_clinical_test.db")
        os.close(cls.temp_db_fd)
        cls.engine.init_database(cls.temp_db_path)

        # Ephemeral port for test HTTP server
        cls.port = 8855
        ChampionshipRequestHandler.engine = OpenRouterAgentEngine(provider="deterministic")
        cls.server = ThreadingHTTPServer((DEFAULT_HOST, cls.port), ChampionshipRequestHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        """Clean up HTTP server, temporary database, and restore environment."""
        cls.server.shutdown()
        cls.server.server_close()
        cls.server_thread.join(timeout=2.0)

        if os.path.exists(cls.temp_db_path):
            try:
                os.remove(cls.temp_db_path)
            except Exception:
                pass

        if cls._orig_audit_key is not None:
            os.environ["TARYAQ_AUDIT_KEY"] = cls._orig_audit_key
        else:
            os.environ.pop("TARYAQ_AUDIT_KEY", None)

    # -------------------------------------------------------------------------
    # Test 1: Ambient Bilingual Dialogue to SOAP Parsing
    # -------------------------------------------------------------------------
    def test_ambient_dialogue_to_soap_parsing(self):
        """Test 1: Verify parsing of full bilingual doctor-patient transcript into structured S, O, A, P."""
        transcript = (
            "Doctor: Good morning Ahmed. Please tell me what brings you in today.\n"
            "Patient: صباح الخير يا دكتور. عندي ألم فظيع في صباع رجلي الكبير ومبقدرش أدوس عليه منذ يومين.\n"
            "Doctor: The right first MTP joint is markedly erythematous, warm, and swollen. Any prior medical history?\n"
            "Patient: عندي وظائف كلى تعبانة وبغسل أو eGFR 22 وعندي ضغط دم مرتفع. وباخد كولشيسين 0.5mg مرتين يومياً.\n"
            "Doctor: I also see in your file that another clinic prescribed Clarithromycin 500mg BID for a respiratory infection.\n"
            "Patient: أيوة يا دكتور، صدرية وبلغم وباخد كلاريثروميسين.\n"
            "Doctor: Let's record vitals: BP is 145/92 mmHg, HR 88 bpm, Temp 37.2°C, SpO2 97%. Recent labs show eGFR 22 mL/min, serum creatinine 2.4 mg/dL, and serum uric acid 9.2 mg/dL."
        )

        metadata = {
            "encounter_id": "ENC-DXB-2026-9901",
            "patient_id": "784-1985-1234567-1",
            "patient_name": "Ahmed",
            "clinician_id": "DHA-MD-88124",
            "encounter_date": "2026-11-11"
        }

        soap_result = self.engine.parse_dialogue_to_soap(transcript, metadata=metadata)

        # 1. Structure Assertions
        self.assertIn("soap", soap_result)
        self.assertIn("subjective", soap_result["soap"])
        self.assertIn("objective", soap_result["soap"])
        self.assertIn("assessment", soap_result["soap"])
        self.assertIn("plan", soap_result["soap"])

        # 2. Subjective Content
        subj = soap_result["soap"]["subjective"]
        self.assertTrue(any(k in subj.lower() for k in ["gout", "joint pain", "mtp", "toe", "flare"]))
        self.assertTrue("CKD" in subj or "Kidney" in subj or "eGFR" in subj)

        # 3. Objective Vitals & Labs Extraction
        obj = soap_result["soap"]["objective"]
        self.assertIn("145/92", obj)
        self.assertIn("88 bpm", obj)
        self.assertIn("22", obj)
        self.assertIn("2.4", obj)
        self.assertIn("9.2", obj)

        # 4. Assessment Diagnoses & C99 Fatal Intercept
        asmt = soap_result["soap"]["assessment"]
        self.assertTrue(any(k in asmt for k in ["Gout", "Podagra", "M10.9"]))
        self.assertTrue(any(k in asmt for k in ["Chronic Kidney Disease", "CKD", "N18.4"]))
        self.assertTrue(len(soap_result["safety_alerts"]) > 0)
        self.assertTrue(any("CONTRAINDICATION" in a or "C99" in a for a in soap_result["safety_alerts"]))

        # 5. Plan Therapeutic Orders
        plan = soap_result["soap"]["plan"]
        self.assertTrue("DISCONTINUE" in plan or "HOLD" in plan)
        self.assertTrue("Colchicine" in plan)
        self.assertTrue("CMP" in plan or "80053" in plan)
        self.assertTrue("Uric Acid" in plan or "84550" in plan)

    # -------------------------------------------------------------------------
    # Test 2: ICD-10 Coding Accuracy
    # -------------------------------------------------------------------------
    def test_icd10_coding_accuracy(self):
        """Test 2: Verify automated extraction of M10.9 (Gout) and N18.4 (CKD Stage 4)."""
        asmt_text = (
            "Diagnoses:\n"
            "1. Acute Gout Flare / Podagra (ICD-10: M10.9) - Hyperuricemia\n"
            "2. Chronic Kidney Disease, Stage 4 Severe (ICD-10: N18.4, eGFR 22 mL/min)\n"
            "3. Acute Upper Respiratory Infection (ICD-10: J06.9)\n"
            "4. Essential Hypertension (ICD-10: I10)"
        )
        subj_text = "Patient complains of excruciating pain in big toe (podagra) and has baseline severe renal failure."

        codes = self.engine.extract_icd10_codes(asmt_text, subj_text)
        code_map = {c["code"]: c for c in codes}

        # Verify M10.9 Gout
        self.assertIn("M10.9", code_map)
        self.assertEqual(code_map["M10.9"]["description"], "Gout, unspecified")
        self.assertGreaterEqual(code_map["M10.9"]["confidence"], 0.90)

        # Verify N18.4 CKD Stage 4
        self.assertIn("N18.4", code_map)
        self.assertEqual(code_map["N18.4"]["description"], "Chronic kidney disease, stage 4 (severe)")
        self.assertGreaterEqual(code_map["N18.4"]["confidence"], 0.90)

        # Verify J06.9 and I10
        self.assertIn("J06.9", code_map)
        self.assertIn("I10", code_map)

    # -------------------------------------------------------------------------
    # Test 3: DHA SN 03/2019 Claim Code & Statutory Deadline Mapping
    # -------------------------------------------------------------------------
    def test_dha_sn_03_2019_claim_mapping(self):
        """Test 3: Verify E&M 99214, Labs 80053/84550, and 14-day §3.7.1 submission deadline calculation."""
        soap_mock = {
            "assessment": "Acute Gout Flare, Chronic Kidney Disease Stage 4, High medical decision making",
            "plan": "Order Comprehensive Metabolic Panel (CMP) and Uric acid level",
            "labs": {"egfr": {"value": 22.0}, "uric_acid": {"value": 9.2}}
        }
        enc_date = "2026-11-11"

        claims = self.engine.map_dha_sn_03_2019_claims(soap_mock, encounter_date=enc_date)
        claim_codes = [c.get("cpt_code") or c.get("code") for c in claims]

        # Verify CPT codes present
        self.assertIn("99214", claim_codes)
        self.assertIn("80053", claim_codes)
        self.assertIn("84550", claim_codes)

        # Verify DHA SN 03/2019 Section 3.7.1 initial submission deadline: exactly 14 calendar days
        # 2026-11-11 + 14 days = 2026-11-25
        em_claim = next(c for c in claims if (c.get("cpt_code") or c.get("code")) == "99214")
        self.assertEqual(em_claim["encounter_date"], "2026-11-11")
        self.assertEqual(em_claim["initial_submission_deadline"], "2026-11-25")
        self.assertEqual(em_claim["submission_window_days"], 14)
        self.assertEqual(em_claim["statutory_rule"], "DHA SN 03/2019 §3.7.1")
        self.assertEqual(em_claim["resubmission_window_days"], 30)
        self.assertEqual(em_claim["max_resubmissions"], 2)

    # -------------------------------------------------------------------------
    # Test 4: UAE PDPL SHA-256 Identity Pseudonymization & Narrative PII Scrubber
    # -------------------------------------------------------------------------
    def test_uae_pdpl_sha256_pseudonymization(self):
        """Test 4: Verify Emirates ID is strictly stored as SHA-256 hash and narrative PII is redacted."""
        raw_eid = "784-1985-1234567-1"
        expected_canonical = "784198512345671"
        expected_hash = hashlib.sha256(expected_canonical.encode("utf-8")).hexdigest()

        computed_hash = self.engine.pseudonymize_patient_identity(raw_eid)
        self.assertEqual(len(computed_hash), 64)
        self.assertEqual(computed_hash, expected_hash)
        self.assertEqual(computed_hash, "0a28e03455e062b28ec23e2502160624b8368b04e40e6ef152fa083a01d6cfdd")

        # Test Narrative PII De-Identification
        raw_narrative = (
            "Patient Ahmed presented with severe right big toe pain. "
            "His phone number is +971 50 123 4567 and alternate 0501234567. "
            "National ID: 784-1985-1234567-1 confirmed."
        )
        scrubbed = self.engine.scrub_narrative_pii(raw_narrative, patient_name="Ahmed")

        self.assertNotIn("Ahmed", scrubbed)
        self.assertNotIn("+971 50 123 4567", scrubbed)
        self.assertNotIn("0501234567", scrubbed)
        self.assertNotIn("784-1985-1234567-1", scrubbed)
        self.assertIn("[PATIENT_NAME_REDACTED]", scrubbed)

    # -------------------------------------------------------------------------
    # Test 5: SOAP Database Commit, Retrieval & Signoff Locking
    # -------------------------------------------------------------------------
    def test_soap_database_commit_and_retrieval(self):
        """Test 5: Verify SQLite persistence in clinical_soap_notes, retrieval, and digital signoff locking."""
        record_payload = {
            "encounter_id": "ENC-TEST-5501",
            "patient_id": "784-1985-1234567-1",
            "clinician_id": "DHA-MD-88124",
            "subjective": "Patient complaints of severe joint pain.",
            "objective": "Vitals: BP 145/92 mmHg, HR 88 bpm. Labs: eGFR 22.",
            "assessment": "Gout (M10.9) and CKD Stage 4 (N18.4).",
            "plan": "Hold Colchicine. Order CMP (80053).",
            "icd10": [{"code": "M10.9", "description": "Gout, unspecified", "confidence": 0.95}],
            "dha_claims": [{"code": "99214", "cpt_code": "99214", "type": "E&M"}]
        }

        # 1. Commit note
        note_id = self.engine.commit_soap_to_db(self.temp_db_path, record_payload)
        self.assertTrue(bool(note_id))

        # 2. Retrieve by ID
        note = self.engine.get_soap_note_by_id(self.temp_db_path, note_id)
        self.assertIsNotNone(note)
        self.assertEqual(note["encounter_id"], "ENC-TEST-5501")
        self.assertEqual(note["patient_identifier_hash"], "0a28e03455e062b28ec23e2502160624b8368b04e40e6ef152fa083a01d6cfdd")
        self.assertEqual(note["signed_off"], False)
        self.assertEqual(len(note["icd10"]), 1)
        self.assertEqual(note["icd10"][0]["code"], "M10.9")

        # 3. Retrieve by patient hash filter
        patient_notes = self.engine.get_soap_notes(
            self.temp_db_path,
            patient_hash="0a28e03455e062b28ec23e2502160624b8368b04e40e6ef152fa083a01d6cfdd"
        )
        self.assertGreaterEqual(len(patient_notes), 1)
        self.assertEqual(patient_notes[0]["note_id"], note_id)

        # 4. Signoff Attestation & Locking
        signed_ok = self.engine.signoff_soap_note(
            self.temp_db_path,
            note_id=note_id,
            clinician_id="DHA-MD-88124",
            signature_token="CLINICIAN-SIG-TOKEN-9988"
        )
        self.assertTrue(signed_ok)

        # Verify locked state
        locked_note = self.engine.get_soap_note_by_id(self.temp_db_path, note_id)
        self.assertEqual(locked_note["signed_off"], True)
        self.assertEqual(locked_note["signed_off_by_clinician"], 1)

    # -------------------------------------------------------------------------
    # Test 6: Tri-Modal Mode State Switching
    # -------------------------------------------------------------------------
    def test_tri_modal_mode_switching(self):
        """Test 6: Verify active copilot mode toggling between clinician, pharmacist, and patient."""
        # Initial mode should be clinician
        set_clinical_mode("clinician")
        self.assertEqual(get_clinical_mode(), "clinician")

        # Switch to pharmacist
        set_clinical_mode("pharmacist")
        self.assertEqual(get_clinical_mode(), "pharmacist")

        # Switch to patient
        set_clinical_mode("patient")
        self.assertEqual(get_clinical_mode(), "patient")

        # Invalid mode should not mutate state
        set_clinical_mode("invalid_super_mode")
        self.assertEqual(get_clinical_mode(), "patient")

        # Reset to clinician
        set_clinical_mode("clinician")
        self.assertEqual(get_clinical_mode(), "clinician")

    # -------------------------------------------------------------------------
    # Test 7: REST API SOAP Endpoints
    # -------------------------------------------------------------------------
    def test_rest_api_soap_endpoints(self):
        """Test 7: Verify HTTP client calls for SOAP generate, commit, list, and signoff endpoints."""
        base_url = f"http://{DEFAULT_HOST}:{self.port}"

        # 1. POST /api/clinical/soap/generate (and alias /api/clinical/soap/parse)
        gen_payload = {
            "transcript": "Doctor: Patient presented with severe gout flare in big toe. Prescribed Colchicine 0.5mg and Clarithromycin 500mg. Labs show eGFR = 22 mL/min.",
            "encounter_id": "ENC-REST-7701",
            "patient_id": "784-1985-1234567-1",
            "clinician_id": "DHA-MD-88124"
        }
        req = urllib.request.Request(
            f"{base_url}/api/clinical/soap/generate",
            data=json.dumps(gen_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("soap", data)
            self.assertIn("icd10", data)
            self.assertIn("dha_claims", data)
            self.assertIn("safety_alerts", data)
            soap_obj = data["soap"]

        # Also test alias /api/clinical/soap/parse
        req_alias = urllib.request.Request(
            f"{base_url}/api/clinical/soap/parse",
            data=json.dumps(gen_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_alias, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)

        # 2. POST /api/clinical/soap/commit
        commit_payload = {
            "encounter_id": "ENC-REST-7701",
            "patient_id": "784-1985-1234567-1",
            "clinician_id": "DHA-MD-88124",
            "soap": soap_obj,
            "icd10": data["icd10"],
            "dha_claims": data["dha_claims"]
        }
        req_commit = urllib.request.Request(
            f"{base_url}/api/clinical/soap/commit",
            data=json.dumps(commit_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_commit, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            c_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(c_data["status"], "COMMITTED")
            self.assertTrue(bool(c_data["note_id"]))
            note_id = c_data["note_id"]
            self.assertEqual(c_data["patient_hash"], "0a28e03455e062b28ec23e2502160624b8368b04e40e6ef152fa083a01d6cfdd")

        # 3. GET /api/clinical/soap/notes
        req_list = urllib.request.Request(f"{base_url}/api/clinical/soap/notes?limit=10")
        with urllib.request.urlopen(req_list, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            l_data = json.loads(resp.read().decode("utf-8"))
            notes = l_data if isinstance(l_data, list) else l_data.get("notes", [])
            self.assertIsInstance(notes, list)
            self.assertGreaterEqual(len(notes), 1)

        # 4. GET /api/clinical/soap/{note_id}
        req_single = urllib.request.Request(f"{base_url}/api/clinical/soap/{note_id}")
        with urllib.request.urlopen(req_single, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            s_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(s_data["note_id"], note_id)
            self.assertEqual(s_data["signed_off"], False)

        # 5. POST /api/clinical/soap/signoff
        sign_payload = {
            "note_id": note_id,
            "clinician_id": "DHA-MD-88124",
            "signature_token": "CLIN-SIG-PASS-7788"
        }
        req_sign = urllib.request.Request(
            f"{base_url}/api/clinical/soap/signoff",
            data=json.dumps(sign_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req_sign, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            sig_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(sig_data["status"], "SIGNED")
            self.assertEqual(sig_data["locked"], True)

        # 6. GET & POST /api/clinical/mode
        mode_post_req = urllib.request.Request(
            f"{base_url}/api/clinical/mode",
            data=json.dumps({"mode": "pharmacist"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(mode_post_req, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            m_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(m_data["mode"], "pharmacist")
            self.assertEqual(m_data["status"], "MODE_SWITCHED")

        mode_get_req = urllib.request.Request(f"{base_url}/api/clinical/mode")
        with urllib.request.urlopen(mode_get_req, timeout=5.0) as resp:
            self.assertEqual(resp.status, 200)
            mg_data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(mg_data["mode"], "pharmacist")

        # Reset mode to clinician
        set_clinical_mode("clinician")


if __name__ == "__main__":
    unittest.main()
