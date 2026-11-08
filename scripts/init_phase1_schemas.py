#!/usr/bin/env python3
"""scripts/init_phase1_schemas.py - Unified SQLite Schemas & Migration Script
Dubai AI Agents Championship 2026-2027 (Dubai Future Foundation / DCDE)
Founder & Principal Systems Architect: Mohamed Fathy, BPharm
Architectural Blueprint: docs/PHASE_1_ARCHITECTURE_AND_SCHEMAS.md

Initializes and migrates the physical SQLite schemas for:
  1. corpus/rag_master.db:
     - rag_documents (metadata, authority, legal effective date, SHA-256 digest)
     - rag_chunks (statutory section code, passage, SHA-256, reserved embedding BLOB)
     - rag_chunks_fts (SQLite FTS5 virtual table + insert/update/delete sync triggers)
  2. corpus/airlock_ledger.db:
     - airlock_requests (outbound whitelist audit)
     - airlock_responses (cryptographic payload SHA-256 tracking)
     - airlock_quarantine (HITL pharmacist/admin staging queue)
  3. data/clinical_records.db:
     - clinical_soap_notes (SOAP notes, ICD-10, DHA claim codes, SHA-256 pseudonymized)

Zero external pip dependencies (Pure Python 3 standard library).
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

DEFAULT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CORPUS_DIR = os.path.join(DEFAULT_ROOT_DIR, "corpus")
DEFAULT_DATA_DIR = os.path.join(DEFAULT_ROOT_DIR, "data")

RAG_MASTER_FILENAME = "rag_master.db"
AIRLOCK_LEDGER_FILENAME = "airlock_ledger.db"
CLINICAL_RECORDS_FILENAME = "clinical_records.db"


# ==============================================================================
# SQL DEFINITIONS: RAG MASTER
# ==============================================================================

RAG_MASTER_SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- Master Table of Registered Authoritative Documents
CREATE TABLE IF NOT EXISTS rag_documents (
    doc_id TEXT PRIMARY KEY,               -- e.g. 'DHA-SN-03-2019', 'MOHAP-FORMULARY-2026'
    domain TEXT NOT NULL,                  -- 'CLINICAL', 'CUSTOMS', 'LABOR', 'CIVIC'
    title TEXT NOT NULL,                   -- Official document title
    issuing_authority TEXT NOT NULL,       -- 'DHA', 'MOHAP', 'WHO', 'DUBAI_CUSTOMS', 'DLD'
    effective_date TEXT NOT NULL,          -- ISO 8601 YYYY-MM-DD
    source_url TEXT,                       -- Primary official portal link
    file_sha256 TEXT NOT NULL,             -- Cryptographic digest of source PDF/document
    total_chunks INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- Individual Atomic Chunks with Statutory Offset
CREATE TABLE IF NOT EXISTS rag_chunks (
    chunk_id TEXT PRIMARY KEY,             -- e.g. 'DHA-SN-03-2019:SEC-4.2'
    doc_id TEXT NOT NULL REFERENCES rag_documents(doc_id) ON DELETE CASCADE,
    domain TEXT NOT NULL,
    section_code TEXT NOT NULL,            -- e.g. 'ARTICLE_51', 'SECTION_4.2', 'HS_8517'
    title TEXT NOT NULL,                   -- Heading / Topic title
    passage TEXT NOT NULL,                 -- Full-text statutory or monograph excerpt
    passage_sha256 TEXT NOT NULL,          -- SHA-256 hash of this specific passage
    token_count INTEGER NOT NULL,
    reserved_embedding BLOB,               -- Reserved for 768-dim ModernBERT/nomic vector
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- Full-Text Search Virtual Table (SQLite FTS5 with BM25 Ranking & Diacritic Stripping)
CREATE VIRTUAL TABLE IF NOT EXISTS rag_chunks_fts USING fts5(
    chunk_id UNINDEXED,
    doc_id UNINDEXED,
    domain,
    section_code,
    title,
    passage,
    content='rag_chunks',
    content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);

-- Triggers for FTS5 Synchronization
CREATE TRIGGER IF NOT EXISTS rag_chunks_ai AFTER INSERT ON rag_chunks BEGIN
    INSERT INTO rag_chunks_fts(rowid, chunk_id, doc_id, domain, section_code, title, passage)
    VALUES (new.rowid, new.chunk_id, new.doc_id, new.domain, new.section_code, new.title, new.passage);
END;

CREATE TRIGGER IF NOT EXISTS rag_chunks_ad AFTER DELETE ON rag_chunks BEGIN
    INSERT INTO rag_chunks_fts(rag_chunks_fts, rowid, chunk_id, doc_id, domain, section_code, title, passage)
    VALUES ('delete', old.rowid, old.chunk_id, old.doc_id, old.domain, old.section_code, old.title, old.passage);
END;

CREATE TRIGGER IF NOT EXISTS rag_chunks_au AFTER UPDATE ON rag_chunks BEGIN
    INSERT INTO rag_chunks_fts(rag_chunks_fts, rowid, chunk_id, doc_id, domain, section_code, title, passage)
    VALUES ('delete', old.rowid, old.chunk_id, old.doc_id, old.domain, old.section_code, old.title, old.passage);
    INSERT INTO rag_chunks_fts(rowid, chunk_id, doc_id, domain, section_code, title, passage)
    VALUES (new.rowid, new.chunk_id, new.doc_id, new.domain, new.section_code, new.title, new.passage);
END;

CREATE INDEX IF NOT EXISTS idx_rag_documents_domain ON rag_documents(domain);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc_id ON rag_chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_domain ON rag_chunks(domain);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_section ON rag_chunks(section_code);
"""

RAG_MASTER_DROP_SQL = """
DROP TRIGGER IF EXISTS rag_chunks_au;
DROP TRIGGER IF EXISTS rag_chunks_ad;
DROP TRIGGER IF EXISTS rag_chunks_ai;
DROP TABLE IF EXISTS rag_chunks_fts;
DROP TABLE IF EXISTS rag_chunks;
DROP TABLE IF EXISTS rag_documents;
"""


# ==============================================================================
# SQL DEFINITIONS: AIRLOCK LEDGER & QUARANTINE
# ==============================================================================

AIRLOCK_LEDGER_SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- Outbound Request Audit Log
CREATE TABLE IF NOT EXISTS airlock_requests (
    request_id TEXT PRIMARY KEY,           -- UUIDv4
    agent_id TEXT NOT NULL,                -- 'TARYAQ', 'QALA', 'NIBRAS'
    target_domain TEXT NOT NULL,           -- e.g. 'ncbi.nlm.nih.gov'
    endpoint_path TEXT NOT NULL,
    http_method TEXT NOT NULL DEFAULT 'GET',
    query_params_json TEXT NOT NULL,
    trigger_reason TEXT NOT NULL,          -- e.g. 'DDI_UNMODELED_CLARITHROMYCIN_VERIFICATION'
    requested_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- Cryptographically Hashed Inbound Responses
CREATE TABLE IF NOT EXISTS airlock_responses (
    response_id TEXT PRIMARY KEY,          -- UUIDv4
    request_id TEXT NOT NULL REFERENCES airlock_requests(request_id) ON DELETE CASCADE,
    http_status INTEGER NOT NULL,
    headers_json TEXT NOT NULL,
    payload_raw BLOB NOT NULL,
    payload_sha256 TEXT NOT NULL,          -- SHA-256 for chain-of-custody verification
    received_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

-- Human-In-The-Loop (HITL) Staging Quarantine
CREATE TABLE IF NOT EXISTS airlock_quarantine (
    quarantine_id TEXT PRIMARY KEY,
    response_id TEXT NOT NULL REFERENCES airlock_responses(response_id) ON DELETE CASCADE,
    target_table TEXT NOT NULL,            -- e.g. 'taryaq_ddi_rules', 'customs_tariffs'
    extracted_data_json TEXT NOT NULL,     -- Proposed schema insertion
    status TEXT NOT NULL DEFAULT 'STAGED', -- 'STAGED', 'APPROVED', 'REJECTED'
    reviewer_role TEXT,                    -- 'LICENSED_CLINICAL_PHARMACIST', 'CUSTOMS_OFFICER'
    reviewer_notes TEXT,
    reviewed_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_quarantine_status ON airlock_quarantine(status);
CREATE INDEX IF NOT EXISTS idx_airlock_responses_request ON airlock_responses(request_id);
CREATE INDEX IF NOT EXISTS idx_airlock_quarantine_response ON airlock_quarantine(response_id);
CREATE INDEX IF NOT EXISTS idx_airlock_requests_domain ON airlock_requests(target_domain);
CREATE INDEX IF NOT EXISTS idx_airlock_requests_agent ON airlock_requests(agent_id);
"""

AIRLOCK_LEDGER_DROP_SQL = """
DROP TABLE IF EXISTS airlock_quarantine;
DROP TABLE IF EXISTS airlock_responses;
DROP TABLE IF EXISTS airlock_requests;
"""


# ==============================================================================
# SQL DEFINITIONS: CLINICAL RECORDS (SOAP NOTES)
# ==============================================================================

CLINICAL_RECORDS_SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS clinical_soap_notes (
    note_id TEXT PRIMARY KEY,              -- UUIDv4
    encounter_id TEXT NOT NULL,
    patient_identifier_hash TEXT NOT NULL, -- SHA-256 pseudonymized under UAE PDPL
    clinician_id TEXT NOT NULL,
    subjective_text TEXT NOT NULL,         -- Chief complaint, history of presenting illness
    objective_text TEXT NOT NULL,          -- Labs, vitals, current medication list
    assessment_text TEXT NOT NULL,         -- Clinical assessment, interaction alerts
    plan_text TEXT NOT NULL,               -- Interventions, therapeutic changes
    icd10_codes_json TEXT NOT NULL,        -- Array of matched ICD-10 codes
    dha_claim_codes_json TEXT NOT NULL,    -- Matched DHA billing codes
    signed_off_by_clinician INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
);

CREATE INDEX IF NOT EXISTS idx_soap_encounter ON clinical_soap_notes(encounter_id);
CREATE INDEX IF NOT EXISTS idx_soap_patient ON clinical_soap_notes(patient_identifier_hash);
CREATE INDEX IF NOT EXISTS idx_soap_clinician ON clinical_soap_notes(clinician_id);
"""

CLINICAL_RECORDS_DROP_SQL = """
DROP TABLE IF EXISTS clinical_soap_notes;
"""


# ==============================================================================
# CONNECTION AND MIGRATION ROUTINES
# ==============================================================================

def get_db_connection(db_path: str, timeout: float = 10.0) -> sqlite3.Connection:
    """Creates a configured sqlite3 connection with WAL mode and foreign keys enabled."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=timeout)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_rag_master(db_path: str, reset: bool = False, verbose: bool = False) -> str:
    """Initializes the corpus/rag_master.db schema (rag_documents, rag_chunks, rag_chunks_fts)."""
    if verbose:
        print(f"[INIT] Configuring RAG Master DB at: {db_path}")

    conn = get_db_connection(db_path)
    try:
        with conn:
            if reset:
                if verbose:
                    print("  [RESET] Dropping existing RAG master tables and triggers...")
                conn.executescript(RAG_MASTER_DROP_SQL)

            conn.executescript(RAG_MASTER_SCHEMA_SQL)

        # Sanity check FTS5 availability
        fts_check = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='rag_chunks_fts';"
        ).fetchone()
        if not fts_check:
            raise RuntimeError(f"Failed to create virtual table 'rag_chunks_fts' in {db_path}")

        if verbose:
            print("  [SUCCESS] RAG Master DB initialized (rag_documents, rag_chunks, rag_chunks_fts).")
        return db_path
    finally:
        conn.close()


def init_airlock_ledger(db_path: str, reset: bool = False, verbose: bool = False) -> str:
    """Initializes the corpus/airlock_ledger.db schema (requests, responses, quarantine)."""
    if verbose:
        print(f"[INIT] Configuring Airlock Ledger DB at: {db_path}")

    conn = get_db_connection(db_path)
    try:
        with conn:
            if reset:
                if verbose:
                    print("  [RESET] Dropping existing Airlock ledger tables...")
                conn.executescript(AIRLOCK_LEDGER_DROP_SQL)

            conn.executescript(AIRLOCK_LEDGER_SCHEMA_SQL)

        if verbose:
            print("  [SUCCESS] Airlock Ledger DB initialized (requests, responses, quarantine).")
        return db_path
    finally:
        conn.close()


def init_clinical_records(db_path: str, reset: bool = False, verbose: bool = False) -> str:
    """Initializes the data/clinical_records.db schema (clinical_soap_notes)."""
    if verbose:
        print(f"[INIT] Configuring Clinical Records DB at: {db_path}")

    conn = get_db_connection(db_path)
    try:
        with conn:
            if reset:
                if verbose:
                    print("  [RESET] Dropping existing Clinical Records tables...")
                conn.executescript(CLINICAL_RECORDS_DROP_SQL)

            conn.executescript(CLINICAL_RECORDS_SCHEMA_SQL)

        if verbose:
            print("  [SUCCESS] Clinical Records DB initialized (clinical_soap_notes).")
        return db_path
    finally:
        conn.close()


def init_all(
    corpus_dir: Optional[str] = None,
    data_dir: Optional[str] = None,
    reset: bool = False,
    verbose: bool = False,
) -> Dict[str, str]:
    """Initializes all Phase 1-A SQLite databases idempotently."""
    corpus_dir = os.path.abspath(corpus_dir or DEFAULT_CORPUS_DIR)
    data_dir = os.path.abspath(data_dir or DEFAULT_DATA_DIR)

    os.makedirs(corpus_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    rag_master_path = os.path.join(corpus_dir, RAG_MASTER_FILENAME)
    airlock_ledger_path = os.path.join(corpus_dir, AIRLOCK_LEDGER_FILENAME)
    clinical_records_path = os.path.join(data_dir, CLINICAL_RECORDS_FILENAME)

    init_rag_master(rag_master_path, reset=reset, verbose=verbose)
    init_airlock_ledger(airlock_ledger_path, reset=reset, verbose=verbose)
    init_clinical_records(clinical_records_path, reset=reset, verbose=verbose)

    return {
        "rag_master": rag_master_path,
        "airlock_ledger": airlock_ledger_path,
        "clinical_records": clinical_records_path,
    }


# ==============================================================================
# AUTHORITATIVE API HELPERS (RAG, AIRLOCK, SOAP)
# ==============================================================================

def register_document(
    conn: sqlite3.Connection,
    doc_id: str,
    domain: str,
    title: str,
    issuing_authority: str,
    effective_date: str,
    source_url: Optional[str],
    file_sha256: str,
    total_chunks: int = 0,
) -> str:
    """Registers an authoritative document in rag_documents."""
    query = """
    INSERT INTO rag_documents (
        doc_id, domain, title, issuing_authority, effective_date, source_url, file_sha256, total_chunks
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(doc_id) DO UPDATE SET
        domain = excluded.domain,
        title = excluded.title,
        issuing_authority = excluded.issuing_authority,
        effective_date = excluded.effective_date,
        source_url = excluded.source_url,
        file_sha256 = excluded.file_sha256,
        total_chunks = excluded.total_chunks;
    """
    conn.execute(
        query,
        (doc_id, domain, title, issuing_authority, effective_date, source_url, file_sha256, total_chunks),
    )
    return doc_id


def insert_chunk(
    conn: sqlite3.Connection,
    chunk_id: str,
    doc_id: str,
    domain: str,
    section_code: str,
    title: str,
    passage: str,
    passage_sha256: Optional[str] = None,
    token_count: Optional[int] = None,
    reserved_embedding: Optional[bytes] = None,
) -> str:
    """Inserts a chunk into rag_chunks (and automatically triggers FTS5 sync)."""
    if passage_sha256 is None:
        passage_sha256 = hashlib.sha256(passage.encode("utf-8")).hexdigest()
    if token_count is None:
        token_count = len(passage.split())

    query = """
    INSERT INTO rag_chunks (
        chunk_id, doc_id, domain, section_code, title, passage, passage_sha256, token_count, reserved_embedding
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(chunk_id) DO UPDATE SET
        doc_id = excluded.doc_id,
        domain = excluded.domain,
        section_code = excluded.section_code,
        title = excluded.title,
        passage = excluded.passage,
        passage_sha256 = excluded.passage_sha256,
        token_count = excluded.token_count,
        reserved_embedding = excluded.reserved_embedding;
    """
    conn.execute(
        query,
        (chunk_id, doc_id, domain, section_code, title, passage, passage_sha256, token_count, reserved_embedding),
    )
    return chunk_id


def prepare_fts5_query(query_text: str) -> str:
    """Prepares an arbitrary natural language or keyword query for SQLite FTS5 BM25 search.
    Preserves explicit boolean expressions (AND, OR, NOT, quotes, column filters).
    Converts plain space-separated keywords into OR prefix terms for resilient BM25 scoring."""
    trimmed = query_text.strip()
    if not trimmed:
        return ""
    if any(tok in trimmed for tok in [" AND ", " OR ", " NOT ", '"', "*", ":"]):
        return trimmed

    tokens = re.findall(r"[\w]+", trimmed, flags=re.UNICODE)
    if not tokens:
        return trimmed

    if len(tokens) == 1:
        return f"{tokens[0]}*"

    return " OR ".join(f"{t}*" for t in tokens)


def search_rag(
    conn: sqlite3.Connection,
    query_text: str,
    domain: Optional[str] = None,
    limit: int = 10,
    raw_match: bool = False,
) -> List[sqlite3.Row]:
    """Performs BM25 ranked full-text search against rag_chunks_fts.
    Uses prepare_fts5_query by default unless raw_match is True or explicit FTS syntax is present."""
    fts_query = query_text if raw_match else prepare_fts5_query(query_text)
    if not fts_query:
        return []

    if domain:
        sql = """
        SELECT c.chunk_id, c.doc_id, c.domain, c.section_code, c.title, c.passage,
               c.passage_sha256, c.token_count, fts.rank
        FROM rag_chunks_fts fts
        JOIN rag_chunks c ON c.rowid = fts.rowid
        WHERE rag_chunks_fts MATCH ? AND c.domain = ?
        ORDER BY fts.rank
        LIMIT ?;
        """
        try:
            return conn.execute(sql, (fts_query, domain, limit)).fetchall()
        except sqlite3.OperationalError:
            return conn.execute(sql, (f'"{query_text}"', domain, limit)).fetchall()
    else:
        sql = """
        SELECT c.chunk_id, c.doc_id, c.domain, c.section_code, c.title, c.passage,
               c.passage_sha256, c.token_count, fts.rank
        FROM rag_chunks_fts fts
        JOIN rag_chunks c ON c.rowid = fts.rowid
        WHERE rag_chunks_fts MATCH ?
        ORDER BY fts.rank
        LIMIT ?;
        """
        try:
            return conn.execute(sql, (fts_query, limit)).fetchall()
        except sqlite3.OperationalError:
            return conn.execute(sql, (f'"{query_text}"', limit)).fetchall()


def log_airlock_request(
    conn: sqlite3.Connection,
    agent_id: str,
    target_domain: str,
    endpoint_path: str,
    query_params: Union[str, Dict[str, Any]],
    trigger_reason: str,
    http_method: str = "GET",
    request_id: Optional[str] = None,
) -> str:
    """Audits an outbound whitelisted airlock request."""
    req_id = request_id or str(uuid.uuid4())
    params_str = query_params if isinstance(query_params, str) else json.dumps(query_params, ensure_ascii=False)

    sql = """
    INSERT INTO airlock_requests (
        request_id, agent_id, target_domain, endpoint_path, http_method, query_params_json, trigger_reason
    ) VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    conn.execute(sql, (req_id, agent_id, target_domain, endpoint_path, http_method, params_str, trigger_reason))
    return req_id


def log_airlock_response(
    conn: sqlite3.Connection,
    request_id: str,
    http_status: int,
    headers: Union[str, Dict[str, Any]],
    payload_raw: bytes,
    response_id: Optional[str] = None,
) -> str:
    """Logs and cryptographically hashes an inbound airlock response payload."""
    resp_id = response_id or str(uuid.uuid4())
    headers_str = headers if isinstance(headers, str) else json.dumps(headers, ensure_ascii=False)
    payload_sha256 = hashlib.sha256(payload_raw).hexdigest()

    sql = """
    INSERT INTO airlock_responses (
        response_id, request_id, http_status, headers_json, payload_raw, payload_sha256
    ) VALUES (?, ?, ?, ?, ?, ?);
    """
    conn.execute(sql, (resp_id, request_id, http_status, headers_str, payload_raw, payload_sha256))
    return resp_id


def stage_airlock_quarantine(
    conn: sqlite3.Connection,
    response_id: str,
    target_table: str,
    extracted_data: Union[str, Dict[str, Any], List[Any]],
    quarantine_id: Optional[str] = None,
) -> str:
    """Stages extracted data into the HITL quarantine queue."""
    q_id = quarantine_id or str(uuid.uuid4())
    data_str = extracted_data if isinstance(extracted_data, str) else json.dumps(extracted_data, ensure_ascii=False)

    sql = """
    INSERT INTO airlock_quarantine (
        quarantine_id, response_id, target_table, extracted_data_json, status
    ) VALUES (?, ?, ?, ?, 'STAGED');
    """
    conn.execute(sql, (q_id, response_id, target_table, data_str))
    return q_id


def record_soap_note(
    conn: sqlite3.Connection,
    encounter_id: str,
    patient_id_or_hash: str,
    clinician_id: str,
    subjective_text: str,
    objective_text: str,
    assessment_text: str,
    plan_text: str,
    icd10_codes: Union[str, List[str]],
    dha_claim_codes: Union[str, List[str]],
    signed_off: int = 0,
    note_id: Optional[str] = None,
) -> str:
    """Stores an ambient clinical SOAP note with SHA-256 pseudonymized patient ID under UAE PDPL."""
    n_id = note_id or str(uuid.uuid4())

    # Ensure patient identifier is SHA-256 hashed (64 hex characters)
    if len(patient_id_or_hash) == 64 and all(c in "0123456789abcdefABCDEF" for c in patient_id_or_hash):
        patient_hash = patient_id_or_hash.lower()
    else:
        patient_hash = hashlib.sha256(patient_id_or_hash.encode("utf-8")).hexdigest()

    icd_str = icd10_codes if isinstance(icd10_codes, str) else json.dumps(icd10_codes, ensure_ascii=False)
    dha_str = dha_claim_codes if isinstance(dha_claim_codes, str) else json.dumps(dha_claim_codes, ensure_ascii=False)

    sql = """
    INSERT INTO clinical_soap_notes (
        note_id, encounter_id, patient_identifier_hash, clinician_id,
        subjective_text, objective_text, assessment_text, plan_text,
        icd10_codes_json, dha_claim_codes_json, signed_off_by_clinician
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """
    conn.execute(
        sql,
        (
            n_id,
            encounter_id,
            patient_hash,
            clinician_id,
            subjective_text,
            objective_text,
            assessment_text,
            plan_text,
            icd_str,
            dha_str,
            signed_off,
        ),
    )
    return n_id


# ==============================================================================
# CLI PARSER
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Phase 1-A SQLite Schema Migration & Initializer (Dubai AI Championship 2026-2027)"
    )
    parser.add_argument("--corpus-dir", default=DEFAULT_CORPUS_DIR, help="Path to corpus directory")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR, help="Path to data directory")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables and triggers")
    parser.add_argument("--verify", action="store_true", help="Perform verification query tests on created schemas")
    parser.add_argument("--dump-sql", action="store_true", help="Print the combined DDL SQL statements and exit")
    parser.add_argument("--verbose", "-v", action="store_true", default=True, help="Print detailed progress output")

    args = parser.parse_args()

    if args.dump_sql:
        print("-- Master RAG Schema")
        print(RAG_MASTER_SCHEMA_SQL.strip())
        print("\n-- Airlock Ledger Schema")
        print(AIRLOCK_LEDGER_SCHEMA_SQL.strip())
        print("\n-- Clinical Records Schema")
        print(CLINICAL_RECORDS_SCHEMA_SQL.strip())
        sys.exit(0)

    print("==============================================================================")
    print(" PHASE 1-A: INITIALIZING UNIFIED SQLITE SCHEMAS & MIGRATIONS")
    print(f" Corpus Dir: {args.corpus_dir}")
    print(f" Data Dir:   {args.data_dir}")
    print(f" Mode:       {'RESET / FULL REBUILD' if args.reset else 'SAFE IDEMPOTENT MIGRATION'}")
    print("==============================================================================")

    dbs = init_all(
        corpus_dir=args.corpus_dir,
        data_dir=args.data_dir,
        reset=args.reset,
        verbose=args.verbose,
    )

    if args.verify:
        print("\n[VERIFY] Executing schema validation...")
        # Verify RAG Master
        conn_rag = get_db_connection(dbs["rag_master"])
        try:
            with conn_rag:
                register_document(
                    conn_rag,
                    doc_id="DHA-SN-03-2019-TEST",
                    domain="CLINICAL",
                    title="DHA Safety Notice 03/2019 Verification",
                    issuing_authority="DHA",
                    effective_date="2019-03-01",
                    source_url="https://dha.gov.ae/standards",
                    file_sha256="0000000000000000000000000000000000000000000000000000000000000000",
                    total_chunks=1,
                )
                insert_chunk(
                    conn_rag,
                    chunk_id="DHA-SN-03-2019-TEST:SEC-1",
                    doc_id="DHA-SN-03-2019-TEST",
                    domain="CLINICAL",
                    section_code="SEC-1",
                    title="Colchicine Fatal Contraindication",
                    passage="Concomitant administration of colchicine and clarithromycin is strictly contraindicated.",
                )
                res = search_rag(conn_rag, "clarithromycin", domain="CLINICAL")
                assert len(res) == 1, "FTS5 search failed to retrieve inserted chunk"
                conn_rag.execute("DELETE FROM rag_documents WHERE doc_id = 'DHA-SN-03-2019-TEST';")
                res_after = search_rag(conn_rag, "clarithromycin")
                assert len(res_after) == 0, "FTS5 cascade delete failed"
            print("  [PASS] RAG Master FTS5 & Cascade Trigger Verification succeeded.")
        finally:
            conn_rag.close()

        # Verify Airlock Ledger
        conn_airlock = get_db_connection(dbs["airlock_ledger"])
        try:
            with conn_airlock:
                req_id = log_airlock_request(
                    conn_airlock,
                    agent_id="TARYAQ",
                    target_domain="ncbi.nlm.nih.gov",
                    endpoint_path="/entrez/eutils/esearch.fcgi",
                    query_params={"db": "pubmed", "term": "colchicine AND clarithromycin"},
                    trigger_reason="DDI_UNMODELED_VERIFICATION",
                )
                resp_id = log_airlock_response(
                    conn_airlock,
                    request_id=req_id,
                    http_status=200,
                    headers={"content-type": "application/json"},
                    payload_raw=b'{"idlist": ["12345"]}',
                )
                q_id = stage_airlock_quarantine(
                    conn_airlock,
                    response_id=resp_id,
                    target_table="taryaq_ddi_rules",
                    extracted_data={"primary": "Colchicine", "concurrent": "Clarithromycin"},
                )
                row = conn_airlock.execute("SELECT status FROM airlock_quarantine WHERE quarantine_id = ?", (q_id,)).fetchone()
                assert row and row["status"] == "STAGED", "Airlock quarantine staging failed"
                conn_airlock.execute("DELETE FROM airlock_requests WHERE request_id = ?", (req_id,))
            print("  [PASS] Airlock Ledger Foreign Keys & Quarantine Verification succeeded.")
        finally:
            conn_airlock.close()

        # Verify Clinical Records
        conn_clinical = get_db_connection(dbs["clinical_records"])
        try:
            with conn_clinical:
                note_id = record_soap_note(
                    conn_clinical,
                    encounter_id="ENC-2026-0001",
                    patient_id_or_hash="EMIRATES_ID_784_1985_1234567_1",
                    clinician_id="DHA-MD-88124",
                    subjective_text="Patient presents with acute severe gout flare in left great toe.",
                    objective_text="eGFR: 22 mL/min. Uric acid: 9.2 mg/dL. Current meds: Clarithromycin 500mg BID.",
                    assessment_text="Acute gouty arthritis with stage 4 CKD. Severe DDI alert: Colchicine contraindicated.",
                    plan_text="Withhold colchicine. Prescribe intra-articular steroid or low-dose prednisolone. Cease clarithromycin if alternative available.",
                    icd10_codes=["M10.9", "N18.4"],
                    dha_claim_codes=["DHA-E&M-99214", "DHA-CPT-80053"],
                    signed_off=1,
                )
                row = conn_clinical.execute("SELECT * FROM clinical_soap_notes WHERE note_id = ?", (note_id,)).fetchone()
                assert row is not None, "Failed to retrieve SOAP note"
                assert len(row["patient_identifier_hash"]) == 64, "Patient ID was not pseudonymized to SHA-256 hash"
                conn_clinical.execute("DELETE FROM clinical_soap_notes WHERE note_id = ?", (note_id,))
            print("  [PASS] Clinical Records SOAP Note Verification succeeded.")
        finally:
            conn_clinical.close()

    print("\n[SUCCESS] Phase 1-A SQLite Schemas successfully created and verified.")


if __name__ == "__main__":
    main()
