# DUBAI AI CHAMPIONSHIP 2026–2027: MASTER ORCHESTRATION SPECIFICATION
## The Sovereign Tri-Agent Platform (Taryaq, Qala, Nibras)
**System Role:** Master Control Plane, Integration Test Harness & Governance Engine  
**Version:** 2.0 (Canonical Implementation Contract)  
**Author:** Mohamed Fathy, BPharm (Lead Systems Architect & Founder)

---

### 1. Platform Vision: Sovereign Edge Intelligence for Dubai
The Dubai AI Championship platform unifies three sovereign AI agents engineered for the three pillars of Dubai's future:
1. **Taryaq (Societal):** Air-gapped clinical copilot, 100+ drug pharmacovigilance engine, DHA SN 03/2019 claims scrubber, and 24/7 bilingual patient health companion.
2. **Qala (Business):** Autonomous enterprise operating system and corporate agency mesh (Managing Director + 6 departmental agents) governed by C99 DESC ISR v3.1 sandboxing and Tau-3 FinOps gates (> AED 50k ceiling).
3. **Nibras (Personal):** Dubai sovereign life OS, civic navigator (GDRFA Golden Visa, DLD Ejari, DEWA, RTA, KHDA), and executive family office twin with biological FadeMem context pruning (> 85% token reduction).

```
                            ┌──────────────────────────────────────────────┐
                            │    DUBAI MASTER ORCHESTRATION & CONTROL      │
                            │             (/Desktop/Dubai)                 │
                            ├──────────────────────┬───────────────────────┤
                            │ • Canonical PRD/Spec │ • Tri-Mirror Syncer   │
                            │ • Integration Bench  │ • Audit Verifier      │
                            └───────────┬──────────┴───────────┬───────────┘
                                        │                      │
             ┌──────────────────────────┼──────────────────────┴───────────────────┐
             ▼                          ▼                                          ▼
 ┌───────────────────────┐  ┌───────────────────────┐                  ┌───────────────────────┐
 │     TARYAQ REPO       │  │       QALA REPO       │                  │      NIBRAS REPO      │
 │   (/taryaq-agent)     │  │     (/qala-agent)     │                  │    (/nibras-agent)    │
 ├───────────────────────┤  ├───────────────────────┤                  ├───────────────────────┤
 │ • 100+ Drug SQLite DB │  │ • Corporate Mesh (6)  │                  │ • Civic Navigator (6) │
 │ • Tri-Modal Interfaces│  │ • Tau-3 FinOps 50k    │                  │ • FadeMem Pruning     │
 │ • DHA Claim Engine    │  │ • DESC ISR v3.1 Box   │                  │ • Family Office Vault │
 └───────────────────────┘  └───────────────────────┘                  └───────────────────────┘
             │                          │                                          │
             └──────────────────────────┼──────────────────────────────────────────┘
                                        ▼
                  ┌──────────────────────────────────────────┐
                  │       INVIOLABLE C99 SAFETY KERNEL       │
                  │        (libdubai_adapters.so)            │
                  │   - Sub-0.05ms Deterministic Latency     │
                  │   - SHA-256 HMAC Hash Chaining           │
                  │   - 100% Air-Gapped UAE Edge Hardware    │
                  └──────────────────────────────────────────┘
```

---

### 2. The Tri-Mirror Law (Synchronous Governance)
To maintain absolute configuration integrity across the championship:
$$\text{Local Workspaces (Desktop)} \equiv \text{Google Drive Mirror} \equiv \text{GitHub Remote Repositories}$$
- Every change MUST be committed via feature branches and Pull Requests.
- Direct pushes to `main` are blocked by branch protection (`enforce_admins=true`).
- CI workflows (Linux GCC-13) must pass before merging.
- `./sync_mirror.sh` synchronizes local repos with Google Drive.

---

### 3. Canonical C99 Safety Kernel Shared ABI

All three agents share an identical, high-performance C99 core compiled into `build/libdubai_adapters.so` (or `.dylib` on macOS):
- `adapters/grounding_shield.c` & `grounding_shield.h`: Cryptographic citation validation and anti-hallucination grounding.
- `adapters/taryaq_clinical_adapter.c` & `taryaq_adapters.h`: Deterministic pharmacovigilance and DHA SN 03/2019 claims penalty calculations.
- `adapters/qala_mcp_policy_adapter.c` & `qala_adapters.h`: DESC ISR v3.1 filesystem sandboxing and Tau-3 FinOps approval gating.
- `adapters/nibras_arabic_fademem_adapter.c` & `nibras_adapters.h`: Zero-allocation UTF-8 Arabic text normalizer and Ebbinghaus half-life memory decay.

---

### 4. Master Verification Script (`scripts/verify_all.sh`)

A single, tamper-evident verification script executes the full championship battery:
1. **Compilation Check:** Compiles all C99 adapters, standalone binaries, and shared libraries with `-Wall -Wextra -Werror -O2`.
2. **Audit Ledger Verification:** Generates cryptographic audit ledgers and validates HMAC-SHA256 sequential integrity using `verify_audit.py`.
3. **Tamper Rejection Test:** Injects synthetic bit flips and field alterations into the audit ledger and verifies the verifier immediately halts closed with `VERIFIED_TAMPER_E`.
4. **Agent Scenario Conformance:** Runs acceptance tests across Taryaq, Qala, and Nibras.
5. **Drift & Cleanliness Check:** Verifies that no uncommitted files or un-tracked runtime databases dirty the git status.

---

### 5. Implementation Roadmap & Milestones

| Milestone | Target Component | Core Deliverables | Exit Criteria |
| :--- | :--- | :--- | :--- |
| **M-01** | Taryaq Clinical Core | 100+ Outpatient drug SQLite DB, CYP/eGFR interaction matrices | `test_taryaq_acceptance.py` passes with zero false negatives |
| **M-02** | Taryaq Tri-Modal Engine | Clinician Ambient Copilot, Pharmacist Console, Patient Companion | All 3 user journeys demonstrate trace-linked evidence |
| **M-03** | Qala Corporate Mesh | Managing Director + 6 Departmental Specialists in Python runtime | Cross-departmental container clearance scenario executes |
| **M-04** | Qala C99 Governor | Tau-3 >50k gate, DESC ISR v3.1 sandbox, single-use token consumption | Replay attack rejected with HTTP 409; unauthorized paths blocked |
| **M-05** | Nibras Civic Navigator | GDRFA, Ejari (Decree 43/2013), DEWA, RTA, KHDA, UAE Pass | 100% accuracy on statutory bracket & fee calculations |
| **M-06** | Nibras Executive Twin | FadeMem context decay, Family Office SQLite vault, CFI HUD | > 85% token reduction verified; zero cloud data egress |
| **M-07** | Master Verification | `scripts/verify_all.sh` across all 4 repositories | 100% automated pass with zero manual steps |
