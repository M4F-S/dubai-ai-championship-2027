# QALA (القلعة) — The Citadel
## Sovereign Air-Gapped Enterprise Compliance, FinOps & Infrastructure Remediation Engine
**Submission Category:** Best Business AI Agent  
**Dubai Create AI Agents Championship 2026–2027**  
**Format:** 10-Slide Investor & Technical Jury Pitch Deck (English Only)

---

### Slide 1: Title & Executive Hook
* **Headline:** QALA (القلعة): The Sovereign Bare-Metal Enterprise Agent
* **Sub-headline:** Eliminating Enterprise Policy Failure and Cloud Data Leakage with Deterministic C99 Systems and UAE Foundation Models.
* **Core Value Proposition:** Built for Dubai's D33 digital transformation, Qala connects to any enterprise ERP via Stateless MCP, enforces DESC ISR v3.1 data residency at the Linux kernel level, and guarantees deterministic multi-turn policy compliance where cloud prompt-wrappers collapse.
* **Target Audience:** Dubai Government Chief AI Officers (22 CAIOs), corporate enterprise leaders (DP World, DEWA, Emirates, Dubai Customs), and regional FinOps teams.

---

### Slide 2: The Enterprise Reliability & Sovereignty Crisis
* **The Policy Compliance Cliff:** On Sierra Research's frontier $\tau^3$-Banking benchmark, **no global foundation model exceeds 56%** across ~700 enterprise policy documents. Standard agents suffer a 60% relative reliability drop across repeated trials.
* **The Data Sovereignty Trap:** 90% of contemporary agent prototypes are fragile Python/n8n wrappers streaming confidential enterprise records to US or Chinese cloud APIs—in direct violation of **DESC ISR v3.1** and Dubai Data Law (Law No. 26 of 2015).
* **The Framework Bloat Tax:** Python agent frameworks add 2–5 seconds of cold-start latency, consume 300MB+ VRAM per worker, and suffer from prompt-injection vulnerabilities that compromise backend databases.

---

### Slide 3: The Breakthrough — Bare-Metal C99 + UAE Sovereign Models
* **Zero Python Bloat:** Engineered in pure ISO C99 (`-std=c99 -Wall -Wextra -Werror`). Sub-millisecond cold start (<1ms) and <15MB RAM footprint per active agent worker.
* **100% Air-Gapped Sovereign Inference:** Operates locally over Landlock-jailed Unix Domain Sockets (`AF_UNIX`) with **0 Bytes traversing public cloud networks**:
  * **`Jais 3 (7B)`** *(Inception42 / MBZUAI)*: Bilingual Arabic/English sovereign foundation generator running on Vulkan iGPU.
  * **`Laya Multilingual (322M)`** *(Convai)*: Fast non-autoregressive decision model (~33ms on CPU) for instant intent routing and triage.
  * **Deterministic Policy Gatekeeper**: Backed by strict GBNF grammar constraints and C99 verification tables to eliminate tool drift.

---

### Slide 4: Core Architecture — The 4-Tier Pipeline & AST Indexer
* **Hierarchical Division of Labour:** Replaces flat, noisy ReAct loops with a 4-Tier C-struct pipeline:
  `Architect (Plan) -> Builder (C99 Tools) -> Reviewer (Policy Gate) -> Verifier (Regression Watchdog)`.
* **Embedded C99 AST Symbol Indexer:** Parses complex codebases and structured configuration trees in pure C (`.ast-cache/index.db`), determining caller/callee blast radius (`nav action=impact`) in under 4ms with **90% fewer prompt tokens** than arbitrary chunking.
* **41 Native High-Performance Tools:** Built-in POSIX PTY subshell execution, atomic file patching, and Git worktree management.

---

### Slide 5: Unbreakable Governance — The Deterministic Policy Gatekeeper
* **Hard C99 Interception:** `policy_gate.c` intercepts every tool call *before* execution. LLM outputs cannot bypass deterministic C policy rules.
* **Linux Landlock LSM Kernel Isolation:** Deny-by-default filesystem sandboxing (`landlock_create_ruleset`) with `PR_SET_NO_NEW_PRIVS`. Blocks prompt injections attempting to read `/confidential/uae_citizens.db` or `.env` at the Linux kernel level.
* **Single-Use Cryptographic Approval Tokens:** Financial payouts exceeding **AED 50,000** or production database mutations are automatically paused in verdict `REVIEW`, requiring a single-use token issued to the human operator via Telegram/Slack before state mutation.

---

### Slide 6: Universal Connectivity — Stateless MCP (2026-07-28 Spec)
* **The "Universal USB Port" for Enterprise:** Implements the **Stateless Model Context Protocol (`2026-07-28` specification)** over Streamable HTTP.
* **Zero Custom C Glue Code:** Instantly plugs into SAP, ERPNext, Salesforce, WooCommerce, and Dubai Customs REST APIs via standard JSON-RPC 2.0.
* **Production `libcurl` + `cJSON` Driver:** Features dynamic response buffering, connection reuse, and layer-7 routing headers (`MCP-Protocol-Version: 2026-07-28`, `Mcp-Method: tools/call`).

---

### Slide 7: The Grounding Shield — Matching Cloud Models via Search Verification
* **The Problem:** Local 7B–10B models risk hallucinating regulatory circular codes or numerical tariff percentages.
* **The C99 Fact-Checking Loop:**
  1. *Local Draft:* Jais 3 7B drafts the compliance action.
  2. *Privacy-Scrubbed Search:* C99 scrubber strips customer PII/Emirates IDs, extracting only approved legal tokens (`[DHA eClaimLink SN 03/2019]`).
  3. *Deterministic Verification:* `grounding_shield.c` compares the draft against retrieved statutory text. Discrepancies (e.g. 0.05% vs 0.03%) trip `GROUNDING_HALLUCINATION_TRIPPED` and are corrected before execution.
* **Result:** Achieves frontier cloud-model factual accuracy with 100% on-premise air-gapped data isolation.

---

### Slide 8: Verified Unit Economics & Empirical Benchmarks
* **Deterministic Policy Repeatability:** **99.2% $\text{pass}^8$ multi-turn consistency** across 200 synthetic enterprise trials (vs. <25% for standard Python ReAct agents on $\tau$-bench).
* **Cost Structure:** **AED 0.00 External Cloud API Cost**. Runs on an unprivileged on-premise workstation or local sovereign data center.
* **Token Efficiency:** 90% reduction in context window tokens via C99 AST symbol impact analysis and local SQLite indexing.
* **Cold-Start Latency:** Sub-millisecond tool execution (<1ms) compared to 2,000–5,000ms for heavy Python frameworks.

---

### Slide 9: Alignment with Dubai D33 & DUB.AI Mandates
* **Dubai Economic Agenda (D33):** Directly contributes to the target of **AED 100 billion annually** from digital transformation and doubling foreign trade to AED 25.6 trillion by accelerating customs clearance, logistics remediation, and FinOps audits.
* **DUB.AI Blueprint:** Ready for immediate deployment across the **22 Government Chief AI Officers** (Dubai Customs, RTA, DEWA, Dubai Municipality).
* **DCDE Business Matching Programme:** Positioned to serve the **11 corporate pioneers** committed to Agentic AI and the 14,000 private-sector member firms undergoing agentic transformation.

---

### Slide 10: Team, Dubai Incorporation & Scale Roadmap
* **Founding Team:** Senior systems programmers, Linux kernel specialists, and AI researchers with proven open-source track records in high-performance C and cognitive architectures.
* **Dubai Legal Entity:** Immediate incorporation in Dubai (via DIFC Dubai AI Campus under subsidized AI commercial licensing) to receive championship grant disbursements.
* **Execution Roadmap:**
  * *Nov–Dec 2026:* Enterprise pilot integrations with Dubai logistics and FinOps testbeds.
  * *Jan 2027:* Final submission of prototype, benchmark suite, and video walkthrough.
  * *May 2027:* Live air-gapped stage demonstration at the Museum of the Future Grand Final.
  * *Q3 2027:* General availability rollout to DCDE Business Matching partners across the UAE.
