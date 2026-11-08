#!/usr/bin/env python3
"""scripts/ingest_rag_corpus.py - Authoritative RAG Knowledge Ingestion Engine & Corpus Compiler
Dubai AI Agents Championship 2026-2027 (Dubai Future Foundation / DCDE)
Founder & Principal Systems Architect: Mohamed Fathy, BPharm
Architectural Blueprint: docs/PHASE_1_ARCHITECTURE_AND_SCHEMAS.md
Milestone: SPRINT-11-B (M-11-B)

Ingests, validates, hashes, and indexes all primary statutory and clinical documents
across Taryaq (Societal), Qala (Business), and Nibras (Personal) into corpus/rag_master.db.

Features:
  1. Multiformat Statutory Parser:
     - Bracket tag format: [SECTION: ...], [TITLE: ...], # DOCUMENT: ...
     - Key-value block format: === SECTION ===, doc_id:, section:, text:
  2. Cryptographic Integrity:
     - Document-level and passage-level SHA-256 verification.
  3. FTS5 Virtual Table Indexing:
     - Automatic sync via triggers with unicode61 diacritic stripping.
     - BM25 ranked search benchmarking.
  4. Idempotency:
     - Safe re-runs with ON CONFLICT resolution and clean --reingest support.
  5. CLI Interface:
     - --reingest: Rebuilds index from scratch.
     - --verify-integrity: Verifies disk files, database records, and passage hashes.
     - --benchmark-search: Runs latency and recall benchmark on canonical queries.

Zero external dependencies (Python 3 standard library only).
"""

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.init_phase1_schemas import (
    DEFAULT_CORPUS_DIR,
    RAG_MASTER_FILENAME,
    get_db_connection,
    init_rag_master,
    insert_chunk,
    register_document,
    search_rag,
)

MANIFEST_FILENAME = "manifest.json"

DEFAULT_DOCUMENT_METADATA: Dict[str, Dict[str, str]] = {
    "DHA_SN_03_2019": {
        "domain": "CLINICAL",
        "title": "Dubai Health Authority Standards Notice SN 03/2019 - Payment Rules and Claim Timelines",
        "issuing_authority": "DHA",
        "effective_date": "2019-03-01",
        "source_url": "https://www.dha.gov.ae/en/HealthRegulation",
    },
    "DRUG_MONOGRAPHS_SOVEREIGN_CATALOG": {
        "domain": "CLINICAL",
        "title": "Sovereign Pharmacovigilance Drug Monographs - Nine Core Compounds",
        "issuing_authority": "WHO / FDA / EMA / MOHAP",
        "effective_date": "2024-01-01",
        "source_url": "https://www.who.int/medicines",
    },
    "UAE_LAW_30_2021": {
        "domain": "CLINICAL",
        "title": "UAE Federal Decree Law No. 30 of 2021 on Combating Narcotics and Psychotropic Substances",
        "issuing_authority": "MOHAP",
        "effective_date": "2021-11-27",
        "source_url": "https://www.mohap.gov.ae",
    },
    "DUBAI-CUSTOMS-TARIFF-2026": {
        "domain": "CUSTOMS",
        "title": "Dubai Customs and GCC Common Customs Tariff Schedule",
        "issuing_authority": "DUBAI_CUSTOMS",
        "effective_date": "2026-01-01",
        "source_url": "https://www.dubaicustoms.gov.ae/en/CustomsTariff",
    },
    "UAE-LABOR-LAW-33-2021": {
        "domain": "LABOR",
        "title": "UAE Federal Decree-Law No. 33 of 2021 on the Regulation of Labour Relations",
        "issuing_authority": "MOHRE",
        "effective_date": "2022-02-02",
        "source_url": "https://www.mohre.gov.ae",
    },
    "DLD-EJARI-DECREE-43-2013": {
        "domain": "CIVIC",
        "title": "Decree No. 43 of 2013 Determining Rent Increases for Real Property in Dubai",
        "issuing_authority": "DLD",
        "effective_date": "2013-12-18",
        "source_url": "https://dubailand.gov.ae/en/eservices/rental-index/",
    },
    "DEWA-SLAB-TARIFFS-2026": {
        "domain": "CIVIC",
        "title": "DEWA Slab Tariffs and Residential Utility Billing Regulations",
        "issuing_authority": "DEWA",
        "effective_date": "2026-01-01",
        "source_url": "https://www.dewa.gov.ae/en/consumer/billing/slab-tariff",
    },
    "DESC-ISR-V3.1": {
        "domain": "SECURITY",
        "title": "Dubai Electronic Security Center Information Security Regulation v3.1",
        "issuing_authority": "DESC",
        "effective_date": "2023-01-01",
        "source_url": "https://www.desc.gov.ae",
    },
    "TAU3-FINOPS-POLICY-2026": {
        "domain": "FINOPS",
        "title": "Tau-3 FinOps Enterprise Financial Authority Matrix and Transaction Threshold Policy",
        "issuing_authority": "TAU3_FINOPS",
        "effective_date": "2026-01-01",
        "source_url": "https://tau3.finops.local",
    },
}

CORPUS_FILES_MAP: Dict[str, str] = {
    "dha_sn_03_2019.txt": "DHA_SN_03_2019",
    "drug_monographs.txt": "DRUG_MONOGRAPHS_SOVEREIGN_CATALOG",
    "uae_controlled_substances.txt": "UAE_LAW_30_2021",
    "dubai_customs_tariff.txt": "DUBAI-CUSTOMS-TARIFF-2026",
    "uae_labor_law_33_2021.txt": "UAE-LABOR-LAW-33-2021",
    "dld_ejari_decree_43_2013.txt": "DLD-EJARI-DECREE-43-2013",
    "dewa_slab_tariffs.txt": "DEWA-SLAB-TARIFFS-2026",
    "desc_isr_v3.1.txt": "DESC-ISR-V3.1",
    "tau3_finops_policy.txt": "TAU3-FINOPS-POLICY-2026",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def parse_corpus_file(
    filepath: str,
    manifest_doc_meta: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Parses a corpus file into document metadata and individual atomic chunks.
    Supports both Bracket Tag format ([SECTION:...], [TITLE:...]) and
    Key-Value Block format (=== SECTION ===).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    file_basename = os.path.basename(filepath)
    default_id = CORPUS_FILES_MAP.get(file_basename, os.path.splitext(file_basename)[0].upper())
    default_meta = DEFAULT_DOCUMENT_METADATA.get(default_id, {})
    if manifest_doc_meta:
        default_meta = {**default_meta, **manifest_doc_meta}

    doc_id = default_id
    doc_title = default_meta.get("title", default_id)
    domain = default_meta.get("domain", "CIVIC")
    authority = default_meta.get("issuing_authority", default_meta.get("authority", "UAE Authority"))
    effective_date = default_meta.get("effective_date", "2026-01-01")
    source_url = default_meta.get("source_url")

    # Detect format style
    is_key_value_style = "=== SECTION ===" in content

    chunks: List[Dict[str, Any]] = []

    if is_key_value_style:
        # Key-Value Block Format
        sections = content.split("=== SECTION ===")
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue

            sec_dict: Dict[str, str] = {}
            lines = sec.splitlines()
            text_lines: List[str] = []
            capturing_text = False

            for line in lines:
                if line.startswith("text:") or line.startswith("text :"):
                    capturing_text = True
                    text_lines.append(line.split(":", 1)[1].strip())
                    continue
                if capturing_text:
                    text_lines.append(line.strip())
                    continue
                if ":" in line:
                    k, v = line.split(":", 1)
                    sec_dict[k.strip()] = v.strip()

            c_doc_id = sec_dict.get("doc_id", doc_id)
            c_doc_title = sec_dict.get("doc_title", doc_title)
            c_section = sec_dict.get("section", "UNKNOWN")
            c_title = sec_dict.get("section_title", c_section)
            c_domain = sec_dict.get("domain", domain)

            passage = " ".join([t for t in text_lines if t])
            if not passage:
                continue

            chunk_id = f"{c_doc_id}:{c_section}"
            passage_sha = hashlib.sha256(passage.encode("utf-8")).hexdigest()
            token_count = len(passage.split())

            chunks.append({
                "chunk_id": chunk_id,
                "doc_id": c_doc_id,
                "domain": c_domain,
                "section_code": c_section,
                "title": c_title,
                "passage": passage,
                "passage_sha256": passage_sha,
                "token_count": token_count,
            })
            doc_id = c_doc_id
            doc_title = c_doc_title
            domain = c_domain
    else:
        # Bracket Tag Format
        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith("# DOCUMENT:"):
                doc_id = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("# TITLE:"):
                doc_title = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("# AUTHORITY:"):
                authority = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("# DOMAIN:"):
                domain = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("# EFFECTIVE_DATE:"):
                effective_date = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("# SOURCE_URL:"):
                source_url = line_str.split(":", 1)[1].strip()

        # Split into blocks on [SECTION: ...]
        raw_blocks = re.split(r"(?=\[SECTION:\s*[^\]]+\])", content)
        for block in raw_blocks:
            block = block.strip()
            if not block.startswith("[SECTION:"):
                continue

            sec_match = re.search(r"\[SECTION:\s*([^\]]+)\]", block)
            title_match = re.search(r"\[TITLE:\s*([^\]]+)\]", block)

            section_code = sec_match.group(1).strip() if sec_match else "UNKNOWN"
            title = title_match.group(1).strip() if title_match else section_code

            lines = []
            for line in block.splitlines():
                l_str = line.strip()
                if l_str.startswith("[SECTION:") or l_str.startswith("[TITLE:"):
                    continue
                if l_str.startswith("#"):
                    continue
                if l_str:
                    lines.append(l_str)

            passage = " ".join(lines)
            if not passage:
                continue

            chunk_id = f"{doc_id}:{section_code}"
            passage_sha = hashlib.sha256(passage.encode("utf-8")).hexdigest()
            token_count = len(passage.split())

            chunks.append({
                "chunk_id": chunk_id,
                "doc_id": doc_id,
                "domain": domain,
                "section_code": section_code,
                "title": title,
                "passage": passage,
                "passage_sha256": passage_sha,
                "token_count": token_count,
            })

    doc_meta = {
        "doc_id": doc_id,
        "domain": domain,
        "title": doc_title,
        "issuing_authority": authority,
        "effective_date": effective_date,
        "source_url": source_url,
        "file": file_basename,
        "file_sha256": sha256_file(filepath),
        "total_chunks": len(chunks),
    }

    return doc_meta, chunks


def ingest_corpus(
    corpus_dir: Optional[str] = None,
    db_path: Optional[str] = None,
    manifest_path: Optional[str] = None,
    reingest: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Ingests all corpus documents into rag_master.db and updates manifest.json."""
    corpus_dir = os.path.abspath(corpus_dir or DEFAULT_CORPUS_DIR)
    db_path = os.path.abspath(db_path or os.path.join(corpus_dir, RAG_MASTER_FILENAME))
    manifest_path = os.path.abspath(manifest_path or os.path.join(corpus_dir, MANIFEST_FILENAME))

    if verbose:
        print(f"[INGEST] Starting Knowledge Ingestion Pipeline...")
        print(f"  Corpus Directory: {corpus_dir}")
        print(f"  Target SQLite DB: {db_path}")
        print(f"  Master Manifest:  {manifest_path}")

    # Ensure schema exists (or re-initialize if reingest requested)
    init_rag_master(db_path, reset=reingest, verbose=verbose)

    # Load existing manifest if present for metadata preservation
    existing_manifest: Dict[str, Any] = {"version": "2.0", "documents": {}, "chunks": {}}
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as mf:
                existing_manifest = json.load(mf)
        except Exception as e:
            if verbose:
                print(f"  [WARN] Could not parse existing manifest: {e}")

    # Discover candidate files in corpus directory
    discovered_files: List[str] = []
    # Preferred order of files
    for fname in CORPUS_FILES_MAP.keys():
        fpath = os.path.join(corpus_dir, fname)
        if os.path.isfile(fpath):
            discovered_files.append(fname)

    # Any other .txt files
    for fname in sorted(os.listdir(corpus_dir)):
        if fname.endswith(".txt") and fname not in discovered_files:
            discovered_files.append(fname)

    conn = get_db_connection(db_path)
    total_docs_indexed = 0
    total_chunks_indexed = 0

    manifest_docs: Dict[str, Any] = existing_manifest.get("documents", {})
    manifest_chunks: Dict[str, Any] = existing_manifest.get("chunks", {})

    try:
        with conn:
            for fname in discovered_files:
                fpath = os.path.join(corpus_dir, fname)
                default_id = CORPUS_FILES_MAP.get(fname)
                cached_doc_meta = manifest_docs.get(default_id) if default_id else None

                doc_meta, chunks = parse_corpus_file(fpath, cached_doc_meta)
                if not chunks:
                    if verbose:
                        print(f"  [SKIP] No chunks parsed from: {fname}")
                    continue

                # Register document
                register_document(
                    conn=conn,
                    doc_id=doc_meta["doc_id"],
                    domain=doc_meta["domain"],
                    title=doc_meta["title"],
                    issuing_authority=doc_meta["issuing_authority"],
                    effective_date=doc_meta["effective_date"],
                    source_url=doc_meta["source_url"],
                    file_sha256=doc_meta["file_sha256"],
                    total_chunks=len(chunks),
                )
                total_docs_indexed += 1

                # Update manifest doc entry
                manifest_docs[doc_meta["doc_id"]] = {
                    "file": fname,
                    "domain": doc_meta["domain"],
                    "title": doc_meta["title"],
                    "issuing_authority": doc_meta["issuing_authority"],
                    "effective_date": doc_meta["effective_date"],
                    "source_url": doc_meta["source_url"],
                    "sha256": doc_meta["file_sha256"],
                    "chunk_count": len(chunks),
                }

                # Insert chunks
                for chunk in chunks:
                    insert_chunk(
                        conn=conn,
                        chunk_id=chunk["chunk_id"],
                        doc_id=chunk["doc_id"],
                        domain=chunk["domain"],
                        section_code=chunk["section_code"],
                        title=chunk["title"],
                        passage=chunk["passage"],
                        passage_sha256=chunk["passage_sha256"],
                        token_count=chunk["token_count"],
                    )
                    total_chunks_indexed += 1

                    # Canonical chunk entry in manifest
                    chunk_entry = {
                        "doc_id": chunk["doc_id"],
                        "section": chunk["section_code"],
                        "title": chunk["title"],
                        "passage_sha256": chunk["passage_sha256"],
                        "token_count": chunk["token_count"],
                        "passage_preview": chunk["passage"][:120] + ("..." if len(chunk["passage"]) > 120 else ""),
                    }
                    manifest_chunks[chunk["chunk_id"]] = chunk_entry

                    # Legacy sanitized key compatibility for Round 3 tests (e.g. DHA_SN_03_2019_3_7_2)
                    clean_sec = re.sub(r"[^A-Za-z0-9_]+", "_", chunk["section_code"]).strip("_")
                    legacy_key = f"{chunk['doc_id']}_{clean_sec}"
                    if legacy_key not in manifest_chunks:
                        manifest_chunks[legacy_key] = chunk_entry

                if verbose:
                    print(f"  [INGESTED] {doc_meta['doc_id']} ({len(chunks)} chunks) from {fname}")

        # Update manifest.json on disk
        updated_manifest = {
            "version": "2.0",
            "description": "Dubai Sovereign Statutory & Clinical Master Corpus Manifest (Taryaq, Qala, Nibras)",
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_documents": total_docs_indexed,
            "total_chunks": total_chunks_indexed,
            "documents": manifest_docs,
            "chunks": manifest_chunks,
        }
        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(updated_manifest, mf, indent=2, ensure_ascii=False)

        if verbose:
            print(f"[SUCCESS] Ingested {total_docs_indexed} documents, {total_chunks_indexed} atomic chunks.")
            print(f"[SUCCESS] Manifest updated at: {manifest_path}")

        return {
            "db_path": db_path,
            "manifest_path": manifest_path,
            "documents_indexed": total_docs_indexed,
            "chunks_indexed": total_chunks_indexed,
        }
    finally:
        conn.close()


def verify_integrity(
    db_path: Optional[str] = None,
    corpus_dir: Optional[str] = None,
    manifest_path: Optional[str] = None,
    verbose: bool = True,
) -> bool:
    """Performs end-to-end cryptographic and relational verification of the RAG corpus."""
    corpus_dir = os.path.abspath(corpus_dir or DEFAULT_CORPUS_DIR)
    db_path = os.path.abspath(db_path or os.path.join(corpus_dir, RAG_MASTER_FILENAME))
    manifest_path = os.path.abspath(manifest_path or os.path.join(corpus_dir, MANIFEST_FILENAME))

    if not os.path.isfile(db_path):
        print(f"[-] Integrity Error: Database file not found at: {db_path}", file=sys.stderr)
        return False

    conn = get_db_connection(db_path)
    all_ok = True

    try:
        cur = conn.cursor()

        # 1. Check documents count and file hashes
        docs = cur.execute("SELECT doc_id, domain, title, file_sha256, total_chunks FROM rag_documents ORDER BY doc_id;").fetchall()
        if not docs:
            print("[-] Integrity Error: No documents found in rag_documents", file=sys.stderr)
            return False

        if verbose:
            print("==================================================================")
            print(" RAG MASTER CORPUS INTEGRITY AUDIT")
            print("==================================================================")
            print(f"Database: {db_path}")
            print(f"Total Registered Documents: {len(docs)}")
            print("------------------------------------------------------------------")

        manifest_docs = {}
        if os.path.isfile(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
                manifest_docs = manifest_data.get("documents", {})

        for d in docs:
            doc_id = d["doc_id"]
            db_sha = d["file_sha256"]
            total_chunks = d["total_chunks"]

            # Locate file
            file_meta = manifest_docs.get(doc_id, {})
            fname = file_meta.get("file")
            if not fname:
                for fn, did in CORPUS_FILES_MAP.items():
                    if did == doc_id:
                        fname = fn
                        break

            fpath = os.path.join(corpus_dir, fname) if fname else None
            file_exists = fpath and os.path.isfile(fpath)
            file_sha_match = False
            if file_exists:
                actual_sha = sha256_file(fpath)
                file_sha_match = (actual_sha == db_sha)
            else:
                actual_sha = "MISSING"

            # Check chunk count matches
            actual_chunks = cur.execute("SELECT count(*) as cnt FROM rag_chunks WHERE doc_id = ?;", (doc_id,)).fetchone()["cnt"]
            chunk_match = (actual_chunks == total_chunks) and (actual_chunks > 0)

            status = "PASS" if (file_sha_match and chunk_match) else "FAIL"
            if status != "PASS":
                all_ok = False

            if verbose:
                print(f"[{status}] Doc: {doc_id:<32} | Chunks: {actual_chunks:>2} | SHA: {db_sha[:12]}...")
                if not file_sha_match:
                    print(f"       [-] File Hash Mismatch or File Missing: {fpath} (Actual: {actual_sha})")
                if not chunk_match:
                    print(f"       [-] Chunk Count Mismatch: declared {total_chunks}, found {actual_chunks}")

        # 2. Verify all chunks: non-empty hash, valid token count, FTS sync
        chunks = cur.execute("SELECT chunk_id, doc_id, section_code, passage, passage_sha256, token_count FROM rag_chunks;").fetchall()
        fts_count = cur.execute("SELECT count(*) as cnt FROM rag_chunks_fts;").fetchone()["cnt"]

        if verbose:
            print("------------------------------------------------------------------")
            print(f"Total Chunks in DB:  {len(chunks)}")
            print(f"Total Chunks in FTS: {fts_count}")

        if len(chunks) != fts_count:
            print(f"[-] Integrity Error: rag_chunks count ({len(chunks)}) != rag_chunks_fts count ({fts_count})", file=sys.stderr)
            all_ok = False

        invalid_hashes = 0
        invalid_tokens = 0
        for c in chunks:
            expected_hash = hashlib.sha256(c["passage"].encode("utf-8")).hexdigest()
            if c["passage_sha256"] != expected_hash:
                invalid_hashes += 1
            expected_tokens = len(c["passage"].split())
            if c["token_count"] != expected_tokens or c["token_count"] <= 0:
                invalid_tokens += 1

        if invalid_hashes > 0:
            print(f"[-] Integrity Error: {invalid_hashes} chunks have invalid passage SHA-256 digests!", file=sys.stderr)
            all_ok = False
        if invalid_tokens > 0:
            print(f"[-] Integrity Error: {invalid_tokens} chunks have invalid token counts!", file=sys.stderr)
            all_ok = False

        if verbose:
            if all_ok:
                print("[SUCCESS] All documents, chunk digests, token counts, and FTS5 triggers verified.")
            else:
                print("[-] INTEGRITY AUDIT FAILED.", file=sys.stderr)
            print("==================================================================")

        return all_ok
    finally:
        conn.close()


def benchmark_search(
    db_path: Optional[str] = None,
    corpus_dir: Optional[str] = None,
    verbose: bool = True,
) -> bool:
    """Benchmarks SQLite FTS5 BM25 search latency and verifies retrieval accuracy."""
    corpus_dir = os.path.abspath(corpus_dir or DEFAULT_CORPUS_DIR)
    db_path = os.path.abspath(db_path or os.path.join(corpus_dir, RAG_MASTER_FILENAME))

    if not os.path.isfile(db_path):
        print(f"[-] Benchmark Error: Database file not found: {db_path}", file=sys.stderr)
        return False

    conn = get_db_connection(db_path)

    benchmark_queries = [
        {
            "query": "Colchicine Clarithromycin renal failure",
            "expected_target": "COLCHICINE_MONOGRAPH",
            "check_field": "section_code",
            "domain": "CLINICAL",
        },
        {
            "query": "DHA claim submission 30 days penalty",
            "expected_target": "§3.7.2",
            "check_field": "section_code",
            "domain": "CLINICAL",
        },
        {
            "query": "Customs duty CIF 5 percent",
            "expected_target": "Article 1",
            "check_field": "section_code",
            "domain": "CUSTOMS",
        },
        {
            "query": "Gratuity 21 days 30 days basic wage",
            "expected_target": "Article 51",
            "check_field": "section_code",
            "domain": "LABOR",
        },
        {
            "query": "Ejari rent increase 20 percent",
            "expected_target": "DLD-EJARI-DECREE-43-2013",
            "check_field": "doc_id",
            "domain": "CIVIC",
        },
        {
            "query": "DEWA electricity green slab 23 fils",
            "expected_target": "DEWA-SLAB-TARIFFS-2026",
            "check_field": "doc_id",
            "domain": "CIVIC",
        },
        {
            "query": "dual authorization approval token DESC ISR",
            "expected_target": "DESC-ISR-V3.1",
            "check_field": "doc_id",
            "domain": "SECURITY",
        },
        {
            "query": "AED 50000 finops threshold",
            "expected_target": "TAU3-FINOPS-POLICY-2026",
            "check_field": "doc_id",
            "domain": "FINOPS",
        },
    ]

    if verbose:
        print("==================================================================")
        print(" SQLITE FTS5 BM25 SEARCH BENCHMARK & RETRIEVAL RECALL")
        print("==================================================================")

    all_passed = True
    latencies: List[float] = []

    try:
        for idx, item in enumerate(benchmark_queries, 1):
            q_text = item["query"]
            target = item["expected_target"]
            field = item["check_field"]

            t0 = time.perf_counter()
            results = search_rag(conn, q_text, limit=5)
            dt_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(dt_ms)

            if not results:
                passed = False
                matched_val = "NO_MATCH"
                chunk_id = "NONE"
            else:
                top = results[0]
                matched_val = top[field]
                chunk_id = top["chunk_id"]
                passed = (target in matched_val) or (target in chunk_id) or (target == top["doc_id"]) or (target == top["section_code"])

            if not passed:
                all_passed = False
                status = "FAIL"
            else:
                status = "PASS"

            if verbose:
                print(f"[{status}] Q{idx:02d}: \"{q_text}\"")
                print(f"        Latency: {dt_ms:.3f} ms | Rank #1: {chunk_id} ({field}={matched_val})")
                if not passed:
                    print(f"        [-] Expected target '{target}' not found in top result!")

        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
        max_lat = max(latencies) if latencies else 0.0

        if verbose:
            print("------------------------------------------------------------------")
            print(f"Queries Tested: {len(benchmark_queries)} | All Accurate: {all_passed}")
            print(f"Mean Latency:   {avg_lat:.3f} ms | Peak Latency: {max_lat:.3f} ms")
            print("==================================================================")

        return all_passed
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Authoritative Knowledge Ingestion & Corpus Compiler (SPRINT-11-B)",
    )
    parser.add_argument("--corpus-dir", default=DEFAULT_CORPUS_DIR, help="Path to corpus directory")
    parser.add_argument("--db-path", default=None, help="Path to rag_master.db")
    parser.add_argument("--manifest-path", default=None, help="Path to manifest.json")
    parser.add_argument("--reingest", action="store_true", help="Drop and rebuild corpus database")
    parser.add_argument("--verify-integrity", action="store_true", help="Audit cryptographic hashes and FTS triggers")
    parser.add_argument("--benchmark-search", action="store_true", help="Benchmark BM25 query latency and recall")
    parser.add_argument("--verbose", "-v", action="store_true", default=True, help="Verbose output")

    args = parser.parse_args()

    # If no flags specified, perform standard idempotent ingestion
    perform_ingest = args.reingest or (not args.verify_integrity and not args.benchmark_search)

    if args.reingest or perform_ingest:
        ingest_corpus(
            corpus_dir=args.corpus_dir,
            db_path=args.db_path,
            manifest_path=args.manifest_path,
            reingest=args.reingest,
            verbose=args.verbose,
        )

    success = True
    if args.verify_integrity or perform_ingest:
        ok = verify_integrity(
            db_path=args.db_path,
            corpus_dir=args.corpus_dir,
            manifest_path=args.manifest_path,
            verbose=args.verbose,
        )
        success = success and ok

    if args.benchmark_search:
        ok = benchmark_search(
            db_path=args.db_path,
            corpus_dir=args.corpus_dir,
            verbose=args.verbose,
        )
        success = success and ok

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
