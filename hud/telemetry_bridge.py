#!/usr/bin/env python3
"""
hud/telemetry_bridge.py - Sovereign C99 Agent Telemetry Bridge (Dubai 2027)
Pure Python 3 Standard Library RFC 6455 WebSocket & HTTP Event Ingress Server.

Features:
- RFC 6455 WebSocket server on ws://127.0.0.1:8787/telemetry
- HTTP POST /emit event ingress broadcasting to all connected clients
- HTTP GET /health returning server status and connected client count
- HTTP GET/POST /shutdown for clean connection draining and process exit
- CLI flag --demo: timed sequence broadcasting all 8 event types every 1.5s
- Supported event types:
    * task_started
    * tool_call
    * gate_verdict
    * approval_required
    * state_committed
    * security_block
    * taryaq_clinical
    * grounding_verify
"""

import sys
import os
import time
import json
import base64
import hashlib
import struct
import socket
import signal
import threading
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver

WS_MAGIC_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
DEFAULT_DEMO_INTERVAL = 1.5


def make_ws_frame(data, opcode=0x1) -> bytes:
    """Encode an unmasked server-to-client RFC 6455 WebSocket frame."""
    payload = data.encode("utf-8") if isinstance(data, str) else data
    length = len(payload)
    head = bytearray()
    head.append(0x80 | (opcode & 0x0F))  # FIN=1, opcode

    if length <= 125:
        head.append(length)
    elif length <= 65535:
        head.append(126)
        head.extend(struct.pack(">H", length))
    else:
        head.append(127)
        head.extend(struct.pack(">Q", length))

    return bytes(head) + payload


def recv_exact(sock: socket.socket, n: int, is_shutting_down_fn=None):
    """Read exactly n bytes from a socket with timeout handling."""
    buf = bytearray()
    while len(buf) < n:
        if is_shutting_down_fn and is_shutting_down_fn():
            return None
        try:
            chunk = sock.recv(n - len(buf))
        except (socket.timeout, TimeoutError):
            continue
        except OSError:
            return None
        if not chunk:
            return None
        buf.extend(chunk)
    return bytes(buf)


def parse_ws_frame(sock: socket.socket, is_shutting_down_fn):
    """
    Parse an incoming client-to-server RFC 6455 WebSocket frame.
    Client frames MUST be masked per RFC 6455 Section 5.1.
    """
    while True:
        if is_shutting_down_fn():
            return None, None
        try:
            head = sock.recv(2)
        except (socket.timeout, TimeoutError):
            continue
        except OSError:
            return None, None

        if not head:
            return None, None
        if len(head) == 1:
            try:
                more = sock.recv(1)
            except (socket.timeout, TimeoutError):
                continue
            except OSError:
                return None, None
            if not more:
                return None, None
            head += more
        break

    b0, b1 = head[0], head[1]
    fin = bool(b0 & 0x80)
    opcode = b0 & 0x0F
    masked = bool(b1 & 0x80)
    plen = b1 & 0x7F

    if plen == 126:
        ext = recv_exact(sock, 2, is_shutting_down_fn)
        if ext is None:
            return None, None
        plen = struct.unpack(">H", ext)[0]
    elif plen == 127:
        ext = recv_exact(sock, 8, is_shutting_down_fn)
        if ext is None:
            return None, None
        plen = struct.unpack(">Q", ext)[0]

    mask_key = None
    if masked:
        mask_key = recv_exact(sock, 4, is_shutting_down_fn)
        if mask_key is None:
            return None, None

    if plen > 0:
        raw = recv_exact(sock, plen, is_shutting_down_fn)
        if raw is None:
            return None, None
        if masked:
            payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(raw))
        else:
            payload = bytes(raw)
    else:
        payload = b""

    return opcode, payload


class WSClient:
    """Wrapper around a connected WebSocket client socket."""
    def __init__(self, sock: socket.socket, addr):
        self.sock = sock
        self.addr = addr
        self.lock = threading.Lock()
        self.closed = False

    def send_text(self, text: str) -> bool:
        with self.lock:
            if self.closed:
                return False
            try:
                frame = make_ws_frame(text, opcode=0x1)
                self.sock.sendall(frame)
                return True
            except OSError:
                self.closed = True
                return False

    def close(self):
        with self.lock:
            if not self.closed:
                self.closed = True
                try:
                    self.sock.sendall(bytes([0x88, 0x00]))
                except Exception:
                    pass
                try:
                    self.sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    self.sock.close()
                except Exception:
                    pass


class TelemetryBridge:
    """Manages active WebSocket client connections and event broadcasting."""
    def __init__(self):
        self.clients = []
        self.lock = threading.Lock()
        self.shutting_down = False

    def register(self, client: WSClient):
        with self.lock:
            self.clients.append(client)

    def unregister(self, client: WSClient):
        with self.lock:
            if client in self.clients:
                self.clients.remove(client)

    def client_count(self) -> int:
        with self.lock:
            return len(self.clients)

    def broadcast(self, event_data) -> int:
        text = json.dumps(event_data) if isinstance(event_data, dict) else str(event_data)
        with self.lock:
            active = []
            for client in self.clients:
                if client.send_text(text):
                    active.append(client)
                else:
                    client.close()
            self.clients = active
            return len(self.clients)

    def close_all_clients(self):
        self.shutting_down = True
        with self.lock:
            for client in list(self.clients):
                client.close()
            self.clients.clear()


class TelemetryHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        # Suppress routine HTTP request logging to keep output clean
        pass

    def _send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def _send_json(self, status_code: int, data_dict: dict):
        body = (json.dumps(data_dict) + "\n").encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._send_cors()
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {
                "status": "ok",
                "clients": self.server.bridge.client_count(),
                "service": "qala_nibras_taryaq_hud_bridge"
            })
            return

        if self.path == "/shutdown":
            self.handle_shutdown()
            return

        if self.path.startswith("/telemetry"):
            upgrade = self.headers.get("Upgrade", "").lower()
            connection = self.headers.get("Connection", "").lower()
            if "websocket" in upgrade and "upgrade" in connection:
                self.handle_websocket()
                return
            else:
                body = b"WebSocket Upgrade Required: connect using ws://<host>:<port>/telemetry\n"
                self.send_response(426, "Upgrade Required")
                self.send_header("Content-Type", "text/plain")
                self.send_header("Upgrade", "websocket")
                self.send_header("Connection", "Upgrade")
                self._send_cors()
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(body)
                self.wfile.flush()
                return

        if self.path == "/":
            body = (
                b"QALA | NIBRAS EXECUTIVE | TARYAQ HUD Telemetry Bridge (Dubai 2027)\n"
                b"WebSocket Endpoint: ws://127.0.0.1:8787/telemetry\n"
                b"HTTP Event Ingress: POST http://127.0.0.1:8787/emit\n"
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self._send_cors()
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/shutdown":
            self.handle_shutdown()
            return

        if self.path == "/emit":
            try:
                content_len = int(self.headers.get("Content-Length", 0))
                if content_len <= 0:
                    self._send_json(400, {"error": "Missing or empty Content-Length"})
                    return
                raw_body = self.rfile.read(content_len)
                payload = json.loads(raw_body.decode("utf-8"))
            except Exception as e:
                self._send_json(400, {"error": f"Invalid JSON payload: {e}"})
                return

            event_type = payload.get("event_type") or payload.get("type", "custom")
            client_count = self.server.bridge.broadcast(payload)
            self._send_json(200, {
                "status": "emitted",
                "clients": client_count,
                "event_type": event_type
            })
            return

        self.send_error(404, "Not Found")

    def handle_shutdown(self):
        self._send_json(200, {"status": "shutting_down"})

        def _do_shutdown(srv):
            time.sleep(0.05)
            srv.shutdown_server()

        threading.Thread(target=_do_shutdown, args=(self.server,), daemon=True).start()

    def handle_websocket(self):
        sec_key = self.headers.get("Sec-WebSocket-Key")
        if not sec_key:
            self.send_error(400, "Missing Sec-WebSocket-Key")
            return

        accept_token = base64.b64encode(
            hashlib.sha1((sec_key.strip() + WS_MAGIC_GUID).encode("utf-8")).digest()
        ).decode("ascii")

        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept_token}\r\n"
            "\r\n"
        )
        try:
            self.request.sendall(response.encode("ascii"))
        except OSError:
            return

        self.request.settimeout(0.5)
        client = WSClient(self.request, self.client_address)
        self.server.bridge.register(client)

        try:
            while not self.server.bridge.shutting_down and not client.closed:
                opcode, payload = parse_ws_frame(
                    self.request, lambda: self.server.bridge.shutting_down
                )
                if opcode is None or opcode == 0x8:  # Close frame or connection dropped
                    break
                elif opcode == 0x9:  # Ping
                    pong_frame = make_ws_frame(payload, opcode=0xA)
                    with client.lock:
                        if not client.closed:
                            client.sock.sendall(pong_frame)
                elif opcode == 0xA:  # Pong
                    pass
                elif opcode == 0x1:  # Text frame from client (if any)
                    pass
        except OSError:
            pass
        finally:
            self.server.bridge.unregister(client)
            client.close()
            self.close_connection = True


class ThreadedTelemetryServer(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass, bridge: TelemetryBridge):
        self.bridge = bridge
        super().__init__(server_address, RequestHandlerClass)

    def shutdown_server(self):
        self.bridge.close_all_clients()
        threading.Thread(target=self.shutdown, daemon=True).start()


def get_demo_events():
    """Return the 8 canonical Dubai 2027 stage telemetry demo events."""
    now = int(time.time())
    return [
        {
            "event_type": "task_started",
            "task_id": "dubai-stage-demo-001",
            "title": "Autonomous Customs & Clinical Audit Workflow",
            "ast_time": "3.4 ms (41 Tools Ready)",
            "token_saved": "18% (Day 0 Baseline)",
            "gate_status": "INITIALIZED (READY)",
            "log": json.dumps({
                "timestamp_utc": now,
                "event": "task_started",
                "task": "dubai-stage-demo-001",
                "agent": "QALA/NIBRAS/TARYAQ"
            })
        },
        {
            "event_type": "tool_call",
            "tool": "customs_duty_calculator",
            "tool_name": "customs_duty_calculator",
            "duration_ms": 2.1,
            "ready_tools": 41,
            "mcp_frame": (
                "POST /mcp HTTP/1.1\r\n"
                "Host: 127.0.0.1:8765\r\n"
                "Content-Type: application/json\r\n"
                "MCP-Protocol-Version: 2026-07-28\r\n"
                "Mcp-Name: qala-native-c99\r\n"
                "Mcp-Method: tools/call\r\n\r\n"
                "{\"jsonrpc\":\"2.0\",\"id\":42,\"method\":\"tools/call\","
                "\"params\":{\"name\":\"customs_duty_calculator\","
                "\"arguments\":{\"declared_value_aed\":125000.0}}}"
            ),
            "log": json.dumps({
                "timestamp_utc": now + 1,
                "tool": "customs_duty_calculator",
                "action": "calc",
                "verdict": "SAFE"
            })
        },
        {
            "event_type": "approval_required",
            "tool": "erp_customs_settlement",
            "amount_aed": 125000.00,
            "threshold_aed": 50000.00,
            "scope": "finops_remediate",
            "log": json.dumps({
                "timestamp_utc": now + 2,
                "tool": "erp_customs_settlement",
                "amount_aed": 125000.00,
                "status": "AWAITING_TELEGRAM_TOKEN"
            })
        },
        {
            "event_type": "gate_verdict",
            "verdict": "APPROVED & VERIFIED (SAFE)",
            "token": "DUBAI-APPROVE-9941-X",
            "tool": "erp_customs_settlement",
            "log": json.dumps({
                "timestamp_utc": now + 3,
                "tool": "erp_customs_settlement",
                "amount_aed": 125000.00,
                "approval_supplied": True,
                "verdict": "SAFE",
                "code": "policy_verified"
            })
        },
        {
            "event_type": "security_block",
            "tool": "fs_read",
            "target": "/confidential/uae_citizens.db",
            "reason": "C99 Path Allowlist Deny (EACCES)",
            "log": json.dumps({
                "timestamp_utc": now + 4,
                "tool": "fs_read",
                "target_path": "/confidential/uae_citizens.db",
                "verdict": "UNSAFE",
                "code": "landlock_fs_denied"
            })
        },
        {
            "event_type": "state_committed",
            "token_saved": "97% Saved (+7 Days @ 10080x)",
            "node1_pct": "(I = 0.003 -> PRUNED)",
            "node1_bar": "0%",
            "node2_pct": "(I = 0.004 -> PRUNED)",
            "node2_bar": "0%",
            "log": json.dumps({
                "timestamp_utc": now + 5,
                "action": "state_committed",
                "fademem_pruned": 2,
                "token_saved": "97%"
            })
        },
        {
            "event_type": "taryaq_clinical",
            "drugs": "Colchicine + Clarithromycin",
            "egfr": 22.0,
            "verdict": "FATAL CONTRAINDICATION BLOCKED",
            "code": "FATAL_CYP3A4_RENAL_CONTRAINDICATION",
            "log": json.dumps({
                "timestamp_utc": now + 6,
                "agent": "Taryaq",
                "tool": "rx_prescribe",
                "primary_drug": "Colchicine",
                "egfr": 22.0,
                "verdict": "CLINICAL_CONTRAINDICATION_BLOCK",
                "code": "FATAL_CYP3A4_RENAL_CONTRAINDICATION"
            })
        },
        {
            "event_type": "grounding_verify",
            "pii_redacted": "patient name & Emirates ID (784-1988-...)",
            "claimed_val": "0.05% daily penalty",
            "grounded_val": "0.03% daily penalty",
            "citation": "DHA SN 03/2019",
            "verdict": "HALLUCINATION BLOCKED (CORRECTED)",
            "log": json.dumps({
                "timestamp_utc": now + 7,
                "agent": "Qala/Taryaq",
                "tool": "grounding_verify",
                "claimed_val": 0.05,
                "grounded_val": 0.03,
                "citation": "DHA_SN_03_2019",
                "verdict": "HALLUCINATION_BLOCKED"
            })
        }
    ]


def run_demo_loop(bridge: TelemetryBridge, interval: float):
    """Continuously broadcast demo events in order every interval seconds."""
    print(f"[hud_bridge] Demo loop started (interval: {interval}s)", flush=True)
    events = get_demo_events()
    idx = 0
    while not bridge.shutting_down:
        event = events[idx % len(events)].copy()
        try:
            if "log" in event:
                log_obj = json.loads(event["log"])
                log_obj["timestamp_utc"] = int(time.time())
                event["log"] = json.dumps(log_obj)
        except Exception:
            pass

        active_clients = bridge.broadcast(event)
        event_name = event.get("event_type")
        print(f"[hud_bridge:demo] Emitted '{event_name}' (clients: {active_clients})", flush=True)
        idx += 1
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Qala/Nibras/Taryaq HUD Telemetry Bridge (Dubai 2027)")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Listen host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Listen port (default: {DEFAULT_PORT})")
    parser.add_argument("--demo", action="store_true", help="Broadcast timed sequence of all event types every 1.5s")
    parser.add_argument("--interval", type=float, default=DEFAULT_DEMO_INTERVAL, help=f"Demo broadcast interval in seconds (default: {DEFAULT_DEMO_INTERVAL})")
    args = parser.parse_args()

    bridge = TelemetryBridge()
    server = ThreadedTelemetryServer((args.host, args.port), TelemetryHandler, bridge)

    def sig_handler(sig, frame):
        print("\n[hud_bridge] Received termination signal, shutting down...", flush=True)
        server.shutdown_server()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    print(f"[hud_bridge] ========================================================", flush=True)
    print(f"[hud_bridge] WebSocket Telemetry Bridge: ws://{args.host}:{args.port}/telemetry", flush=True)
    print(f"[hud_bridge] HTTP Event Ingress:        POST http://{args.host}:{args.port}/emit", flush=True)
    print(f"[hud_bridge] Health Check:               GET http://{args.host}:{args.port}/health", flush=True)
    print(f"[hud_bridge] Clean Shutdown:             POST http://{args.host}:{args.port}/shutdown", flush=True)
    if args.demo:
        print(f"[hud_bridge] Mode: DEMO BROADCASTER (interval: {args.interval}s)", flush=True)
    else:
        print(f"[hud_bridge] Mode: PRODUCTION DAEMON (awaiting /emit events)", flush=True)
    print(f"[hud_bridge] ========================================================", flush=True)

    if args.demo:
        demo_thread = threading.Thread(target=run_demo_loop, args=(bridge, args.interval), daemon=True)
        demo_thread.start()

    try:
        server.serve_forever()
    finally:
        server.server_close()
        print("[hud_bridge] Bridge stopped. Port released.", flush=True)


if __name__ == "__main__":
    main()
