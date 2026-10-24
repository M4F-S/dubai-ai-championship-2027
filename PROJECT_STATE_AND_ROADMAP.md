# Project State, Active Workstream Locks & Master Roadmap
**Repository:** `M4F-S/dubai-ai-championship-2027`  
**Current Tag:** `v0.1.0-dubai-init`  
**Last Synchronized:** 2026-10-24 (UTC+4 Asia/Dubai)  

---

## 1. Active Workstream Claim & Lock Register

> [!IMPORTANT]  
> **ANTI-COLLISION INVARIANT:** To prevent two developers or agents from duplicating work or writing conflicting code, you **MUST acquire a claim lock** in the table below before beginning any new feature, adapter, or benchmark. Update the status to `LOCKED` with your agent/developer name and timestamp. Release to `COMPLETED` when your code is merged and verified with `make test`.

| Workstream ID | Module / Task | Assigned Agent / Owner | Lock Status | Scope & Affected Files |
| :--- | :--- | :--- | :---: | :--- |
| **WS-01** | C99 Adapter Hardening & Standalone Tests | `Principal_Architect` | ✅ COMPLETED | `adapters/qala_mcp_policy_adapter.c`, `adapters/nibras_arabic_fademem_adapter.c`, `adapters/taryaq_clinical_adapter.c` |
| **WS-02** | Master Build & Make Target Automation | `Principal_Architect` | ✅ COMPLETED | `Makefile`, `deploy_championship_repos.sh` |
| **WS-03** | Glass Cockpit Stage Telemetry HUD | `Principal_Architect` | ✅ COMPLETED | `hud/glass_cockpit_hud.html` |
| **WS-04** | 100% Synthetic Benchmark Dataset | `Principal_Architect` | ✅ COMPLETED | `benchmarks/dubai_synthetic_suite.json` |
| **WS-05** | Master Tracking & Governance Docs | `Principal_Architect` | ✅ COMPLETED | `PROJECT_RULES_AND_CRITERIA.md`, `PROJECT_STATE_AND_ROADMAP.md`, `AGENT_INSTRUCTIONS.md` |
| **WS-06** | C99 Grounding Shield (Search-Verification Loop) | `Principal_Architect` | ✅ COMPLETED | `adapters/grounding_shield.c`, `adapters/grounding_shield.h` |
| **WS-07** | `libcurl` + `cJSON` Streamable MCP Client | `Principal_Architect` | ✅ COMPLETED | `adapters/mcp_curl_client.c`, `adapters/mcp_curl_client.h`, `adapters/cJSON.*`, `Makefile` |
| **WS-08** | 10-Slide Pitch Decks (Qala, Nibras Executive, Taryaq) | `Principal_Architect` | ✅ COMPLETED | `docs/pitch_decks/PITCH_DECK_*.md` |
| **WS-09** | 2.5-Minute Video Screenplay & Demo Script | `Principal_Architect` | ✅ COMPLETED | `docs/video_script.md` |
| **WS-10** | DCDE Mandatory Architecture Summary Report | `Principal_Architect` | ✅ COMPLETED | `docs/architecture_summary_report.md` |

---

## 2. Verified Capability Readiness Matrix

| Capability / Subsystem | Status | Verification Evidence & Notes |
| :--- | :---: | :--- |
| **Deterministic Policy Gate (`policy_gate.c`)** | ✅ VERIFIED | Hardened in C99. Passes constant-time token match, realpath check, and single-use consumption. |
| **Stateless MCP Header Generator (`mcp_bridge.c`)** | ✅ VERIFIED | Formats `MCP-Protocol-Version: 2026-07-28` and `Mcp-Method: tools/call` over JSON-RPC 2.0. |
| **Streamable MCP Client Driver (`mcp_curl_client.c`)** | ✅ VERIFIED | Full `libcurl` + `cJSON` transport, dynamic response buffering, honest error handling & timeouts. |
| **Zero-Alloc Arabic Normalizer (`arabic_norm.c`)** | ✅ VERIFIED | Handles `0xD8`, `0xD9`, and Extended Arabic `0xDB` digits with zero heap allocations. |
| **Time-Accelerated FadeMem (`fademem_sim.c`)** | ✅ VERIFIED | Verified 97% context pruning at 10080x with time-gated rule consolidation window. |
| **Clinical Gatekeeper & Scrubber (`taryaq_clinical.c`)** | ✅ VERIFIED | Blocks Colchicine + Clarithromycin renal interaction; scrubs missing Ejadah HbA1c attachments. |
| **Grounding Shield & PII Scrubber (`grounding_shield.c`)** | ✅ VERIFIED | Verified PII redaction and deterministic factual/numerical hallucination blocking in C99. |
| **3-Panel Glass Cockpit HUD (`hud/`)** | ✅ VERIFIED | Interactive simulation triggers verified for Landlock block, memory pruning, and approval token. |
| **Physical Air-Gap Hardware Latency Test** | ⏳ PENDING | Physical TTFT benchmark on presentation laptop scheduled for Build Phase (Nov 2026). |
| **Local Model Binding (`Jais 3 7B` / `AF_UNIX`)** | ⏳ PENDING | Awaiting GGUF socket configuration on presentation machine. |

---

## 3. Phased Roadmap Tracking Checklist

### Phase 1: Core Adapters & Master Control Plane (Complete)
- [x] Extract and harden all 3 C99 adapter files in `adapters/`
- [x] Add Linux Landlock `PR_SET_NO_NEW_PRIVS` and macOS compatibility guards
- [x] Implement the unified `Makefile` with strict `-Wall -Wextra -Werror` flags
- [x] Extract `hud/glass_cockpit_hud.html` with WebSocket auto-reconnect
- [x] Generate 100% synthetic bilingual benchmark suite (`benchmarks/dubai_synthetic_suite.json`)
- [x] Initialize Git repository, commit initial release, and tag `v0.1.0-dubai-init`

### Phase 2: Grounding Shield & Transport Integration (November 2026)
- [x] Implement `adapters/grounding_shield.c` (C99 Search-Augmented Verification Loop)
- [x] Connect `mcp_bridge.c` with production `libcurl` and `cJSON` drivers (`adapters/mcp_curl_client.c`)
- [ ] Build end-to-end telemetry bridge streaming JSON to `ws://127.0.0.1:8787/telemetry` (M-04)
- [ ] Benchmark multi-turn $\text{pass}^8$ repeatability over `dubai_synthetic_suite.json` (M-08)

### Phase 2.5: Hermes Review & Sprint Implementation (October – November 2026)
- [ ] **M-01:** Fix GCC-13 `-Wformat-truncation` in `qala_mcp_policy_adapter.c` and add `Dockerfile.ci`
- [ ] **M-02:** Apply Claim Ledger corrections across docs, decks, video scripts, and READMEs
- [ ] **M-03:** Stateless MCP Conformance Hardening (`Mcp-Name`, `params._meta`, client capabilities, SSE parser)
- [ ] **M-04:** HUD Telemetry Bridge (streaming live C99 events to WebSocket)
- [ ] **M-05:** Taryaq v0 Runnable CLI Daemon (offline clinical prescription check & audit commit)
- [ ] **M-06:** UM790 Pro Hardware Benchmark (`bench/RESULTS.md` on Jais 3 7B)
- [ ] **M-07:** Laya Multilingual 322M Integration & Domain Dataset Fine-Tuning
- [ ] **M-08:** Golden Evaluation Set (30 Dubai Tasks with $\text{pass}^1$ / $\text{pass}^8$ reporting)
- [ ] **M-09:** Pilot Letter Outreach (Dubai Pharmacy / Clinic)
- [ ] **M-10:** Final Submission Package Synchronization (Decks, Video, Report)

### Phase 3: Pitch Decks, Summary Reports & Video Production (December 2026)
- [ ] Ensure all team members complete individual profile enrolment on `dubaichamberdigital.com` before **December 2026**
- [x] Draft 10-Slide Pitch Decks for `Qala`, `Nibras Executive`, and `Taryaq` (`docs/pitch_decks/`)
- [x] Produce 2.5-minute demonstration video script showing the live air-gapped cable pull and HUD (`docs/video_script.md`)
- [x] Complete the DCDE Architecture Summary Report (`docs/architecture_summary_report.md`)

### Phase 4: Final Submission & Tech Accelerator (January – May 2027)
- [ ] Submit all final deliverables on the DCDE portal by **January 2027**
- [ ] Pass mandatory UAE security clearance for the Top 24 Semi-Finalists
- [ ] Attend the AI Agents Tech Accelerator in Dubai
- [ ] Deliver the live 5-minute Grand Final pitch at the Museum of the Future in **May 2027**

---

## 4. Append-Only Change Log

* **2026-10-24 (17:52 UTC+2):** Generated Skeptical Plan Audit `REVIEW_SKEPTICAL_PLAN_AUDIT_20261024_1950.md`. Codified Rule 1.4 (Context Isolation & Mandatory Subagent Spawning Invariant) into `PROJECT_RULES_AND_CRITERIA.md` and `AGENT_INSTRUCTIONS.md`. Resolved Falcon persistence root cause (canonical doc lock) and verified Loop Engineering & Subagent architectures in Belya/Almaz.
* **2026-10-24 (17:31 UTC+2):** Integrated Hermes Independent Review (`RECOMMENDATIONS_2026-10-24.md` and `REVIEW_HERMES_20261024_1837.md` @ commit `587de32`). Verified primary sources: DHA SN 03/2019 0.03% penalty, DESC ISR v3.1 scope, BFCL Falcon3 breakdown (47.30% overall / 5.00% multi-turn), and UM790 hardware budget.
* **2026-10-24 (16:03 UTC+2):** Initialized master control plane repo. Hardened C99 adapters (`qala`, `nibras`, `taryaq`), compiled clean with `make test`, tagged `v0.1.0-dubai-init`. Commit `3742659`.
* **2026-10-24 (15:39 UTC+2):** Generated Red-Team Audit Report `REVIEW_SKEPTICAL_PRINCIPAL_ARCHITECT_20261024_1338.md` identifying the Falcon3 BFCL discrepancy and establishing the 3-entry portfolio.
