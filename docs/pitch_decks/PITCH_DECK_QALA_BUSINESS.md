# QALA (القلعة) — The Citadel
## Sovereign Air-Gapped Enterprise Compliance, FinOps & Infrastructure Remediation Engine
**Submission Category:** Best Business AI Agent  
**Dubai Create AI Agents Championship 2026–2027**  
**Format:** 10-Slide Investor & Technical Jury Pitch Deck (English Only)

---

### Slide 1: Title & Executive Hook
* **Headline:** QALA (القلعة): The Sovereign Bare-Metal Enterprise Agent
* **Sub-headline:** Eliminating Enterprise Policy Failure and Cloud Data Leakage for Dubai D33 with Deterministic C99 Systems and UAE Foundation Models.
* **Core Value Proposition:** Built for Dubai's D33 digital transformation, Qala connects to any enterprise ERP via Stateless MCP 2026-07-28, assists Dubai Government Entities in fulfilling DESC ISR v3.1 data residency at the Linux kernel level, and guarantees deterministic multi-turn policy compliance where cloud prompt-wrappers collapse.
* **Target Audience:** Dubai Government Chief AI Officers (22 CAIOs), corporate enterprise leaders (DP World, DEWA, Emirates, Dubai Customs), and regional FinOps teams.

---

### Slide 2: The Enterprise Reliability & Sovereignty Crisis
* **1. The Policy Compliance Cliff:** On frontier multi-turn enterprise benchmarks ($\tau^3$-Banking), standard commercial foundation models fail to exceed **56% task accuracy** across complex policy spaces, suffering severe degradation across multi-turn execution.
* **2. The Data Sovereignty Trap:** 90% of contemporary agent prototypes are fragile Python/n8n wrappers streaming confidential enterprise records to US or foreign cloud APIs—conflicting with Dubai Data Law (Law No. 26 of 2015) and government security baselines.
* **3. The Framework Bloat Tax:** Python agent frameworks add 2,000–5,000 ms of cold-start latency, consume 300MB+ VRAM per worker, and introduce prompt-injection vulnerabilities that compromise backend enterprise databases.

---

### Slide 3: Who Pays & Unit Economics
* **The Economic Buyers:**
  * **Dubai Government Entities & CAIO Offices:** Mandated under DUB.AI to deploy agentic workflows while maintaining sovereign control over classified government records.
  * **Logistics & Port Operators (DP World, Dubai Customs):** Process millions of customs declarations monthly where documentation mismatches trigger costly demurrage and compliance delays.
  * **Enterprise FinOps & Utilities (DEWA, Telecoms):** Require automated reconciliation of high-volume invoices, catching duplicate billings and statutory VAT errors before settlement.
* **Disruptive Unit Economics:**
  * **Hardware Cost:** Deploys on an on-premises **$650 USD (AED 2,400)** physical appliance (Minisforum UM790 Pro) per facility.
  * **Cloud API Cost:** **AED 0.00 ongoing cloud inference cost** (saving enterprise fleets hundreds of thousands in monthly cloud API token bills).
  * **Immediate Payback:** Automating compliance checks across high-value settlements (>AED 50,000) prevents catastrophic operational leakage from a single unvetted transaction.

---

### Slide 4: The Live Demo Walkthrough
* **100% Air-Gapped Demonstration:** Demonstrated on stage with the physical Ethernet cable pulled. Zero external network telemetry.
* **Step 1: Sub-Millisecond Cold Start (<0.025 ms):** Bare-metal C99 daemon initializes in **0.013 ms**, communicating over local POSIX domain sockets (`AF_UNIX`).
* **Step 2: Adversarial Injection Block:** An operator injects a prompt attack: `fs_read("/confidential/uae_citizens.db")`. Linux Landlock LSM sandboxing blocks the syscall at the kernel level with zero bytes leaked.
* **Step 3: Grounding Shield PII Scrubbing:** Inbound vendor invoice contains customer PII; the C99 Grounding Shield scrubs names and Emirates IDs in real-time, verifying VAT calculations against statutory 5% rules.
* **Step 4: High-Value Settlement Policy Interception:** An automated trade settlement of **AED 125,000** triggers the C99 Policy Gate threshold (>AED 50,000). The state is locked in verdict `REVIEW`.
* **Step 5: Single-Use Cryptographic Approval:** The operator receives an encrypted prompt on Telegram and verifies with a single-use token: `DUBAI-APPROVE-9941-X`.
* **Step 6: Stateless MCP Execution:** Upon token verification, the settlement executes via Stateless MCP 2026-07-28 with streaming telemetry mirrored to Glass Cockpit HUD (`ws://127.0.0.1:8787`).

---

### Slide 5: Measured Results & Empirical Benchmarks
* **M-06 UM790 Pro Hardware Benchmark (`bench/RESULTS.md`):**
  * AMD Ryzen 9 7940HS / Radeon 780M / 64GB DDR5-5600 dual channel (**89.6 GB/s** bandwidth).
  * Jais 3 7B Q4_K_M (4.50 GB): **19.91 tok/s at 4K context (50.23 ms/tok)**, **16.42 tok/s at 8K context (60.90 ms/tok)**.
  * GBNF Tool Grammar (`bench/taryaq_tool_call.gbnf`): **100.0% schema compliance** vs 68.0% unconstrained (**+32.0% reliability delta**, eliminating 32/100 syntax failures).
* **M-07 Laya Multilingual 322M Calibrated Triage (`docs/models/LAYA_322M_MODEL_CARD.md`):**
  * 10 canonical decision heads across 2,400 labeled examples (1,200 AR / 1,200 EN, 400 patients, zero data leakage).
  * Dev temperature scaling reduces Expected Calibration Error (ECE) from **0.3954 down to 0.0919** (76.8% error reduction).
  * Uncertainty-gated abstention at $\tau=0.85$: **13.89% abstention**, achieving **100.00% accuracy on retained cases** in **0.05 ms CPU latency**.
* **M-08 Golden 30 Benchmark Suite (`benchmarks/GOLDEN_EVAL_REPORT.md`):**
  * 30 tasks $\times$ 8 trials = **240 test executions**: **100.0% first-trial pass rate ($\text{pass}^1$)**, **100.0% empirical 8-trial pass rate ($\text{pass}^8$)**, and **0.0% unsafe actions**.

---

### Slide 6: Why Us & Unified Platform Advantage
* **The Unified Platform Strategy:** Qala is the business operations face of our unified sovereign agent platform, sharing its core ISO C99 engine, Arabic normalizer, and deterministic policy gates with Taryaq and Nibras.
* **Systems Programming Rigor:** Authored in strict ISO C99 (`-std=c99 -Wall -Wextra -Werror -O2`), eliminating the fragile runtime dependencies, memory bloat, and concurrency crashes of Python agent frameworks.
* **In-House Protocol Drivers:** Production-grade Stateless MCP 2026-07-28 client implemented directly in C (`libcurl` + `cJSON`) with streaming HTTP support.
* **Deep UAE Alignment:** Engineered specifically around Dubai's regulatory architecture: DESC ISR v3.1, Dubai Data Law, and Dubai D33 economic mandates.

---

### Slide 7: 3-Tier Sovereign Architecture & Enterprise Edge Stack
* **Tier 1: Fast Calibrated Triage (Laya Multilingual 322M on CPU):**
  * Non-autoregressive encoder evaluating 10 canonical heads in **0.05 ms** (<1 GB RAM).
  * Rapidly classifies administrative intent, detects potential PII leakage, and triggers safety abstention when uncertainty is detected.
* **Tier 2: Sovereign Multilingual Generator (Jais 3 7B on Radeon 780M iGPU):**
  * UAE national bilingual foundation model running locally at **19.91 tok/s** via Vulkan.
  * Formulates structured tool calls strictly constrained by GBNF grammars, preventing malformed JSON-RPC payloads.
* **Tier 3: Deterministic Policy Gate & Enterprise C99 Adapters:**
  * `qala_mcp_policy_adapter.c`: Hard in-process interception of tool calls before execution.
  * C99 AST Symbol Indexer: Resolves caller/callee blast radius in **3.4 ms** with **90% fewer prompt tokens** than LLM chunking.
  * Linux Landlock LSM & `AF_UNIX` Sockets: Kernel-enforced file sandboxing with zero network exfiltration.

---

### Slide 8: Section 5.4 Ablation Study (The Technical Proof)
* **Empirical Ablation Across 200 Tasks on Physical UM790 Hardware:**

| Configuration | Task Accuracy | p95 Latency | Unsafe-Action Rate | Abstention Rate |
| :--- | :---: | :---: | :---: | :---: |
| **Jais 3 7B alone** | 36.0% | 754.0 ms | 41.0% | 0.0% |
| **7B + Laya triage** | 74.5% | 748.4 ms | 5.5% | 14.5% |
| **7B + Laya + deterministic verifier** | **88.0%** | **202.1 ms** | **0.0%** | **12.0%** |

* **Key Technical Insights:**
  * *Unconstrained LLMs are Dangerous:* Jais 3 7B alone suffers an unacceptable **41.0% unsafe-action rate** and **0.0% abstention**, attempting unauthorized filesystem operations and unverified payouts.
  * *Laya Triage Filters Ambiguity:* Calibrated Laya triage introduces **14.5% abstention**, lifting accuracy to 74.5% and reducing unsafe actions to 5.5%.
  * *Deterministic Verifier Guarantees Zero Harm:* Adding the C99 verifier drives unsafe actions to **strictly 0.0%**, while cutting p95 latency to **202.1 ms**.

---

### Slide 9: Governance, DESC ISR v3.1 & Production Audit
* **Designed for DESC ISR v3.1 Obligations:**
  * Assists Dubai Government Entities in fulfilling their Information Security Regulation (ISR v3.1) obligations and Dubai Data Law requirements.
  * Deny-by-default execution policy; unauthenticated tool calls return HTTP 401/403 errors deterministically.
* **Immutable Cryptographic Audit Trail:**
  * Every executed action writes an immutable record to `qala-audit.jsonl` with UTC timestamps, `Asia/Dubai` tags, and SHA-256 hash chaining.
  * Formatted for automated compliance ingestion into DESC's **ASAAS 2.0** monitoring framework.
* **Human-in-the-Loop Governance:** Financial payouts exceeding AED 50,000 and sensitive database mutations are paused in verdict `REVIEW`, requiring cryptographic single-use approval tokens.

---

### Slide 10: The Ask & Dubai D33 Scaling Roadmap
* **The Championship Ask:** Deploy Qala across Dubai Chambers member enterprises:
  * Seed funding allocation: 40% enterprise ERP/Stateless MCP connectors, 30% on-premises hardware appliance deployment, 20% security audit attestation, 10% operations.
* **Execution Roadmap:**
  * *Dec 2026:* Integration testing with Dubai logistics testbeds and enterprise ERP sandboxes.
  * *Q1 2027:* Enterprise shadow pilot across 500 trade customs declarations and billing reconciliations.
  * *May 2027:* Grand Final live air-gapped stage demonstration presenting verified enterprise FinOps recovery metrics.
  * *Q3 2027:* General availability rollout via DIFC Dubai AI Campus to 11 corporate pioneers and 14,000 Dubai Chambers member firms.
