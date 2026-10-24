# Project Rules, Criteria & Technical Invariants
**Dubai Create AI Agents Championship (2026–2027)**  
**Organizer:** Dubai Chamber of Digital Economy (DCDE)  
**Patronage:** H.H. Sheikh Hamdan bin Mohammed bin Rashid Al Maktoum  
**Prize Pool:** AED 2,500,000+ ($750,000+ USD)  

---

## 1. Statutory Mandates & Competition Invariants

All team members (human engineers and autonomous AI agents) must strictly adhere to these verified rules:

### 1.1 The Anti-Leakage & Data Protection Rule (Strict Disqualification Risk)
* **Official Rule:** *"The solution must protect personal, confidential and organizational data and prevent information leakage. Using real customer or corporate records in demonstration videos or prototypes risks immediate disqualification."*
* **Invariant:** All tests, live stage demos, and video screen recordings must use **100% synthetic datasets** (`benchmarks/dubai_synthetic_suite.json`). Never commit real PII, API keys, patient records, or internal credentials.

### 1.2 Multi-Entry Architecture (3 Targeted Submissions)
The official DCDE rules permit a single team to submit multiple applications without registering twice. Our competition portfolio consists of three distinct entries:
1. **`Qala` (القلعة)** — *Best Business AI Agent* (Sovereign Enterprise Compliance, FinOps, DESC ISR v3.1 Gate, Stateless MCP ERP Bridge).
2. **`Nibras Executive` (نبراس)** — *Best Personal AI Agent* (C-Suite Sovereign Shadow Chief-of-Staff, 97% Context Pruning via FadeMem, Long-Horizon Deal Memory).
3. **`Taryaq` (ترياق)** — *Best Societal AI Agent* (Sovereign Clinical Safety & DHA `eClaimLink` / `Ejadah` Reimbursement Firewall).

### 1.3 Key Competition Dates
* **Initial Registration & Profile Enrolment:** Closes in **December 2026**.
* **Build Phase & Final Deliverables (Code, Deck, 2.5m Video, Report):** Closes in **January 2027**.
* **Grand Final Live Pitch (12 Teams):** First week of **May 2027** in Dubai.

### 1.4 Context Isolation & Mandatory Subagent Spawning Invariant
* **Official Invariant:** To prevent context contamination, prompt bloat, and context window exhaustion, all autonomous AI agents and engineers working on this project MUST delegate research, code auditing, verification, and distinct subtasks to isolated subagents.
* **Execution Boundary:** The primary conversation context must remain dedicated to high-level coordination, architectural synthesis, and decision-making. 
* **Envelope Isolation:** Intermediate tool outputs, raw grep traces, file dumps, and multi-step investigation logs must be contained within the subagent's execution envelope and discarded after synthesis, returning only concise, actionable findings to the primary agent.
* **Recursion Guard:** Subagents must operate with bounded turn limits (max 5 turns) and must never spawn unbounded recursive child agent chains.

---

## 2. Technical & Architectural Standards

### 2.1 Pure Bare-Metal C99 Core
* All adapter code must conform strictly to **ISO C99** (`-std=c99 -Wall -Wextra -Werror -O2`).
* Zero dynamic Python interpreter bloat, zero runtime dependency hell.
* All code must compile cleanly on both Linux (`gcc`) and macOS (`clang`).

### 2.2 Sovereign Air-Gapped Local Inference
* All foundation model inference must run 100% locally over **Unix Domain Sockets (`AF_UNIX`)** using `llama.cpp` or `vLLM`.
* Zero bytes of prompt or enterprise context may traverse foreign cloud APIs.
* **Primary Foundation Model:** **`Jais 3 (7B/13B)`** (Inception42/MBZUAI) for bilingual Arabic/English 512K-token reasoning.
* **Background Daemon:** **`Falcon3-Mamba-7B`** (TII Abu Dhabi) for $O(1)$ constant memory background goal execution.
* **Constrained Function Calling:** Enforce strict **GBNF grammars** on all local model tool outputs to eliminate syntax and argument drift.

### 2.3 Universal Enterprise Connectivity via Stateless MCP
* Implement the **Stateless Model Context Protocol (`2026-07-28` specification)** over Streamable HTTP.
* Mandatory request headers:
  * `Content-Type: application/json`
  * `Accept: application/json`
  * `MCP-Protocol-Version: 2026-07-28`
  * `Mcp-Method: tools/call` (or `tools/list`)
* Use battle-tested **`libcurl`** and **`cJSON`** for transport and serialization. Never rewrite custom raw socket HTTP parsers.

### 2.4 Deterministic Policy Gatekeeping & Kernel Sandboxing
* Intercept every tool call before execution with `policy_verify_call()`.
* On Linux, apply **Linux Landlock LSM** with the mandatory `prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)` invariant.
* Require single-use, scope-bound cryptographic approval codes (`approval_code`) for state mutations or transactions exceeding **AED 50,000**.
* Write tamper-evident, append-only JSONL audit logs (`qala-audit.jsonl`) with sanitized strings (`json_escape_string`) and synchronized timestamps.

---

## 3. Formatting, Currency & Timezone Conventions

* **Currency:** All financial figures and policy thresholds must use **AED** (United Arab Emirates Dirham).
* **Timezone:** Human-facing reports, slides, and logs use **`Asia/Dubai` (`UTC+4`)**.
* **Audit Timestamps:** All machine-readable JSONL logs and SQLite records must use strict **ISO-8601 UTC** epoch integers.
* **Language:** All official submission materials (pitch decks, summary reports, video audio/captions) must be in **English only**, with bilingual Arabic capabilities demonstrated within the agent interface.
