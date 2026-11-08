# 🏛️ MASTER CHAMPIONSHIP HANDOFF & ARCHITECTURAL REVISION PLAN (2026–2027)

**Document Reference:** `docs/CHAMPIONSHIP_HANDOFF_AND_REVISION_PLAN_2026.md`  
**Arena:** Dubai Create AI Agents Championship 2026–2027 (Dubai Future Foundation / DCDE, AED 2.5M+ Prize Pool)  
**Founder / Lead Systems Architect:** Mohamed Fathy, BPharm (Licensed Clinical Pharmacist & Systems Architect)  
**Lead AI Orchestrator:** Antigravity (Google DeepMind Agentic Pair Programmer)  
**Date:** November 2026  
**Status:** **AUTHORITATIVE MASTER SPECIFICATION & HANDOFF DOSSIER**

---

## 1. Executive Context & Founder Mandate

This document serves as the single source of truth for the transition from the **Foundation Hardening Phase (Milestones M-00 to M-10)** to the **Full-Scale Autonomous Capabilities Phase (RAG, Official Web Airlock, Bi-Directional Voice, and Multi-Turn Clinical Scribe)**.

### Operating Rules & Constraints:
1. **Strict Rule: 1 session = 1 feature/part.** Do not attempt to code everything at once. The Orchestrator plans and defines handoff prompts; dedicated Implementation Sessions execute code, run tests, and commit PRs.
2. **Tri-Mirror Law:** The local working directories on Desktop, the Google Drive mirror (`Dubai_AI_Championship_2027`), and the GitHub remote (`origin/main`) must remain synchronized after every sprint via `sync_mirror.sh`.
3. **Gomaa Memory Ledger:** Central SQLite ledger at `~/.gomaa/gomaa.db` (table `sprint_tasks`) tracks every milestone from `SPRINT-00` onward.
4. **Domain Precision:** Clinical pharmacy, pharmacology, and UAE statutory numbers must remain exact and non-diluted. All numbers must trace to primary statutory sources (DHA SN 03/2019, Dubai Customs Mirsal II, UAE Decree-Law 33/2021, DLD Ejari Decree 43/2013, DESC ISR v3.1, UAE PDPL Decree-Law 45/2021).

---

## 2. Infrastructure & Repository Topology

### A. Repositories (Split-Repo Architecture):
* **Master Control Plane:** `/Users/mohamedfathy/Desktop/Dubai`  
  - GitHub: `https://github.com/M4F-S/dubai-ai-championship-2027.git`
  - 8,648 LOC of deterministic C99 adapters (`adapters/`), Glass Cockpit HUD (`hud/`), Python bridge server (`bridge/`), and cross-repo test harness (`scripts/verify_all.sh`).
* **TARYAQ (ترياق) — Best Societal AI Agent:** `/Users/mohamedfathy/Desktop/taryaq-agent`  
  - GitHub: `https://github.com/M4F-S/taryaq-agent.git`
  - 88 Rust tests, 30 PubMed-verified DDI rules, DHA claim delay penalty scrubber, HITL clinical quarantine buffer.
* **QALA (القلعة) — Best Business AI Agent:** `/Users/mohamedfathy/Desktop/qala-agent`  
  - GitHub: `https://github.com/M4F-S/qala-agent.git`
  - 21 Rust tests, Dubai Customs Mirsal II 10.25% landed tax calculation, Article 51 gratuity calculation, MoHRE Nafis Emiratisation compliance, Tau-3 AED 50k gate.
* **NIBRAS (نبراس) — Best Personal AI Agent:** `/Users/mohamedfathy/Desktop/nibras-agent`  
  - GitHub: `https://github.com/M4F-S/nibras-agent.git`
  - 28 Rust tests, authenticated AES-256-GCM encrypted sovereign vault, FadeMem biological decay ($R = e^{-t/S}$), Ejari 5-tier rental increase calculator.

### B. Hardware Deployment Targets:
1. **Physical Edge Appliance (Primary Championship Demo Rig):**
   - **Machine:** Minisforum Venus Series UM790 Pro
   - **Processor:** AMD Ryzen 9 7940HS (8 cores / 16 threads, Zen 4, AVX-512 support, boost up to 5.2 GHz)
   - **Graphics:** AMD Radeon 780M iGPU (RDNA 3, 12 CUs, up to 2800 MHz, shared UMA DDR5 memory)
   - **Memory & Storage:** 64GB/32GB dual-channel DDR5-5600 (89.6 GB/s bandwidth), 1TB NVMe SSD (unlocked to ~936 GB ext4 partition)
   - **Operating System:** Ubuntu 24.04 LTS (Kernel 6.8.0-147-generic)
   - **Network & Access:** Tailscale IP `100.122.195.39` (hostname: `agentsvps`, user: `mo237`), passwordless SSH authorized from Mac.
   - **Pre-installed Edge Models:**
     - Ollama: `qwen2.5:7b-instruct-q4_K_M` (4.7 GB), `qwen2.5:14b-instruct-q4_K_M` (9.0 GB), `llama3.2:3b` (2.0 GB)
     - Decision Head: `laya v0.4.29` (ModernBERT 421M System 1 router, installed in `~/laya-env`)
     - Speech-to-Text: `whisper.cpp` compiled at `~/whisper.cpp/build/bin/whisper-cli`, symlinked to `/usr/local/bin/whisper`, with `ggml-large-v3-turbo-q5_0.bin` (548 MB).
     - Local Workspace: `~/championship/` containing clean clones of all 4 repositories.
2. **VPS Testing Enclave:**
   - IP: `187.124.2.26` (root)
   - Hosts Hermes Adversarial Agent (Toy), Belya, Almaz sandboxes, and automated audit CI.

---

## 3. Current Milestones Ledger (All Sprints 00–10 Complete)

Every sprint from `SPRINT-00` through `SPRINT-10` is **100% COMPLETED** in `~/.gomaa/gomaa.db`:
- **SPRINT-00:** Master C99 Test Harness & Gomaa Sync.
- **SPRINT-01:** Taryaq Rust Engine Skeleton & C99 FFI Bridge.
- **SPRINT-02:** Taryaq Empty Clinical Vessel & 30 PubMed Drug Interactions.
- **SPRINT-03:** Taryaq Tri-Modal Interfaces & Voice Pipeline Skeleton.
- **SPRINT-04:** Taryaq Background Scanner & Pharmacist HITL Quarantine Gate.
- **SPRINT-05:** Qala Standalone Rust Crate & Agency Mesh (DESC ISR v3.1).
- **SPRINT-06:** Qala Dubai Customs Mirsal II (10.25%) & MoHRE Labor (Art. 51).
- **SPRINT-07:** Nibras Standalone Rust Crate & Civic Navigator (Ejari, DEWA, KHDA, GDRFA).
- **SPRINT-08:** Nibras FadeMem Cognitive Decay ($R = e^{-t/S}$) & Sovereign Vault.
- **SPRINT-09:** Master Integration & Certified Adversarial Audit by Hermes VPS.
- **SPRINT-10:** Adversarial Advisory Remediation (A-1 Harness Idempotency via `mktemp` scratch DB isolation; A-2 Nibras Vault AES-256-GCM encryption-at-rest under UAE PDPL; Local Ollama Edge Air-Gap Bridge wiring).

**Test Verification Count:** **137/137 Rust tests passing**, 399 C99 assertions passing, 0 compiler warnings, 0 failed, git working tree clean across all repositories.

---

## 4. Honest Architectural Critique: Why We Must Expand

Despite the 100% green test record, testing the Cockpit UI exposed critical real-world limitations:

### A. The Forensic Diagnosis of the Cockpit Failure
When tested with an acute gout scenario (*"Colchicine + Clarithromycin with eGFR 22"*), Qwen 2.5 7B produced:
```json
{
  "tool": "interaction_check",
  "args": {
    "primary_drug": "كولشيسين",
    "patient_egfr": 22,
    "concurrent_drug": "クラリスロマイシン"
  }
}
```
1. **Multilingual Script Leak:** Qwen 2.5 translated *"Clarithromycin"* into Japanese Katakana (`クラリスロマイシン`). The C99 engine safely rejected it as unmodeled (`UNVERIFIED_DRUG_REQUIRES_PHARMACIST_REVIEW`), missing the fatal contraindication.
2. **Missing 2nd-Turn Conversational Synthesis:** When a tool executed, the bridge server returned the raw JSON card and terminated the turn (`[DONE]`). It never fed the execution result back to the model to generate a natural, empathetic, bilingual explanation.
3. **Casual Chat Over-triggering:** Greeting the agent ("Hello, who are you?") caused it to aggressively invoke `med_lookup('كولشيسين')` because the system prompt over-primed it on medical tools.

### B. Core Missing Capabilities:
1. **Shallow Knowledge Corpora:** The database contains small tables (140 drugs, 46 interactions). It lacks full-text official reference documents (DHA clinical standards, WHO guidelines, UAE MoHAP formulary, Dubai Customs tariff book).
2. **No Live Official Internet Research:** The agents cannot dynamically query external authoritative APIs (PubMed E-Utilities, OpenFDA, WHO, UAE government portals) when information is missing.
3. **Disconnected Bi-Directional Voice:** Whisper was compiled, but there is no real-time audio pipeline listening to microphone input, doing voice activity detection (VAD), or speaking back via local Text-to-Speech (TTS).

---

## 5. The 4 Essential Pillars to Build (The True Product Vision)

### Pillar 1: Authoritative RAG Pipeline (Official Primary Sources)
* **Taryaq (Clinical):**
  - Ingest WHO Essential Medicines List, UAE MoHAP Registered Drug List, and DHA Clinical Guidelines into a dedicated SQLite FTS5 + BM25/Vector store.
  - Enable semantic similarity + full-text search with exact page/line citations.
* **Qala (Enterprise):**
  - Ingest the complete Dubai Customs Integrated Tariff schedule (HS codes, duty percentages, exemptions), UAE Federal Decree-Law 33/2021 executive regulations, and FTA corporate tax rules.
* **Nibras (Civic):**
  - Ingest DLD rental valuation index rules, DEWA slab schedules, KHDA school inspection manuals, and GDRFA immigration schedules.

### Pillar 2: Curated Web Research Airlock (Gated Live Ingestion)
* When an agent cannot find authoritative data in its local RAG corpus, it initiates an **Airlock Web Research Query**.
* **Strict Whitelist of Official Domains Only:**
  - `ncbi.nlm.nih.gov` (PubMed E-Utilities API)
  - `api.fda.gov` (OpenFDA Drug Enforcement & Adverse Events)
  - `who.int` (WHO Global Health & Pharmacovigilance)
  - `mohap.gov.ae` (UAE Ministry of Health Circulars)
  - `dha.gov.ae` (Dubai Health Authority Standards)
  - `dubaicustoms.gov.ae` (Dubai Customs Notices)
* All retrieved web responses are hashed (SHA-256), assigned provenance metadata, and staged into `hitl_quarantine` before ingestion into clinical/operational tables.

### Pillar 3: Bi-Directional Voice Engine (STT + TTS)
* **Speech-to-Text (STT):**
  - Wire `whisper.cpp` (`large-v3-turbo` model on Minisforum) to accept streamed audio buffers from microphone or browser WebAudio.
  - Implement Voice Activity Detection (VAD) to split conversational turns automatically.
* **Dialectal Gulf/Masri Normalizer:**
  - Translate conversational Arabic dialectal terms into canonical clinical and legal concepts.
* **Text-to-Speech (TTS):**
  - Integrate a fast, lightweight local neural TTS engine (e.g. `piper-tts` or `melo-tts`) running on the UM790 Pro CPU.
  - Synthesize natural, low-latency spoken Arabic and English responses.

### Pillar 4: Conversational Tri-Modal Copilot & UI Polish
* **Multi-Turn Bridge Execution:**
  - Turn 1: User prompt $\rightarrow$ LLM proposes tool call.
  - Intercept: C99 / Rust safety kernel executes tool in $<0.05$ ms.
  - Turn 2: Tool execution verdict is appended to context $\rightarrow$ LLM generates human-level clinical or business synthesis.
* **Anti-Hallucination & Script Normalization Guardrails:**
  - Strict system prompt rules prohibiting translation of drug or legal entities into non-Latin/Arabic scripts.
  - Fallback normalizer in C99/Python to sanitize input strings before table lookup.
* **Ambient Clinical Scribing:**
  - Automatically parse multi-turn doctor-patient conversations into structured **SOAP notes** (Subjective, Objective, Assessment, Plan) with assigned ICD-10 codes.

---

## 6. Multi-Phase Roadmap for Next Sessions

```
Phase 1: Architecture, Schemas & Knowledge Ingestion Plan
Phase 2: Authoritative RAG Corpus Ingestion (Official Primary Datasets)
Phase 3: Curated Web Research Airlock (PubMed / OpenFDA / UAE Portals)
Phase 4: Bi-Directional Voice Engine (Audio Stream -> Whisper -> TTS)
Phase 5: Multi-Turn Conversational Engine & Tri-Modal Clinical Scribing
Phase 6: Live Stage Rehearsal & "Cable-Pull" Air-Gap Video Recording
```

---

## 7. Instructions for the New Master Orchestration Session

When opening the new session, paste the starter prompt:
1. Instruct the agent to read this document (`docs/CHAMPIONSHIP_HANDOFF_AND_REVISION_PLAN_2026.md`) completely.
2. The agent will act as **Master Orchestrator**, formulating specifications and implementation prompts for each phase without directly altering code.
3. Every step must adhere to the **1 session = 1 feature/part** rule and maintain the **Tri-Mirror Law**.
