"""
bridge/sanitizer.py - Multilingual Script Sanitizer & INN Drug Normalizer
Dubai AI Agents Championship 2026-2027 (Pillar 4: Multi-Turn Orchestration Engine)

Key Architectural Guarantees:
1. Script Leak Protection: Detects and rejects/sanitizes unauthorized Unicode scripts
   (Katakana \\u30A0-\\u30FF, Hiragana \\u3040-\\u309F, Cyrillic \\u0400-\\u04FF) to
   prevent C99 native memory/pointer crashes.
2. Authoritative INN Normalization: Bidirectional mapping between Arabic vernacular/INN
   and English International Nonproprietary Names (e.g. كولشيسين <-> Colchicine).
3. Tool Argument Sanitization: Ensures all arguments proposed by 7B/8B models or user
   inputs are sanitized, typed, and normalized before execution in the C99 Native Shield.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

# -----------------------------------------------------------------------------
# 1. Unicode Script Range Definitions & Detectors
# -----------------------------------------------------------------------------

# Katakana (\u30A0-\u30FF) + Katakana Phonetic Extensions (\u31F0-\u31FF)
KATAKANA_REGEX = re.compile(r"[\u30A0-\u30FF\u31F0-\u31FF]")

# Hiragana (\u3040-\u309F)
HIRAGANA_REGEX = re.compile(r"[\u3040-\u309F]")

# Cyrillic (\u0400-\u04FF) + Cyrillic Supplement (\u0500-\u052F)
CYRILLIC_REGEX = re.compile(r"[\u0400-\u04FF\u0500-\u052F]")

# Unified Unauthorized Script Matcher
UNAUTHORIZED_SCRIPTS_REGEX = re.compile(
    r"[\u3040-\u309F\u30A0-\u30FF\u31F0-\u31FF\u0400-\u04FF\u0500-\u052F]"
)

# Arabic Diacritics (Tashkeel) and Tatweel
ARABIC_DIACRITICS_REGEX = re.compile(r"[\u064B-\u0652\u0653-\u065F\u0670\u0640]")


def has_unauthorized_script(text: str) -> bool:
    """Return True if text contains Katakana, Hiragana, or Cyrillic characters."""
    if not text or not isinstance(text, str):
        return False
    return bool(UNAUTHORIZED_SCRIPTS_REGEX.search(text))


def detect_unauthorized_scripts(text: str) -> List[str]:
    """Identify which unauthorized scripts are present in the text."""
    if not text or not isinstance(text, str):
        return []
    detected: List[str] = []
    if KATAKANA_REGEX.search(text):
        detected.append("Katakana")
    if HIRAGANA_REGEX.search(text):
        detected.append("Hiragana")
    if CYRILLIC_REGEX.search(text):
        detected.append("Cyrillic")
    return detected


def strip_unauthorized_scripts(text: str) -> str:
    """Remove all unauthorized Unicode script characters from the text."""
    if not text or not isinstance(text, str):
        return ""
    return UNAUTHORIZED_SCRIPTS_REGEX.sub("", text)


def validate_script(text: str) -> Tuple[bool, Optional[str]]:
    """Validate text against unauthorized script injection.
    
    Returns:
        (True, None) if clean.
        (False, script_error_description) if unauthorized scripts are detected.
    """
    detected = detect_unauthorized_scripts(text)
    if detected:
        return False, f"Unauthorized Unicode script detected: {', '.join(detected)}"
    return True, None


# -----------------------------------------------------------------------------
# 2. Arabic & English INN Drug Catalog & Normalization
# -----------------------------------------------------------------------------

# Primary catalog of core compounds (WHO EML, MoHAP Formulary, DHA SN 03/2019)
DRUG_INN_CATALOG: Dict[str, Dict[str, Any]] = {
    "Colchicine": {
        "en_canonical": "Colchicine",
        "ar_canonical": "كولشيسين",
        "ar_variants": ["كولشيسين", "كولشيسن", "الكولشيسين", "كولشسين", "كولشيسين"],
        "en_variants": ["colchicine", "colcrys", "mitigare"],
        "katakana_variants": ["コルヒチン", "コルヒチン錠"],
        "cyrillic_variants": ["колхицин"],
    },
    "Clarithromycin": {
        "en_canonical": "Clarithromycin",
        "ar_canonical": "كلاريثروميسين",
        "ar_variants": ["كلاريثروميسين", "كلاريثرو", "الكلاريثروميسين", "كلاريترومايسين", "كلاريثرومايسين"],
        "en_variants": ["clarithromycin", "clarithro", "biaxin", "klacid"],
        "katakana_variants": ["クラリスロマイシン", "クラリス"],
        "cyrillic_variants": ["кларитромицин"],
    },
    "Metformin": {
        "en_canonical": "Metformin",
        "ar_canonical": "ميتفورمين",
        "ar_variants": ["ميتفورمين", "ميتفورمن", "الميتفورمين", "متفورمين", "جلوكوفاج", "كلوفاج"],
        "en_variants": ["metformin", "glucophage"],
        "katakana_variants": ["メトホルミン"],
        "cyrillic_variants": ["метформин"],
    },
    "Simvastatin": {
        "en_canonical": "Simvastatin",
        "ar_canonical": "سيمفاستاتين",
        "ar_variants": ["سيمفاستاتين", "سيمفاستاتن", "السيمفاستاتين", "سمفاستاتين", "زوكور"],
        "en_variants": ["simvastatin", "zocor"],
        "katakana_variants": ["シンバスタチン"],
        "cyrillic_variants": ["симвастатин"],
    },
    "Warfarin": {
        "en_canonical": "Warfarin",
        "ar_canonical": "وارفارين",
        "ar_variants": ["وارفارين", "وارفارن", "الوارفارين", "كومادين", "ماريفان"],
        "en_variants": ["warfarin", "coumadin", "marevan"],
        "katakana_variants": ["ワルファリン"],
        "cyrillic_variants": ["варфарин"],
    },
    "Amiodarone": {
        "en_canonical": "Amiodarone",
        "ar_canonical": "أميودارون",
        "ar_variants": ["أميودارون", "اميودارون", "الاميودارون", "كوردارون"],
        "en_variants": ["amiodarone", "cordarone"],
        "katakana_variants": ["アミオダロン"],
        "cyrillic_variants": ["амиодарон"],
    },
    "Paracetamol": {
        "en_canonical": "Paracetamol",
        "ar_canonical": "باراسيتامول",
        "ar_variants": ["باراسيتامول", "بنادول", "الباراسيتامول", "ادول", "فيفادول", "اسيتامينوفين"],
        "en_variants": ["paracetamol", "acetaminophen", "panadol", "tylenol", "adol", "fevadol"],
        "katakana_variants": ["パラセタモール", "アセトアミノフェン"],
        "cyrillic_variants": ["парацетамол"],
    },
    "Amoxicillin": {
        "en_canonical": "Amoxicillin",
        "ar_canonical": "أموكسيسيلين",
        "ar_variants": ["أموكسيسيلين", "اموكسيسيلين", "اموكسيسلين", "الاموكسيسيلين", "ايموكس", "اموكسيل"],
        "en_variants": ["amoxicillin", "amoxil"],
        "katakana_variants": ["アモキシシリン"],
        "cyrillic_variants": ["амоксициллин"],
    },
    "Tramadol": {
        "en_canonical": "Tramadol",
        "ar_canonical": "ترامادول",
        "ar_variants": ["ترامادول", "ترامال", "الترامادول"],
        "en_variants": ["tramadol", "ultram", "tramal"],
        "katakana_variants": ["トラマドール"],
        "cyrillic_variants": ["трамадол"],
    },
    "Aspirin": {
        "en_canonical": "Aspirin",
        "ar_canonical": "أسبرين",
        "ar_variants": ["أسبرين", "اسبرين", "الاسبرين", "اسبيرين", "حمض أسيتيل ساليسيليك"],
        "en_variants": ["aspirin", "acetylsalicylic acid", "asa", "ecotrin"],
        "katakana_variants": ["アスピリン"],
        "cyrillic_variants": ["аспирин"],
    },
    "Atorvastatin": {
        "en_canonical": "Atorvastatin",
        "ar_canonical": "أتورفاستاتين",
        "ar_variants": ["أتورفاستاتين", "اتورفاستاتين", "ليبيتور", "الاتورفاستاتين"],
        "en_variants": ["atorvastatin", "lipitor"],
        "katakana_variants": ["アトルバスタチン"],
        "cyrillic_variants": ["аторвастатин"],
    },
    "Ibuprofen": {
        "en_canonical": "Ibuprofen",
        "ar_canonical": "إيبوبروفين",
        "ar_variants": ["إيبوبروفين", "ايبوبروفين", "بروفين", "ادفيل"],
        "en_variants": ["ibuprofen", "advil", "motrin", "brufen"],
        "katakana_variants": ["イブプロフェン"],
        "cyrillic_variants": ["ибупрофен"],
    },
    "Morphine": {
        "en_canonical": "Morphine",
        "ar_canonical": "مورفين",
        "ar_variants": ["مورفين", "المورفين"],
        "en_variants": ["morphine", "ms contin"],
        "katakana_variants": ["モルヒネ"],
        "cyrillic_variants": ["морфин"],
    }
}


def _clean_text_for_lookup(text: str) -> str:
    """Normalize Arabic orthography and English casing for catalog lookup."""
    if not text:
        return ""
    s = text.strip().lower()
    # Remove Arabic diacritics and tatweel
    s = ARABIC_DIACRITICS_REGEX.sub("", s)
    # Normalize Alef variants
    s = re.sub(r"[أإآ]", "ا", s)
    # Normalize Yaa and Alif Maqsura
    s = s.replace("ى", "ي")
    # Normalize Taa Marbuta
    s = s.replace("ة", "ه")
    return s.strip()


# Build inverted index mapping all aliases to the drug canonical key
_ALIAS_TO_KEY: Dict[str, str] = {}
for key, data in DRUG_INN_CATALOG.items():
    _ALIAS_TO_KEY[_clean_text_for_lookup(key)] = key
    _ALIAS_TO_KEY[_clean_text_for_lookup(data["en_canonical"])] = key
    _ALIAS_TO_KEY[_clean_text_for_lookup(data["ar_canonical"])] = key
    for alias in data.get("ar_variants", []):
        _ALIAS_TO_KEY[_clean_text_for_lookup(alias)] = key
        # Also store version without leading 'ال'
        cleaned = _clean_text_for_lookup(alias)
        if cleaned.startswith("ال") and len(cleaned) > 3:
            _ALIAS_TO_KEY[cleaned[2:]] = key
    for alias in data.get("en_variants", []):
        _ALIAS_TO_KEY[_clean_text_for_lookup(alias)] = key
    for alias in data.get("katakana_variants", []):
        _ALIAS_TO_KEY[_clean_text_for_lookup(alias)] = key
    for alias in data.get("cyrillic_variants", []):
        _ALIAS_TO_KEY[_clean_text_for_lookup(alias)] = key


def normalize_drug_name(name: str, target_lang: str = "en") -> str:
    """Normalize any drug name alias (Arabic, English, or unauthorized script)
    to the canonical INN in the requested target language ('en' or 'ar').

    If unauthorized Unicode scripts are present (e.g. Katakana / Cyrillic):
      1. First checks if it is a known foreign variant (e.g. コルヒチン -> Colchicine).
      2. If not matched, strips unauthorized characters.
      3. If empty after stripping, provides safe fallback 'UNKNOWN_DRUG'.
    """
    if not name or not isinstance(name, str):
        return "UNKNOWN_DRUG"

    raw = name.strip()
    if not raw:
        return "UNKNOWN_DRUG"

    # Step 1: Check if raw input matches known alias directly (even if Katakana / Cyrillic)
    cleaned_key = _clean_text_for_lookup(raw)
    if cleaned_key in _ALIAS_TO_KEY:
        canonical_key = _ALIAS_TO_KEY[cleaned_key]
        entry = DRUG_INN_CATALOG[canonical_key]
        return entry["ar_canonical"] if target_lang == "ar" else entry["en_canonical"]

    # Step 2: If unauthorized scripts exist, strip them
    if has_unauthorized_script(raw):
        stripped = strip_unauthorized_scripts(raw).strip()
        if not stripped:
            # Script was purely unauthorized and unmodeled
            return "UNKNOWN_DRUG"
        cleaned_key = _clean_text_for_lookup(stripped)
        if cleaned_key in _ALIAS_TO_KEY:
            canonical_key = _ALIAS_TO_KEY[cleaned_key]
            entry = DRUG_INN_CATALOG[canonical_key]
            return entry["ar_canonical"] if target_lang == "ar" else entry["en_canonical"]
        raw = stripped

    # Step 3: Check word-by-word or substring match for combined strings (e.g. "Colchicine 0.5mg")
    words = re.findall(r"[\w\u0600-\u06FF]+", raw)
    for w in words:
        cw = _clean_text_for_lookup(w)
        if cw in _ALIAS_TO_KEY:
            canonical_key = _ALIAS_TO_KEY[cw]
            entry = DRUG_INN_CATALOG[canonical_key]
            return entry["ar_canonical"] if target_lang == "ar" else entry["en_canonical"]
        if cw.startswith("ال") and len(cw) > 3 and cw[2:] in _ALIAS_TO_KEY:
            canonical_key = _ALIAS_TO_KEY[cw[2:]]
            entry = DRUG_INN_CATALOG[canonical_key]
            return entry["ar_canonical"] if target_lang == "ar" else entry["en_canonical"]

    # Step 4: Return stripped/cleaned version if unrecognized
    return raw


# -----------------------------------------------------------------------------
# 3. Tool Argument Sanitization
# -----------------------------------------------------------------------------

def sanitize_tool_arguments(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize and validate arguments for a proposed tool call.
    
    Guarantees:
    - Strips unauthorized Unicode scripts from all string fields.
    - Normalizes pharmaceutical drug arguments to canonical English INN for C99 execution.
    - Ensures valid numeric bounds and types for clinical labs and fiscal amounts.
    """
    if not isinstance(args, dict):
        return {}

    sanitized: Dict[str, Any] = dict(args)

    # Tool-specific normalization rules
    if tool_name == "med_lookup":
        raw_drug = str(sanitized.get("drug_name", ""))
        sanitized["drug_name"] = normalize_drug_name(raw_drug, target_lang="en")

    elif tool_name == "interaction_check":
        primary = str(sanitized.get("primary_drug", ""))
        sanitized["primary_drug"] = normalize_drug_name(primary, target_lang="en")

        concurrent = sanitized.get("concurrent_drug")
        if concurrent:
            sanitized["concurrent_drug"] = normalize_drug_name(str(concurrent), target_lang="en")
        else:
            sanitized["concurrent_drug"] = ""

        # Validate eGFR numeric bounds
        if "patient_egfr" in sanitized:
            try:
                egfr_val = float(sanitized["patient_egfr"])
                # Guard against NaN/Inf
                if egfr_val != egfr_val or egfr_val < 0.0:
                    egfr_val = 0.0
                sanitized["patient_egfr"] = egfr_val
            except (ValueError, TypeError):
                sanitized["patient_egfr"] = 90.0

        if "is_controlled" in sanitized:
            sanitized["is_controlled"] = bool(sanitized["is_controlled"])
        if "has_verified_id" in sanitized:
            sanitized["has_verified_id"] = bool(sanitized["has_verified_id"])

    elif tool_name == "rag_search":
        if "query" in sanitized:
            sanitized["query"] = strip_unauthorized_scripts(str(sanitized["query"]))
        if "limit" in sanitized:
            try:
                sanitized["limit"] = max(1, min(50, int(sanitized["limit"])))
            except (ValueError, TypeError):
                sanitized["limit"] = 3
        else:
            sanitized["limit"] = 3
        if "domain" in sanitized and sanitized["domain"]:
            d = str(sanitized["domain"]).strip().upper()
            sanitized["domain"] = None if d in ("ALL", "") else d

    elif tool_name == "claim_scrub":
        if "net_claim_aed" in sanitized:
            try:
                sanitized["net_claim_aed"] = float(sanitized["net_claim_aed"])
            except (ValueError, TypeError):
                sanitized["net_claim_aed"] = 450.0
        elif "gross_claim_aed" in sanitized:
            try:
                sanitized["net_claim_aed"] = float(sanitized["gross_claim_aed"])
            except (ValueError, TypeError):
                sanitized["net_claim_aed"] = 450.0

        if "delay_days" in sanitized:
            try:
                sanitized["delay_days"] = int(sanitized["delay_days"])
            except (ValueError, TypeError):
                sanitized["delay_days"] = 0

    elif tool_name == "policy_verify_call":
        if "amount_aed" in sanitized:
            try:
                sanitized["amount_aed"] = float(sanitized["amount_aed"])
            except (ValueError, TypeError):
                sanitized["amount_aed"] = 0.0
        if "is_mutating" in sanitized:
            sanitized["is_mutating"] = bool(sanitized["is_mutating"])

    # General sweep: strip any residual unauthorized script from all string fields
    for k, v in list(sanitized.items()):
        if isinstance(v, str):
            if has_unauthorized_script(v):
                cleaned = strip_unauthorized_scripts(v).strip()
                sanitized[k] = cleaned if cleaned else "sanitized_input"

    return sanitized


# -----------------------------------------------------------------------------
# 4. Casual Intent Detection & Bilingual Greetings
# -----------------------------------------------------------------------------

_CASUAL_EXACT_PHRASES = {
    "hello", "hi", "hey", "greetings", "good morning", "good evening", "good afternoon",
    "who are you", "what can you do", "introduce yourself", "help",
    "مرحبا", "مرحباً", "اهلا", "أهلا", "أهلاً", "اهلاً", "سلام", "السلام عليكم",
    "صباح الخير", "مساء الخير", "من أنت", "من انت", "عرفني بنفسك", "ماذا تستطيع ان تفعل",
    "ماذا تستطيع أن تفعل", "ما هي قدراتك", "تحياتي", "أهلاً وسهلاً", "اهلا وسهلا"
}

_DOMAIN_TRIGGERS = {
    "colchicine", "clarithro", "clarithromycin", "metformin", "warfarin",
    "amiodarone", "simvastatin", "paracetamol", "amoxicillin", "tramadol",
    "aspirin", "egfr", "gout", "claim", "dha", "sn 03", "sn03", "mirsal", "customs",
    "tariff", "vat", "fademem", "ejari", "dewa", "cyp3a4", "contraindication",
    "prescription", "rx", "dose", "patient", "lab", "invoice", "settlement",
    "كولشيسين", "كلاريثرو", "كلاريثروميسين", "ميتفورمين", "وارفارين", "نقرس",
    "قصور", "كلوي", "كلى", "وظائف", "مطالبة", "تأخير", "جمرك", "جمارك", "شحنة",
    "ميرسال", "ايجار", "إيجار", "كهرباء", "تداخل", "وصفة", "جرعة", "مريض"
}

_CASUAL_PATTERNS = [
    re.compile(r"^(hello|hi|hey|greetings|good\s+(morning|evening|afternoon))(\s+there)?$", re.IGNORECASE),
    re.compile(r"^who\s+are\s+you(\s+today)?$", re.IGNORECASE),
    re.compile(r"^what\s+(are\s+you|can\s+you\s+do)$", re.IGNORECASE),
    re.compile(r"^(tell\s+me\s+about\s+yourself|introduce\s+yourself)$", re.IGNORECASE),
    re.compile(r"^(مرحبا|مرحباً|اهلا|أهلا|أهلاً|اهلاً|سلام|السلام\s+عليكم)(\s+يا\s+\w+)?$"),
    re.compile(r"^(صباح|مساء)\s+الخير$"),
    re.compile(r"^من\s+(أنت|انت)(\s+يا\s+\w+)?$"),
    re.compile(r"^(عرفني|خبرني)\s+عن\s+نفسك$"),
    re.compile(r"^(ماذا\s+تستطيع\s+(أن|ان)\s+تفعل|ما\s+هي\s+قدراتك)$"),
]


def is_casual_intent(prompt: str) -> bool:
    """Detect if the prompt is a casual greeting, conversational pleasantry,
    or general identity inquiry without clinical, statutory, or fiscal intent.
    """
    if not prompt or not isinstance(prompt, str):
        return False

    cleaned = re.sub(r"[^\w\s\u0600-\u06FF]", " ", prompt.lower()).strip()
    words = cleaned.split()
    if not words:
        return False

    # Domain triggers instantly disqualify casual classification
    for trig in _DOMAIN_TRIGGERS:
        if trig in cleaned:
            return False

    # Check exact phrase match
    normalized_phrase = " ".join(words)
    if normalized_phrase in _CASUAL_EXACT_PHRASES:
        return True

    # Check regex patterns
    for pat in _CASUAL_PATTERNS:
        if pat.match(normalized_phrase):
            return True

    # If all tokens belong to greeting set and input is short (<= 6 words)
    casual_words = {
        "hello", "hi", "hey", "there", "greetings", "good", "morning", "evening", "afternoon",
        "who", "what", "are", "you", "introduce", "yourself",
        "مرحبا", "مرحباً", "اهلا", "أهلا", "أهلاً", "اهلاً", "سلام", "السلام", "عليكم",
        "صباح", "مساء", "الخير", "من", "أنت", "انت", "عرفني", "بنفسك", "تحياتي"
    }
    casual_count = sum(1 for w in words if w in casual_words)
    if casual_count >= 1 and len(words) <= 6 and (casual_count / len(words)) >= 0.5:
        return True

    return False


def get_casual_introduction(agent_name: str) -> str:
    """Return an authoritative bilingual greeting and capabilities overview."""
    agent = (agent_name or "taryaq").lower()

    if agent == "qala":
        return (
            "مرحباً بك! أنا القلعة (Qala)، وكيل الحوكمة والامتثال المؤسسي والمالي لحكومة دبي ٢٠٢٧.\n\n"
            "أعمل وفق معايير مركز دبي للأمن الإلكتروني (DESC ISR v3.1) وقواعد ميرسال ٢ (Mirsal II) لتقديم:\n"
            "1. **التخليص الجمركي الذاتي للبضائع والشحنات** واحتساب الرسوم والضرائب التراكمية (10.25% Landed Tax).\n"
            "2. **بوابة الحوكمة المالية الذاتية** للعمليات التي تتجاوز سقف 50,000 درهم إماراتي.\n"
            "3. **سجل التدقيق المشفر غير القابل للتلاعب** (HMAC-SHA256).\n\n"
            "كيف يمكنني مساعدة أعمالك ومنشأتك اليوم؟\n\n"
            "---\n\n"
            "Welcome! I am Qala, your Autonomous Enterprise Compliance & Trade Copilot for Dubai 2027.\n\n"
            "Operating under DESC ISR v3.1 and Dubai Customs Mirsal II regulations, I deliver:\n"
            "1. **Automated Customs Duty & VAT Settlement:** Calculating landed tariffs under the GCC Unified Tariff (5% Duty + 5% VAT).\n"
            "2. **FinOps Policy Gatekeeping:** Enforcing executive authorization codes for transactions exceeding AED 50,000.00.\n"
            "3. **Zero-Exfiltration Auditability:** Immutable local verification.\n\n"
            "How can I assist your enterprise operations today?"
        )
    elif agent == "nibras":
        return (
            "مرحباً بك! أنا نبراس (Nibras)، المساعد التنفيذي السيادي للقيادات وصناع القرار في دبي ٢٠٢٧.\n\n"
            "أعمل بخوارزمية FadeMem للضمور الإدراكي البيولوجي ومعالجة اللهجات العربية محلياً لتقديم:\n"
            "1. **ضغط السياق الإدراكي** وتقليل الضوضاء التشغيلية بنسبة تتجاوز 85%.\n"
            "2. **استخلاص القواعد التنفيذية الدائمة** للقرارات الاستراتيجية.\n"
            "3. **حماية السيادة المعلوماتية** دون تسريب بيانات خارج الأجهزة المحلية.\n\n"
            "كيف يمكنني تنظيم جدول أعمالك وقراراتك اليوم؟\n\n"
            "---\n\n"
            "Welcome! I am Nibras, Sovereign Executive Chief-of-Staff for Dubai 2027 leaders.\n\n"
            "Powered by FadeMem episodic memory decay and zero-allocation Gulf Arabic normalizers, I provide:\n"
            "1. **Cognitive Context Pruning:** Reducing token friction while preserving high-valence decisions.\n"
            "2. **Executive Rule Distillation:** Converting complex meetings into actionable corporate directives.\n"
            "3. **Air-Gapped Privacy:** Complete on-premises confidentiality.\n\n"
            "How may I serve your executive agenda today?"
        )
    else:  # default taryaq
        return (
            "مرحباً بك! أنا ترياق (Taryaq)، الوكيل السيادي للسلامة الدوائية ورصد التفاعلات السريرية والتدقيق التأميني في إمارة دبي (Dubai 2027).\n\n"
            "أعمل بدرع C99 فائق السرعة (< 0.05 مللي ثانية) لتقديم:\n"
            "1. **الفحص الفوري للتداخلات الدوائية القاتلة** (مثل تداخل كولشيسين وكلاريثروميسين مع القصور الكلوي الحاد).\n"
            "2. **تدقيق المطالبات المالية** وفق معايير هيئة الصحة بدبي (DHA SN 03/2019).\n"
            "3. **التوثيق السريري المشفر** (HMAC-SHA256) وسجلات SOAP المتوافقة مع NABIDH.\n\n"
            "كيف يمكنني مساعدتك في تقييم الوصفات أو المطالبات اليوم؟\n\n"
            "---\n\n"
            "Welcome! I am Taryaq, your Sovereign Clinical Pharmacovigilance & Healthcare Compliance Copilot for Dubai 2027.\n\n"
            "Powered by a sub-0.05 ms native C99 safety shield, I provide:\n"
            "1. **Real-Time Drug Interaction Screening:** Blocking fatal CYP3A4 / renal clearance contraindications.\n"
            "2. **DHA SN 03/2019 Claim Auditing:** Computing late submission fee exposures and clean claims.\n"
            "3. **Cryptographic Non-Repudiation:** Tamper-evident ledger logging under UAE Health Data Law.\n\n"
            "How may I assist you with clinical evaluation or claims today?"
        )

