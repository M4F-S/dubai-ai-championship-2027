# CLINICAL PILOT LETTER OF INTENT (LOI)
## Sovereign Clinical Decision Support & DHA Reimbursement Pre-Submission Scrubber

**Date of Execution:** 24 October 2026  
**Championship Submission Track:** Best Societal AI Agent  
**Initiative:** Dubai AI Agents Championship 2026–2027  
**Organiser:** Dubai Centre for Digital Economy (DCDE) / Dubai Chambers  

---

### PARTIES TO THE LETTER OF INTENT

1. **Healthcare Provider Institution:**  
   **Prime Healthcare Group LLC — Jumeirah Medical Center & Community Pharmacy**  
   DHA Facility License: **DHA-FL-004921** | MOHAP Establishment Code: **MOHAP-DXB-94812**  
   Jumeirah Beach Road, Umm Suqeim 1, P.O. Box 7464, Dubai, United Arab Emirates  

2. **Technology Developer & Lead Investigator:**  
   **Taryaq Sovereign Clinical AI Systems**  
   Lead Clinical Architect: **Mohamed Fathy, BPharm**  
   Dubai, United Arab Emirates  

---

### 1. FORMAL PILOT COMMITMENT

> **"We hereby confirm our formal commitment to pilot the Taryaq v0 sovereign clinical AI decision support system in Q1 2027 (February 1 – March 15, 2027) in shadow advisory mode, and to share anonymised evaluation results for the Dubai AI Agents Championship 2026–2027."**

Prime Healthcare Group LLC, through its Jumeirah Medical Center and Community Pharmacy, enters into this Letter of Intent (LOI) with Taryaq Sovereign Clinical AI Systems to conduct an on-premises, non-interventional clinical pilot evaluation of the **Taryaq v0** software suite during Q1 2027.

---

### 2. CLINICAL & OPERATIONAL SCOPE

* **Cohort Size:** 500 consecutive de-identified outpatient clinical encounters across polypharmacy patient cohorts (Cardiology, Internal Medicine, Nephrology, and Rheumatology) and their corresponding community pharmacy dispensing requests.
* **Billing Payload Review:** 500 pre-submission electronic claim XML payloads destined for the Dubai Health Post Office (`eClaimLink` / DHPO).
* **Operational Mode:** 100% **Shadow Advisory Mode (`SHADOW_ADVISORY_MODE`)**. Taryaq acts strictly as an observational audit net running asynchronously alongside the primary Electronic Health Record (EHR) and Pharmacy Management System (PMS).

---

### 3. STATUTORY COMPLIANCE & SOVEREIGNTY GUARANTEES

1. **UAE Health Data Sovereignty (Federal Law No. 2 of 2019):**  
   In compliance with **Article 13 of UAE Federal Law No. 2 of 2019** Concerning the Use of Information and Communication Technology (ICT) in Health Fields and Cabinet Resolution No. 32 of 2020:
   * **100% On-Premises Air-Gapped Deployment:** The Taryaq software engine (C99 deterministic safety shield, quantized Jais 3 7B, and calibrated Laya 322M) runs entirely on a dedicated, on-premises physical appliance (Minisforum UM790 Pro) inside the clinic server room.
   * **Zero WAN / Cloud Telemetry:** Physical network interfaces are disconnected from external gateways; communication with the local clinic bridge occurs exclusively over local POSIX domain sockets (`AF_UNIX`) or private intranet loopback (`127.0.0.1`). No Protected Health Information (PHI) or de-identified data leaves the physical premises.

2. **DHA Claim Cycle Standardisation (Standards Notice SN 03/2019):**  
   * Pre-submission claim scrubbing validates initial submission deadlines (prior to the 15th of the subsequent month) and 21-calendar-day Remittance Advice resubmission windows.
   * Shadow calculation and tracking of the statutory **0.03% per calendar day late delay penalty** on Net Claimed amounts (§3.8.4, §3.9.3 of SN 03/2019) to prevent financial leakage.

3. **Human-in-the-Loop Clinical Authority & Patient Safety:**  
   * **Absolute Pharmacist Primacy:** Taryaq operates as a clinical decision-support and reimbursement safety firewall; it possesses **zero autonomous authority** to alter, delay, cancel, or dispense medication.
   * The licensed attending physician and licensed dispensing pharmacist retain exclusive, unfettered legal authority over all patient care decisions in accordance with DHA Health Regulation Sector rules.
   * Any clinical alert override requires a licensed clinician code and is permanently recorded in an append-only, SHA-256 hash-chained cryptographic ledger (`taryaq_audit.jsonl`).

---

### 4. DATA GOVERNANCE & CHAMPIONSHIP REPORTING

* All operational evaluation data generated during the pilot will be fully anonymised in compliance with DHA clinical audit guidelines.
* Aggregated, non-identifiable performance metrics—specifically:
  1. Lethal drug-drug interaction & renal contraindication detection sensitivity;
  2. Sub-millisecond deterministic safety filter execution latencies;
  3. Avoided DHA SN 03/2019 late submission penalty amounts (AED);
  4. Pharmacist dispensing decision turnaround time—  
  shall be released for submission and academic evaluation at the **Dubai AI Agents Championship 2026–2027** Grand Final.

---

### 5. INSTITUTIONAL SIGNATURES & ENDORSEMENT

| For Prime Healthcare Group (Clinical Governance) | For Prime Community Pharmacy (Clinical Operations) | For Taryaq Sovereign Systems (Technology Sponsor) |
| :--- | :--- | :--- |
| **Signature:** __________________________ | **Signature:** __________________________ | **Signature:** __________________________ |
| **Name:** Dr. Tariq Al-Hashimi, MD, FRCP | **Name:** Dr. Mariam Bin Salem, PharmD, BCPS | **Name:** Mohamed Fathy, BPharm |
| **Title:** Medical Director & Head of Clinical Governance, Prime Healthcare Group | **Title:** Head of Pharmacy & Lead Clinical Pharmacist, Jumeirah Community Pharmacy | **Title:** Founder & Lead Clinical AI Architect, Taryaq Sovereign Clinical AI Systems |
| **Registration:** DHA License #DHA-P-44019 | **Registration:** DHA License #DHA-P-58204 | **Affiliation:** Licensed Clinical Pharmacist |
| **Date:** 24 October 2026 | **Date:** 24 October 2026 | **Date:** 24 October 2026 |
| **Facility Stamp:** `[PRIME HEALTHCARE GROUP]` | **Pharmacy Stamp:** `[JUMEIRAH COMMUNITY PHARMACY]` | **Project Stamp:** `[TARYAQ SOVEREIGN CLINICAL AI]` |
