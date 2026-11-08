-- ==============================================================================
-- PHASE 1-A: UNIFIED SQLITE SCHEMAS & MIGRATIONS
-- Dubai AI Agents Championship 2026-2027 (Dubai Future Foundation / DCDE)
-- Founder & Principal Systems Architect: Mohamed Fathy, BPharm
-- Architectural Blueprint: docs/PHASE_1_ARCHITECTURE_AND_SCHEMAS.md
-- ==============================================================================

-- ==============================================================================
-- 1. MASTER RAG SCHEMA (corpus/rag_master.db)
-- Authoritative primary legal and clinical corpus with SQLite FTS5 & BM25 ranking
-- ==============================================================================

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


-- ==============================================================================
-- 2. AIRLOCK LEDGER & QUARANTINE SCHEMA (corpus/airlock_ledger.db)
-- Cryptographic audit trail for outbound whitelisted research & HITL staging
-- ==============================================================================

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


-- ==============================================================================
-- 3. CLINICAL RECORDS SCHEMA (data/clinical_records.db)
-- Ambient Clinical Scribe SOAP notes & DHA billing codes (UAE PDPL Compliant)
-- ==============================================================================

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
