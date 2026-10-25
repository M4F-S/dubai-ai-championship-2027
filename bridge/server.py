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
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, List

from bridge.c99_bindings import get_engine_status
from bridge.openrouter_client import (
    OpenRouterAgentEngine,
    AUDIT_LOG_FILE,
    VALID_OVERRIDE_TOKEN,
    _consumed_override_tokens,
    _override_lock
)

DEFAULT_PORT = 8080
DEFAULT_HOST = "127.0.0.1"

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
    }
]


class ChampionshipRequestHandler(BaseHTTPRequestHandler):
    engine = OpenRouterAgentEngine()

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
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        """Handle POST requests."""
        url_path = self.path.split("?")[0]

        if url_path == "/api/chat":
            self._handle_chat_stream()
        elif url_path == "/api/override":
            self._handle_override()
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
        status["server_time_utc"] = int(time.time())
        status["active_model"] = self.engine.model
        status["api_key_configured"] = bool(self.engine.api_key)
        status["active_agent"] = self.engine.active_agent
        status["mode"] = "HYBRID_CLOUD_C99_SHIELD" if self.engine.api_key else "SOVEREIGN_AIRGAP_C99_ONLY"

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

    def _serve_audit_verify(self):
        """Cryptographically verify the SHA-256 hash chain from genesis (AF-11)."""
        import hashlib
        records = []
        is_valid = True
        error_msg = ""
        prev_sha = None

        if os.path.exists(AUDIT_LOG_FILE):
            try:
                with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                    for line_idx, line in enumerate(f):
                        line = line.strip()
                        if not line:
                            continue
                        record = json.loads(line)
                        records.append(record)

                        expected_sig = record.get("sha256_signature")
                        recorded_prev = record.get("prev_sha256")

                        if expected_sig and recorded_prev is not None:
                            # Verify signature matches entry payload
                            rec_copy = dict(record)
                            rec_copy.pop("sha256_signature", None)
                            recomputed = hashlib.sha256(json.dumps(rec_copy, sort_keys=True).encode("utf-8")).hexdigest()
                            if expected_sig != recomputed:
                                is_valid = False
                                error_msg = f"Signature mismatch at record {line_idx}"
                                break

                            # If chained to a known previous hash, check continuity
                            if prev_sha is not None and recorded_prev != prev_sha and recorded_prev != "0000000000000000000000000000000000000000000000000000000000000000":
                                is_valid = False
                                error_msg = f"Chain break at record {line_idx}: expected prev {prev_sha}, found {recorded_prev}"
                                break

                        if expected_sig:
                            prev_sha = expected_sig
            except Exception as e:
                is_valid = False
                error_msg = str(e)

        res = {
            "chain_intact": is_valid,
            "total_records": len(records),
            "latest_sha256": prev_sha or "GENESIS",
            "status": "VERIFIED_TAMPER_EVIDENT" if is_valid else "CHAIN_INTEGRITY_COMPROMISED",
            "error": error_msg or None
        }
        body = json.dumps(res, indent=2).encode("utf-8")
        self.send_response(200 if is_valid else 400)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

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


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """Start the multi-threaded HTTP/SSE server."""
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, ChampionshipRequestHandler)
    print(f"==================================================================")
    print(f" DUBAI AI AGENTS CHAMPIONSHIP 2026-2027 | AGENT BRIDGE SERVER")
    print(f"==================================================================")
    print(f"[*] Server listening on: http://{host}:{port}")
    print(f"[*] SSE Chat endpoint:   http://{host}:{port}/api/chat")
    print(f"[*] Health endpoint:     http://{host}:{port}/api/health")
    print(f"[*] Audit ledger:        http://{host}:{port}/api/audit")
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
    args = parser.parse_args()
    run_server(args.host, args.port)
