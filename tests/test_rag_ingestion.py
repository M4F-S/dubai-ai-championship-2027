#!/usr/bin/env python3
"""tests/test_rag_ingestion.py - Automated Verification Suite for RAG Corpus Ingestion & FTS5 BM25
Dubai AI Agents Championship 2026-2027 (Dubai Future Foundation / DCDE)
Founder & Principal Systems Architect: Mohamed Fathy, BPharm
Architectural Blueprint: docs/PHASE_1_ARCHITECTURE_AND_SCHEMAS.md
Milestone: SPRINT-11-B (M-11-B)

Validates:
  1. All chunks have non-empty SHA-256 digests and strictly valid token counts.
  2. BM25 queries return exact statutory and clinical citations:
     - "Colchicine Clarithromycin renal failure" -> COLCHICINE_MONOGRAPH
     - "DHA claim submission 30 days penalty" -> DHA_SN_03_2019:§3.7.2
     - "Customs duty CIF 5 percent" -> DUBAI-CUSTOMS-TARIFF-2026:Article 1
     - "Gratuity 21 days 30 days basic wage" -> UAE-LABOR-LAW-33-2021:Article 51
     - "Ejari rent increase 20 percent" -> DLD-EJARI-DECREE-43-2013
  3. Ingestion idempotency: Running twice produces identical counts without duplicates.
  4. FTS5 trigger synchronization and domain filtering.
  5. CLI operational flags (--verify-integrity, --benchmark-search).

Pure Python 3 standard library (unittest, sqlite3, hashlib, subprocess, tempfile).
"""

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.init_phase1_schemas import get_db_connection, search_rag
from scripts.ingest_rag_corpus import (
    DEFAULT_CORPUS_DIR,
    RAG_MASTER_FILENAME,
    MANIFEST_FILENAME,
    ingest_corpus,
    verify_integrity,
    benchmark_search,
)


class TestRAGIngestionSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus_dir = os.path.join(ROOT_DIR, "corpus")
        cls.db_path = os.path.join(cls.corpus_dir, RAG_MASTER_FILENAME)
        cls.manifest_path = os.path.join(cls.corpus_dir, MANIFEST_FILENAME)
        # Ensure fresh authoritative ingestion
        ingest_corpus(
            corpus_dir=cls.corpus_dir,
            db_path=cls.db_path,
            manifest_path=cls.manifest_path,
            reingest=True,
            verbose=False,
        )

    def test_01_all_primary_documents_registered(self):
        """Verifies that all primary statutory and clinical documents are registered with SHA-256."""
        conn = get_db_connection(self.db_path)
        try:
            docs = conn.execute("SELECT * FROM rag_documents ORDER BY doc_id;").fetchall()
            doc_ids = {d["doc_id"] for d in docs}

            expected_docs = {
                "DHA_SN_03_2019",
                "DRUG_MONOGRAPHS_SOVEREIGN_CATALOG",
                "UAE_LAW_30_2021",
                "DUBAI-CUSTOMS-TARIFF-2026",
                "UAE-LABOR-LAW-33-2021",
                "DLD-EJARI-DECREE-43-2013",
                "DEWA-SLAB-TARIFFS-2026",
                "DESC-ISR-V3.1",
                "TAU3-FINOPS-POLICY-2026",
            }

            for expected in expected_docs:
                self.assertIn(expected, doc_ids, f"Missing expected document: {expected}")

            for doc in docs:
                self.assertIn(doc["domain"], ["CLINICAL", "CUSTOMS", "LABOR", "CIVIC", "SECURITY", "FINOPS"])
                self.assertTrue(doc["title"], f"Empty title in doc: {doc['doc_id']}")
                self.assertTrue(doc["issuing_authority"], f"Empty issuing authority in doc: {doc['doc_id']}")
                self.assertTrue(doc["effective_date"], f"Empty effective date in doc: {doc['doc_id']}")
                self.assertEqual(len(doc["file_sha256"]), 64, f"Invalid SHA-256 for doc: {doc['doc_id']}")
                self.assertGreater(doc["total_chunks"], 0, f"No chunks registered for doc: {doc['doc_id']}")
        finally:
            conn.close()

    def test_02_all_chunks_have_non_empty_sha256_and_tokens(self):
        """Verifies that every chunk has non-empty SHA-256 matching its passage and valid token counts."""
        conn = get_db_connection(self.db_path)
        try:
            chunks = conn.execute("SELECT * FROM rag_chunks;").fetchall()
            self.assertGreaterEqual(len(chunks), 35, f"Expected at least 35 chunks, got {len(chunks)}")

            for c in chunks:
                chunk_id = c["chunk_id"]
                passage = c["passage"]
                passage_sha = c["passage_sha256"]
                token_count = c["token_count"]

                self.assertTrue(passage, f"Empty passage in chunk {chunk_id}")
                self.assertEqual(len(passage_sha), 64, f"Invalid SHA-256 length in chunk {chunk_id}")

                # Cryptographic check
                computed_sha = hashlib.sha256(passage.encode("utf-8")).hexdigest()
                self.assertEqual(passage_sha, computed_sha, f"SHA-256 mismatch in chunk {chunk_id}")

                # Token count check
                expected_tokens = len(passage.split())
                self.assertGreater(token_count, 0, f"Token count must be positive in chunk {chunk_id}")
                self.assertEqual(token_count, expected_tokens, f"Token count mismatch in chunk {chunk_id}")
        finally:
            conn.close()

    def test_03_fts5_virtual_table_sync(self):
        """Verifies that FTS5 virtual table contains exactly the same count as the physical table."""
        conn = get_db_connection(self.db_path)
        try:
            chunks_cnt = conn.execute("SELECT count(*) as cnt FROM rag_chunks;").fetchone()["cnt"]
            fts_cnt = conn.execute("SELECT count(*) as cnt FROM rag_chunks_fts;").fetchone()["cnt"]
            self.assertEqual(chunks_cnt, fts_cnt, "FTS5 row count must equal physical chunks count")
        finally:
            conn.close()

    def test_04_bm25_exact_citations(self):
        """Verifies that standard BM25 queries return exact authoritative citations as Rank #1:
           - 'Colchicine Clarithromycin renal failure' -> COLCHICINE_MONOGRAPH
           - 'DHA claim submission 30 days penalty' -> DHA_SN_03_2019:§3.7.2
           - 'Customs duty CIF 5 percent' -> DUBAI-CUSTOMS-TARIFF-2026:Article 1
           - 'Gratuity 21 days 30 days basic wage' -> UAE-LABOR-LAW-33-2021:Article 51
           - 'Ejari rent increase 20 percent' -> DLD-EJARI-DECREE-43-2013
        """
        conn = get_db_connection(self.db_path)
        try:
            # 1. Colchicine Clarithromycin renal failure -> COLCHICINE_MONOGRAPH
            res1 = search_rag(conn, "Colchicine Clarithromycin renal failure", limit=3)
            self.assertTrue(res1, "Query 1 returned no results")
            top1 = res1[0]
            self.assertTrue(
                top1["section_code"] == "COLCHICINE_MONOGRAPH" or "COLCHICINE_MONOGRAPH" in top1["chunk_id"],
                f"Query 1 expected COLCHICINE_MONOGRAPH, got {top1['chunk_id']}"
            )

            # 2. DHA claim submission 30 days penalty -> DHA_SN_03_2019:§3.7.2
            res2 = search_rag(conn, "DHA claim submission 30 days penalty", limit=3)
            self.assertTrue(res2, "Query 2 returned no results")
            top2 = res2[0]
            expected_citation_2 = "DHA_SN_03_2019:§3.7.2"
            self.assertTrue(
                top2["chunk_id"] == expected_citation_2 or (top2["doc_id"] == "DHA_SN_03_2019" and top2["section_code"] == "§3.7.2"),
                f"Query 2 expected {expected_citation_2}, got {top2['chunk_id']}"
            )

            # 3. Customs duty CIF 5 percent -> DUBAI-CUSTOMS-TARIFF-2026:Article 1
            res3 = search_rag(conn, "Customs duty CIF 5 percent", limit=3)
            self.assertTrue(res3, "Query 3 returned no results")
            top3 = res3[0]
            expected_citation_3 = "DUBAI-CUSTOMS-TARIFF-2026:Article 1"
            self.assertTrue(
                top3["chunk_id"] == expected_citation_3 or (top3["doc_id"] == "DUBAI-CUSTOMS-TARIFF-2026" and top3["section_code"] == "Article 1"),
                f"Query 3 expected {expected_citation_3}, got {top3['chunk_id']}"
            )

            # 4. Gratuity 21 days 30 days basic wage -> UAE-LABOR-LAW-33-2021:Article 51
            res4 = search_rag(conn, "Gratuity 21 days 30 days basic wage", limit=3)
            self.assertTrue(res4, "Query 4 returned no results")
            top4 = res4[0]
            expected_citation_4 = "UAE-LABOR-LAW-33-2021:Article 51"
            self.assertTrue(
                top4["chunk_id"] == expected_citation_4 or (top4["doc_id"] == "UAE-LABOR-LAW-33-2021" and top4["section_code"] == "Article 51"),
                f"Query 4 expected {expected_citation_4}, got {top4['chunk_id']}"
            )

            # 5. Ejari rent increase 20 percent -> DLD-EJARI-DECREE-43-2013
            res5 = search_rag(conn, "Ejari rent increase 20 percent", limit=3)
            self.assertTrue(res5, "Query 5 returned no results")
            top5 = res5[0]
            self.assertTrue(
                top5["doc_id"] == "DLD-EJARI-DECREE-43-2013" or "DLD-EJARI-DECREE-43-2013" in top5["chunk_id"],
                f"Query 5 expected DLD-EJARI-DECREE-43-2013, got {top5['chunk_id']}"
            )
        finally:
            conn.close()

    def test_05_domain_filtering_precision(self):
        """Verifies that domain filtering isolates results strictly to requested regulatory domain."""
        conn = get_db_connection(self.db_path)
        try:
            # Query clinical domain only
            clinical_res = search_rag(conn, "renal impairment contraindication", domain="CLINICAL", limit=5)
            self.assertTrue(clinical_res)
            for r in clinical_res:
                self.assertEqual(r["domain"], "CLINICAL")

            # Query customs domain only
            customs_res = search_rag(conn, "valuation declaration release order", domain="CUSTOMS", limit=5)
            self.assertTrue(customs_res)
            for r in customs_res:
                self.assertEqual(r["domain"], "CUSTOMS")

            # Query civic domain only
            civic_res = search_rag(conn, "smart rental index benchmark", domain="CIVIC", limit=5)
            self.assertTrue(civic_res)
            for r in civic_res:
                self.assertEqual(r["domain"], "CIVIC")
        finally:
            conn.close()

    def test_06_ingestion_idempotency(self):
        """Verifies that re-running ingestion without --reingest produces identical record counts without duplicates."""
        conn = get_db_connection(self.db_path)
        try:
            initial_docs = conn.execute("SELECT count(*) as cnt FROM rag_documents;").fetchone()["cnt"]
            initial_chunks = conn.execute("SELECT count(*) as cnt FROM rag_chunks;").fetchone()["cnt"]
            initial_fts = conn.execute("SELECT count(*) as cnt FROM rag_chunks_fts;").fetchone()["cnt"]
        finally:
            conn.close()

        # Re-run ingestion in-place without reset
        ingest_corpus(
            corpus_dir=self.corpus_dir,
            db_path=self.db_path,
            manifest_path=self.manifest_path,
            reingest=False,
            verbose=False,
        )

        conn = get_db_connection(self.db_path)
        try:
            after_docs = conn.execute("SELECT count(*) as cnt FROM rag_documents;").fetchone()["cnt"]
            after_chunks = conn.execute("SELECT count(*) as cnt FROM rag_chunks;").fetchone()["cnt"]
            after_fts = conn.execute("SELECT count(*) as cnt FROM rag_chunks_fts;").fetchone()["cnt"]

            self.assertEqual(initial_docs, after_docs, "Document count changed after idempotent re-run")
            self.assertEqual(initial_chunks, after_chunks, "Chunk count changed after idempotent re-run")
            self.assertEqual(initial_fts, after_fts, "FTS5 count changed after idempotent re-run")
        finally:
            conn.close()

    def test_07_cli_flags_execution(self):
        """Verifies that scripts/ingest_rag_corpus.py CLI flags execute cleanly with code 0."""
        script_path = os.path.join(ROOT_DIR, "scripts", "ingest_rag_corpus.py")

        # Test --verify-integrity
        res_v = subprocess.run(
            [sys.executable, script_path, "--verify-integrity"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_v.returncode, 0, f"--verify-integrity failed: {res_v.stderr}")
        self.assertIn("All documents, chunk digests, token counts, and FTS5 triggers verified", res_v.stdout)

        # Test --benchmark-search
        res_b = subprocess.run(
            [sys.executable, script_path, "--benchmark-search"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_b.returncode, 0, f"--benchmark-search failed: {res_b.stderr}")
        self.assertIn("All Accurate: True", res_b.stdout)


if __name__ == "__main__":
    unittest.main()
