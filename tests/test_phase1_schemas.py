#!/usr/bin/env python3
"""tests/test_phase1_schemas.py - Comprehensive Unit Verification Suite for Phase 1-A Schemas
Dubai AI Agents Championship 2026-2027 (Dubai Future Foundation / DCDE)
Founder & Principal Systems Architect: Mohamed Fathy, BPharm
Architectural Blueprint: docs/PHASE_1_ARCHITECTURE_AND_SCHEMAS.md

Validates:
  1. corpus/rag_master.db:
     - rag_documents, rag_chunks, rag_chunks_fts
     - Foreign key integrity and ON DELETE CASCADE
     - SQLite FTS5 BM25 ranked retrieval
     - FTS5 synchronization triggers (Insert, Update, Delete, Cascade)
     - 768-dim float32 vector embedding BLOB storage
  2. corpus/airlock_ledger.db:
     - airlock_requests, airlock_responses, airlock_quarantine
     - Foreign keys, cascade deletions, indexes
     - Cryptographic SHA-256 payload integrity
     - Quarantine HITL staging and review lifecycle
  3. data/clinical_records.db:
     - clinical_soap_notes schema and indexes
     - UAE PDPL pseudonymization (SHA-256 hashing of patient identifier)
     - ICD-10 and DHA claim codes JSON serialization
  4. Migration idempotency and reset safety.

Pure Python standard library (unittest, sqlite3, hashlib, json, struct).
"""

import hashlib
import json
import os
import sqlite3
import struct
import tempfile
import unittest
import uuid

import sys
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.init_phase1_schemas import (
    get_db_connection,
    init_rag_master,
    init_airlock_ledger,
    init_clinical_records,
    init_all,
    register_document,
    insert_chunk,
    search_rag,
    log_airlock_request,
    log_airlock_response,
    stage_airlock_quarantine,
    record_soap_note,
    RAG_MASTER_FILENAME,
    AIRLOCK_LEDGER_FILENAME,
    CLINICAL_RECORDS_FILENAME,
)


class TestRAGMasterSchema(unittest.TestCase):
    """Validates the authoritative RAG Master database schema and FTS5 triggers."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "rag_master.db")
        init_rag_master(self.db_path, reset=True)
        self.conn = get_db_connection(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_01_tables_and_columns_exist(self):
        """Verifies that rag_documents, rag_chunks, and rag_chunks_fts are created with proper schemas."""
        tables = [row["name"] for row in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()]

        self.assertIn("rag_documents", tables)
        self.assertIn("rag_chunks", tables)
        self.assertIn("rag_chunks_fts", tables)

        # Verify rag_documents columns
        doc_cols = [row["name"] for row in self.conn.execute("PRAGMA table_info(rag_documents);").fetchall()]
        for col in ["doc_id", "domain", "title", "issuing_authority", "effective_date", "source_url", "file_sha256", "total_chunks", "created_at"]:
            self.assertIn(col, doc_cols)

        # Verify rag_chunks columns
        chunk_cols = [row["name"] for row in self.conn.execute("PRAGMA table_info(rag_chunks);").fetchall()]
        for col in ["chunk_id", "doc_id", "domain", "section_code", "title", "passage", "passage_sha256", "token_count", "reserved_embedding", "created_at"]:
            self.assertIn(col, chunk_cols)

    def test_02_foreign_key_enforcement(self):
        """Verifies that inserting a chunk referencing a non-existent document fails with IntegrityError."""
        with self.assertRaises(sqlite3.IntegrityError):
            with self.conn:
                self.conn.execute(
                    """
                    INSERT INTO rag_chunks (
                        chunk_id, doc_id, domain, section_code, title, passage, passage_sha256, token_count
                    ) VALUES ('ORPHAN-CHUNK', 'NON-EXISTENT-DOC', 'CLINICAL', 'SEC-1', 'Title', 'Passage', 'hash', 1);
                    """
                )

    def test_03_fts5_insert_trigger_and_bm25_search(self):
        """Verifies that inserting into rag_chunks automatically populates rag_chunks_fts for BM25 search."""
        with self.conn:
            register_document(
                self.conn,
                doc_id="DHA-SN-03-2019",
                domain="CLINICAL",
                title="DHA Standards on Fatal Drug-Drug Interactions",
                issuing_authority="DHA",
                effective_date="2019-03-01",
                source_url="https://dha.gov.ae/standards/ddi-2019",
                file_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                total_chunks=2,
            )
            insert_chunk(
                self.conn,
                chunk_id="DHA-SN-03-2019:SEC-4.2",
                doc_id="DHA-SN-03-2019",
                domain="CLINICAL",
                section_code="SECTION_4.2",
                title="Colchicine and Clarithromycin Contraindication",
                passage="Concomitant administration of colchicine and clarithromycin is strictly contraindicated in patients with renal or hepatic impairment due to fatal toxicity.",
            )
            insert_chunk(
                self.conn,
                chunk_id="DHA-SN-03-2019:SEC-4.3",
                doc_id="DHA-SN-03-2019",
                domain="CLINICAL",
                section_code="SECTION_4.3",
                title="Warfarin and Metronidazole Interaction",
                passage="Concurrent use of warfarin and metronidazole significantly prolongs prothrombin time and elevates INR, substantially increasing hemorrhage risk.",
            )

        # Search for 'colchicine'
        results = search_rag(self.conn, "colchicine")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["chunk_id"], "DHA-SN-03-2019:SEC-4.2")
        self.assertEqual(results[0]["domain"], "CLINICAL")
        self.assertIn("strictly contraindicated", results[0]["passage"])

        # Search with domain filtering
        results_clinical = search_rag(self.conn, "warfarin", domain="CLINICAL")
        self.assertEqual(len(results_clinical), 1)
        self.assertEqual(results_clinical[0]["chunk_id"], "DHA-SN-03-2019:SEC-4.3")

        # Domain mismatch should yield zero
        results_customs = search_rag(self.conn, "warfarin", domain="CUSTOMS")
        self.assertEqual(len(results_customs), 0)

    def test_04_fts5_update_trigger(self):
        """Verifies that updating a chunk in rag_chunks updates rag_chunks_fts and clears old tokens."""
        with self.conn:
            register_document(
                self.conn,
                doc_id="CUSTOMS-TARIFF-2026",
                domain="CUSTOMS",
                title="Dubai Customs Tariff Schedule 2026",
                issuing_authority="DUBAI_CUSTOMS",
                effective_date="2026-01-01",
                source_url="https://dubaicustoms.gov.ae",
                file_sha256="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                total_chunks=1,
            )
            insert_chunk(
                self.conn,
                chunk_id="CUSTOMS:HS-8517",
                doc_id="CUSTOMS-TARIFF-2026",
                domain="CUSTOMS",
                section_code="HS_8517.13.00",
                title="Smartphones and Cellular Devices",
                passage="Smartphones classified under HS 8517.13.00 are subject to standard 5 percent customs duty plus 5 percent VAT.",
            )

        # Verify initial search
        res1 = search_rag(self.conn, "Smartphones")
        self.assertEqual(len(res1), 1)

        # Update title and passage
        with self.conn:
            self.conn.execute(
                """
                UPDATE rag_chunks
                SET title = 'Wearable Tech and Smartwatches',
                    passage = 'Cellular wearable devices and smartwatches under HS 8517.62.00 duty exempt under IT Agreement.'
                WHERE chunk_id = 'CUSTOMS:HS-8517';
                """
            )

        # Old term 'Smartphones' must no longer match
        res_old = search_rag(self.conn, "Smartphones")
        self.assertEqual(len(res_old), 0)

        # New term 'smartwatches' must match
        res_new = search_rag(self.conn, "smartwatches")
        self.assertEqual(len(res_new), 1)
        self.assertEqual(res_new[0]["chunk_id"], "CUSTOMS:HS-8517")

    def test_05_fts5_delete_trigger(self):
        """Verifies that deleting a chunk removes it from the FTS5 index."""
        with self.conn:
            register_document(
                self.conn,
                doc_id="MOHRE-LABOR-2021",
                domain="LABOR",
                title="Federal Decree-Law No. 33 of 2021 on Labor Relations",
                issuing_authority="MOHRE",
                effective_date="2022-02-02",
                source_url="https://mohre.gov.ae",
                file_sha256="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                total_chunks=1,
            )
            insert_chunk(
                self.conn,
                chunk_id="MOHRE:ART-51",
                doc_id="MOHRE-LABOR-2021",
                domain="LABOR",
                section_code="ARTICLE_51",
                title="End of Service Gratuity Calculation",
                passage="Article 51 specifies 21 days basic wage for each year of the first five years, and 30 days for each additional year.",
            )

        self.assertEqual(len(search_rag(self.conn, "Gratuity")), 1)

        with self.conn:
            self.conn.execute("DELETE FROM rag_chunks WHERE chunk_id = 'MOHRE:ART-51';")

        self.assertEqual(len(search_rag(self.conn, "Gratuity")), 0)

    def test_06_foreign_key_cascade_deletes_and_cleans_fts(self):
        """Verifies that deleting a document cascades to all chunks and purges rag_chunks_fts."""
        with self.conn:
            register_document(
                self.conn,
                doc_id="DLD-EJARI-43-2013",
                domain="CIVIC",
                title="Decree No. 43 of 2013 Determining Rent Increases in Dubai",
                issuing_authority="DLD",
                effective_date="2013-12-18",
                source_url="https://dubailand.gov.ae",
                file_sha256="1111111111111111111111111111111111111111111111111111111111111111",
                total_chunks=2,
            )
            insert_chunk(
                self.conn,
                chunk_id="DLD:TIER-1",
                doc_id="DLD-EJARI-43-2013",
                domain="CIVIC",
                section_code="TIER_1",
                title="Rent 0 to 10 percent below average",
                passage="No rent increase is permissible if the current rent is up to 10 percent below the average market rent.",
            )
            insert_chunk(
                self.conn,
                chunk_id="DLD:TIER-4",
                doc_id="DLD-EJARI-43-2013",
                domain="CIVIC",
                section_code="TIER_4",
                title="Rent over 40 percent below average",
                passage="Maximum 20 percent increase permissible if current rent is more than 40 percent below the average market rent.",
            )

        # Confirm 2 chunks indexed in FTS
        self.assertEqual(len(search_rag(self.conn, "permissible")), 2)

        # Cascade delete the document
        with self.conn:
            self.conn.execute("DELETE FROM rag_documents WHERE doc_id = 'DLD-EJARI-43-2013';")

        # rag_chunks must be empty
        chunks_count = self.conn.execute("SELECT count(*) as cnt FROM rag_chunks;").fetchone()["cnt"]
        self.assertEqual(chunks_count, 0)

        # rag_chunks_fts must be empty
        self.assertEqual(len(search_rag(self.conn, "permissible")), 0)

    def test_07_embedding_blob_storage_and_retrieval(self):
        """Verifies that a 768-dimensional float32 vector (3072 bytes) can be stored and retrieved bit-exact."""
        # Create a synthetic 768-dim float vector
        synthetic_vector = [0.001 * i for i in range(768)]
        packed_blob = struct.pack(f"{len(synthetic_vector)}f", *synthetic_vector)
        self.assertEqual(len(packed_blob), 768 * 4)  # 3072 bytes

        with self.conn:
            register_document(
                self.conn,
                doc_id="EMBED-TEST-DOC",
                domain="CLINICAL",
                title="Vector Test Document",
                issuing_authority="WHO",
                effective_date="2026-01-01",
                source_url=None,
                file_sha256="2222222222222222222222222222222222222222222222222222222222222222",
            )
            insert_chunk(
                self.conn,
                chunk_id="EMBED-CHUNK-1",
                doc_id="EMBED-TEST-DOC",
                domain="CLINICAL",
                section_code="VEC-01",
                title="ModernBERT Embedding Chunk",
                passage="Testing 768-dimensional vector preservation in SQLite BLOB column.",
                reserved_embedding=packed_blob,
            )

        row = self.conn.execute("SELECT reserved_embedding FROM rag_chunks WHERE chunk_id = 'EMBED-CHUNK-1';").fetchone()
        retrieved_blob = row["reserved_embedding"]
        self.assertIsNotNone(retrieved_blob)
        self.assertEqual(len(retrieved_blob), 3072)
        self.assertEqual(retrieved_blob, packed_blob)

        unpacked_vector = list(struct.unpack("768f", retrieved_blob))
        self.assertEqual(len(unpacked_vector), 768)
        self.assertAlmostEqual(unpacked_vector[0], 0.0)
        self.assertAlmostEqual(unpacked_vector[100], 0.1)

    def test_08_latin_diacritic_removal_in_fts5(self):
        """Verifies that unicode61 remove_diacritics 2 enables matching regardless of accents."""
        with self.conn:
            register_document(
                self.conn,
                doc_id="ACCENT-TEST",
                domain="CLINICAL",
                title="Multilingual Accents Test",
                issuing_authority="WHO",
                effective_date="2026-01-01",
                source_url=None,
                file_sha256="3333333333333333333333333333333333333333333333333333333333333333",
            )
            insert_chunk(
                self.conn,
                chunk_id="ACCENT-CHUNK-1",
                doc_id="ACCENT-TEST",
                domain="CLINICAL",
                section_code="PHARMACOPEIA",
                title="Pharmacopée Européenne Monograph",
                passage="La néomycine et la streptomycine présentent des propriétés ototoxiques sévères.",
            )

        # Match with plain Latin characters 'neomycine'
        res = search_rag(self.conn, "neomycine")
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["chunk_id"], "ACCENT-CHUNK-1")


class TestAirlockLedgerSchema(unittest.TestCase):
    """Validates outbound whitelist research auditing and quarantine staging."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "airlock_ledger.db")
        init_airlock_ledger(self.db_path, reset=True)
        self.conn = get_db_connection(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_01_schema_structure(self):
        """Verifies airlock_requests, airlock_responses, and airlock_quarantine exist."""
        tables = [row["name"] for row in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table';"
        ).fetchall()]

        self.assertIn("airlock_requests", tables)
        self.assertIn("airlock_responses", tables)
        self.assertIn("airlock_quarantine", tables)

        req_cols = [row["name"] for row in self.conn.execute("PRAGMA table_info(airlock_requests);").fetchall()]
        for col in ["request_id", "agent_id", "target_domain", "endpoint_path", "http_method", "query_params_json", "trigger_reason", "requested_at"]:
            self.assertIn(col, req_cols)

        resp_cols = [row["name"] for row in self.conn.execute("PRAGMA table_info(airlock_responses);").fetchall()]
        for col in ["response_id", "request_id", "http_status", "headers_json", "payload_raw", "payload_sha256", "received_at"]:
            self.assertIn(col, resp_cols)

        quar_cols = [row["name"] for row in self.conn.execute("PRAGMA table_info(airlock_quarantine);").fetchall()]
        for col in ["quarantine_id", "response_id", "target_table", "extracted_data_json", "status", "reviewer_role", "reviewer_notes", "reviewed_at", "created_at"]:
            self.assertIn(col, quar_cols)

    def test_02_foreign_key_and_cascade_lifecycle(self):
        """Verifies foreign key constraints and cascade deletions across the airlock chain."""
        # Inserting response with invalid request_id fails
        with self.assertRaises(sqlite3.IntegrityError):
            with self.conn:
                self.conn.execute(
                    """
                    INSERT INTO airlock_responses (
                        response_id, request_id, http_status, headers_json, payload_raw, payload_sha256
                    ) VALUES ('BAD-RESP', 'NON-EXISTENT-REQ', 200, '{}', x'00', 'hash');
                    """
                )

        # Full valid chain
        with self.conn:
            req_id = log_airlock_request(
                self.conn,
                agent_id="TARYAQ",
                target_domain="api.fda.gov",
                endpoint_path="/drug/enforcement.json",
                query_params={"search": "product_description:colchicine"},
                trigger_reason="FDA_RECALL_VERIFICATION",
            )
            raw_payload = b'{"results": [{"status": "Ongoing", "classification": "Class I"}]}'
            resp_id = log_airlock_response(
                self.conn,
                request_id=req_id,
                http_status=200,
                headers={"Content-Type": "application/json"},
                payload_raw=raw_payload,
            )
            q_id = stage_airlock_quarantine(
                self.conn,
                response_id=resp_id,
                target_table="taryaq_recalls",
                extracted_data={"class": "Class I", "action": "Recall"},
            )

        # Confirm cryptographic SHA-256 calculation
        expected_sha = hashlib.sha256(raw_payload).hexdigest()
        row = self.conn.execute("SELECT payload_sha256 FROM airlock_responses WHERE response_id = ?", (resp_id,)).fetchone()
        self.assertEqual(row["payload_sha256"], expected_sha)

        # Verify review workflow transition
        with self.conn:
            self.conn.execute(
                """
                UPDATE airlock_quarantine
                SET status = 'APPROVED',
                    reviewer_role = 'LICENSED_CLINICAL_PHARMACIST',
                    reviewer_notes = 'Verified against FDA Enforcement Report 2026.',
                    reviewed_at = datetime('now', 'utc')
                WHERE quarantine_id = ?;
                """,
                (q_id,),
            )
        q_row = self.conn.execute("SELECT status, reviewer_role FROM airlock_quarantine WHERE quarantine_id = ?", (q_id,)).fetchone()
        self.assertEqual(q_row["status"], "APPROVED")
        self.assertEqual(q_row["reviewer_role"], "LICENSED_CLINICAL_PHARMACIST")

        # Cascade deletion from request_id
        with self.conn:
            self.conn.execute("DELETE FROM airlock_requests WHERE request_id = ?", (req_id,))

        self.assertIsNone(self.conn.execute("SELECT * FROM airlock_responses WHERE response_id = ?", (resp_id,)).fetchone())
        self.assertIsNone(self.conn.execute("SELECT * FROM airlock_quarantine WHERE quarantine_id = ?", (q_id,)).fetchone())


class TestClinicalRecordsSchema(unittest.TestCase):
    """Validates the ambient clinical scribe SOAP notes schema and UAE PDPL compliance."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "clinical_records.db")
        init_clinical_records(self.db_path, reset=True)
        self.conn = get_db_connection(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_01_schema_and_indexes(self):
        """Verifies clinical_soap_notes columns and indexes."""
        cols = [row["name"] for row in self.conn.execute("PRAGMA table_info(clinical_soap_notes);").fetchall()]
        for col in [
            "note_id", "encounter_id", "patient_identifier_hash", "clinician_id",
            "subjective_text", "objective_text", "assessment_text", "plan_text",
            "icd10_codes_json", "dha_claim_codes_json", "signed_off_by_clinician", "created_at"
        ]:
            self.assertIn(col, cols)

        idx_names = [row["name"] for row in self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='clinical_soap_notes';"
        ).fetchall()]
        self.assertIn("idx_soap_encounter", idx_names)
        self.assertIn("idx_soap_patient", idx_names)
        self.assertIn("idx_soap_clinician", idx_names)

    def test_02_soap_note_insertion_and_pdpl_pseudonymization(self):
        """Verifies storing a SOAP note automatically computes a SHA-256 hash for patient identity."""
        raw_emirates_id = "784-1985-1234567-1"
        expected_hash = hashlib.sha256(raw_emirates_id.encode("utf-8")).hexdigest()

        with self.conn:
            note_id = record_soap_note(
                self.conn,
                encounter_id="ENC-DXB-2026-9901",
                patient_id_or_hash=raw_emirates_id,
                clinician_id="DHA-PHARM-4402",
                subjective_text="Patient reports severe knee pain after fasting; took colchicine with leftover clarithromycin.",
                objective_text="Cr: 2.8 mg/dL, eGFR: 22 mL/min, BP: 145/90 mmHg.",
                assessment_text="Stage 4 CKD with acute colchicine toxicity risk due to CYP3A4 inhibition.",
                plan_text="Immediate cessation of colchicine and clarithromycin. Refer to nephrology at Rashid Hospital.",
                icd10_codes=["M10.9", "N18.4", "T42.8X5A"],
                dha_claim_codes=["DHA-E&M-99204", "DHA-CPT-80053", "DHA-CPT-84520"],
                signed_off=1,
            )

        row = self.conn.execute("SELECT * FROM clinical_soap_notes WHERE note_id = ?", (note_id,)).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["encounter_id"], "ENC-DXB-2026-9901")
        self.assertEqual(row["patient_identifier_hash"], expected_hash)
        self.assertNotEqual(row["patient_identifier_hash"], raw_emirates_id)
        self.assertEqual(row["signed_off_by_clinician"], 1)

        # JSON code arrays deserialization
        icd_codes = json.loads(row["icd10_codes_json"])
        self.assertIn("M10.9", icd_codes)
        self.assertIn("N18.4", icd_codes)

        dha_codes = json.loads(row["dha_claim_codes_json"])
        self.assertIn("DHA-E&M-99204", dha_codes)


class TestMigrationIdempotency(unittest.TestCase):
    """Validates that running init_all repeatedly is completely safe and non-destructive."""

    def test_idempotent_migration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            corpus_dir = os.path.join(temp_dir, "corpus")
            data_dir = os.path.join(temp_dir, "data")

            # First run: creates tables
            dbs1 = init_all(corpus_dir=corpus_dir, data_dir=data_dir, reset=False)

            # Insert sample data into rag_master
            conn = get_db_connection(dbs1["rag_master"])
            with conn:
                register_document(
                    conn,
                    doc_id="DOC-1",
                    domain="CIVIC",
                    title="Idempotency Test Doc",
                    issuing_authority="DEWA",
                    effective_date="2026-01-01",
                    source_url=None,
                    file_sha256="4444444444444444444444444444444444444444444444444444444444444444",
                    total_chunks=1,
                )
                insert_chunk(
                    conn,
                    chunk_id="CHUNK-1",
                    doc_id="DOC-1",
                    domain="CIVIC",
                    section_code="DEWA-01",
                    title="DEWA Slab Tariff",
                    passage="Electricity tariff slab rates 2026.",
                )
            conn.close()

            # Second run: must succeed without error and preserve DOC-1
            dbs2 = init_all(corpus_dir=corpus_dir, data_dir=data_dir, reset=False)
            self.assertEqual(dbs1, dbs2)

            conn2 = get_db_connection(dbs2["rag_master"])
            cnt = conn2.execute("SELECT count(*) as c FROM rag_documents;").fetchone()["c"]
            self.assertEqual(cnt, 1)

            res = search_rag(conn2, "Slab")
            self.assertEqual(len(res), 1)
            conn2.close()

            # Third run with reset=True: wipes clean
            init_all(corpus_dir=corpus_dir, data_dir=data_dir, reset=True)
            conn3 = get_db_connection(dbs2["rag_master"])
            cnt_after = conn3.execute("SELECT count(*) as c FROM rag_documents;").fetchone()["c"]
            self.assertEqual(cnt_after, 0)
            conn3.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
