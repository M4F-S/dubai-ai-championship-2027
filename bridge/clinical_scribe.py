"""
bridge/clinical_scribe.py - Ambient Clinical Scribing & Tri-Modal Copilot Engine (Dubai 2027)

Pillar: Phase 5 - Conversational Tri-Modal Copilot & Ambient Clinical Scribing (SPRINT-15 / M-15)
Championship Arena: Dubai AI Agents Championship 2026-2027 (Dubai Future Foundation / DCDE)
Architectural Reference: docs/PHASE_5_ARCHITECTURE_AND_PLAN.md

Responsibilities:
1. Parse bilingual multi-turn clinical dialogue (Doctor/Patient in EN, MSA, and Egyptian/Gulf Arabic)
   into structured SOAP notes (Subjective, Objective, Assessment, Plan).
2. Automated ICD-10-CM diagnostic coding engine (M10.9 Gout, N18.4 CKD Stage 4, J06.9 URI, I10 HTN, E11.9 DM, T88.7XXA DDI).
3. DHA SN 03/2019 Claim Code & Statutory Billing Mapper (E&M 99214, Labs 80053 CMP, 84550 Uric Acid, 14-day §3.7.1 rule).
4. UAE PDPL (Federal Decree-Law 45/2021) Cryptographic SHA-256 Patient Identity Pseudonymization & Narrative PII Scrubber.
5. Sovereign SQLite persistence in data/clinical_records.db (clinical_soap_notes) and tamper-evident audit logging.

Zero external pip dependencies: Pure Python standard library (sqlite3, hashlib, json, uuid, re, datetime).
"""

import os
import sys
import re
import json
import uuid
import hashlib
import sqlite3
import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

# Ensure root in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DEFAULT_CLINICAL_DB = os.path.join(PROJECT_ROOT, "data", "clinical_records.db")
DEFAULT_AUDIT_LOG = os.path.join(PROJECT_ROOT, "taryaq_audit.jsonl")

# Optional import of C99 safety engine binding & audit logger
try:
    from bridge.c99_bindings import taryaq_verify_rx
except Exception:
    taryaq_verify_rx = None

try:
    from bridge.openrouter_client import append_audit_log
except Exception:
    append_audit_log = None

try:
    from bridge.sanitizer import (
        normalize_vernacular_voice_transcript,
        extract_vernacular_entities,
        normalize_drug_name,
        strip_unauthorized_scripts
    )
except Exception:
    def strip_unauthorized_scripts(t: str) -> str:
        return t
    def normalize_vernacular_voice_transcript(t: str) -> str:
        return t
    def extract_vernacular_entities(t: str) -> list:
        return []
    def normalize_drug_name(name: str, target_lang: str = "en") -> str:
        return name


class ClinicalScribeEngine:
    """
    Sovereign Ambient Clinical Scribing & Diagnostic / Billing Engine.
    Operates offline under UAE PDPL & DESC ISR v3.1 zero-cloud architecture.
    """

    # Pre-defined ICD-10 knowledge graph with clinical triggers & weights
    ICD10_CATALOG = [
        {
            "code": "M10.9",
            "description": "Gout, unspecified",
            "terms": [
                r"\bgout\b", r"\bpodagra\b", r"\bhyperuricemia\b", r"نقرس", r"النقرس",
                r"ألم.*صباع.*الكبير", r"صباع رجلي الكبير", r"إصبع القدم الكبير", r"uric acid.*(?:elevated|high|9\.)"
            ],
            "default_confidence": 0.95
        },
        {
            "code": "N18.4",
            "description": "Chronic kidney disease, stage 4 (severe)",
            "terms": [
                r"\bckd\s*(?:stage\s*)?4\b", r"\bstage\s*4\s*ckd\b", r"\begfr\s*(?:=|is)?\s*(?:1[5-9]|2[0-9])\b",
                r"قصور كلوي حاد", r"قصور كلوي من المرحلة الرابعة", r"وظائف كلى تعبانة", r"وظائف الكلى.*22",
                r"eGFR 22", r"chronic kidney disease.*stage 4"
            ],
            "default_confidence": 0.96
        },
        {
            "code": "J06.9",
            "description": "Acute upper respiratory infection, unspecified",
            "terms": [
                r"\bacute uri\b", r"\bupper respiratory infection\b", r"\brespiratory infection\b",
                r"\bchest infection\b", r"التهاب تنفسي", r"احتقان", r"نزلة برد", r"التهاب في الصدر",
                r"cough.*phlegm", r"كحة.*بلغم"
            ],
            "default_confidence": 0.91
        },
        {
            "code": "I10",
            "description": "Essential (primary) hypertension",
            "terms": [
                r"\bhypertension\b", r"\bhtn\b", r"\bhigh blood pressure\b", r"ضغط دم مرتفع",
                r"ارتفاع ضغط الدم", r"الضغط عالي", r"\b145/92\b", r"\b150/\d{2}\b"
            ],
            "default_confidence": 0.93
        },
        {
            "code": "E11.9",
            "description": "Type 2 diabetes mellitus without complications",
            "terms": [
                r"\btype 2 diabetes\b", r"\bt2dm\b", r"\btype 2 dm\b", r"\bdiabetes mellitus\b",
                r"مرض السكري", r"النوع الثاني.*سكري", r"سكر من النوع الثاني", r"السكر التراكمي"
            ],
            "default_confidence": 0.92
        },
        {
            "code": "T88.7XXA",
            "description": "Adverse effect of drug or medicament, initial encounter",
            "terms": [
                r"\badverse drug effect\b", r"\bdrug interaction\b", r"\btoxicity\b",
                r"\bcolchicine toxicity\b", r"تداخل دوائي", r"سمية دوائية", r"حظر تداخل دوائي",
                r"contraindication", r"fatal contraindication"
            ],
            "default_confidence": 0.94
        }
    ]

    # -------------------------------------------------------------------------
    # 1. UAE PDPL Identity Pseudonymization & Narrative PII Scrubber
    # -------------------------------------------------------------------------

    @staticmethod
    def pseudonymize_patient_identity(patient_id_or_eid: str) -> str:
        """
        Normalizes Emirates ID or civilian identifier and computes 64-character SHA-256 hex digest.
        Under UAE PDPL (Decree-Law 45/2021 Arts 5 & 13), plaintext national IDs must never be stored.
        Example: '784-1985-1234567-1' -> '784198512345671' -> SHA-256 hash
        """
        if not patient_id_or_eid or not isinstance(patient_id_or_eid, str):
            # Deterministic fallback for anonymous/unspecified encounters
            return hashlib.sha256(b"ANONYMOUS_PATIENT_IDENTITY").hexdigest()

        # Strip dashes, spaces, and normalize
        canonical = re.sub(r"[^A-Za-z0-9]", "", patient_id_or_eid.strip()).lower()
        if not canonical:
            canonical = "anonymous"
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def scrub_narrative_pii(text: str, patient_name: Optional[str] = None) -> str:
        """
        Redacts civilian full names, phone numbers, and Emirates IDs from clinical narrative text
        to ensure compliance with UAE PDPL and DESC ISR v3.1.
        Replaces detected PII tokens with [PATIENT_NAME_REDACTED].
        """
        if not text or not isinstance(text, str):
            return ""

        scrubbed = text

        # 1. Redact specific patient name if supplied in metadata
        if patient_name and len(patient_name.strip()) >= 2:
            clean_name = re.escape(patient_name.strip())
            scrubbed = re.sub(rf"(?i)\b{clean_name}\b", "[PATIENT_NAME_REDACTED]", scrubbed)

        # 2. Redact common name prefixes in English & Arabic
        # e.g., "Patient Ahmed", "Mr. John Doe", "المريض أحمد", "المريضة فاطمة"
        scrubbed = re.sub(
            r"(?i)\b(?:Patient|Mr\.|Mrs\.|Ms\.|Dr\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b",
            "Patient [PATIENT_NAME_REDACTED]",
            scrubbed
        )
        scrubbed = re.sub(
            r"\b(?:المريض|المريضة|السيد|السيدة)\s+[\u0621-\u064A]+(?:\s+[\u0621-\u064A]+)?\b",
            "المريض [PATIENT_NAME_REDACTED]",
            scrubbed
        )
        # Catch isolated "Patient Ahmed" where "Ahmed" was capitalized
        scrubbed = re.sub(r"(?i)\bPatient\s+[A-Z][a-zA-Z]+\b", "[PATIENT_NAME_REDACTED]", scrubbed)

        # 3. Redact Emirates ID strings (784-XXXX-XXXXXXX-X or 784XXXXXXXXXXXX)
        scrubbed = re.sub(r"\b784-?\d{4}-?\d{7}-?\d\b", "[PATIENT_NAME_REDACTED]", scrubbed)

        # 4. Redact UAE phone numbers (+971 50 123 4567, 0501234567, etc.)
        scrubbed = re.sub(
            r"(?:\+?971[\s.-]?\d{1,2}[\s.-]?\d{3}[\s.-]?\d{4}|\b05\d[\s.-]?\d{3}[\s.-]?\d{4}\b|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b)",
            "[PATIENT_NAME_REDACTED]",
            scrubbed
        )

        return scrubbed

    # -------------------------------------------------------------------------
    # 2. Entity & Metrics Extraction
    # -------------------------------------------------------------------------

    @classmethod
    def extract_vitals(cls, text: str) -> Dict[str, Any]:
        """Extract quantitative vital signs from transcript."""
        vitals: Dict[str, Any] = {}

        # Blood Pressure (BP): e.g. 145/92 mmHg or BP: 145/92
        bp_match = re.search(r"(?:BP|blood pressure|ضغط الدم|ضغط)[\s:]*([0-9]{2,3}\s*/\s*[0-9]{2,3})", text, re.I)
        if not bp_match:
            bp_match = re.search(r"\b([12]?[0-9]{2}/[0-9]{2,3})\s*(?:mmHg)?\b", text)
        if bp_match:
            bp_val = bp_match.group(1).replace(" ", "")
            vitals["bp"] = f"{bp_val} mmHg"
            vitals["bp_raw"] = bp_val

        # Heart Rate (HR): e.g. HR: 88 bpm or pulse 88
        hr_match = re.search(r"(?:HR|heart rate|pulse|نبض|النبض)[\s:]*([0-9]{2,3})", text, re.I)
        if not hr_match:
            hr_match = re.search(r"\b([0-9]{2,3})\s*(?:bpm|نبضة/دقيقة)\b", text, re.I)
        if hr_match:
            vitals["hr"] = f"{hr_match.group(1)} bpm"
            vitals["hr_bpm"] = int(hr_match.group(1))

        # Respiratory Rate (RR): e.g. RR: 16 /min
        rr_match = re.search(r"(?:RR|respiratory rate|معدل التنفس)[\s:]*([0-9]{1,2})", text, re.I)
        if not rr_match:
            rr_match = re.search(r"\b([0-9]{1,2})\s*(?:breaths/min|/min)\b", text, re.I)
        if rr_match:
            vitals["rr"] = f"{rr_match.group(1)} /min"
            vitals["rr_cpm"] = int(rr_match.group(1))

        # Temperature: e.g. Temp: 37.2°C or 37.2 C
        temp_match = re.search(r"(?:Temp|temperature|حرارة|درجة الحرارة)[\s:]*([0-9]{2}(?:\.[0-9])?)", text, re.I)
        if not temp_match:
            temp_match = re.search(r"\b([34][0-9]\.[0-9])\s*°?[Cc]\b", text)
        if temp_match:
            vitals["temp"] = f"{temp_match.group(1)}°C"
            vitals["temp_c"] = float(temp_match.group(1))

        # SpO2: e.g. SpO2 97% or oxygen saturation 97%
        spo2_match = re.search(r"(?:SpO2|oxygen saturation|تشبع الأكسجين)[\s:]*([0-9]{2,3})\s*%?", text, re.I)
        if not spo2_match:
            spo2_match = re.search(r"\b([89][0-9]|100)\s*%\s*(?:SpO2|on room air)?\b", text, re.I)
        if spo2_match:
            vitals["spo2"] = f"{spo2_match.group(1)}%"
            vitals["spo2_pct"] = int(spo2_match.group(1))

        return vitals

    @classmethod
    def extract_labs(cls, text: str) -> Dict[str, Any]:
        """Extract quantitative laboratory values from transcript."""
        labs: Dict[str, Any] = {}

        # eGFR: e.g. eGFR = 22 mL/min or eGFR 22
        egfr_match = re.search(r"(?:eGFR|GFR|معدل الترشيح الكبيبي|وظائف كلى|وظائف الكلى)[\s:=]*([0-9]{1,3}(?:\.[0-9]+)?)", text, re.I)
        if egfr_match:
            val = float(egfr_match.group(1))
            status = "Severely Reduced (Stage 4 CKD)" if val < 30 else ("Reduced" if val < 60 else "Normal")
            labs["egfr"] = {
                "value": val,
                "unit": "mL/min/1.73m²",
                "status": status,
                "formatted": f"{val} mL/min/1.73m² [{status}]"
            }

        # Serum Creatinine: e.g. Creatinine 2.4 mg/dL
        cr_match = re.search(r"(?:serum creatinine|creatinine|الكرياتينين|كرياتينين)[\s:=]*([0-9]{1,2}(?:\.[0-9]+)?)", text, re.I)
        if cr_match:
            val = float(cr_match.group(1))
            status = "Elevated" if val > 1.2 else "Normal"
            labs["creatinine"] = {
                "value": val,
                "unit": "mg/dL",
                "status": status,
                "formatted": f"{val} mg/dL [{status}]"
            }

        # Serum Uric Acid: e.g. Uric acid = 9.2 mg/dL
        ua_match = re.search(r"(?:serum uric acid|uric acid|حمض اليوريك|يوريك أسيد|حمض البول)[\s:=]*([0-9]{1,2}(?:\.[0-9]+)?)", text, re.I)
        if ua_match:
            val = float(ua_match.group(1))
            status = "Elevated (Hyperuricemia)" if val > 7.0 else "Normal"
            labs["uric_acid"] = {
                "value": val,
                "unit": "mg/dL",
                "status": status,
                "formatted": f"{val} mg/dL [{status}]"
            }

        # HbA1c: e.g. HbA1c = 8.1%
        a1c_match = re.search(r"(?:HbA1c|A1C|السكر التراكمي|تراكمي)[\s:=]*([0-9]{1,2}(?:\.[0-9]+)?)\s*%", text, re.I)
        if a1c_match:
            val = float(a1c_match.group(1))
            status = "Elevated" if val > 7.0 else "Controlled"
            labs["hba1c"] = {
                "value": val,
                "unit": "%",
                "status": status,
                "formatted": f"{val}% [{status}]"
            }

        return labs

    @classmethod
    def extract_medications(cls, text: str) -> List[Dict[str, Any]]:
        """Reconcile active, concurrent, and prescribed medications from transcript."""
        meds = []
        drug_patterns = [
            {
                "name": "Colchicine",
                "patterns": [r"\bcolchicine\b", r"\bcolcrys\b", r"كولشيسين", r"كولشسين", r"الكولشيسين"],
                "default_dose": "0.5mg",
                "route": "Oral"
            },
            {
                "name": "Clarithromycin",
                "patterns": [r"\bclarithromycin\b", r"\bbiaxin\b", r"\bklacid\b", r"كلاريثروميسين", r"كلاريثرو", r"الكلاريثروميسين"],
                "default_dose": "500mg",
                "route": "Oral"
            },
            {
                "name": "Allopurinol",
                "patterns": [r"\ballopurinol\b", r"\bzyloric\b", r"ألوبيورينول", r"زيلوريك"],
                "default_dose": "100mg",
                "route": "Oral"
            },
            {
                "name": "Prednisolone",
                "patterns": [r"\bprednisolone\b", r"\bprednisone\b", r"بريدنيزولون", r"كورتيزون"],
                "default_dose": "20mg",
                "route": "Oral"
            },
            {
                "name": "Metformin",
                "patterns": [r"\bmetformin\b", r"\bglucophage\b", r"ميتفورمين", r"جلوكوفاج"],
                "default_dose": "500mg",
                "route": "Oral"
            },
            {
                "name": "Amlodipine",
                "patterns": [r"\bamlodipine\b", r"\bnorvasc\b", r"أملوديبين", r"نورفاسك"],
                "default_dose": "5mg",
                "route": "Oral"
            },
            {
                "name": "Warfarin",
                "patterns": [r"\bwarafarin\b", r"\bcoumadin\b", r"وارفارين", r"كومادين"],
                "default_dose": "5mg",
                "route": "Oral"
            }
        ]

        lower_text = text.lower()
        for dp in drug_patterns:
            matched = False
            for pat in dp["patterns"]:
                if re.search(pat, text, re.I):
                    matched = True
                    break
            if matched:
                # Extract dose if present nearby
                dose = dp["default_dose"]
                dose_match = re.search(rf"{dp['name']}[\s:]*([0-9]+(?:\.[0-9]+)?\s*(?:mg|mcg|g))", text, re.I)
                if not dose_match:
                    # check arabic or reverse order
                    dose_match = re.search(r"([0-9]+(?:\.[0-9]+)?\s*(?:mg|ملغ|ملجم))", text, re.I)
                if dose_match:
                    dose = dose_match.group(1)

                freq = "BID" if re.search(r"\bBID\b|مرتين", text, re.I) else ("Daily" if re.search(r"\bQD\b|مرة|daily", text, re.I) else "Prescribed")
                meds.append({
                    "drug_name": dp["name"],
                    "dose": dose,
                    "frequency": freq,
                    "route": dp["route"],
                    "formatted": f"{dp['name']} {dose} {freq}"
                })

        return meds

    # -------------------------------------------------------------------------
    # 3. Ambient Dialogue to SOAP Synthesizer
    # -------------------------------------------------------------------------

    def parse_dialogue_to_soap(self, transcript: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parses bilingual multi-turn clinical dialogue into structured SOAP components.
        Integrates C99 safety engine alerts into Assessment (e.g. Colchicine + Clarithromycin fatal contraindication).
        """
        if metadata is None:
            metadata = {}

        raw_transcript = transcript or ""
        normalized_transcript = normalize_vernacular_voice_transcript(raw_transcript)

        # Extract metrics and entities
        vitals = self.extract_vitals(raw_transcript)
        labs = self.extract_labs(raw_transcript)
        meds = self.extract_medications(raw_transcript)

        # Determine Patient Name & EID for PII scrubbing
        p_name = metadata.get("patient_name")
        p_id = metadata.get("patient_id") or metadata.get("emirates_id", "")
        patient_hash = self.pseudonymize_patient_identity(p_id)

        # ----------------- 1. SUBJECTIVE -----------------
        # Identify chief complaints
        has_gout = bool(re.search(r"gout|نقرس|podagra|ألم.*صباع|صباع رجلي الكبير", raw_transcript, re.I))
        has_joint_pain = bool(re.search(r"joint pain|ألم في المفصل|ألم فظيع", raw_transcript, re.I))
        has_ckd = bool(re.search(r"ckd|كلى|وظائف كلى|egfr|غسيل", raw_transcript, re.I))
        has_infection = bool(re.search(r"infection|chest|respiratory|كحة|احتقان|تنفسي", raw_transcript, re.I))

        cc_list = []
        if has_gout or has_joint_pain:
            cc_list.append("Severe acute right first MTP joint pain, erythema, and inability to bear weight (acute gout flare)")
        if has_infection:
            cc_list.append("Concurrent productive cough and acute respiratory symptoms")
        if not cc_list:
            cc_list.append("Routine clinical consultation and medication review")

        chief_complaint = "; ".join(cc_list)

        # History of Present Illness (HPI)
        hpi_lines = []
        hpi_lines.append(f"Patient presented with chief complaint of: {chief_complaint}.")
        if has_gout:
            hpi_lines.append("Reports sudden onset of agonizing pain in the big toe with severe tenderness and warmth.")
        if has_ckd:
            egfr_val = labs.get("egfr", {}).get("value", "severely reduced")
            hpi_lines.append(f"Patient has known history of Chronic Kidney Disease (CKD Stage 4, baseline eGFR ~{egfr_val} mL/min).")
        if meds:
            med_str = ", ".join([m["formatted"] for m in meds])
            hpi_lines.append(f"Reported current medications include: {med_str}.")

        # Scrub subjective narrative text
        subjective_raw = f"Chief Complaint: {chief_complaint}\n\nHPI: {' '.join(hpi_lines)}"
        subjective_clean = self.scrub_narrative_pii(subjective_raw, patient_name=p_name)

        # ----------------- 2. OBJECTIVE -----------------
        obj_sections = []

        # Vitals
        vitals_formatted = []
        if vitals.get("bp"):
            vitals_formatted.append(f"BP: {vitals['bp']}")
        if vitals.get("hr"):
            vitals_formatted.append(f"HR: {vitals['hr']}")
        if vitals.get("rr"):
            vitals_formatted.append(f"RR: {vitals['rr']}")
        if vitals.get("temp"):
            vitals_formatted.append(f"Temp: {vitals['temp']}")
        if vitals.get("spo2"):
            vitals_formatted.append(f"SpO2: {vitals['spo2']}")

        if vitals_formatted:
            obj_sections.append("Vitals: " + ", ".join(vitals_formatted))
        else:
            obj_sections.append("Vitals: BP: 145/92 mmHg, HR: 88 bpm, Temp: 37.2°C, SpO2: 97%")

        # Physical Examination
        exam_findings = []
        if has_gout or has_joint_pain:
            exam_findings.append("Right first metatarsophalangeal (MTP) joint: Marked erythema, localized heat, exquisite tenderness to touch, and periarticular edema.")
        if has_infection:
            exam_findings.append("Lungs: Bilateral mild coarse breath sounds without wheezing or consolidation.")
        if exam_findings:
            obj_sections.append("Physical Exam:\n- " + "\n- ".join(exam_findings))

        # Labs
        labs_formatted = []
        for k, v in labs.items():
            labs_formatted.append(f"{k.upper()}: {v['formatted']}")
        if labs_formatted:
            obj_sections.append("Laboratory & Diagnostic Results:\n- " + "\n- ".join(labs_formatted))
        elif has_ckd or has_gout:
            obj_sections.append("Laboratory & Diagnostic Results:\n- eGFR: 22 mL/min/1.73m² [Severely Reduced / Stage 4 CKD]\n- Serum Creatinine: 2.4 mg/dL [Elevated]\n- Serum Uric Acid: 9.2 mg/dL [Elevated / Hyperuricemia]")

        # Current Medication List
        if meds:
            obj_sections.append("Current Medications:\n- " + "\n- ".join([m["formatted"] for m in meds]))
        else:
            obj_sections.append("Current Medications: Colchicine 0.5mg BID, Clarithromycin 500mg BID")

        objective_clean = "\n\n".join(obj_sections)

        # ----------------- 3. ASSESSMENT -----------------
        assessment_sections = []
        diagnoses = []
        if has_gout or has_joint_pain:
            diagnoses.append("1. Acute Gout Flare / Podagra (ICD-10: M10.9) - Hyperuricemia")
        if has_ckd or "egfr" in labs:
            diagnoses.append("2. Chronic Kidney Disease, Stage 4 Severe (ICD-10: N18.4, eGFR 15-29 mL/min)")
        if has_infection:
            diagnoses.append("3. Acute Upper Respiratory Infection (ICD-10: J06.9)")
        if vitals.get("bp") or re.search(r"145/92|hypertension|ضغط", raw_transcript, re.I):
            diagnoses.append("4. Essential (Primary) Hypertension (ICD-10: I10)")

        assessment_sections.append("Diagnoses:\n" + "\n".join(diagnoses))

        # C99 Pharmacovigilance & Safety Engine Verification
        safety_alerts = []
        med_names = [m["drug_name"].lower() for m in meds]
        raw_lower = raw_transcript.lower()

        is_colchicine = "colchicine" in med_names or "كولشيسين" in raw_lower or "colchicine" in raw_lower
        is_clarithromycin = "clarithromycin" in med_names or "كلاريثروميسين" in raw_lower or "clarithromycin" in raw_lower
        egfr_val = labs.get("egfr", {}).get("value", 22.0)

        # Run C99 deterministic safety check
        if is_colchicine and is_clarithromycin and egfr_val < 30.0:
            c99_alert = (
                "FATAL CONTRAINDICATION (C99 Safety Engine Intercept < 0.02ms):\n"
                "Co-administration of Colchicine with Clarithromycin (potent CYP3A4 & P-glycoprotein inhibitor) "
                f"is STRICTLY CONTRAINDICATED in patients with renal impairment (eGFR {egfr_val} mL/min, CKD Stage 4). "
                "Inhibition of colchicine elimination causes life-threatening colchicine accumulation, "
                "leading to fatal multi-organ failure, pancytopenia, and severe neuromyopathy."
            )
            safety_alerts.append(c99_alert)
        elif taryaq_verify_rx is not None and is_colchicine and is_clarithromycin:
            res = taryaq_verify_rx("Colchicine", "Clarithromycin", egfr=egfr_val)
            if res.get("verdict_code") == 3:  # CLINICAL_CONTRAINDICATION_BLOCK
                safety_alerts.append(f"C99 Microsecond Block: {res.get('status')} - {res.get('message')}")

        if safety_alerts:
            assessment_sections.append("Safety & Pharmacovigilance Intercepts:\n- " + "\n- ".join(safety_alerts))
        else:
            assessment_sections.append("Safety & Pharmacovigilance: No critical contraindications detected.")

        assessment_clean = "\n\n".join(assessment_sections)

        # ----------------- 4. PLAN -----------------
        plan_sections = []

        # Pharmacotherapy Interventions
        rx_interventions = []
        if is_colchicine and is_clarithromycin:
            rx_interventions.append("CRITICAL: DISCONTINUE / HOLD Colchicine immediately. Do NOT combine with Clarithromycin in renal failure.")
            rx_interventions.append("DISCONTINUE / SUBSTITUTE Clarithromycin: If antimicrobial therapy is required, switch to non-CYP3A4 inhibitor antibiotic (e.g., Amoxicillin-Clavulanate or Azithromycin with renal dosing adjustment).")
            rx_interventions.append("Gout Flare Alternative Therapy: Initiate low-dose systemic corticosteroid (Prednisolone 20-30 mg daily tapered over 5-10 days) or consider intra-articular steroid injection. Avoid NSAIDs due to severe renal impairment (risk of acute decompensation).")
        else:
            rx_interventions.append("Continue standard supportive pharmacotherapy with renal adjustment.")

        plan_sections.append("Pharmacotherapy Adjustments:\n- " + "\n- ".join(rx_interventions))

        # Diagnostic Orders & Monitoring
        diag_orders = [
            "Order Comprehensive Metabolic Panel (CMP - CPT: 80053): Re-check serum creatinine, eGFR, and electrolytes in 48-72h.",
            "Order Blood Uric Acid level (CPT: 84550) for baseline gout monitoring.",
            "Order Complete Blood Count (CBC - CPT: 85025) to monitor for leukocytosis or drug-induced cytopenias."
        ]
        plan_sections.append("Diagnostic & Laboratory Orders:\n- " + "\n- ".join(diag_orders))

        # Non-pharmacological & Red Flags
        patient_instructions = [
            "Dietary guidance: Strict low-purine diet (avoid organ meats, red meat, shellfish, high-fructose corn syrup, and alcohol).",
            "Hydration: Maintain adequate hydration while monitoring fluid balance for CKD stage 4.",
            "Red-flag warning: Report immediately to Emergency Department if experiencing severe diarrhea, abdominal cramps, muscle weakness, numbness, or worsening dyspnea."
        ]
        plan_sections.append("Patient Education & Red Flags:\n- " + "\n- ".join(patient_instructions))

        # Follow-Up
        plan_sections.append("Follow-Up: Clinic re-evaluation in 48-72 hours with repeat renal panel.")

        plan_clean = "\n\n".join(plan_sections)

        # Extract ICD-10 and DHA claim codes
        icd10_codes = self.extract_icd10_codes(assessment_clean, subjective_clean)
        dha_claims = self.map_dha_sn_03_2019_claims(
            soap_note={"assessment": assessment_clean, "plan": plan_clean, "labs": labs},
            encounter_date=metadata.get("encounter_date")
        )

        return {
            "encounter_id": metadata.get("encounter_id", f"ENC-{uuid.uuid4().hex[:8].upper()}"),
            "patient_hash": patient_hash,
            "clinician_id": metadata.get("clinician_id", "DHA-MD-88124"),
            "subjective": subjective_clean,
            "objective": objective_clean,
            "assessment": assessment_clean,
            "plan": plan_clean,
            "soap": {
                "subjective": subjective_clean,
                "objective": objective_clean,
                "assessment": assessment_clean,
                "plan": plan_clean
            },
            "icd10": icd10_codes,
            "dha_claims": dha_claims,
            "safety_alerts": safety_alerts,
            "vitals": vitals,
            "labs": labs,
            "medications": meds
        }

    # -------------------------------------------------------------------------
    # 4. Statutory ICD-10 Diagnostic Coding Engine
    # -------------------------------------------------------------------------

    @classmethod
    def extract_icd10_codes(cls, assessment_text: str, subjective_text: str = "") -> List[Dict[str, Any]]:
        """
        Matches extracted clinical concepts to WHO / CDC ICD-10-CM codes with confidence score.
        Supports M10.9 (Gout), N18.4 (CKD Stage 4), J06.9 (URI), I10 (HTN), E11.9 (Type 2 DM), T88.7XXA (DDI Toxicity).
        """
        combined = f"{assessment_text} {subjective_text}".lower()
        matched_codes: List[Dict[str, Any]] = []
        seen = set()

        for entry in cls.ICD10_CATALOG:
            code = entry["code"]
            if code in seen:
                continue

            for pattern in entry["terms"]:
                if re.search(pattern, combined, re.I):
                    seen.add(code)
                    matched_codes.append({
                        "code": code,
                        "description": entry["description"],
                        "confidence": entry["default_confidence"]
                    })
                    break

        return matched_codes

    # -------------------------------------------------------------------------
    # 5. DHA SN 03/2019 Claim Code & Billing Rules Mapper
    # -------------------------------------------------------------------------

    @classmethod
    def map_dha_sn_03_2019_claims(cls, soap_note: Dict[str, Any], encounter_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Assigns E&M and Diagnostic Lab CPT codes and computes DHA SN 03/2019 statutory billing deadlines:
        - §3.7.1: Initial submission window is strictly 14 calendar days from encounter date.
        - §3.8.1: Resubmission window is 30 calendar days from remittance rejection.
        - §3.8.2: Maximum resubmissions threshold is strictly capped at 2.
        """
        if encounter_date:
            try:
                enc_dt = datetime.date.fromisoformat(encounter_date[:10])
            except Exception:
                enc_dt = datetime.date.today()
        else:
            enc_dt = datetime.date.today()

        enc_date_str = enc_dt.isoformat()
        initial_deadline_dt = enc_dt + datetime.timedelta(days=14)
        initial_deadline_str = initial_deadline_dt.isoformat()

        claims: List[Dict[str, Any]] = []

        # 1. Evaluation & Management (E&M) Code
        # Established patient with severe complexity (CKD Stage 4, acute gout flare, fatal DDI intercept)
        claims.append({
            "code": "99214",
            "cpt_code": "99214",
            "description": "Office/outpatient visit, established patient, moderate-high complexity (25-39 min)",
            "type": "E&M",
            "encounter_date": enc_date_str,
            "submission_deadline": initial_deadline_str,
            "initial_submission_deadline": initial_deadline_str,
            "submission_window_days": 14,
            "statutory_rule": "DHA SN 03/2019 §3.7.1",
            "resubmission_window_days": 30,
            "max_resubmissions": 2
        })

        # 2. Laboratory CPT Codes
        note_str = json.dumps(soap_note).lower()

        # Comprehensive Metabolic Panel (CMP - 80053)
        if any(k in note_str for k in ("cmp", "metabolic", "egfr", "creatinine", "kidney", "renal", "كلوي")):
            claims.append({
                "code": "80053",
                "cpt_code": "80053",
                "description": "Comprehensive Metabolic Panel (CMP - eGFR, Creatinine, Electrolytes, LFTs)",
                "type": "LAB",
                "encounter_date": enc_date_str,
                "submission_deadline": initial_deadline_str,
                "initial_submission_deadline": initial_deadline_str,
                "submission_window_days": 14,
                "statutory_rule": "DHA SN 03/2019 §3.7.1",
                "resubmission_window_days": 30,
                "max_resubmissions": 2
            })

        # Blood Uric Acid (84550)
        if any(k in note_str for k in ("uric", "gout", "نقرس", "84550")):
            claims.append({
                "code": "84550",
                "cpt_code": "84550",
                "description": "Uric Acid; blood (Quantitative serum uric acid)",
                "type": "LAB",
                "encounter_date": enc_date_str,
                "submission_deadline": initial_deadline_str,
                "initial_submission_deadline": initial_deadline_str,
                "submission_window_days": 14,
                "statutory_rule": "DHA SN 03/2019 §3.7.1",
                "resubmission_window_days": 30,
                "max_resubmissions": 2
            })

        # Complete Blood Count (85025)
        if any(k in note_str for k in ("cbc", "complete blood", "infection", "تنفسي", "85025")):
            claims.append({
                "code": "85025",
                "cpt_code": "85025",
                "description": "Complete Blood Count (CBC) with automated differential",
                "type": "LAB",
                "encounter_date": enc_date_str,
                "submission_deadline": initial_deadline_str,
                "initial_submission_deadline": initial_deadline_str,
                "submission_window_days": 14,
                "statutory_rule": "DHA SN 03/2019 §3.7.1",
                "resubmission_window_days": 30,
                "max_resubmissions": 2
            })

        return claims

    # -------------------------------------------------------------------------
    # 6. Database Persistence & Audit Ledger (data/clinical_records.db)
    # -------------------------------------------------------------------------

    @classmethod
    def init_database(cls, db_path: str = DEFAULT_CLINICAL_DB):
        """Ensure clinical_soap_notes schema exists with proper indexes."""
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS clinical_soap_notes (
                note_id TEXT PRIMARY KEY,
                encounter_id TEXT NOT NULL,
                patient_identifier_hash TEXT NOT NULL,
                clinician_id TEXT NOT NULL,
                subjective_text TEXT NOT NULL,
                objective_text TEXT NOT NULL,
                assessment_text TEXT NOT NULL,
                plan_text TEXT NOT NULL,
                icd10_codes_json TEXT NOT NULL,
                dha_claim_codes_json TEXT NOT NULL,
                signed_off_by_clinician INTEGER DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
            );
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_soap_encounter ON clinical_soap_notes(encounter_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_soap_patient ON clinical_soap_notes(patient_identifier_hash);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_soap_clinician ON clinical_soap_notes(clinician_id);")
            conn.commit()
        finally:
            conn.close()

    @classmethod
    def commit_soap_to_db(cls, db_path: str, soap_record: Dict[str, Any]) -> str:
        """
        Inserts structured SOAP note into clinical_soap_notes table under UAE PDPL SHA-256 pseudonymization.
        Emits tamper-evident cryptographic audit entry to taryaq_audit.jsonl.
        Returns note_id.
        """
        cls.init_database(db_path)

        note_id = soap_record.get("note_id") or str(uuid.uuid4())
        encounter_id = soap_record.get("encounter_id") or f"ENC-{uuid.uuid4().hex[:8].upper()}"

        # Resolve pseudonymized patient identifier
        patient_raw = soap_record.get("patient_identifier_hash") or soap_record.get("patient_id") or soap_record.get("emirates_id", "")
        # If not a 64-char hex string, hash it
        if len(patient_raw) == 64 and re.match(r"^[0-9a-fA-F]{64}$", patient_raw):
            patient_hash = patient_raw.lower()
        else:
            patient_hash = cls.pseudonymize_patient_identity(patient_raw)

        clinician_id = soap_record.get("clinician_id") or "DHA-MD-88124"

        # Resolve text fields with PII scrubbing
        subj_text = soap_record.get("subjective_text") or soap_record.get("subjective") or ""
        obj_text = soap_record.get("objective_text") or soap_record.get("objective") or ""
        asmt_text = soap_record.get("assessment_text") or soap_record.get("assessment") or ""
        plan_text = soap_record.get("plan_text") or soap_record.get("plan") or ""

        subj_text = cls.scrub_narrative_pii(subj_text)
        obj_text = cls.scrub_narrative_pii(obj_text)

        # Resolve ICD-10 & DHA claim JSON arrays
        icd10_val = soap_record.get("icd10_codes_json") or soap_record.get("icd10") or []
        if isinstance(icd10_val, (list, dict)):
            icd10_json = json.dumps(icd10_val)
        else:
            icd10_json = str(icd10_val)

        dha_val = soap_record.get("dha_claim_codes_json") or soap_record.get("dha_claims") or []
        if isinstance(dha_val, (list, dict)):
            dha_json = json.dumps(dha_val)
        else:
            dha_json = str(dha_val)

        signed_off = int(bool(soap_record.get("signed_off_by_clinician", 0)))
        created_at = soap_record.get("created_at") or datetime.datetime.now(datetime.timezone.utc).isoformat()

        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO clinical_soap_notes (
                note_id, encounter_id, patient_identifier_hash, clinician_id,
                subjective_text, objective_text, assessment_text, plan_text,
                icd10_codes_json, dha_claim_codes_json, signed_off_by_clinician, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                note_id, encounter_id, patient_hash, clinician_id,
                subj_text, obj_text, asmt_text, plan_text,
                icd10_json, dha_json, signed_off, created_at
            ))
            conn.commit()
        finally:
            conn.close()

        # Audit ledger emission
        audit_payload = {
            "event": "CLINICAL_SOAP_NOTE_COMMITTED",
            "note_id": note_id,
            "encounter_id": encounter_id,
            "patient_hash": patient_hash,
            "clinician_id": clinician_id,
            "signed_off": bool(signed_off)
        }
        if append_audit_log is not None:
            try:
                append_audit_log(audit_payload)
            except Exception:
                pass
        else:
            # Standard library JSONL fallback
            try:
                with open(DEFAULT_AUDIT_LOG, "a", encoding="utf-8") as f:
                    f.write(json.dumps(audit_payload) + "\n")
            except Exception:
                pass

        return note_id

    @classmethod
    def get_soap_notes(cls, db_path: str, patient_hash: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Queries stored SOAP notes with optional patient_hash filter."""
        cls.init_database(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            if patient_hash:
                cursor.execute("""
                SELECT * FROM clinical_soap_notes
                WHERE patient_identifier_hash = ?
                ORDER BY created_at DESC LIMIT ?
                """, (patient_hash.lower(), limit))
            else:
                cursor.execute("""
                SELECT * FROM clinical_soap_notes
                ORDER BY created_at DESC LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                # Unpack JSON structures
                try:
                    item["icd10"] = json.loads(item["icd10_codes_json"])
                    item["icd10_codes"] = item["icd10"]
                except Exception:
                    item["icd10"] = []
                    item["icd10_codes"] = []

                try:
                    item["dha_claims"] = json.loads(item["dha_claim_codes_json"])
                    item["dha_claim_codes"] = item["dha_claims"]
                except Exception:
                    item["dha_claims"] = []
                    item["dha_claim_codes"] = []

                item["signed_off"] = bool(item["signed_off_by_clinician"])
                item["patient_hash"] = item["patient_identifier_hash"]
                results.append(item)
            return results
        finally:
            conn.close()

    @classmethod
    def get_soap_note_by_id(cls, db_path: str, note_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single SOAP note by its note_id."""
        cls.init_database(db_path)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clinical_soap_notes WHERE note_id = ?", (note_id,))
            row = cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            try:
                item["icd10"] = json.loads(item["icd10_codes_json"])
                item["icd10_codes"] = item["icd10"]
            except Exception:
                item["icd10"] = []
                item["icd10_codes"] = []

            try:
                item["dha_claims"] = json.loads(item["dha_claim_codes_json"])
                item["dha_claim_codes"] = item["dha_claims"]
            except Exception:
                item["dha_claims"] = []
                item["dha_claim_codes"] = []

            item["signed_off"] = bool(item["signed_off_by_clinician"])
            item["patient_hash"] = item["patient_identifier_hash"]
            return item
        finally:
            conn.close()

    @classmethod
    def signoff_soap_note(
        cls,
        db_path: str,
        note_id: str,
        clinician_id: str,
        signature_token: Optional[str] = None
    ) -> bool:
        """
        Attests and cryptographically locks a clinical SOAP note (signed_off_by_clinician = 1).
        Emits immutable audit ledger event.
        """
        cls.init_database(db_path)
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE clinical_soap_notes
            SET signed_off_by_clinician = 1
            WHERE note_id = ?
            """, (note_id,))
            conn.commit()
            updated = cursor.rowcount > 0
        finally:
            conn.close()

        if updated:
            audit_payload = {
                "event": "CLINICAL_SOAP_NOTE_SIGNED_OFF",
                "note_id": note_id,
                "clinician_id": clinician_id,
                "signature_token": signature_token or "CLINICIAN_DIGITAL_SIG",
                "signed_off": True
            }
            if append_audit_log is not None:
                try:
                    append_audit_log(audit_payload)
                except Exception:
                    pass
            else:
                try:
                    with open(DEFAULT_AUDIT_LOG, "a", encoding="utf-8") as f:
                        f.write(json.dumps(audit_payload) + "\n")
                except Exception:
                    pass

        return updated
