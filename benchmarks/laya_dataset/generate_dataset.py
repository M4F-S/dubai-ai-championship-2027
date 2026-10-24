#!/usr/bin/env python3
"""
benchmarks/laya_dataset/generate_dataset.py
-------------------------------------------
Sovereign Clinical & Regulatory Dataset Generator for Laya Multilingual 322M.
Part of the Dubai AI Agents Championship 2026-2027 (Task M-07).

Key Properties:
- 10 Canonical Sovereign Decision Questions (Intent, Urgency, Renal Risk,
  CYP3A4 Interaction, Controlled Drugs, Claim Delay, PII Leakage,
  Contradiction, Human Override, Air-Gap Fallback).
- 2,400 labeled examples (240 per question).
- Balanced 50% Arabic and 50% English coverage across EVERY option head.
- Mix of clear prototypical cases (~86%) and subtle borderline clinical
  scenarios (~14%) to reflect real-world clinical nuance and calibrated triage.
- Strict patient-level stratified split:
    * 400 distinct patients (DXB-PAT-0001 .. DXB-PAT-0400)
    * Train: 280 patients (70%, 1,680 examples, 6 per patient)
    * Dev:    60 patients (15%, 360 examples, 6 per patient)
    * Test:   60 patients (15%, 360 examples, 6 per patient)
    * ZERO patient ID overlap across splits (guaranteed no data leakage).
- Authentic Dubai/UAE context: DHA SN 03/2019 (0.03%/day delay penalty),
  MOHAP Controlled Drug Schedules, DESC ISR v3.1 sovereign enclaves,
  Emirates ID formats (784-YYYY-XXXXXXX-Z), and bilingual clinical entities.
"""

import os
import sys
import json
import random
import argparse
from typing import Dict, List, Any, Tuple
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. CANONICAL DECISION HEAD DEFINITIONS
# -----------------------------------------------------------------------------

DECISION_QUESTIONS: Dict[str, Dict[str, Any]] = {
    "Q1_INTENT_ROUTING": {
        "title": "Intent Routing & Workflow Dispatch",
        "options": [
            "CLINICAL_INTAKE",
            "CLAIM_SCRUB",
            "MED_LOOKUP",
            "POLICY_AUDIT",
            "GENERAL_QUERY"
        ],
        "description": "Routes user interaction to the appropriate operational agent or module."
    },
    "Q2_CLINICAL_URGENCY": {
        "title": "Clinical Urgency & Triage Triangulation",
        "options": [
            "STAT_EMERGENCY",
            "URGENT_CARE",
            "ROUTINE_DISPENSE"
        ],
        "description": "Assesses clinical acuity for immediate resuscitation vs urgent care vs routine dispense."
    },
    "Q3_RENAL_RISK_SUSPECT": {
        "title": "Renal Impairment & Dose Adjustment Suspect",
        "options": [
            "NORMAL_RENAL",
            "SUSPECTED_IMPAIRMENT_STAGE3_PLUS"
        ],
        "description": "Flags CKD Stage 3+ (eGFR < 60 mL/min) or elevated serum creatinine requiring dose reduction."
    },
    "Q4_CYP3A4_INTERACTION_RISK": {
        "title": "CYP3A4 & P-gp Fatal Interaction Risk",
        "options": [
            "SAFE_COMBINATION",
            "POTENT_CYP3A4_CONTRAINDICATION"
        ],
        "description": "Detects lethal metabolic inhibition (e.g. Colchicine + Clarithromycin, Simvastatin + Ketoconazole)."
    },
    "Q5_CONTROLLED_SUBSTANCE_CHECK": {
        "title": "MOHAP Controlled Substance Verification",
        "options": [
            "STANDARD_PRESCRIPTION",
            "UAE_SCHEDULED_NARCOTIC_PSYCHOTROPIC"
        ],
        "description": "Identifies UAE MOHAP Schedule Semi-Controlled / Controlled / Psychotropic drugs."
    },
    "Q6_CLAIM_DELAY_PENALTY_RISK": {
        "title": "DHA SN 03/2019 Claim Submission Cycle Scrubber",
        "options": [
            "ON_TIME_SUBMISSION",
            "DHA_SN_03_2019_DELAY_PENALTY"
        ],
        "description": "Calculates statutory 0.03%/day late submission fee liability under DHA SN 03/2019 (§3.8.4)."
    },
    "Q7_PII_LEAK_RISK": {
        "title": "DESC ISR v3.1 PII & Identity Redaction Risk",
        "options": [
            "PII_CLEAN",
            "SENSITIVE_EMIRATES_ID_OR_NAME_DETECTED"
        ],
        "description": "Detects raw Emirates ID numbers, patient full names, and sensitive identifiers."
    },
    "Q8_CONTRADICTION_DETECTED": {
        "title": "Indication vs ICD-10 Contradiction Check",
        "options": [
            "CLINICAL_MATCH",
            "INDICATION_DIAGNOSIS_MISMATCH"
        ],
        "description": "Flags clinical incompatibility between prescribed therapy and documented ICD-10 indication."
    },
    "Q9_HUMAN_OVERRIDE_REQUIRED": {
        "title": "Autonomous Safety Gate & Physician Override",
        "options": [
            "AUTOMATED_CLEARANCE",
            "MANDATORY_PHYSICIAN_OVERRIDE"
        ],
        "description": "Determines if automated sign-off is permitted or mandatory physician review is required."
    },
    "Q10_AIR_GAP_FALLBACK": {
        "title": "Sovereign Air-Gap vs Cloud Escalation",
        "options": [
            "SOVEREIGN_ON_DEVICE",
            "CLOUD_ESCALATION_PERMITTED"
        ],
        "description": "Governs whether execution must stay offline on-device or secondary cloud consensus is allowed."
    }
}

# -----------------------------------------------------------------------------
# 2. DUBAI CLINICAL DOMAIN POOLS
# -----------------------------------------------------------------------------

DUBAI_HOSPITALS = [
    ("Dubai Hospital", "مستشفى دبي"),
    ("Rashid Hospital Trauma Centre", "مركز راشد للإصابات والحوادث"),
    ("Latifa Women and Children Hospital", "مستشفى لطيفة للنساء والأطفال"),
    ("Al Jalila Children's Specialty Hospital", "مستشفى الجليلة التخصصي للأطفال"),
    ("Mediclinic City Hospital Dubai Healthcare City", "ميديكلينيك مستشفى المدينة"),
    ("Aster Clinic Bur Dubai", "عيادة أستر بر دبي"),
    ("Clemenceau Medical Center Dubai", "مركز كليمنصو الطبي دبي"),
    ("King's College Hospital London Dubai", "مستشفى كينغز كوليدج لندن دبي"),
    ("Prime Hospital Garhoud", "مستشفى برايم القرهود"),
    ("Saudi German Hospital Al Barsha", "المستشفى السعودي الألماني البرشاء")
]

DOCTORS = [
    ("Dr. Mariam Al-Falasi", "د. مريم الفلاسي", "DHA-P-44012"),
    ("Dr. Tariq Mansoor", "د. طارق منصور", "DHA-P-77192"),
    ("Dr. Zayed Al-Ketbi", "د. زايد الكتبي", "DHA-P-11204"),
    ("Dr. Aisha Al-Suwaidi", "د. عائشة السويدي", "DHA-P-99381"),
    ("Dr. Ramesh Sharma", "د. راميش شارما", "DHA-P-55291"),
    ("Dr. Sarah Davies", "د. سارة ديفيز", "DHA-P-33109"),
    ("Dr. Mohammed Al-Hashimi", "د. محمد الهاشمي", "DHA-P-88410"),
    ("Dr. Fatima Al-Nuaimi", "د. فاطمة النعيمي", "DHA-P-66271")
]

PATIENT_NAMES_AR = [
    "أحمد بن راشد الكعبي", "فاطمة المنصوري", "محمد سالم المري", "مريم الشامسي",
    "عبد الله المهيري", "نورة الظاهري", "حمد القاسمي", "شماء البلوشي",
    "زايد الفلاسي", "عائشة السويدي", "سلطان المزروعي", "ميثاء الهاجري",
    "خالد الحوسني", "حصة الرميثي", "عمر بن ثاني", "سلامة العامري"
]

PATIENT_NAMES_EN = [
    "Ahmed Rashid Al-Kaabi", "Fatima Al-Mansoor", "Salem Mohammed Al-Marri", "Maryam Al-Shamsi",
    "Abdullah Al-Muhairi", "Noura Al-Dhaheri", "Hamad Al-Qasimi", "Shamma Al-Baloushi",
    "Zayed Al-Falasi", "Aisha Al-Suwaidi", "Sultan Al-Mazrouei", "Maitha Al-Hajri",
    "Khaled Al-Hosani", "Hessa Al-Rumaithi", "Omar Bin Thani", "Salama Al-Ameri"
]

def _make_eid(rnd: random.Random) -> str:
    y = rnd.randint(1955, 2005)
    seq = rnd.randint(1000000, 9999999)
    chk = rnd.randint(1, 9)
    return f"784-{y}-{seq}-{chk}"

# -----------------------------------------------------------------------------
# 3. DOMAIN GENERATORS PER QUESTION (PROTOTYPICAL + BORDERLINE CASES)
# -----------------------------------------------------------------------------

def generate_q1_examples(rnd: random.Random, n: int) -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Q1_INTENT_ROUTING: 5 classes."""
    options = DECISION_QUESTIONS["Q1_INTENT_ROUTING"]["options"]
    combos = [(opt, lang) for opt in options for lang in ["ar", "en"]]
    examples = []
    
    for i in range(n):
        opt, lang = combos[i % len(combos)]
        hosp_en, hosp_ar = rnd.choice(DUBAI_HOSPITALS)
        doc_en, doc_ar, lic = rnd.choice(DOCTORS)
        is_borderline = (i % 7 == 0)
        
        if opt == "CLINICAL_INTAKE":
            if is_borderline:
                if lang == "ar":
                    text = f"مريض في {hosp_ar} يقدم وصفة جديدة لمراجعة الجرعة، ويسأل في ذات الوقت عن تغطية التأمين، الأولوية لفحص الوصفة السريرية."
                else:
                    text = f"Patient presenting at {hosp_en} for clinical intake with new prescription; also inquires about insurance coverage, primary action is clinical order verification."
            else:
                if lang == "ar":
                    text = f"يرجى تسجيل وتقييم وصفة طبية جديدة صادرة من {hosp_ar}، الطبيب المعالج {doc_ar}: فحص الجرعة الموصوفة، تداخل الأدوية، وحالة الحساسية للمريض."
                else:
                    text = f"Initiate clinical intake review for new outpatient prescription issued at {hosp_en} by {doc_en} ({lic}): verify dosage calculation, drug allergy screening, and clinical appropriateness."
            meta = {"intent": "clinical_intake", "is_borderline": is_borderline}
            
        elif opt == "CLAIM_SCRUB":
            clm_id = f"CLM-DXB-{rnd.randint(10000, 99999)}"
            delay = rnd.randint(3, 40)
            if is_borderline:
                if lang == "ar":
                    text = f"تدقيق مطالبة تأمين eClaimLink رقم {clm_id} ومطابقة بنود الفاتورة مع التغطية التأمينية المعتمدة."
                else:
                    text = f"Scrub eClaimLink payload for claim {clm_id} from {hosp_en}: cross-reference invoice line items with policy coverage."
            else:
                if lang == "ar":
                    text = f"تدقيق ومطابقة مطالبة تأمين صحي eClaimLink رقم {clm_id}: فحص مهلة التقديم حسب تعميم هيئة الصحة بدبي DHA SN 03/2019، والتأكد من توافق رموز ICD-10 مع الخدمات المسعرة."
                else:
                    text = f"Scrub eClaimLink submission payload for claim {clm_id} from {hosp_en}: validate submission window under DHA SN 03/2019, deductible codes, and ICD-10 billing consistency."
            meta = {"intent": "claim_scrub", "claim_id": clm_id, "is_borderline": is_borderline}
            
        elif opt == "MED_LOOKUP":
            drug = rnd.choice(["Metformin", "Colchicine", "Pregabalin", "Atorvastatin", "Clarithromycin"])
            if is_borderline:
                if lang == "ar":
                    text = f"البحث في الدليل الدوائي الإماراتي عن تفاصيل التركيز والشركة المصنعة لدواء {drug}."
                else:
                    text = f"Formulary search in UAE registered drug index for concentration and manufacturer details of {drug}."
            else:
                if lang == "ar":
                    text = f"استعلام وبحث دوائي في دليل الأدوية المعتمدة بوزارة الصحة ووقاية المجتمع (MOHAP): التحقق من البدائل الجنيسة المتاحة لدواء {drug} وتحديد الجرعات الموصى بها للبالغين."
                else:
                    text = f"Formulary lookup in UAE MOHAP registered drug directory: search available bioequivalent generic alternatives for {drug} and verify standard adult dosing monographs."
            meta = {"intent": "med_lookup", "drug": drug, "is_borderline": is_borderline}
            
        elif opt == "POLICY_AUDIT":
            if is_borderline:
                if lang == "ar":
                    text = f"مراجعة سجلات الامتثال وقرارات التجاوز الإداري للصيدلية للشهر المنصرم."
                else:
                    text = f"Review compliance logs and administrative override decisions for the pharmacy from past month."
            else:
                if lang == "ar":
                    text = f"إجراء مراجعة وتدقيق امتثال رقابي لسجل التجاوزات الصيدلانية في {hosp_ar}: التحقق من تطابق القرارات مع ضوابط معايير أمن المعلومات DESC ISR v3.1 وتوقيع الصيدلي المسؤول."
                else:
                    text = f"Conduct supervisory policy audit on clinical override audit logs at {hosp_en}: ensure full compliance with DESC ISR v3.1 access governance and pharmacist sign-off protocols."
            meta = {"intent": "policy_audit", "is_borderline": is_borderline}
            
        else: # GENERAL_QUERY
            if is_borderline:
                if lang == "ar":
                    text = f"استفسار عن موقع الصيدلية ورقم الهاتف للاستعلام عن استلام الأدوية."
                else:
                    text = f"General query regarding pharmacy location and phone contact for medicine collection inquiries."
            else:
                if lang == "ar":
                    text = f"استفسار عام: ما هي مواعيد عمل صيدلية العيادات الخارجية في {hosp_ar} خلال عطلة نهاية الأسبوع ورقم تحويلة الاستقبال الدوائي؟"
                else:
                    text = f"General operational inquiry: What are the outpatient pharmacy operating hours and direct telephone extensions at {hosp_en} during public holidays?"
            meta = {"intent": "general_query", "is_borderline": is_borderline}
            
        examples.append((text, opt, lang, meta))
    return examples

def generate_q2_examples(rnd: random.Random, n: int) -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Q2_CLINICAL_URGENCY: 3 classes."""
    options = DECISION_QUESTIONS["Q2_CLINICAL_URGENCY"]["options"]
    combos = [(opt, lang) for opt in options for lang in ["ar", "en"]]
    examples = []
    
    for i in range(n):
        opt, lang = combos[i % len(combos)]
        hosp_en, hosp_ar = rnd.choice(DUBAI_HOSPITALS)
        is_borderline = (i % 7 == 0)
        
        if opt == "STAT_EMERGENCY":
            bp_sys = rnd.randint(65, 80)
            bp_dia = rnd.randint(35, 50)
            if is_borderline:
                if lang == "ar":
                    text = f"حالة طوارئ: مريض يعاني من صعوبة حادة بالتنفس وزرقة في الأطراف وضغط دم {bp_sys}/{bp_dia}، استدعاء فريق الطوارئ فوراً."
                else:
                    text = f"Emergency resuscitation: Patient experiencing severe cyanosis, acute respiratory failure, BP {bp_sys}/{bp_dia} mmHg, code blue alert."
            else:
                if lang == "ar":
                    text = f"حالة طارئة حرجة فورية (STAT): مريض في {hosp_ar} يعاني من صدمة تأقية حادة، صرير تنفسي، تورم الوجه، وضغط دم {bp_sys}/{bp_dia} مم زئبق بعد إعطاء جرعة وريدية. يتطلب إبينفرين وإنعاش فوري."
                else:
                    text = f"STAT Emergency Alert: Patient at {hosp_en} presenting with acute anaphylactic shock, stridor, facial angioedema, and BP {bp_sys}/{bp_dia} mmHg following intravenous administration. Immediate epinephrine resuscitation required."
            meta = {"urgency": "STAT", "is_borderline": is_borderline}
            
        elif opt == "URGENT_CARE":
            temp = round(rnd.uniform(38.8, 39.7), 1)
            if is_borderline:
                if lang == "ar":
                    text = f"حالة عاجلة: مريض سكري يعاني من جرح ملتهب بالقدم مع سخونة موضعية وحرارة {temp}، يحتاج مضاداً حيوياً ورؤية الطبيب خلال ساعات."
                else:
                    text = f"Urgent care needed: Diabetic patient with inflamed foot ulcer, localized erythema, temperature {temp} C; needs antibiotics and physician evaluation today."
            else:
                if lang == "ar":
                    text = f"حالة عاجلة ذات أولوية: مريض يعاني من نوبة نقرس حادة وشديدة بمفصل القدم مع حمى {temp} مئوية وألم لا يحتمل، يحتاج تدخلاً علاجياً وتسكين خلال ساعتين."
                else:
                    text = f"Urgent Care Priority: Patient presenting with acute monoarticular gout flare, severe joint inflammation, pyrexia ({temp} C), requiring clinical evaluation and analgesia within 2 hours."
            meta = {"urgency": "URGENT", "is_borderline": is_borderline}
            
        else: # ROUTINE_DISPENSE
            days = rnd.choice([30, 60, 90])
            if is_borderline:
                if lang == "ar":
                    text = f"تجديد وصفة روتينية: مريض مزمن مستقر لصرف علاج الضغط الشهري، لا توجد شكاوى مستجدة."
                else:
                    text = f"Refill prescription: Stable chronic patient requesting standard 30-day antihypertensive refill, no new symptoms reported."
            else:
                if lang == "ar":
                    text = f"صرف روتيني اعتيادي: تجديد شهري منتظم لمدة {days} يوماً لوصفة مريض سكري وضغط مستقر، أدوية ميتفورمين وأملوديبين، لا توجد أي شكاوى حادة أو تغير في الفحوصات."
                else:
                    text = f"Routine Outpatient Dispense: Regular {days}-day maintenance refill for stable chronic patient with well-controlled Type 2 Diabetes and Hypertension (Metformin 850mg, Amlodipine 5mg). No acute distress."
            meta = {"urgency": "ROUTINE", "is_borderline": is_borderline}
            
        examples.append((text, opt, lang, meta))
    return examples

def generate_q3_examples(rnd: random.Random, n: int) -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Q3_RENAL_RISK_SUSPECT: 2 classes."""
    options = DECISION_QUESTIONS["Q3_RENAL_RISK_SUSPECT"]["options"]
    combos = [(opt, lang) for opt in options for lang in ["ar", "en"]]
    examples = []
    
    for i in range(n):
        opt, lang = combos[i % len(combos)]
        is_borderline = (i % 7 == 0)
        
        if opt == "NORMAL_RENAL":
            if is_borderline:
                egfr = round(rnd.uniform(61.0, 66.0), 1)
                cr = round(rnd.uniform(1.05, 1.18), 2)
                if lang == "ar":
                    text = f"فحص كلى: eGFR يبلغ {egfr} مل/دقيقة، الكرياتينين {cr} ملغ/ديسيلتر، ضمن الحدود الطبيعية المقبولة ولا يتطلب خفض جرعة الدواء."
                else:
                    text = f"Renal assessment: eGFR {egfr} mL/min, Creatinine {cr} mg/dL, borderline normal range (Stage 2 preserved function); standard dosing valid."
            else:
                egfr = round(rnd.uniform(80.0, 115.0), 1)
                cr = round(rnd.uniform(0.7, 1.0), 2)
                if lang == "ar":
                    text = f"فحوصات وظائف الكلى المخبرية: معدل الترشيح الكبيبي المقدر eGFR يبلغ {egfr} مل/دقيقة/1.73م2، والكرياتينين {cr} ملغ/ديسيلتر. وظائف الكلى طبيعية والجرعات القياسية ملائمة."
                else:
                    text = f"Laboratory Renal Panel: Estimated eGFR is {egfr} mL/min/1.73m2, Serum Creatinine {cr} mg/dL. Normal renal clearance; patient is eligible for standard standard dosing."
            meta = {"egfr": egfr, "cr": cr, "renal_status": "NORMAL", "is_borderline": is_borderline}
            
        else: # SUSPECTED_IMPAIRMENT_STAGE3_PLUS
            if is_borderline:
                egfr = round(rnd.uniform(53.0, 58.5), 1)
                cr = round(rnd.uniform(1.28, 1.55), 2)
                if lang == "ar":
                    text = f"تقرير المختبر: eGFR {egfr} مل/دقيقة، الكرياتينين {cr} ملغ/ديسيلتر، قصور كلوي مرحلة 3a مبكرة، يلزم تعديل الجرعات الكلوية."
                else:
                    text = f"Lab finding: eGFR {egfr} mL/min/1.73m2, Creatinine {cr} mg/dL, early CKD Stage 3a impairment; dose reduction suspect."
            else:
                egfr = round(rnd.uniform(14.0, 45.0), 1)
                cr = round(rnd.uniform(2.1, 4.2), 2)
                stage = "Stage 4 (Severe)" if egfr < 30 else "Stage 3b (Moderate-Severe)"
                if lang == "ar":
                    text = f"تنبيه قصور كلوي: نتائج المختبر تظهر هبوطاً حاداً في eGFR إلى {egfr} مل/دقيقة/1.73م2 مع ارتفاع الكرياتينين إلى {cr} ملغ/ديسيلتر ({stage}). اشتباه قوي بقصور كلوي يتطلب خفض الجرعة أو تجنب الدواء."
                else:
                    text = f"Renal Impairment Alert: Patient lab reveals compromised eGFR of {egfr} mL/min/1.73m2 and elevated Serum Creatinine {cr} mg/dL indicative of CKD {stage}. High risk of drug accumulation; dosage adjustment mandatory."
            meta = {"egfr": egfr, "cr": cr, "renal_status": "IMPAIRED", "is_borderline": is_borderline}
            
        examples.append((text, opt, lang, meta))
    return examples

def generate_q4_examples(rnd: random.Random, n: int) -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Q4_CYP3A4_INTERACTION_RISK: 2 classes."""
    options = DECISION_QUESTIONS["Q4_CYP3A4_INTERACTION_RISK"]["options"]
    combos = [(opt, lang) for opt in options for lang in ["ar", "en"]]
    examples = []
    
    safe_pairs = [
        ("Metformin", "Lisinopril", "ميتفورمين", "ليزينوبريل"),
        ("Paracetamol", "Amoxicillin", "باراسيتامول", "أموكسيسيلين"),
        ("Atorvastatin", "Metformin", "أتورفاستاتين", "ميتفورمين"),
        ("Pantoprazole", "Amlodipine", "بانتوبرازول", "أملوديبين")
    ]
    contra_pairs = [
        ("Colchicine", "Clarithromycin", "كولشيسين", "كلاريثروميسين", "FATAL_CYP3A4_RENAL_CONTRAINDICATION"),
        ("Simvastatin", "Ketoconazole", "سيمفاستاتين", "كيتوكونازول", "RHABDOMYOLYSIS_CYP3A4_BLOCK"),
        ("Fentanyl", "Ritonavir", "فينتانيل", "ريتونافير", "RESPIRATORY_DEPRESSION_CYP3A4_BLOCK"),
        ("Colchicine", "Itraconazole", "كولشيسين", "إيتراكونازول", "FATAL_CYP3A4_TOXICITY")
    ]
    
    for i in range(n):
        opt, lang = combos[i % len(combos)]
        is_borderline = (i % 7 == 0)
        
        if opt == "SAFE_COMBINATION":
            d1_en, d2_en, d1_ar, d2_ar = rnd.choice(safe_pairs)
            if is_borderline:
                if lang == "ar":
                    text = f"وصف دوائي مشترك: {d1_ar} مع {d2_ar}. مسارات الاستقلاب الدوائي منفصلة ولا يوجد تثبيط إنزيمي خطير."
                else:
                    text = f"Co-administration of {d1_en} and {d2_en}: Distinct metabolic clearance routes, no fatal enzymatic CYP interaction."
            else:
                if lang == "ar":
                    text = f"تقييم سلامة التداخل الدوائي بين {d1_ar} و {d2_ar}: لا يوجد تثبيط معنوي لإنزيم كبدي CYP3A4 أو مضخة P-gp، والتوليفة العلاجية تعتبر آمنة وفق المعايير السريرية المعتمدة."
                else:
                    text = f"Pharmacokinetic interaction screening for concurrent administration of {d1_en} and {d2_en}: No clinically significant CYP3A4 or P-gp metabolic pathway conflict detected. Combination cleared as safe."
            meta = {"drug1": d1_en, "drug2": d2_en, "is_borderline": is_borderline}
            
        else: # POTENT_CYP3A4_CONTRAINDICATION
            d1_en, d2_en, d1_ar, d2_ar, code = rnd.choice(contra_pairs)
            if is_borderline:
                if lang == "ar":
                    text = f"تحذير تداخل: وصف متزامن لـ {d1_ar} مع مثبط قوي {d2_ar}، مانع سريري قاطع لمنع التسمم."
                else:
                    text = f"Drug interaction hazard: Concomitant {d1_en} with potent inhibitor {d2_en}, contraindicated due to severe accumulation toxicity."
            else:
                if lang == "ar":
                    text = f"تحذير خطير: وصف دواء {d1_ar} بالتزامن مع {d2_ar}. يمثل هذا التثبيط القوي لإنزيم CYP3A4 ومضخة P-gp خطراً مهدداً للحياة مع احتمالية تسمم حاد مميت. مانع طبي قاطع."
                else:
                    text = f"Critical Contraindication Alert: Co-prescription of {d1_en} with potent CYP3A4 / P-gp inhibitor {d2_en}. Substantial risk of life-threatening toxicity ({code}). Automated dispensing must be blocked."
            meta = {"drug1": d1_en, "drug2": d2_en, "code": code, "is_borderline": is_borderline}
            
        examples.append((text, opt, lang, meta))
    return examples

def generate_q5_examples(rnd: random.Random, n: int) -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Q5_CONTROLLED_SUBSTANCE_CHECK: 2 classes."""
    options = DECISION_QUESTIONS["Q5_CONTROLLED_SUBSTANCE_CHECK"]["options"]
    combos = [(opt, lang) for opt in options for lang in ["ar", "en"]]
    examples = []
    
    standard_meds = [
        ("Amoxicillin-Clavulanate 1g", "أموكسيسيلين-كلافولانات 1 جم"),
        ("Omeprazole 20mg capsules", "أوميبرازول 20 ملغ كبسولات"),
        ("Atorvastatin 40mg tablets", "أتورفاستاتين 40 ملغ أقراص"),
        ("Metformin 1000mg ER", "ميتفورمين 1000 ملغ ممتد المفعول")
    ]
    controlled_meds = [
        ("Tramadol 50mg capsules", "ترامادول 50 ملغ كبسولات", "Schedule_Semi_Controlled"),
        ("Pregabalin 150mg capsules", "بريغابالين 150 ملغ كبسولات", "Schedule_Semi_Controlled"),
        ("Diazepam 5mg tablets", "ديازيبام 5 ملغ أقراص", "Schedule_Psychotropic_CD"),
        ("Morphine Sulfate 10mg IV ampoules", "كبريتات المورفين 10 ملغ أمبولات", "Schedule_Narcotic_Controlled")
    ]
    
    for i in range(n):
        opt, lang = combos[i % len(combos)]
        is_borderline = (i % 7 == 0)
        
        if opt == "STANDARD_PRESCRIPTION":
            med_en, med_ar = rnd.choice(standard_meds)
            if is_borderline:
                if lang == "ar":
                    text = f"صرف وصفة: دواء {med_ar}، لا يخضع لرقابة الأدوية المخدرة، صنف دوائي اعتيادي."
                else:
                    text = f"Dispensing order: {med_en}, standard unscheduled prescription medication, routine clearance."
            else:
                if lang == "ar":
                    text = f"وصفة طبية اعتيادية لصرف: {med_ar}. الدواء غير مدرج بجداول المواد المخدرة أو المؤثرات العقلية المراقبة بوزارة الصحة ووقاية المجتمع (MOHAP). صرف روتيني مسموح."
                else:
                    text = f"Prescription item review: {med_en}. Non-scheduled therapeutic substance under UAE MOHAP pharmacy regulations. Cleared for standard prescription dispensing."
            meta = {"drug": med_en, "is_borderline": is_borderline}
            
        else: # UAE_SCHEDULED_NARCOTIC_PSYCHOTROPIC
            med_en, med_ar, sched = rnd.choice(controlled_meds)
            if is_borderline:
                if lang == "ar":
                    text = f"تحقق أدوية مراقبة: صرف {med_ar}، مدرج بجداول الرقابة الدوائية بوزارة الصحة، يلزم تسجيل الهوية."
                else:
                    text = f"Controlled drug verification: {med_en}, regulated on UAE MOHAP schedules, patient ID check required."
            else:
                if lang == "ar":
                    text = f"تنبيه مراقبة الأدوية: تحتوي الوصفة على {med_ar} المدرج تحت جداول الأدوية المراقبة والمؤثرات العقلية ({sched}). يتطلب التحقق الإلزامي من الهوية الإماراتية وتوقيع الطبيب المعتمد."
                else:
                    text = f"Controlled Substance Warning: Prescription contains {med_en}, classified under UAE MOHAP {sched}. Mandatory Emirates ID verification, serial registry tracking, and licensed physician endorsement required."
            meta = {"drug": med_en, "schedule": sched, "is_borderline": is_borderline}
            
        examples.append((text, opt, lang, meta))
    return examples

def generate_q6_examples(rnd: random.Random, n: int) -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Q6_CLAIM_DELAY_PENALTY_RISK: 2 classes."""
    options = DECISION_QUESTIONS["Q6_CLAIM_DELAY_PENALTY_RISK"]["options"]
    combos = [(opt, lang) for opt in options for lang in ["ar", "en"]]
    examples = []
    
    for i in range(n):
        opt, lang = combos[i % len(combos)]
        clm_id = f"CLM-DHA-{rnd.randint(10000, 99999)}"
        amount_aed = rnd.randint(800, 15000)
        is_borderline = (i % 7 == 0)
        
        if opt == "ON_TIME_SUBMISSION":
            delay = rnd.randint(12, 14) if is_borderline else rnd.randint(1, 10)
            if is_borderline:
                if lang == "ar":
                    text = f"مطالبة eClaimLink {clm_id} تم رفعها بعد {delay} يوماً، على حافة مهلة التقديم ولكنها مقبولة دون احتساب غرامة تأخير."
                else:
                    text = f"eClaimLink claim {clm_id} submitted at {delay} days, close to statutory deadline but within acceptable timely window."
            else:
                if lang == "ar":
                    text = f"مطالبة eClaimLink رقم {clm_id} بقيمة {amount_aed} درهم: تم إرسال المطالبة بعد {delay} أيام من تاريخ الخدمة. الإرسال ضمن المهلة القانونية لتعميم هيئة الصحة بدبي DHA SN 03/2019 بدون أي غرامات تأخير."
                else:
                    text = f"eClaimLink claim {clm_id} valued at AED {amount_aed}: submitted {delay} days post-encounter. Fully compliant with DHA SN 03/2019 submission window; zero penalty exposure."
            meta = {"claim_id": clm_id, "delay_days": delay, "is_borderline": is_borderline}
            
        else: # DHA_SN_03_2019_DELAY_PENALTY
            delay = rnd.randint(16, 22) if is_borderline else rnd.randint(35, 95)
            penalty_aed = round(amount_aed * (0.0003 * delay), 2)
            if is_borderline:
                if lang == "ar":
                    text = f"تأخر تقديم مطالبة eClaimLink {clm_id} لمدة {delay} يوماً (تجاوزت مهلة 14 يوماً)، تطبق غرامة تأخير DHA SN 03/2019 بنسبة 0.03% يومياً."
                else:
                    text = f"Late submission on claim {clm_id} ({delay} days elapsed, exceeding 14-day limit): triggers DHA SN 03/2019 statutory 0.03%/day late fee."
            else:
                if lang == "ar":
                    text = f"مخالفة دورة المطالبات: مطالبة eClaimLink رقم {clm_id} بقيمة {amount_aed} درهم تم تقديمها بعد تأخير {delay} يوماً. يتوجب تطبيق غرامة التأخير القانونية 0.03% يومياً حسب تعميم DHA SN 03/2019 بقيمة تقديرية {penalty_aed} درهم."
                else:
                    text = f"Claim Cycle Non-Compliance: eClaimLink submission {clm_id} (AED {amount_aed}) submitted with {delay} days delay. Incurs statutory 0.03%/day late submission penalty under DHA SN 03/2019 (§3.8.4), penalty exposure: AED {penalty_aed}."
            meta = {"claim_id": clm_id, "delay_days": delay, "penalty_aed": penalty_aed, "is_borderline": is_borderline}
            
        examples.append((text, opt, lang, meta))
    return examples

def generate_q7_examples(rnd: random.Random, n: int) -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Q7_PII_LEAK_RISK: 2 classes."""
    options = DECISION_QUESTIONS["Q7_PII_LEAK_RISK"]["options"]
    combos = [(opt, lang) for opt in options for lang in ["ar", "en"]]
    examples = []
    
    for i in range(n):
        opt, lang = combos[i % len(combos)]
        pat_code = f"DXB-ENC-{rnd.randint(1000, 9999)}"
        is_borderline = (i % 7 == 0)
        
        if opt == "PII_CLEAN":
            if is_borderline:
                if lang == "ar":
                    text = f"استشارة سريرية للمريض كود {pat_code} بإشراف د. مريم الفلاسي، تقرير دوائي خالي من الأسماء الشخصية أو أرقام الهوية للمريض."
                else:
                    text = f"Clinical consult for de-identified subject {pat_code} signed by Dr. Mariam Al-Falasi, zero patient identity tokens present."
            else:
                age = rnd.randint(25, 78)
                gender = rnd.choice(["male", "female"])
                gender_ar = "ذكر" if gender == "male" else "أنثى"
                if lang == "ar":
                    text = f"بيانات سريرية مشفرة ومجردة من الهوية للمريض كود [{pat_code}]، {gender_ar} {age} عاماً: مراجعة جرعة دواء السكري ميتفورمين وحساب تصفية الكرياتينين. لا توجد أي بيانات هوية شخصية أو أرقام وطنية."
                else:
                    text = f"De-identified clinical context for subject [{pat_code}], {gender} {age}yo: review Metformin dosage against creatinine clearance. Zero personally identifiable information (PII clean, compliant with DESC ISR v3.1)."
            meta = {"patient_code": pat_code, "has_pii": False, "is_borderline": is_borderline}
            
        else: # SENSITIVE_EMIRATES_ID_OR_NAME_DETECTED
            eid = _make_eid(rnd)
            name_en = rnd.choice(PATIENT_NAMES_EN)
            name_ar = rnd.choice(PATIENT_NAMES_AR)
            phone = f"+971-50-{rnd.randint(1000000, 9999999)}"
            if is_borderline:
                if lang == "ar":
                    text = f"مذكرة مريض: المراجع {name_ar} يحمل بطاقة هوية {eid}، طلب تجديد الأدوية."
                else:
                    text = f"Patient chart: Patient {name_en}, Emirates ID {eid}, prescription renewal request."
            else:
                if lang == "ar":
                    text = f"بيانات مريض شخصية: الاسم {name_ar}، رقم الهوية الإماراتية {eid}، هاتف {phone}، العنوان دبي ند الشبا. يرجى استخراج تقرير التاريخ المرضي الكامل."
                else:
                    text = f"Patient record contains sensitive PII: Name {name_en}, Emirates ID {eid}, Mobile {phone}, resident of Jumeirah 2 Dubai. Intercepted for privacy redaction under DESC ISR v3.1."
            meta = {"emirates_id": eid, "has_pii": True, "is_borderline": is_borderline}
            
        examples.append((text, opt, lang, meta))
    return examples

def generate_q8_examples(rnd: random.Random, n: int) -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Q8_CONTRADICTION_DETECTED: 2 classes."""
    options = DECISION_QUESTIONS["Q8_CONTRADICTION_DETECTED"]["options"]
    combos = [(opt, lang) for opt in options for lang in ["ar", "en"]]
    examples = []
    
    matches = [
        ("E11.9", "Type 2 diabetes without complications", "Metformin 850mg PO BID", "ميتفورمين 850 ملغ"),
        ("I10", "Essential hypertension", "Amlodipine 5mg PO daily", "أملوديبين 5 ملغ"),
        ("J45.909", "Unspecified asthma, uncomplicated", "Salbutamol 100mcg inhaler", "بخاخ سالبيوتامول"),
        ("M10.0", "Idiopathic gout", "Colchicine 500mcg PO", "كولشيسين 500 ميكروغرام")
    ]
    mismatches = [
        ("H66.0", "Acute suppurative otitis media", "Sildenafil 100mg PO TID", "سيلدينافيل 100 ملغ"),
        ("J02.9", "Acute pharyngitis", "Methotrexate 25mg PO daily", "ميثوتريكسات 25 ملغ"),
        ("K21.9", "Gastro-esophageal reflux disease", "Warfarin 10mg PO daily", "وارفارين 10 ملغ"),
        ("Z00.0", "General adult medical examination", "Chemotherapy Cisplatin 100mg IV", "سيسبلاتين كيماوي 100 ملغ")
    ]
    
    for i in range(n):
        opt, lang = combos[i % len(combos)]
        is_borderline = (i % 7 == 0)
        
        if opt == "CLINICAL_MATCH":
            icd, diag, rx_en, rx_ar = rnd.choice(matches)
            if is_borderline:
                if lang == "ar":
                    text = f"مراجعة علاجية: تشخيص {diag} وصرف {rx_ar}، استخدام علاجي سليم."
                else:
                    text = f"Therapeutic verification: Documented {diag} treated with {rx_en}, valid clinical match."
            else:
                if lang == "ar":
                    text = f"تدقيق التوافق السريري: التشخيص المسجل هو {diag} (رمز ICD-10: {icd})، والعلاج الموصوف هو {rx_ar}. تطابق علاجي سليم ومثبت سريرياً."
                else:
                    text = f"Clinical Indication Audit: Recorded diagnosis is {diag} (ICD-10: {icd}) with prescribed medication {rx_en}. Valid therapeutic indication and coherent clinical match."
            meta = {"icd10": icd, "match": True, "is_borderline": is_borderline}
            
        else: # INDICATION_DIAGNOSIS_MISMATCH
            icd, diag, rx_en, rx_ar = rnd.choice(mismatches)
            if is_borderline:
                if lang == "ar":
                    text = f"تناقض سريري: تشخيص {diag} بينما الدواء المصروف {rx_ar}، لا يوجد ارتباط طبي معتمد."
                else:
                    text = f"Clinical discrepancy: Diagnosis {diag} paired with unrelated medication {rx_en}, indication mismatch."
            else:
                if lang == "ar":
                    text = f"تعارض سريري خطير: التشخيص المسجل بالمطالبة {diag} (رمز ICD-10: {icd}) بينما الدواء الموصوف هو {rx_ar}. تناقض صارخ ولا توجد صلة علاجية مقبولة بين التشخيص وهذا الدواء."
                else:
                    text = f"Critical Indication Contradiction: Documented ICD-10 diagnosis is {diag} ({icd}) while prescribed therapy is {rx_en}. Severe indication-therapy mismatch; possible medical error or fraudulent claim."
            meta = {"icd10": icd, "match": False, "is_borderline": is_borderline}
            
        examples.append((text, opt, lang, meta))
    return examples

def generate_q9_examples(rnd: random.Random, n: int) -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Q9_HUMAN_OVERRIDE_REQUIRED: 2 classes."""
    options = DECISION_QUESTIONS["Q9_HUMAN_OVERRIDE_REQUIRED"]["options"]
    combos = [(opt, lang) for opt in options for lang in ["ar", "en"]]
    examples = []
    
    for i in range(n):
        opt, lang = combos[i % len(combos)]
        is_borderline = (i % 7 == 0)
        
        if opt == "AUTOMATED_CLEARANCE":
            if is_borderline:
                if lang == "ar":
                    text = "وصفة روتينية سليمة، فحوصات طبيعية، مصرح بالإفراج الآلي المباشر."
                else:
                    text = "Clean routine prescription order, normal labs, cleared for automated dispensing."
            else:
                if lang == "ar":
                    text = "وصفة طبية روتينية كاملة ومستوفية للشروط: جرعات قياسية، فحوصات وظائف كبد وكلى طبيعية، لا توجد تداخلات دوائية، والمريض لا يتناول أي أدوية مراقبة. مصرح بالصرف والاعتماد الآلي الفوري."
                else:
                    text = "Fully compliant routine refill: Standard adult dosing, uncompromised renal panel, zero adverse drug-drug interactions, non-controlled drug. Cleared for autonomous end-to-end dispensing."
            meta = {"clearance": "AUTOMATED", "is_borderline": is_borderline}
            
        else: # MANDATORY_PHYSICIAN_OVERRIDE
            if is_borderline:
                if lang == "ar":
                    text = "اكتشاف تداخل دوائي حرج مع هبوط ترشيح كلوي، يتطلب تجاوزاً واعتماداً كتابياً من الطبيب."
                else:
                    text = "Critical drug interaction in renal impairment detected, physician sign-off override required."
            else:
                risk_desc = "تداخل دوائي قاتل بين كولشيسين وكلاريثروميسين مع قصور كلوي حاد"
                risk_desc_en = "Fatal CYP3A4 interaction between Colchicine and Clarithromycin in CKD Stage 4"
                if lang == "ar":
                    text = f"إيقاف حظر أمان فوري: تم اكتشاف {risk_desc}. يُحظر الصرف الآلي نهائياً، ويلزم تجاوز خطي رسمي مع تعليل طبي موثق من الطبيب المعالج المشرف."
                else:
                    text = f"Critical Safety Gate Halt: Detected {risk_desc_en}. Automated execution rejected; mandatory attending physician override with formal clinical rationale required."
            meta = {"clearance": "BLOCKED", "is_borderline": is_borderline}
            
        examples.append((text, opt, lang, meta))
    return examples

def generate_q10_examples(rnd: random.Random, n: int) -> List[Tuple[str, str, str, Dict[str, Any]]]:
    """Q10_AIR_GAP_FALLBACK: 2 classes."""
    options = DECISION_QUESTIONS["Q10_AIR_GAP_FALLBACK"]["options"]
    combos = [(opt, lang) for opt in options for lang in ["ar", "en"]]
    examples = []
    
    for i in range(n):
        opt, lang = combos[i % len(combos)]
        is_borderline = (i % 7 == 0)
        
        if opt == "SOVEREIGN_ON_DEVICE":
            if is_borderline:
                if lang == "ar":
                    text = "معالجة ملفات مراجعين محلية حساسة، الالتزام بالعزل المحلي دون إرسال بيانات خارجية."
                else:
                    text = "Local processing of sensitive patient clinic charts, execute strictly on-device without cloud exfiltration."
            else:
                if lang == "ar":
                    text = "معالجة بيانات طبية وسجلات مواطنين سرية تابعة لهيئة الصحة بدبي: يجب الإبقاء على المعالجة محلياً 100% داخل البيئة السيادية المعزولة على الجهاز دون أي اتصال بالإنترنت امتثالاً لضوابط DESC ISR v3.1."
                else:
                    text = "Sovereign on-device processing mandate: Handling sensitive Dubai citizen electronic health records. Must execute strictly within local air-gapped Minisforum UM790 hardware enclave per DESC ISR v3.1 sovereignty rules."
            meta = {"enclave": "LOCAL_AIR_GAP", "is_borderline": is_borderline}
            
        else: # CLOUD_ESCALATION_PERMITTED
            if is_borderline:
                if lang == "ar":
                    text = "استشارة طبية نادرة منزوعة البيانات الشخصية، يسمح بطلب رأي خارجي سحابي بموافقة الصيدلي."
                else:
                    text = "De-identified complex research query, secondary cloud reference lookup permitted with pharmacist sign-off."
            else:
                if lang == "ar":
                    text = "استشارة طبية نادرة مجردة تماماً من الهوية حول أبحاث دوائية عالمية حديثة: بموافقة الصيدلي السريري، يسمح بالاستعانة بالمعالجة السحابية الموسعة للوصول إلى أحدث أوراق الأبحاث الدولية."
                else:
                    text = "Cloud escalation permitted: Anonymized complex pharmacogenomic query with verified clinician opt-in for secondary external consensus and international medical literature lookup."
            meta = {"enclave": "HYBRID_ESCALATION", "is_borderline": is_borderline}
            
        examples.append((text, opt, lang, meta))
    return examples

QUESTION_GENERATORS = {
    "Q1_INTENT_ROUTING": generate_q1_examples,
    "Q2_CLINICAL_URGENCY": generate_q2_examples,
    "Q3_RENAL_RISK_SUSPECT": generate_q3_examples,
    "Q4_CYP3A4_INTERACTION_RISK": generate_q4_examples,
    "Q5_CONTROLLED_SUBSTANCE_CHECK": generate_q5_examples,
    "Q6_CLAIM_DELAY_PENALTY_RISK": generate_q6_examples,
    "Q7_PII_LEAK_RISK": generate_q7_examples,
    "Q8_CONTRADICTION_DETECTED": generate_q8_examples,
    "Q9_HUMAN_OVERRIDE_REQUIRED": generate_q9_examples,
    "Q10_AIR_GAP_FALLBACK": generate_q10_examples,
}

# -----------------------------------------------------------------------------
# 4. DATASET GENERATION ORCHESTRATION WITH PATIENT-LEVEL STRATIFICATION
# -----------------------------------------------------------------------------

def generate_laya_dataset(
    output_dir: str,
    total_patients: int = 400,
    examples_per_question: int = 240,
    seed: int = 20261024
) -> Dict[str, Any]:
    """
    Generates 2,400 examples partitioned across 400 patients with strict
    train (70%), dev (15%), test (15%) patient-level split (zero leakage).
    Every patient receives exactly 6 clinical encounters across splits.
    """
    rnd = random.Random(seed)
    os.makedirs(output_dir, exist_ok=True)
    
    patient_ids = [f"DXB-PAT-{i:04d}" for i in range(1, total_patients + 1)]
    
    n_train_pat = int(total_patients * 0.70)  # 280
    n_dev_pat = int(total_patients * 0.15)    # 60
    n_test_pat = total_patients - n_train_pat - n_dev_pat  # 60
    
    train_patients = set(patient_ids[:n_train_pat])
    dev_patients = set(patient_ids[n_train_pat:n_train_pat + n_dev_pat])
    test_patients = set(patient_ids[n_train_pat + n_dev_pat:])
    
    # Zero patient overlap verification
    assert len(train_patients & dev_patients) == 0, "Patient leakage between train and dev!"
    assert len(train_patients & test_patients) == 0, "Patient leakage between train and test!"
    assert len(dev_patients & test_patients) == 0, "Patient leakage between dev and test!"
    
    print(f"[*] Patient Partition: {len(train_patients)} Train, {len(dev_patients)} Dev, {len(test_patients)} Test (Zero Leakage)")
    
    train_per_q = int(examples_per_question * 0.70)  # 168
    dev_per_q = int(examples_per_question * 0.15)    # 36
    test_per_q = examples_per_question - train_per_q - dev_per_q  # 36
    
    train_pat_list = sorted(list(train_patients))
    dev_pat_list = sorted(list(dev_patients))
    test_pat_list = sorted(list(test_patients))
    
    train_examples: List[Dict[str, Any]] = []
    dev_examples: List[Dict[str, Any]] = []
    test_examples: List[Dict[str, Any]] = []
    
    global_counter = 1
    question_stats = {}
    
    # Continuous cursors to cycle across ALL patients across questions
    train_cursor = 0
    dev_cursor = 0
    test_cursor = 0
    
    for q_id, q_info in DECISION_QUESTIONS.items():
        generator_fn = QUESTION_GENERATORS[q_id]
        raw_items = generator_fn(rnd, examples_per_question)
        
        ar_items = [it for it in raw_items if it[2] == "ar"]
        en_items = [it for it in raw_items if it[2] == "en"]
        
        train_ar = ar_items[:train_per_q // 2]
        train_en = en_items[:train_per_q // 2]
        dev_ar = ar_items[train_per_q // 2 : train_per_q // 2 + dev_per_q // 2]
        dev_en = en_items[train_per_q // 2 : train_per_q // 2 + dev_per_q // 2]
        test_ar = ar_items[train_per_q // 2 + dev_per_q // 2 :]
        test_en = en_items[train_per_q // 2 + dev_per_q // 2 :]
        
        train_batch = train_ar + train_en
        dev_batch = dev_ar + dev_en
        test_batch = test_ar + test_en
        
        rnd.shuffle(train_batch)
        rnd.shuffle(dev_batch)
        rnd.shuffle(test_batch)
        
        q_stats = {"total": 0, "ar": 0, "en": 0, "options": {opt: 0 for opt in q_info["options"]}}
        
        # Process train batch
        for text, label, lang, meta in train_batch:
            assigned_patient = train_pat_list[train_cursor % len(train_pat_list)]
            train_cursor += 1
            ex_id = f"LAYA-{global_counter:05d}"
            global_counter += 1
            record = {
                "id": ex_id,
                "patient_id": assigned_patient,
                "question_id": q_id,
                "question_title": q_info["title"],
                "language": lang,
                "prompt": text,
                "options": q_info["options"],
                "gold_label": label,
                "split": "train",
                "clinical_metadata": meta
            }
            train_examples.append(record)
            q_stats["total"] += 1
            q_stats[lang] += 1
            q_stats["options"][label] = q_stats["options"].get(label, 0) + 1
            
        # Process dev batch
        for text, label, lang, meta in dev_batch:
            assigned_patient = dev_pat_list[dev_cursor % len(dev_pat_list)]
            dev_cursor += 1
            ex_id = f"LAYA-{global_counter:05d}"
            global_counter += 1
            record = {
                "id": ex_id,
                "patient_id": assigned_patient,
                "question_id": q_id,
                "question_title": q_info["title"],
                "language": lang,
                "prompt": text,
                "options": q_info["options"],
                "gold_label": label,
                "split": "dev",
                "clinical_metadata": meta
            }
            dev_examples.append(record)
            q_stats["total"] += 1
            q_stats[lang] += 1
            q_stats["options"][label] = q_stats["options"].get(label, 0) + 1
            
        # Process test batch
        for text, label, lang, meta in test_batch:
            assigned_patient = test_pat_list[test_cursor % len(test_pat_list)]
            test_cursor += 1
            ex_id = f"LAYA-{global_counter:05d}"
            global_counter += 1
            record = {
                "id": ex_id,
                "patient_id": assigned_patient,
                "question_id": q_id,
                "question_title": q_info["title"],
                "language": lang,
                "prompt": text,
                "options": q_info["options"],
                "gold_label": label,
                "split": "test",
                "clinical_metadata": meta
            }
            test_examples.append(record)
            q_stats["total"] += 1
            q_stats[lang] += 1
            q_stats["options"][label] = q_stats["options"].get(label, 0) + 1
            
        question_stats[q_id] = q_stats

    splits = [
        ("train.jsonl", train_examples),
        ("dev.jsonl", dev_examples),
        ("test.jsonl", test_examples)
    ]
    
    for filename, data in splits:
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"[*] Wrote {len(data)} examples to {filepath}")
        
    summary = {
        "dataset_name": "Laya Sovereign Bilingual Triage Dataset 2026",
        "generated_at": datetime.now().isoformat(),
        "total_examples": len(train_examples) + len(dev_examples) + len(test_examples),
        "split_counts": {
            "train": len(train_examples),
            "dev": len(dev_examples),
            "test": len(test_examples)
        },
        "patient_cohort": {
            "total_patients": total_patients,
            "train_patients": len(train_patients),
            "dev_patients": len(dev_patients),
            "test_patients": len(test_patients),
            "patient_overlap": 0
        },
        "language_distribution": {
            "ar": sum(q["ar"] for q in question_stats.values()),
            "en": sum(q["en"] for q in question_stats.values())
        },
        "questions_summary": question_stats
    }
    
    summary_path = os.path.join(output_dir, "dataset_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[*] Saved dataset summary to {summary_path}")
    
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Laya Multilingual Sovereign Triage Dataset")
    parser.add_argument("--output-dir", type=str, default="benchmarks/laya_dataset")
    parser.add_argument("--patients", type=int, default=400)
    parser.add_argument("--per-question", type=int, default=240)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    
    summary = generate_laya_dataset(
        output_dir=args.output_dir,
        total_patients=args.patients,
        examples_per_question=args.per_question,
        seed=args.seed
    )
    print(f"[SUCCESS] Generated {summary['total_examples']} sovereign triage examples across {summary['patient_cohort']['total_patients']} patients.")
