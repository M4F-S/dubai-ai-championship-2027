# CANONICAL PRODUCT REQUIREMENTS DOCUMENT (PRD)
## Dubai Create AI Agents Championship 2026–2027
**Document Tag:** `PRD-CANONICAL-V1.0-FROZEN`  
**Status:** **NON-EDITABLE BASELINE SPECIFICATION**  
**Lead Systems Architect & Founder:** Mohamed Fathy, BPharm  
**Role:** Master System Orchestrator  
**Date of Ratification:** 2026-10-29  

---

## 1. Executive Mandate & Strategic Vision

### 1.1 The Championship Mission
The **Dubai Create AI Agents Championship 2026–2027** (hosted by Dubai Future Foundation / Dubai Centre for AI / DCDE) recognizes the world's most capable autonomous AI agents across three distinct tracks:
1. **Best Societal AI Agent:** **Taryaq (ترياق)** — Sovereign Clinical Safety, Pharmacovigilance & DHA Claim Cycle Firewall.
2. **Best Personal AI Agent:** **Nibras (نبراس)** — Sovereign Cognitive Memory, Executive Exocortex & Arabic-First Assistant.
3. **Best Business AI Agent:** **Qala (القلعة)** — Sovereign Enterprise Policy, DESC Sandbox & DP World Trade Gatekeeper.

### 1.2 The Core Invariant: Stop Compliance Theater, Build the Real Agents
This PRD supersedes all intermediate micro-refactoring rounds. We officially freeze the architecture and establish the canonical specification to eliminate drift:
- **No Mock Models:** Throw out keyword-hash stubs disguised as neural networks (e.g. fake Laya MD5 scripts). Either an AI model is live (local GGUF or sovereign API) or it is not claimed.
- **No 8-Drug Toys:** Taryaq must possess a genuine, class-based pharmacological knowledge base and medical RAG engine serving doctors, pharmacists, and patients.
- **Cross-Platform Availability:** Every agent must be accessible across **iOS, Android, Web, and Desktop** via WebAssembly (WASM) and a unified, responsive client interface.
- **The Neuro-Symbolic "Two-Brain" Law:** 
  - **Brain 1 (Fluency & Reasoning):** Generative LLMs handle messy natural language dialogue, chart extraction, summarization, and intention understanding in Arabic and English.
  - **Brain 2 (Sovereign Governor):** Bare-metal ISO C99 deterministic safety engines intercept every proposed action, enforce statutory laws, execute sub-millisecond mathematical checks, and record immutable HMAC-SHA256 audit ledgers.

---

## 2. Global Architecture: The Neuro-Symbolic Tri-Tier Model

```
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                                    USER-FACING INTERFACES                                         |
|                     iOS (PWA/Mobile) • Android (PWA/Mobile) • Web App • Desktop                   |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
                                                  │
                                                  ▼
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                           TIER 1: GENERATIVE NEURAL AGENT (BRAIN 1)                               |
|        • Models: Local GGUF (Llama-3.2-3B / Qwen-2.5-7B) or Sovereign Private Endpoint             |
|        • Multi-Turn Conversational Reasoning • Bilingual Arabic/English Code-Switching            |
|        • Stakeholder Prompts: Doctor Chart Review • Pharmacist Scrub • Patient Guidance           |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
                                                  │ (Proposed Tool Calls & Clinical Prescriptions)
                                                  ▼
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                        TIER 2: SOVEREIGN DETERMINISTIC GOVERNOR (BRAIN 2)                         |
|        • ISO C99 Core (-std=c99 -Wall -Wextra -Werror -O2) • Sub-Millisecond Execution           |
|        • Unbypassable Boundary Gates:                                                             |
|          - Taryaq: Class-Based Pharmacology Matrix & DHA SN 03/2019 Claim Arithmetic              |
|          - Qala: DESC ISR v3.1 Path Sandbox & Tau-3 FinOps AED 50,000 Approval Gate              |
|          - Nibras: FadeMem Ebbinghaus Biological Memory Decay & Token Pruning (>85%)              |
|        • Grounding Shield: Verification of numerical/factual claims against statutory manifests   |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
                                                  │ (Signed Execution & Ledger Logging)
                                                  ▼
+───────────────────────────────────────────────────────────────────────────────────────────────────+
|                         TIER 3: CRYPTOGRAPHIC AUDIT & STATUTORY STORAGE                           |
|        • HMAC-SHA256 Hash-Chained Audit Ledger (Tamper-Evident Backward Linking)                  |
|        • Single-Use Cryptographic Override Codes (Replay Attack Prevention)                       |
|        • Full Data Residency: UAE Health Data Law No. 2 of 2019 & UAE PDPL Law No. 45 of 2021     |
+───────────────────────────────────────────────────────────────────────────────────────────────────+
```

---

## 3. Agent 1 Specification: TARYAQ (ترياق)
**Track:** Best Societal AI Agent  
**Domain:** Clinical Pharmacovigilance, Prescription Safety & Healthcare Economics  
**Founder & Clinical Lead:** Mohamed Fathy, BPharm  

### 3.1 The Three Stakeholder Modes

#### Mode A: For Doctors (The Clinical Copilot)
1. **Ambient & Chart Regimen Review:** Analyzes multi-drug patient regimens for complex adverse drug events (ADEs), drug-disease contraindications, and narrow therapeutic index hazards.
2. **Renal Posology Engine (eGFR & CKD Staging):**
   - Automatically stages chronic kidney disease (CKD Stages 1 through 5, dialyzed vs non-dialyzed).
   - Enforces statutory renal cutoffs and calculates required posology reductions (e.g. Metformin in eGFR < 30, Enoxaparin in eGFR < 30, Colchicine in eGFR < 60 with CYP3A4 inhibitors).
3. **Longitudinal Trajectory Tracking:** Visualizes historical eGFR decline, flagged overrides, and prior adverse reactions across multiple visits.
4. **Physician Override Workflow:** Requires documented clinical rationale and consumes single-use signed approval codes to override severe contraindications.

#### Mode B: For Pharmacists (The Formulary & Claims Gatekeeper)
1. **DHA SN 03/2019 Claim Cycle Scrubber:**
   - Evaluates Dubai `eClaimLink` initial submission and remittance advice resubmission windows.
   - Enforces statutory 30-day grace rule and computes exact daily delay penalties:  
     $$\text{Penalty (AED)} = \max(0, \text{days} - 30) \times 0.03\% \times \text{Net Claim Amount}$$
2. **UAE Controlled Substance Verification (Federal Law No. 30 of 2021):**
   - Classifies medications against MoHAP Schedule 1 (Narcotics), Schedule 2 (Psychotropics), and Semi-Controlled Lists.
   - Validates prescription duration limits (maximum 30 days for narcotics, 3-day emergency prescriptions) and mandatory Emirates ID logging.
3. **Therapeutic Alternative Recommender:** Suggests non-interacting therapeutic alternatives within the same pharmacological class when a severe contraindication is detected.

#### Mode C: For Patients (The Intelligent Medication Companion)
1. **Bilingual Lay-Language Translation:** Translates dense medical Latin/English directions into clear, culturally fluent Arabic and English (e.g. *"Take 1 tablet with food at bedtime"* $\rightarrow$ *"قرص واحد مع وجبة العشاء قبل النوم"*).
2. **Administration & Food Interaction Guidance:** Warns against taking medications with grapefruit juice, dairy products, or antacids, and coordinates administration timing.
3. **Emergency Red-Flag Symptom Triage:** Detects acute anaphylaxis, severe dyspnea, acute chest pain, or bleeding signs; immediately triggers emergency protocol and displays nearest emergency hospital contact.

### 3.2 Real Class-Based Pharmacological Knowledge Base
Taryaq strictly rejects hardcoded 8-drug lists. It is powered by a structured SQLite formulary database:
- **Comprehensive Drug Ontology:** Active ingredients, brand names (Arabic & English), ATC codes.
- **Pharmacological Classes:** Strong/Moderate CYP3A4 inhibitors & inducers, CYP2D6, CYP2C9, P-glycoprotein inhibitors/substrates, Vitamin K Antagonists, DOACs, ACEi, ARBs, Biguanides, Macrolides, Azole Antifungals, Statins, NSAIDs.
- **Class-Level Interaction Engine:** A single rule dynamically protects **hundreds of drug pairs**:
  $$\text{Substrate}_{\text{CYP3A4/NTI}} + \text{Inhibitor}_{\text{Potent CYP3A4}} + (\text{eGFR} < 60) \implies \text{FATAL\_CONTRAINDICATION\_BLOCK}$$

### 3.3 Clinical RAG Engine
- Authoritative Corpus: Summary of Product Characteristics (SmPCs), British National Formulary (BNF), FDA Boxed Warnings, DHA Standards Notices, UAE MoHAP Drug Schedules.
- SQLite FTS5 BM25 search chunked by section, returning exact citations (`doc_id`, `section`, `passage_sha256`).

---

## 4. Agent 2 Specification: NIBRAS (نبراس)
**Track:** Best Personal AI Agent  
**Domain:** Sovereign Cognitive Memory, Executive Exocortex & Daily Personal Assistant  

### 4.1 Executive Deal & Decision Memory
1. **Meeting Minutes & Executive Action Tracker:** Ingests unformatted notes, transcripts, or dictated audio; extracts formal decisions, commitments, counter-parties, amounts, and deadlines.
2. **Personal Knowledge Retrieval:** Enables natural queries (e.g. *"When did I meet the DHA Chair and what was agreed regarding NABIDH?"*) with exact note citations and passage SHA-256 verification.
3. **Anti-Hallucination Shield:** Refuses to invent unrecorded meetings, dates, or promises. Emits `UNVERIFIABLE` when evidence is missing.

### 4.2 FadeMem Biological Memory OS
1. **Ebbinghaus Forgetting Curves & Sleep Consolidation:**
   - Evaluates note importance index: $I \in [0.0, 1.0]$.
   - Ephemeral chatter ($I < 0.25$) undergoes biological decay and automated context pruning.
   - Core decisions, statutory rules, and pinned commitments ($I = 1.0$) are consolidated into long-term permanent storage.
2. **Token Efficiency Target:** Consistently achieves **>85% context token savings** (reducing raw context windows from 1,500+ tokens to <150 tokens without losing critical facts).
3. **Arabic-First NLP Normalizer:** Bare-metal C99 zero-allocation normalizer handling Arabic character forms, diacritics (tashkeel), Eastern Arabic numerals (`٠-٩`), and entity extraction for UAE entities (DHA, DIFC, ADGM, ministries, AED currency amounts).

### 4.3 Sovereign On-Device Privacy (UAE PDPL Law No. 45 of 2021)
- 100% on-device sovereign memory ledger.
- Zero telemetry egress to third-party tracking services or external foundation model training pipelines.

---

## 5. Agent 3 Specification: QALA (القلعة)
**Track:** Best Business AI Agent  
**Domain:** Enterprise Policy Governance, DESC Compliance & Trade Settlement  

### 5.1 DESC ISR v3.1 Security Sandbox
1. **Canonical Path Containment:** Validates all file operations against an authorized workspace root using canonical `realpath()` prefix checking.
2. **Zero Directory Traversal:** Fail-closed blocking of directory escape attempts (`../`, `..%2f`), absolute paths (`/etc/shadow`), and sensitive file access (`.env`, `.git`, `.ssh`).
3. **Command & Script Containment:** Restricts autonomous tool execution to approved, read-only and audited business tasks.

### 5.2 Tau-3 FinOps Policy Gate (AED 50,000 Ceiling)
1. **Statutory Financial Threshold:**
   - Transactions $< \text{AED } 50,000.00$ execute autonomously if compliant.
   - Transactions $\ge \text{AED } 50,000.00$ immediately trigger `VERDICT_REVIEW` and lock execution.
2. **Single-Use Replay-Proof Approval Token:**
   - Unlocking requires a scope-bound approval code (e.g. `QALA-AUTH-DPW-9921`).
   - The token is consumed into a persistent on-disk ledger (`qala-tokens.jsonl`); repeat execution attempts fail closed (`VERDICT_UNSAFE`).

### 5.3 DP World Customs & UAE FTA VAT Settlement
1. **Customs Clearance Calculation:** Automated calculation of 5% UAE Customs Tariff based on Cost, Insurance, and Freight (CIF) valuation.
2. **VAT Reconciliation:** Enforces statutory 5% UAE Federal Tax Authority (FTA) VAT reconciliation, generating audit-compliant tax invoices.
3. **Stateless MCP Transport (JSON-RPC 2.0):** Connects to enterprise ERP systems (SAP, ERPNext) and customs APIs via standard Model Context Protocol.
4. **Case Memory:** SQLite FTS5 BM25 search over historical financial decisions to answer: *"Has this vendor or transaction type been approved previously?"*

---

## 6. Multi-Platform Delivery Matrix (iOS, Android, Web, Desktop)

To win the championship, the agents must be touchable and testable on actual devices by VIP judges.

| Platform | Deployment Technology | Execution Architecture | User Experience Profile |
| :--- | :--- | :--- | :--- |
| **iOS (iPhone & iPad)** | Mobile Progressive Web App (PWA) / Safari Standalone | Client-Side WebAssembly (WASM) C99 Engine + Sovereign API Bridge | Touch-optimized, instant camera/file prescription upload, biometric unlock. |
| **Android** | Progressive Web App (PWA) / WebAPK | Client-Side WASM C99 Engine + Sovereign API Bridge | Full offline caching, fast touch controls, Arabic/English voice input. |
| **Web Browser** | Next.js / React Modern Application | WASM Core + Live WebSocket Telemetry HUD | Multi-column clinical cockpit, drug regimen builder, real-time audit graphs. |
| **Desktop (macOS / Windows)** | Tauri / PWA Desktop Shell | Native C99 dynamic library (`.dylib` / `.so` / `.dll`) or local WASM | High-throughput batch processing for hospital billing and customs filings. |

---

## 7. Strict Truthfulness Policy & Zero-Tolerance Anti-Patterns

### 7.1 Banned Claims (Until Proven by Runnable Machine Command)
1. **No Simulated Models:** Do not claim "Laya 322M" or "Jais 3 7B" unless genuine model weights are executing inference on the target device.
2. **No Fictional Hardware Benchmarks:** All benchmark tables must include date, host machine specifications, and reproducible benchmark commands.
3. **No Redefined Terms:** Data residency means data stays within UAE borders under Federal Law No. 2 of 2019; do not describe file path allowlisting as "data residency".
4. **No Unanchored Citations:** Every statutory claim or drug interaction rule must cite its authoritative source (DHA SN 03/2019 section, SmPC section, or MoHAP Law 30 schedule).

### 7.2 The Tri-Mirror Law
Every repository must remain synchronized across all three mirrors at all times:
$$\text{Local Desktop Workspace} \equiv \text{Google Drive Mirror} \equiv \text{GitHub Remote Repository}$$
Every modification must be verified with `make clean && make test`, committed, pushed to GitHub, and mirrored via `./sync_mirror.sh`.

---

## 8. Phased Implementation Roadmap (From Foundation to Championship Stage)

### Phase 1: Real Knowledge Engines & Formulary Database (Immediate)
- Ingest real structured pharmacological ontology: 100+ common outpatient medications mapped to drug classes, renal cutoffs, CYP/P-gp metabolisms.
- Build class-based C99 clinical evaluation rules to replace 8-drug `if` checks.
- Expand clinical RAG corpus with authoritative SmPCs, BNF guidelines, and MoHAP schedules.

### Phase 2: Live Generative AI & WebAssembly Portability
- Connect a live LLM runner (local GGUF model via `llama.cpp` or sovereign private endpoint) with three dedicated stakeholder system prompts (Doctor, Pharmacist, Patient).
- Compile C99 engines (`libtaryaq`, `libqala`, `libnibras`) to WebAssembly (`.wasm`) using Emscripten.

### Phase 3: Unified Multi-Platform Application (iOS, Android, Web, Desktop)
- Build responsive, touch-friendly UI in Next.js PWA / React:
  - Doctor View: Regimen builder, renal trajectory graph, override modal.
  - Pharmacist View: Claim scrubber, 30-day penalty calculator, controlled drug check.
  - Patient View: Bilingual Arabic/English chat, prescription explainer, emergency triage.

### Phase 4: Video, Pitch & Stage Demonstration
- Record real 2.5-minute video on actual hardware.
- Prepare disconnected air-gap demonstration test.
- Final submission package and number traceability audit.
