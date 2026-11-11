"""
bridge/server.py - High-Performance HTTP & SSE Server for Sovereign Agent Bridge (Dubai 2027)

Exposes:
- GET  /              -> Serves the Championship Glass Cockpit UI
- GET  /api/health    -> Diagnostic health status, loaded C99 symbols, active model
- POST /api/chat      -> Server-Sent Events (SSE) streaming chat endpoint
- POST /api/override  -> Single-use clinician override verification & consumption
- GET  /api/audit     -> Cryptographic audit ledger log entries
- GET  /api/scenarios -> Pre-configured championship demonstration scenarios

Pure Python standard library implementation with zero external dependencies.
"""

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import json
import time
import argparse
import subprocess
import urllib.parse
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List, Optional, Tuple, Union

from bridge.c99_bindings import get_engine_status
from bridge.openrouter_client import (
    OpenRouterAgentEngine,
    AUDIT_LOG_FILE,
    VALID_OVERRIDE_TOKEN,
    _consumed_override_tokens,
    _override_lock
)
from bridge.voice_stt import transcribe_audio, validate_wav_pcm
from bridge.voice_tts import synthesize_speech, validate_tts_wav, VOICE_CACHE_DIR
from bridge.clinical_scribe import ClinicalScribeEngine, DEFAULT_CLINICAL_DB

# Active Tri-Modal Copilot Mode ('clinician' | 'pharmacist' | 'patient')
_active_clinical_mode = "clinician"
_scribe_engine = ClinicalScribeEngine()


def get_clinical_mode() -> str:
    """Return the current active tri-modal copilot mode."""
    global _active_clinical_mode
    return _active_clinical_mode


def set_clinical_mode(mode: str) -> str:
    """Set the active tri-modal copilot mode."""
    global _active_clinical_mode
    mode = str(mode).strip().lower()
    if mode in ("clinician", "pharmacist", "patient"):
        _active_clinical_mode = mode
    return _active_clinical_mode

DEFAULT_PORT = 8080
DEFAULT_HOST = "127.0.0.1"
# Canonical HMAC ledger verifier (vendored byte-identical from taryaq-agent).
VERIFY_SCRIPT = os.path.join(PROJECT_ROOT, "tools", "verify_audit.py")

# Predefined judge demonstration scenarios
DEMO_SCENARIOS = [
    {
        "id": "scenario_taryaq_fatal",
        "agent": "taryaq",
        "title_en": "1. Taryaq: Fatal Drug Interaction Block (CKD Stage 4)",
        "title_ar": "١. الترياق: حظر تداخل دوائي مميت (قصور كلوي حاد)",
        "prompt": "Patient Ahmed (Emirates ID 784-1985-1234567-1, DOB 1985-04-12) presented with acute gout flare. Prescribed كولشيسين 0.5mg BID and Clarithromycin 500mg BID for concurrent respiratory infection. Current laboratory report shows eGFR = 22 mL/min/1.73m².",
        "expected": "C99 Fatal CYP3A4 + Renal Contraindication Block (< 0.02 ms)",
        "override_code": "TARYAQ-OVERRIDE-8842-CLIN"
    },
    {
        "id": "scenario_taryaq_claim",
        "agent": "taryaq",
        "title_en": "2. Taryaq: DHA SN 03/2019 Claim Submission Delay",
        "title_ar": "٢. الترياق: تدقيق تأخير المطالبة وفق تعميم هيئة الصحة بدبي",
        "prompt": "Review insurance claim invoice #DHA-CLM-9921 for AED 450.00 submitted 12 days past the statutory 30-day window under DHA SN 03/2019 rules.",
        "expected": "DHA SN 03/2019 statutory late penalty scrub (0.03%/day = AED 1.62 penalty)",
        "override_code": ""
    },
    {
        "id": "scenario_qala_customs",
        "agent": "qala",
        "title_en": "3. Qala: DP World Trade Clearance & FinOps Gate",
        "title_ar": "٣. القلعة: تسوية جمركية موانئ دبي وبوابة الحوكمة المالية",
        "prompt": "Initiate automated customs settlement clearance for DP World Jebel Ali container shipment #DPW-DXB-88301 with transaction value AED 125,000.00.",
        "expected": "DESC ISR v3.1 / Tau-3 Policy Review Required (Exceeds AED 50,000 threshold)",
        "override_code": "QALA-CONFIRM-50K"
    },
    {
        "id": "scenario_nibras_fademem",
        "agent": "nibras",
        "title_en": "4. Nibras: FadeMem Arabic Context Compression",
        "title_ar": "٤. النبراس: خوارزمية FadeMem للضغط الإدراكي للذاكرة العربية",
        "prompt": "قم بتلخيص وتنظيم جدول مواعيد الرئيس التنفيذي في دبي ٢٠٢٧، وتفريغ الذاكرة المؤقتة للضوضاء التشغيلية مع استخلاص القواعد الدائمة.",
        "expected": "C99 Arabic Normalizer + FadeMem episodic decay (> 85% token reduction)",
        "override_code": ""
    },
    {
        "id": "scenario_nibras_civic",
        "agent": "nibras",
        "title_en": "5. Nibras: DLD Ejari Decree 43/2013 Rent Dispute RAG",
        "title_ar": "٥. النبراس: التحقق من نزاعات زيادة الإيجار وفق مرسوم إيجاري ٤٣/٢٠١٣",
        "prompt": "صاحب الشقة رفع عليا الايجار 20%، هل هذا قانوني وفق مرسوم إيجاري رقم 43 لسنة 2013 الصادر عن دائرة الأراضي والأملاك؟",
        "expected": "Dynamic RAG retrieval of DLD-EJARI-DECREE-43-2013:Article 1 tiers with cryptographic SHA-256 proof",
        "override_code": ""
    }
]


class ChampionshipRequestHandler(BaseHTTPRequestHandler):
    engine = None

    def __init__(self, *args, **kwargs):
        if ChampionshipRequestHandler.engine is None:
            ChampionshipRequestHandler.engine = OpenRouterAgentEngine()
        super().__init__(*args, **kwargs)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        url_path = self.path.split("?")[0]

        if url_path == "/" or url_path == "/index.html":
            self._serve_ui()
        elif url_path == "/api/health":
            self._serve_health()
        elif url_path == "/api/audit":
            self._serve_audit()
        elif url_path == "/api/audit/verify":
            self._serve_audit_verify()
        elif url_path == "/api/scenarios":
            self._serve_scenarios()
        elif url_path == "/api/airlock/quarantine":
            self._serve_airlock_quarantine()
        elif url_path == "/api/voice/synthesize":
            self._handle_voice_synthesize()
        elif url_path == "/api/clinical/mode":
            self._handle_get_clinical_mode()
        elif url_path in ("/api/clinical/soap/notes", "/api/clinical/soap/list"):
            self._handle_get_soap_notes()
        elif url_path.startswith("/api/clinical/soap/"):
            note_id = url_path[len("/api/clinical/soap/"):].strip("/")
            if note_id and not note_id.endswith("/sign") and note_id not in ("notes", "list"):
                self._handle_get_soap_note_by_id(note_id)
            else:
                self.send_error(404, "Endpoint not found")
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        """Handle POST requests."""
        url_path = self.path.split("?")[0]

        if url_path == "/api/chat":
            self._handle_chat_stream()
        elif url_path == "/api/override":
            self._handle_override()
        elif url_path == "/api/airlock/review":
            self._handle_airlock_review()
        elif url_path == "/api/voice/transcribe":
            self._handle_voice_transcribe()
        elif url_path == "/api/voice/synthesize":
            self._handle_voice_synthesize()
        elif url_path in ("/api/clinical/soap/generate", "/api/clinical/soap/parse"):
            self._handle_soap_generate()
        elif url_path == "/api/clinical/soap/commit":
            self._handle_soap_commit()
        elif url_path == "/api/clinical/soap/signoff":
            self._handle_soap_signoff()
        elif url_path.startswith("/api/clinical/soap/") and url_path.endswith("/sign"):
            note_id = url_path[len("/api/clinical/soap/"):-len("/sign")].strip("/")
            self._handle_soap_signoff(note_id_from_path=note_id)
        elif url_path == "/api/clinical/mode":
            self._handle_post_clinical_mode()
        else:
            self.send_error(404, "Endpoint not found")

    def _serve_ui(self):
        """Serve the Glass Cockpit HTML UI."""
        # Find UI template: first check hud/glass_cockpit_hud.html, or bridge/cockpit.html
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ui_path = os.path.join(root_dir, "hud", "glass_cockpit_hud.html")
        alt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cockpit.html")

        target = alt_path if os.path.exists(alt_path) else ui_path

        if os.path.exists(target):
            with open(target, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, "UI template not found")

    def _serve_health(self):
        """Return diagnostic health and hardware status."""
        status = get_engine_status()
        status["c99_loaded"] = status.get("c99_library_loaded", True)
        status["server_time_utc"] = int(time.time())
        status["provider"] = self.engine.provider
        status["active_model"] = (
            self.engine.ollama_model if self.engine.provider == "ollama"
            else (self.engine.model if self.engine.provider == "openrouter" else "deterministic_c99")
        )
        status["ollama_base_url"] = self.engine.ollama_base_url
        status["ollama_model"] = self.engine.ollama_model
        status["api_key_configured"] = bool(self.engine.api_key)
        status["active_agent"] = self.engine.active_agent
        status["voice_engine"] = {
            "stt": "whisper.cpp (large-v3-turbo 16kHz PCM)",
            "tts": "piper-tts (bilingual ar/en 22.05 kHz WAV)",
            "cache_dir": VOICE_CACHE_DIR
        }
        status["clinical_mode"] = _active_clinical_mode
        status["scribe_engine"] = "ClinicalScribeEngine (ICD-10 + DHA SN 03/2019)"
        if self.engine.provider == "ollama":
            status["mode"] = "LOCAL_OLLAMA_AIRGAP_C99_SHIELD"
        elif self.engine.provider == "openrouter":
            status["mode"] = "HYBRID_CLOUD_C99_SHIELD"
        else:
            status["mode"] = "SOVEREIGN_AIRGAP_C99_ONLY"

        body = json.dumps(status, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_audit(self):
        """Return the most recent audit records."""
        lines = []
        if os.path.exists(AUDIT_LOG_FILE):
            try:
                with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            lines.append(json.loads(line))
            except Exception:
                pass

        # Return latest 50 records reversed
        recent = lines[-50:][::-1]
        body = json.dumps({"count": len(recent), "records": recent}, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_scenarios(self):
        """Return predefined championship demonstration scenarios."""
        body = json.dumps({"scenarios": DEMO_SCENARIOS}, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _handle_chat_stream(self):
        """Stream SSE chunks for chat interactions."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            req_data = json.loads(body)
        except Exception:
            self.send_error(400, "Invalid JSON body")
            return

        user_message = req_data.get("message", "")
        agent_name = req_data.get("agent", "taryaq")
        override_token = req_data.get("override_token")
        override_rationale = req_data.get("override_rationale")
        chat_history = req_data.get("history", [])

        self.engine.set_agent(agent_name)

        # Set SSE headers
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        # Stream generator output as SSE frames
        for event in self.engine.process_chat(
            user_message=user_message,
            chat_history=chat_history,
            override_token=override_token,
            override_rationale=override_rationale
        ):
            frame = f"data: {json.dumps(event)}\n\n".encode("utf-8")
            try:
                self.wfile.write(frame)
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                break

        # Send closing frame and mark connection closed for HTTP clients
        try:
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        self.close_connection = True

    def _send_json(self, payload: Dict[str, Any], code: int = 200):
        """Emit a JSON response with the CORS header the cockpit expects."""
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _serve_audit_verify(self):
        """Verify the HMAC-chained audit ledger via tools/verify_audit.py.

        The C writer signs HMAC-SHA256(key, prev_sha256 || "\\n" || canonical). This
        endpoint delegates to the same verifier the CLI uses, so "verified" has exactly
        one definition. Fail-closed: a missing key is a 503 (never a success), and a
        record without canonical/prev_sha256/mac is a failure — there is no
        "skip unsigned records" path, which is the bug this replaces.
        """
        total = 0
        latest_mac = "GENESIS"

        if os.path.exists(AUDIT_LOG_FILE):
            try:
                with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        total += 1
                        rec = json.loads(line)
                        if rec.get("mac"):
                            latest_mac = rec["mac"]
            except Exception as e:
                self._send_json({
                    "chain_intact": False, "total_records": total,
                    "latest_sha256": latest_mac,
                    "status": "LEDGER_UNREADABLE", "error": str(e)
                }, 400)
                return

        key = os.environ.get("TARYAQ_AUDIT_KEY", "")
        if len(key.encode("utf-8")) < 32:
            self._send_json({
                "chain_intact": False, "total_records": total,
                "latest_sha256": latest_mac,
                "status": "AUDIT_KEY_MISSING",
                "error": "TARYAQ_AUDIT_KEY missing or shorter than 32 bytes; refusing to verify."
            }, 503)
            return

        if total == 0:
            self._send_json({
                "chain_intact": True, "total_records": 0,
                "latest_sha256": "GENESIS",
                "status": "EMPTY_LEDGER", "error": None
            }, 200)
            return

        try:
            proc = subprocess.run(
                [sys.executable, VERIFY_SCRIPT, "--ledger", AUDIT_LOG_FILE, "--key", key],
                capture_output=True, text=True, timeout=30
            )
        except Exception as e:
            self._send_json({
                "chain_intact": False, "total_records": total,
                "latest_sha256": latest_mac,
                "status": "VERIFIER_ERROR", "error": str(e)
            }, 500)
            return

        ok = proc.returncode == 0
        detail = (proc.stderr or proc.stdout or "").strip()
        self._send_json({
            "chain_intact": ok,
            "total_records": total,
            "latest_sha256": latest_mac,
            "status": "VERIFIED" if ok else "CHAIN_INTEGRITY_COMPROMISED",
            "error": None if ok else (detail or "verification failed")
        }, 200 if ok else 400)

    def _handle_override(self):
        """AF-04 Fix: Validate and consume clinician override token under lock with replay check."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            req_data = json.loads(body)
        except Exception:
            self.send_error(400, "Invalid JSON body")
            return

        token = req_data.get("token", "").strip()
        rationale = req_data.get("rationale", "").strip()

        with _override_lock:
            if not token:
                res = {"status": "ERROR", "message": "Missing override token"}
                code = 400
            elif token in _consumed_override_tokens:
                res = {"status": "REJECTED", "message": "Conflict: Override token has already been consumed. Replay rejected under single-use security policy."}
                code = 409
            elif token != VALID_OVERRIDE_TOKEN:
                res = {"status": "REJECTED", "message": "Invalid token. Authorized clinician signature required."}
                code = 403
            elif not rationale:
                res = {"status": "REJECTED", "message": "Clinical rationale justification cannot be empty."}
                code = 400
            else:
                _consumed_override_tokens.add(token)
                res = {
                    "status": "VALIDATED",
                    "token": token,
                    "rationale": rationale,
                    "timestamp_utc": int(time.time()),
                    "message": "Clinician token accepted. Gated safety barrier unblocked for single execution."
                }
                code = 200

        resp_bytes = json.dumps(res).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(resp_bytes)

    def _serve_airlock_quarantine(self):
        """List staged HITL quarantine candidates from corpus/airlock_ledger.db."""
        from bridge.airlock import list_quarantine_items

        parsed_url = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed_url.query)
        status_filter = qs.get("status", [None])[0]
        limit_val = 50
        if "limit" in qs:
            try:
                limit_val = int(qs["limit"][0])
            except (ValueError, TypeError):
                limit_val = 50

        try:
            items = list_quarantine_items(status=status_filter, limit=limit_val)
            self._send_json({
                "status": "SUCCESS",
                "count": len(items),
                "quarantine": items
            }, 200)
        except Exception as e:
            self._send_json({
                "status": "ERROR",
                "error": str(e)
            }, 500)

    def _handle_airlock_review(self):
        """Review endpoint for licensed clinicians to approve or reject quarantine candidates."""
        from bridge.airlock import review_quarantine_item

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            req_data = json.loads(body)
        except Exception:
            self._send_json({"status": "ERROR", "message": "Invalid JSON body"}, 400)
            return

        quarantine_id = req_data.get("quarantine_id", "").strip()
        status = req_data.get("status", "").strip().upper()
        notes = req_data.get("notes") or req_data.get("reviewer_notes")
        reviewer_role = req_data.get("reviewer_role", "LICENSED_CLINICAL_PHARMACIST")

        if not quarantine_id:
            self._send_json({"status": "ERROR", "message": "Missing quarantine_id parameter"}, 400)
            return

        if status not in ("APPROVED", "REJECTED"):
            self._send_json({
                "status": "ERROR",
                "message": f"Invalid review status '{status}'. Must be 'APPROVED' or 'REJECTED'."
            }, 400)
            return

        try:
            res = review_quarantine_item(
                quarantine_id=quarantine_id,
                status=status,
                notes=notes,
                reviewer_role=reviewer_role
            )
            self._send_json({
                "status": "SUCCESS",
                "message": f"Quarantine item {quarantine_id} reviewed successfully.",
                "review": res
            }, 200)
        except KeyError:
            self._send_json({"status": "ERROR", "message": f"Quarantine ID '{quarantine_id}' not found."}, 404)
        except Exception as e:
            self._send_json({"status": "ERROR", "message": str(e)}, 500)

    def _handle_voice_transcribe(self):
        """POST /api/voice/transcribe: Transcribes audio bytes to normalized text.
        
        Accepts:
        - Content-Type: audio/wav, audio/x-wav, audio/wave, application/octet-stream
        - Content-Type: multipart/form-data with audio chunk
        - Content-Type: application/json with {"audio_base64": "..."}
        
        Returns:
            JSON: {"transcript": "...", "normalized": "...", "language": "..."}
        """
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            self._send_json({"status": "ERROR", "message": "Empty audio payload in request body"}, 400)
            return

        raw_body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        audio_bytes: bytes = b""

        if "multipart/form-data" in content_type:
            boundary = ""
            for part in content_type.split(";"):
                part = part.strip()
                if part.startswith("boundary="):
                    boundary = part[len("boundary="):].strip('"')
            if boundary:
                b_boundary = f"--{boundary}".encode("utf-8")
                parts = raw_body.split(b_boundary)
                for p in parts:
                    if b"\r\n\r\n" in p:
                        header_part, body_part = p.split(b"\r\n\r\n", 1)
                        if body_part.endswith(b"\r\n"):
                            body_part = body_part[:-2]
                        if b"RIFF" in body_part:
                            riff_idx = body_part.find(b"RIFF")
                            audio_bytes = body_part[riff_idx:]
                            break
                        elif b"filename=" in header_part or b"name=" in header_part:
                            audio_bytes = body_part
                            break
            if not audio_bytes:
                riff_idx = raw_body.find(b"RIFF")
                if riff_idx >= 0:
                    audio_bytes = raw_body[riff_idx:]
                else:
                    audio_bytes = raw_body

        elif "application/json" in content_type:
            try:
                import base64
                req_json = json.loads(raw_body.decode("utf-8"))
                b64_audio = req_json.get("audio_base64") or req_json.get("audio") or req_json.get("audio_hex")
                if b64_audio:
                    if req_json.get("audio_hex"):
                        audio_bytes = bytes.fromhex(b64_audio)
                    else:
                        audio_bytes = base64.b64decode(b64_audio)
                else:
                    self._send_json({"status": "ERROR", "message": "Missing audio_base64 in JSON body"}, 400)
                    return
            except Exception as e:
                self._send_json({"status": "ERROR", "message": f"Invalid JSON payload: {e}"}, 400)
                return
        else:
            audio_bytes = raw_body

        try:
            res = transcribe_audio(audio_bytes)
            self._send_json({
                "status": "SUCCESS",
                "transcript": res["transcript"],
                "normalized": res["normalized"],
                "language": res["language"],
                "engine": res["engine"],
                "latency_ms": res["latency_ms"]
            }, 200)
        except Exception as e:
            self._send_json({"status": "ERROR", "message": f"Transcription error: {str(e)}"}, 400)

    def _handle_voice_synthesize(self):
        """POST or GET /api/voice/synthesize: Synthesizes text into clean 22.05 kHz WAV audio stream.
        
        Accepts:
        - POST JSON: {"text": "...", "lang": "ar|en"}
        - GET Query: ?text=...&lang=ar|en
        
        Returns:
            audio/wav binary stream
        """
        text = ""
        lang = "ar"

        if self.command == "GET":
            parsed_url = urllib.parse.urlparse(self.path)
            qs = urllib.parse.parse_qs(parsed_url.query)
            text = qs.get("text", [""])[0]
            lang = qs.get("lang", [qs.get("language", ["ar"])[0]])[0]
        else:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                raw_body = self.rfile.read(content_length).decode("utf-8")
                try:
                    req_json = json.loads(raw_body)
                    text = req_json.get("text", "")
                    lang = req_json.get("lang") or req_json.get("language") or "ar"
                except Exception:
                    self._send_json({"status": "ERROR", "message": "Invalid JSON body"}, 400)
                    return

        if not text:
            self._send_json({"status": "ERROR", "message": "Missing text parameter for speech synthesis"}, 400)
            return

        try:
            wav_bytes = synthesize_speech(text, language=lang)
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(wav_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "public, max-age=86400")
            self.end_headers()
            self.wfile.write(wav_bytes)
        except Exception as e:
            self._send_json({"status": "ERROR", "message": f"Synthesis error: {str(e)}"}, 500)

    # -------------------------------------------------------------------------
    # Ambient Clinical Scribing & Tri-Modal Copilot Endpoints (M-15)
    # -------------------------------------------------------------------------

    def _handle_soap_generate(self):
        """POST /api/clinical/soap/generate (or /api/clinical/soap/parse):
        Parses multi-turn clinical dialogue into structured SOAP note, ICD-10 codes, and DHA claims.
        """
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
        try:
            req_data = json.loads(body) if body else {}
        except Exception as e:
            self._send_json({"status": "ERROR", "message": f"Invalid JSON body: {e}"}, 400)
            return

        transcript = req_data.get("transcript") or req_data.get("dialogue") or req_data.get("text", "")
        if not transcript:
            self._send_json({"status": "ERROR", "message": "Missing 'transcript' in request body"}, 400)
            return

        metadata = {
            "encounter_id": req_data.get("encounter_id"),
            "patient_id": req_data.get("patient_id") or req_data.get("emirates_id"),
            "patient_name": req_data.get("patient_name"),
            "clinician_id": req_data.get("clinician_id"),
            "encounter_date": req_data.get("encounter_date")
        }

        try:
            res = _scribe_engine.parse_dialogue_to_soap(transcript, metadata=metadata)
            response_payload = {
                "status": "SUCCESS",
                "soap": res["soap"],
                "icd10": res["icd10"],
                "dha_claims": res["dha_claims"],
                "safety_alerts": res["safety_alerts"],
                "encounter_id": res["encounter_id"],
                "patient_hash": res["patient_hash"],
                "clinician_id": res["clinician_id"],
                "vitals": res.get("vitals", {}),
                "labs": res.get("labs", {}),
                "medications": res.get("medications", [])
            }
            self._send_json(response_payload, 200)
        except Exception as e:
            self._send_json({"status": "ERROR", "message": f"SOAP parsing error: {e}"}, 500)

    def _handle_soap_commit(self):
        """POST /api/clinical/soap/commit:
        Commits SOAP note to sovereign SQLite database with SHA-256 patient pseudonymization.
        """
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
        try:
            req_data = json.loads(body) if body else {}
        except Exception as e:
            self._send_json({"status": "ERROR", "message": f"Invalid JSON body: {e}"}, 400)
            return

        # If payload contains nested 'soap', unwrap it
        if "soap" in req_data and isinstance(req_data["soap"], dict):
            for k in ("subjective", "objective", "assessment", "plan"):
                if k in req_data["soap"] and k not in req_data:
                    req_data[k] = req_data["soap"][k]

        patient_raw = (
            req_data.get("patient_identifier_hash")
            or req_data.get("patient_hash")
            or req_data.get("patient_id")
            or req_data.get("emirates_id", "")
        )
        if len(patient_raw) == 64 and re.match(r"^[0-9a-fA-F]{64}$", patient_raw):
            patient_hash = patient_raw.lower()
        else:
            patient_hash = ClinicalScribeEngine.pseudonymize_patient_identity(patient_raw)

        req_data["patient_identifier_hash"] = patient_hash

        try:
            note_id = ClinicalScribeEngine.commit_soap_to_db(DEFAULT_CLINICAL_DB, req_data)
            self._send_json({
                "status": "COMMITTED",
                "note_id": note_id,
                "patient_hash": patient_hash
            }, 200)
        except Exception as e:
            self._send_json({"status": "ERROR", "message": f"Commit failed: {e}"}, 500)

    def _handle_get_soap_notes(self):
        """GET /api/clinical/soap/notes (or /api/clinical/soap/list):
        Retrieves list of stored clinical records with optional filtering.
        """
        parsed_url = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed_url.query)

        patient_hash = qs.get("patient_hash", [qs.get("patient_id", [None])[0]])[0]
        if patient_hash and (len(patient_hash) != 64 or not re.match(r"^[0-9a-fA-F]{64}$", patient_hash)):
            patient_hash = ClinicalScribeEngine.pseudonymize_patient_identity(patient_hash)

        limit_val = 20
        if "limit" in qs:
            try:
                limit_val = int(qs["limit"][0])
            except (ValueError, TypeError):
                limit_val = 20

        try:
            notes = ClinicalScribeEngine.get_soap_notes(
                DEFAULT_CLINICAL_DB,
                patient_hash=patient_hash,
                limit=limit_val
            )
            self._send_json(notes, 200)
        except Exception as e:
            self._send_json({"status": "ERROR", "message": f"Failed to retrieve notes: {e}"}, 500)

    def _handle_get_soap_note_by_id(self, note_id: str):
        """GET /api/clinical/soap/{note_id}:
        Retrieves a single SOAP note by ID.
        """
        try:
            note = ClinicalScribeEngine.get_soap_note_by_id(DEFAULT_CLINICAL_DB, note_id)
            if note is None:
                self._send_json({"status": "ERROR", "message": f"SOAP note '{note_id}' not found"}, 404)
            else:
                self._send_json(note, 200)
        except Exception as e:
            self._send_json({"status": "ERROR", "message": f"Failed to retrieve note: {e}"}, 500)

    def _handle_soap_signoff(self, note_id_from_path: Optional[str] = None):
        """POST /api/clinical/soap/signoff (or /api/clinical/soap/{note_id}/sign):
        Attests and locks a clinical SOAP note.
        """
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
        try:
            req_data = json.loads(body) if body else {}
        except Exception:
            req_data = {}

        note_id = note_id_from_path or req_data.get("note_id")
        if not note_id:
            self._send_json({"status": "ERROR", "message": "Missing 'note_id' parameter"}, 400)
            return

        clinician_id = req_data.get("clinician_id", "DHA-MD-88124")
        sig_token = req_data.get("signature_token") or "CLINICIAN_DIGITAL_SIG"

        try:
            ok = ClinicalScribeEngine.signoff_soap_note(
                DEFAULT_CLINICAL_DB,
                note_id=note_id,
                clinician_id=clinician_id,
                signature_token=sig_token
            )
            if ok:
                self._send_json({
                    "status": "SIGNED",
                    "note_id": note_id,
                    "locked": True
                }, 200)
            else:
                self._send_json({"status": "ERROR", "message": f"SOAP note '{note_id}' not found"}, 404)
        except Exception as e:
            self._send_json({"status": "ERROR", "message": f"Signoff error: {e}"}, 500)

    def _handle_get_clinical_mode(self):
        """GET /api/clinical/mode: Returns current active UI mode."""
        self._send_json({"mode": get_clinical_mode()}, 200)

    def _handle_post_clinical_mode(self):
        """POST /api/clinical/mode: Sets current active UI mode."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
        try:
            req_data = json.loads(body) if body else {}
        except Exception:
            self._send_json({"status": "ERROR", "message": "Invalid JSON body"}, 400)
            return

        target_mode = str(req_data.get("mode", "")).strip().lower()
        if target_mode not in ("clinician", "pharmacist", "patient"):
            self._send_json({
                "status": "ERROR",
                "message": f"Invalid mode '{target_mode}'. Must be 'clinician', 'pharmacist', or 'patient'."
            }, 400)
            return

        current = set_clinical_mode(target_mode)
        self._send_json({
            "mode": current,
            "status": "MODE_SWITCHED"
        }, 200)


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, provider: str = "auto"):
    """Start the multi-threaded HTTP/SSE server."""
    ChampionshipRequestHandler.engine = OpenRouterAgentEngine(provider=provider)
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, ChampionshipRequestHandler)
    print(f"==================================================================")
    print(f" DUBAI AI AGENTS CHAMPIONSHIP 2026-2027 | AGENT BRIDGE SERVER")
    print(f"==================================================================")
    print(f"[*] Server listening on: http://{host}:{port}")
    print(f"[*] SSE Chat endpoint:   http://{host}:{port}/api/chat")
    print(f"[*] Health endpoint:     http://{host}:{port}/api/health")
    print(f"[*] Audit ledger:        http://{host}:{port}/api/audit")
    print(f"[*] Active Provider:     {ChampionshipRequestHandler.engine.provider.upper()}")
    print(f"[*] Target Architecture: Bare-Metal C99 Shield + 7B/8B Open Model")
    print(f"==================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down bridge server...")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Championship Agent Bridge Server")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Host address to bind")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind")
    parser.add_argument(
        "--provider",
        choices=["auto", "ollama", "openrouter", "deterministic"],
        default="auto",
        help="Inference provider: auto (detect Ollama -> OpenRouter -> C99), ollama, openrouter, or deterministic"
    )
    args = parser.parse_args()
    run_server(args.host, args.port, args.provider)
