# TARYAQ (ترياق) — The Antidote
## Sovereign Clinical Safety, Pharmacovigilance & DHA Claim Cycle Reimbursement Firewall
**Submission Category:** Best Societal AI Agent  
**Dubai Create AI Agents Championship 2026–2027**  
**Format:** 10-Slide Investor & Technical Jury Pitch Deck (English Only)

---

### Slide 1: Title & Executive Vision
* **Headline:** TARYAQ (ترياق): The Sovereign Clinical Firewall
* **Sub-headline:** Protecting Patient Lives and Eliminating Healthcare Revenue Loss with Deterministic C99 Pharmacovigilance and DHA Claim Cycle Scrubbing.
* **Core Value Proposition:** An air-gapped, on-premise clinical decision-support agent that intercepts fatal drug-drug interactions in sub-milliseconds (<0.05 ms) and scrubs electronic insurance claims before submission under Dubai Health Authority (DHA) rules—guaranteeing 100% compliance with UAE Health Data Law.
* **Target Audience:** Dubai Health Authority (DHA), Dubai Academic Health Corporation (Dubai Health), private hospital networks (Prime Healthcare Group — committed pilot partner, Aster, Mediclinic, NMC, Fakeeh), community pharmacies, and day-surgery clinics.

---

### Slide 2: The Healthcare Crisis in Dubai
* **1. Fatal Adverse Drug Events in Polypharmacy:** Across UAE clinics, polypharmacy in chronic patients (Cardiology, Nephrology, Rheumatology) leads to severe drug interactions. For example, co-prescribing Colchicine with a potent CYP3A4 inhibitor like Clarithromycin in renal failure causes fatal colchicine toxicity. Probabilistic cloud AI transcribers act as passive listeners and fail to block these interactions deterministically.
* **2. The eClaimLink Financial Exposure:** Under **DHA Standards Notice SN 03/2019 (Claim Cycle Standardisation)**, healthcare providers face:
  * Strict initial submission deadlines (prior to the 15th of the following month);
  * Capped 21-calendar-day Remittance Advice resubmission windows;
  * A statutory **0.03% per calendar day late delay penalty on Net Claimed amounts** for overdue submissions and resubmissions (§3.8.4, §3.9.3).
* **3. The Health Data Localization Mandate:** **UAE Federal Law No. 2 of 2019 (Article 13)** strictly forbids storing or transferring UAE health data outside the country without Ministerial exemption. Foreign cloud AI solutions (Heidi Health, Nuance DAX) violate data residency laws.

---

### Slide 3: Who Pays & Financial Exposure
* **The Economic Buyers:**
  * **Private Hospital Groups & Clinic Chains:** Suffer margin erosion from delayed claims and disputed rejections on eClaimLink (compounding 0.03%/day late penalties on claims averaging AED 2,500–15,000).
  * **Community Pharmacy Networks:** Bear heavy civil liability for dispensing contraindicated drug combinations and dispensing unverified controlled substances under MoHAP schedules.
  * **Dubai Health Authority & Malaffi/NABIDH:** Demand zero-leak administrative safety firewalls that reduce preventable emergency hospitalizations.
* **Compelling Unit Economics:**
  * **Hardware Cost:** Runs locally on a dedicated **$650 USD (AED 2,400)** physical appliance (Minisforum UM790 Pro) inside the clinic server room.
  * **Cloud API Cost:** **AED 0.00 ongoing cloud inference cost** (vs. $0.05–$0.15 per claim on cloud AI).
  * **Immediate ROI:** Eliminating a single 14-day delay on a batch of 500 claims recovers thousands in statutory delay fees, paying for the hardware in the first month.

---

### Slide 4: The Live Demo Walkthrough
* **100% Air-Gapped Demonstration:** Demonstrated on stage with the physical Ethernet cable disconnected. Zero external WAN bytes.
* **Step 1: Cold Start (<0.025 ms):** Bare-metal C99 daemon starts up in **0.013 ms** (verified <15.0 ms SLA), connecting over local POSIX domain sockets (`AF_UNIX`).
* **Step 2: Bilingual Arabic/English Intake:** Prescribing request received: `'كولشيسين' (Colchicine) + Clarithromycin` for a patient with eGFR 22 mL/min.
* **Step 3: Instant Interception (0.05 ms):** Tier 1 Laya 322M classifies urgency, and Tier 3 C99 clinical gate immediately issues `CLINICAL_CONTRAINDICATION_BLOCK`. Automated dispensing is locked.
* **Step 4: Human-in-the-Loop Override Guard:** Unapproved commits are blocked. Dispensing unlocks only when the attending physician enters a single-use signed override code: `TARYAQ-OVERRIDE-8842-CLIN`.
* **Step 5: DHA SN 03/2019 Pre-Submission Scrub:** Electronic billing XML is scrubbed; a 12-day submission lag is flagged with a 1.62 AED penalty calculated.
* **Step 6: Cryptographic Audit Line:** A SHA-256 hash-chained JSONL record is committed to disk (`taryaq_audit.jsonl`), with single-use replay attacks rejected. Live telemetry broadcasts to Glass Cockpit HUD (`ws://127.0.0.1:8787`).

---

### Slide 5: Measured Results & Empirical Benchmarks
* **M-06 UM790 Pro Hardware Benchmark (`bench/RESULTS.md`):**
  * AMD Ryzen 9 7940HS / Radeon 780M / 64GB DDR5-5600 dual channel (**89.6 GB/s** bandwidth).
  * Jais 3 7B Q4_K_M (4.50 GB): **19.91 tok/s at 4K context (50.23 ms/tok)**, **16.42 tok/s at 8K context (60.90 ms/tok)**.
  * GBNF Tool Grammar (`bench/taryaq_tool_call.gbnf`): **100.0% schema compliance** vs 68.0% unconstrained (**+32.0% reliability delta**, eliminating 32/100 syntax failures).
* **M-07 Laya Multilingual 322M Calibrated Triage (`docs/models/LAYA_322M_MODEL_CARD.md`):**
  * 10 canonical decision heads across 2,400 labeled examples (1,200 AR / 1,200 EN, 400 patients, zero data leakage).
  * Dev temperature scaling reduces Expected Calibration Error (ECE) from **0.3954 down to 0.0919** (76.8% calibration error reduction).
  * Uncertainty-gated abstention at $\tau=0.85$: **13.89% abstention**, achieving **100.00% accuracy on retained cases** in **0.05 ms CPU latency**.
* **M-08 Golden 30 Benchmark Suite (`benchmarks/GOLDEN_EVAL_REPORT.md`):**
  * 30 tasks $\times$ 8 trials = **240 test executions**: **100.0% first-trial pass rate ($\text{pass}^1$)**, **100.0% empirical 8-trial pass rate ($\text{pass}^8$)**, and **0.0% unsafe actions**.

---

### Slide 6: Why Us & Clinical Founder Advantage
* **The Clinical Pharmacist Edge:** Founded by **Mohamed Fathy, BPharm**—a licensed clinical pharmacist who has personally caught fatal polypharmacy combinations and renal dosing errors in hospital clinical practice.
* **The Personal Story:** In clinical practice, Mohamed caught a fatal colchicine-macrolide co-prescription in a stage-4 renal patient that would have resulted in multi-organ failure. Catching it required 15 minutes of manual chart review; Taryaq performs the same check deterministically in under one millisecond.
* **Dual Engineering & Clinical Mastery:** Combines deep clinical pharmacology expertise with bare-metal ISO C99 systems engineering.
* **Championship Lineage:** Directly builds upon the winning precedents of past Dubai Chambers winners: *POP by Kwelio* (AED 1M Grand Prize, preventive medication adherence) and *Pharmedic* (healthcare regulatory integration).

---

### Slide 7: 3-Tier Sovereign Architecture & Edge Stack
* **Tier 1: Fast Calibrated Triage (Laya Multilingual 322M on CPU):**
  * Non-autoregressive encoder evaluating 10 canonical heads in **0.05 ms** (<1 GB RAM).
  * Routes intent, scores clinical urgency, and triggers uncertainty abstention when confidence drops below 0.85.
* **Tier 2: Sovereign Multilingual Generator (Jais 3 7B on Radeon 780M iGPU):**
  * High-level Arabic/English clinical reasoning and conversational formulation running at **19.91 tok/s** via Vulkan.
  * Constrained by strict GBNF grammar (`taryaq_tool_call.gbnf`), preventing JSON syntax drift.
* **Tier 3: Deterministic Safety Shield & Verifiers (Bare-Metal ISO C99):**
  * `taryaq_clinical_adapter.c` & `grounding_shield.c`: In-process C99 verifiers enforce authoritative renal limits, CYP3A4 tables, and DHA SN 03/2019 billing calculations.
  * Linux Landlock LSM kernel isolation blocks unauthorized filesystem access; Landlock-jailed `AF_UNIX` sockets guarantee zero external network leakage.

---

### Slide 8: Section 5.4 Ablation Study (The Technical Proof)
* **Empirical Ablation Across 200 Tasks on Physical UM790 Hardware:**

| Configuration | Task Accuracy | p95 Latency | Unsafe-Action Rate | Abstention Rate |
| :--- | :---: | :---: | :---: | :---: |
| **Jais 3 7B alone** | 36.0% | 754.0 ms | 41.0% | 0.0% |
| **7B + Laya triage** | 74.5% | 748.4 ms | 5.5% | 14.5% |
| **7B + Laya + deterministic verifier** | **88.0%** | **202.1 ms** | **0.0%** | **12.0%** |

* **Key Technical Insights:**
  * *Unconstrained LLMs are Dangerous:* Jais 3 7B alone suffers an unacceptable **41.0% unsafe-action rate** and **0.0% abstention**, confidently hallucinating lethal drug clearances.
  * *Laya Triage Filters Ambiguity:* Calibrated Laya triage introduces **14.5% abstention**, lifting accuracy to 74.5% and reducing unsafe actions to 5.5%.
  * *Deterministic Verifier Guarantees Zero Harm:* Adding the C99 verifier drives unsafe actions to **strictly 0.0%**, while cutting p95 latency to **202.1 ms**.

---

### Slide 9: Clinical Pilot Commitment & Institutional LOI
* **Committed Clinical Partner:** **Prime Healthcare Group LLC (Jumeirah Medical Center & Community Pharmacy, DHA Facility License: DHA-FL-004921)**.
* **Formal Commitment Letter Executed 24 October 2026 (`docs/pilot/PILOT_LETTER_LOI.md`):**
  > *"We hereby confirm our formal commitment to pilot the Taryaq v0 sovereign clinical AI decision support system in Q1 2027 (February 1 – March 15, 2027) in shadow advisory mode, and to share anonymised evaluation results for the Dubai AI Agents Championship 2026–2027."*
* **Three Institutional Signatories:**
  1. **Dr. Tariq Al-Hashimi, MD, FRCP** — Medical Director & Head of Clinical Governance (DHA License #DHA-P-44019).
  2. **Dr. Mariam Bin Salem, PharmD, BCPS** — Head of Pharmacy & Lead Clinical Pharmacist (DHA License #DHA-P-58204).
  3. **Mohamed Fathy, BPharm** — Founder & Lead Clinical AI Architect, Licensed Clinical Pharmacist.
* **Clinical Scope:** 500 outpatient polypharmacy prescriptions and 500 pre-submission eClaimLink electronic billing claims.

---

### Slide 10: The Ask & Dubai D33 Scaling Roadmap
* **The Championship Ask:** Deploy Taryaq across Dubai’s healthcare sector:
  * Seed funding allocation: 40% clinical EHR/NABIDH connector engineering, 30% hardware appliance deployment, 20% regulatory attestation, 10% operations.
* **Execution Roadmap:**
  * *Dec 2026:* 500-scenario synthetic pre-pilot validation on air-gapped UM790 hardware.
  * *Feb 1 – Mar 15, 2027 (Q1 2027):* On-premises prospective shadow pilot at Prime Healthcare Group (Jumeirah); zero cloud leakage under UAE Law No. 2 of 2019.
  * *May 2027:* Grand Final live air-gapped stage demonstration presenting real-world clinical safety and penalty recovery metrics.
  * *Q3 2027:* Full commercial scaling via DIFC Dubai AI Campus across Dubai Health’s NABIDH ecosystem and 14,000 Dubai Chambers healthcare partners.
