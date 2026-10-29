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
**Domain:** End-to-End Clinical Intelligence, Diagnostic Support, Pharmacotherapy & Claim Firewall  
**Founder & Clinical Lead:** Mohamed Fathy, BPharm  

### 3.1 The Full Clinical Journey: From Diagnosis to Care Plan
Taryaq is an end-to-end clinical intelligence partner that assists clinicians throughout the complete patient clinical lifecycle:

```
[1. DIAGNOSIS ASSISTANCE]  Chief Complaint & Labs ──> Ranked Differential Diagnosis (DDx)
            │
            ▼
[2. CLINICAL RESEARCH]     Authoritative Medical RAG ──> Guidelines & Clinical Trials (KDIGO, ADA, ACC/AHA)
            │
            ▼
[3. WRITING MEDICINE]      Phenotype-Matched Rx ──> Class-Based Pharmacology, Posology & Renal Titration
            │
            ▼
[4. COMPLETE CARE PLAN]    Diagnostic Follow-up, Lifestyle Interventions, Monitoring & Clinical Targets
            │
            ▼
[5. PHARMACY & CLAIMS]     Formulary Verification, Law 30 Controlled Checks & DHA SN 03/2019 Claim Scrub
```

#### Step 1: Diagnostic Assistance & Differential Diagnosis (DDx)
- **Clinical Intake & Synthesis:** Ingests Chief Complaint (CC), History of Present Illness (HPI), Review of Systems (ROS), Vitals, Physical Exam, and Lab panels. Formats structured clinical SOAP notes (Subjective, Objective, Assessment, Plan).
- **Ranked Differential Diagnosis (DDx):** Synthesizes symptoms, signs, and biomarkers to generate a prioritized differential diagnosis:
  - *Primary Suspected Etiology* with probability rationale.
  - *Secondary Differentials* to consider.
  - *"Must-Not-Miss" Red Flags* (e.g., Atypical Acute Coronary Syndrome, Sepsis, Pulmonary Embolism, Acute Mesenteric Ischemia).
- **Diagnostic Workup Recommendations:** Suggests high-yield, cost-effective confirmatory lab tests, imaging modalities, and biomarker panels (e.g. Troponin-I, BNP, eGFR, LFTs, D-dimer, HbA1c, urine albumin-to-creatinine ratio).

#### Step 2: Clinical Research & Evidence Retrieval (Deep Medical RAG)
- **Authoritative Practice Guidelines:** Direct, section-chunked indexing of gold-standard clinical guidelines:
  - *Nephrology:* KDIGO (Kidney Disease: Improving Global Outcomes) 2024 Clinical Practice Guidelines.
  - *Endocrinology:* ADA (American Diabetes Association) Standards of Care in Diabetes.
  - *Cardiology:* ACC/AHA Heart Failure and Hypertension Guidelines.
  - *Pulmonology:* GOLD (COPD) and GINA (Asthma) Management Strategies.
  - *Statutory Dubai/UAE Pathways:* DHA Clinical Practice Guidelines and MoHAP Therapeutic Protocols.
- **Evidence-Based Rationale:** Every clinical diagnostic and therapeutic recommendation provides graded evidence (Class I/II/III, Level of Evidence A/B/C) with exact document citations (`doc_id`, `section`, `passage_sha256`).

#### Step 3: Precision Pharmacotherapy & Posology ("Writing Medicine")
- **Phenotype-Matched Drug Selection:** Tailors first-line, second-line, and add-on medications based on patient-specific parameters:
  - Renal function: Exact eGFR calculation (CKD-EPI formula) and stage-dependent dosing.
  - Hepatic reserve: Child-Pugh and MELD classification.
  - Age, weight/BMI, pregnancy/lactation safety categories.
  - Documented allergies and pharmacogenomic/CYP metabolic phenotype.
- **Precise Posology Formulation:**
  - Initial therapeutic dose, titration schedule, and maximum safe ceiling.
  - Administration directions in medical English and culturally fluent Arabic.
  - Dynamic renal/hepatic dose reductions (e.g. 50% dose reduction, extending dosing interval from q12h to q24h).
- **Multidimensional Interaction Shield:** Deterministically intercepts:
  - Drug-Drug Interactions (CYP3A4, CYP2D6, CYP2C9, P-glycoprotein, QT prolongation).
  - Drug-Disease Contraindications (e.g., NSAIDs in Stage 4 CKD, Beta-blockers in severe active bronchospasm).
  - Drug-Food & Timing Interactions (grapefruit CYP3A4 inhibition, calcium/iron chelation with tetracyclines/quinolones).

#### Step 4: Comprehensive Diagnostic & Therapeutic Care Plan
Taryaq generates a structured, holistic patient management plan encompassing both medical and operational tracks:
1. **Pharmacological Prescriptions:** Complete electronic prescription orders with active ingredient, brand name, strength, dosage form, route, frequency, and duration.
2. **Diagnostic Monitoring & Re-Testing Schedule:**
   - Pre-scheduled laboratory follow-up (e.g., repeat serum creatinine and potassium 7–14 days after initiating ACEi/ARB or spironolactone; regular INR tracking for warfarin; therapeutic drug monitoring for vancomycin/tacrolimus).
   - Surveillance imaging and specialist referrals.
3. **Non-Pharmacological & Lifestyle Interventions:**
   - Specific dietary recommendations (e.g., sodium restriction < 2 g/day, potassium management, renal protein goals).
   - Hydration rules, physical activity guidelines, and smoking cessation support.
4. **Explicit Clinical Targets & Milestones:**
   - Target blood pressure (e.g. < 130/80 mmHg in proteinuric CKD).
   - Target HbA1c (< 7.0% or individualized for frail elderly).
   - Target LDL-C (< 55 mg/dL in very high cardiovascular risk).
5. **Patient Safety & Escalation Rules:**
   - Warning symptoms requiring immediate emergency hospital presentation.
   - Self-monitoring instructions (home blood glucose logs, daily morning weights for heart failure).

#### Step 5: Pharmacy Scrubbing, Controlled Drugs & DHA Claims
1. **DHA SN 03/2019 Claim Cycle Scrubber:**
   - Evaluates Dubai `eClaimLink` initial submission and remittance advice resubmission windows.
   - Enforces statutory 30-day grace rule and computes exact daily delay penalties:  
     $$\text{Penalty (AED)} = \max(0, \text{days} - 30) \times 0.03\% \times \text{Net Claim Amount}$$
2. **UAE Controlled Substance Verification (Federal Law No. 30 of 2021):**
   - Classifies medications against MoHAP Schedule 1 (Narcotics), Schedule 2 (Psychotropics), and Semi-Controlled Lists.
   - Validates prescription duration limits (maximum 30 days for narcotics, 3-day emergency prescriptions) and mandatory Emirates ID logging.
3. **Therapeutic Alternative Recommender:** Suggests non-interacting therapeutic alternatives within the same pharmacological class when a severe contraindication is detected.

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
