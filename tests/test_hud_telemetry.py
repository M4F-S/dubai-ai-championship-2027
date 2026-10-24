#!/usr/bin/env python3
"""
tests/test_hud_telemetry.py - Automated End-to-End Test Suite for HUD Telemetry Bridge
Pure Python 3 Standard Library verification (Zero pip dependencies).

Verifies:
a) Bridge starts and binds to port 8787 (/health returns 200 OK).
b) Client connects over WebSocket RFC 6455 handshake (101 Switching Protocols & Accept Token).
c) HTTP POST /emit sends events; client receives unmasked broadcast frame over WebSocket.
   (Verifies all 8 event types + multi-client broadcast + extended payload framing).
d) Clean shutdown drops client connection and frees TCP port.
e) --demo flag broadcasts periodic telemetry sequence without external /emit calls.
"""

import sys
import os
import time
import json
import base64
import hashlib
import struct
import socket
import urllib.request
import subprocess
import unittest

MAGIC_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
TEST_PORT = int(os.environ.get("HUD_TEST_PORT", 8787))
TEST_HOST = "127.0.0.1"


class SimpleWebSocketClient:
    """Pure Python standard library RFC 6455 test client."""
    def __init__(self, host=TEST_HOST, port=TEST_PORT, path="/telemetry"):
        self.host = host
        self.port = port
        self.path = path
        self.sock = None
        self.key = None

    def connect(self, timeout=3.0) -> bool:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((self.host, self.port))

        raw_key = os.urandom(16)
        self.key = base64.b64encode(raw_key).decode("ascii")

        req = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {self.key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        self.sock.sendall(req.encode("ascii"))

        resp_data = bytearray()
        while b"\r\n\r\n" not in resp_data:
            chunk = self.sock.recv(1024)
            if not chunk:
                raise ConnectionError("Server closed connection during handshake")
            resp_data.extend(chunk)

        header_bytes, _, _ = resp_data.partition(b"\r\n\r\n")
        header_text = header_bytes.decode("latin1")
        lines = header_text.split("\r\n")
        status_line = lines[0]
        if "101" not in status_line:
            raise ConnectionError(f"Handshake failed with status: {status_line}")

        headers = {}
        for line in lines[1:]:
            if ":" in line:
                k, v = line.split(":", 1)
                headers[k.strip().lower()] = v.strip()

        expected_accept = base64.b64encode(
            hashlib.sha1((self.key + MAGIC_GUID).encode("utf-8")).digest()
        ).decode("ascii")

        actual_accept = headers.get("sec-websocket-accept")
        if actual_accept != expected_accept:
            raise ConnectionError(
                f"Invalid Sec-WebSocket-Accept: expected {expected_accept}, got {actual_accept}"
            )

        return True

    def _recv_exact(self, n: int) -> bytes:
        data = bytearray()
        while len(data) < n:
            chunk = self.sock.recv(n - len(data))
            if not chunk:
                break
            data.extend(chunk)
        return bytes(data)

    def recv_frame(self, timeout=3.0):
        self.sock.settimeout(timeout)
        head = self._recv_exact(2)
        if not head or len(head) < 2:
            return None, None
        b0, b1 = head[0], head[1]
        opcode = b0 & 0x0F
        masked = bool(b1 & 0x80)
        payload_len = b1 & 0x7F

        if payload_len == 126:
            ext = self._recv_exact(2)
            payload_len = struct.unpack(">H", ext)[0]
        elif payload_len == 127:
            ext = self._recv_exact(8)
            payload_len = struct.unpack(">Q", ext)[0]

        mask_key = None
        if masked:
            mask_key = self._recv_exact(4)

        raw = self._recv_exact(payload_len) if payload_len > 0 else b""
        if masked:
            payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(raw))
        else:
            payload = raw

        return opcode, payload

    def close(self):
        if self.sock:
            try:
                mask = os.urandom(4)
                # Client close frame: opcode 8 (0x88), masked (0x80)
                self.sock.sendall(bytes([0x88, 0x80]) + mask)
            except Exception:
                pass
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None


class TestHUDTelemetryBridge(unittest.TestCase):
    bridge_proc = None

    @classmethod
    def setUpClass(cls):
        bridge_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "hud", "telemetry_bridge.py"
        )
        cls.bridge_proc = subprocess.Popen(
            [sys.executable, bridge_path, "--host", TEST_HOST, "--port", str(TEST_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        ready = False
        health_url = f"http://{TEST_HOST}:{TEST_PORT}/health"
        for _ in range(30):
            try:
                req = urllib.request.Request(health_url)
                with urllib.request.urlopen(req, timeout=0.5) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(0.1)

        if not ready:
            cls.bridge_proc.kill()
            raise RuntimeError(f"HUD Telemetry Bridge failed to start on port {TEST_PORT}")

    @classmethod
    def tearDownClass(cls):
        if cls.bridge_proc and cls.bridge_proc.poll() is None:
            try:
                shutdown_url = f"http://{TEST_HOST}:{TEST_PORT}/shutdown"
                req = urllib.request.Request(shutdown_url, data=b"{}", headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=1.0)
            except Exception:
                cls.bridge_proc.terminate()
            cls.bridge_proc.wait(timeout=3.0)

    def test_01_health_and_binding(self):
        """a) Verify bridge starts and binds to port 8787."""
        url = f"http://{TEST_HOST}:{TEST_PORT}/health"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data.get("status"), "ok")
            self.assertIn("clients", data)

    def test_02_websocket_handshake(self):
        """b) Verify client connects over WebSocket RFC 6455 handshake."""
        client = SimpleWebSocketClient(TEST_HOST, TEST_PORT)
        connected = client.connect(timeout=2.0)
        self.assertTrue(connected)

        # Health endpoint should reflect 1 active client
        url = f"http://{TEST_HOST}:{TEST_PORT}/health"
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.assertGreaterEqual(data.get("clients", 0), 1)

        client.close()

    def test_03_emit_and_broadcast_all_events(self):
        """c) Verify HTTP POST /emit sends event, client receives broadcast frame over WebSocket."""
        client = SimpleWebSocketClient(TEST_HOST, TEST_PORT)
        client.connect(timeout=2.0)
        time.sleep(0.1)

        event_types = [
            ("task_started", {"task_id": "dubai-t-1", "ast_time": "3.1 ms"}),
            ("tool_call", {"tool": "customs_duty_calculator", "duration_ms": 1.9}),
            ("gate_verdict", {"verdict": "APPROVED & VERIFIED (SAFE)", "token": "DUBAI-APPROVE-9941-X"}),
            ("approval_required", {"tool": "erp_customs_settlement", "amount_aed": 125000.0, "scope": "finops_remediate"}),
            ("state_committed", {"token_saved": "97% Saved", "node1_pct": "(I = 0.003 -> PRUNED)"}),
            ("security_block", {"tool": "fs_read", "target": "/confidential/uae_citizens.db", "verdict": "UNSAFE"}),
            ("taryaq_clinical", {"drugs": "Colchicine + Clarithromycin", "egfr": 22.0, "verdict": "FATAL CONTRAINDICATION BLOCKED"}),
            ("grounding_verify", {"citation": "DHA SN 03/2019", "claimed_val": 0.05, "grounded_val": 0.03, "verdict": "HALLUCINATION BLOCKED (CORRECTED)"}),
        ]

        emit_url = f"http://{TEST_HOST}:{TEST_PORT}/emit"
        for etype, payload in event_types:
            event_obj = {"event_type": etype, **payload, "log": f'{{"test_event":"{etype}"}}'}
            req_data = json.dumps(event_obj).encode("utf-8")
            req = urllib.request.Request(
                emit_url, data=req_data, headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as resp:
                self.assertEqual(resp.status, 200)
                body = json.loads(resp.read().decode("utf-8"))
                self.assertEqual(body.get("status"), "emitted")
                self.assertEqual(body.get("event_type"), etype)
                self.assertGreaterEqual(body.get("clients", 0), 1)

            opcode, frame_data = client.recv_frame(timeout=2.0)
            self.assertEqual(opcode, 0x1, f"Expected text opcode 1 for {etype}")
            received_obj = json.loads(frame_data.decode("utf-8"))
            self.assertEqual(received_obj.get("event_type"), etype)
            for k, v in payload.items():
                self.assertEqual(received_obj.get(k), v)

        client.close()

    def test_04_multi_client_broadcast(self):
        """Verify simultaneous broadcast to multiple connected browser clients."""
        c1 = SimpleWebSocketClient(TEST_HOST, TEST_PORT)
        c2 = SimpleWebSocketClient(TEST_HOST, TEST_PORT)
        c3 = SimpleWebSocketClient(TEST_HOST, TEST_PORT)

        c1.connect()
        c2.connect()
        c3.connect()
        time.sleep(0.1)

        event = {"event_type": "gate_verdict", "verdict": "APPROVED & VERIFIED (SAFE)"}
        emit_url = f"http://{TEST_HOST}:{TEST_PORT}/emit"
        req = urllib.request.Request(
            emit_url, data=json.dumps(event).encode("utf-8"), headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(body.get("clients"), 3)

        for client in (c1, c2, c3):
            op, data = client.recv_frame(timeout=2.0)
            self.assertEqual(op, 0x1)
            ev = json.loads(data.decode("utf-8"))
            self.assertEqual(ev.get("verdict"), "APPROVED & VERIFIED (SAFE)")

        c1.close()
        c2.close()
        c3.close()

    def test_05_clean_shutdown_and_offline_drop(self):
        """d) Verify clean shutdown drops connection and frees port (offline state)."""
        client = SimpleWebSocketClient(TEST_HOST, TEST_PORT)
        client.connect()

        # Issue POST /shutdown
        shutdown_url = f"http://{TEST_HOST}:{TEST_PORT}/shutdown"
        req = urllib.request.Request(
            shutdown_url, data=b"{}", headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)

        # The client should see connection close (close frame or socket EOF)
        op, data = client.recv_frame(timeout=2.0)
        self.assertIn(op, (None, 0x8))
        client.close()

        # Subprocess should cleanly exit
        self.bridge_proc.wait(timeout=3.0)
        self.assertEqual(self.bridge_proc.returncode, 0)

        # Port should now reject new connections (confirming offline state)
        s = socket.socket()
        try:
            with self.assertRaises(ConnectionRefusedError):
                s.connect((TEST_HOST, TEST_PORT))
        finally:
            s.close()

    def test_06_demo_flag_broadcast(self):
        """e) Verify --demo flag broadcasts periodic telemetry sequence without /emit calls."""
        demo_port = TEST_PORT + 10
        bridge_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "hud", "telemetry_bridge.py"
        )
        proc = subprocess.Popen(
            [sys.executable, bridge_path, "--port", str(demo_port), "--demo", "--interval", "0.2"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            # Wait for demo bridge ready
            ready = False
            for _ in range(30):
                try:
                    with urllib.request.urlopen(f"http://{TEST_HOST}:{demo_port}/health", timeout=0.5) as r:
                        if r.status == 200:
                            ready = True
                            break
                except Exception:
                    time.sleep(0.1)
            self.assertTrue(ready, "Demo bridge failed to bind")

            # Connect client
            client = SimpleWebSocketClient(TEST_HOST, demo_port)
            client.connect(timeout=2.0)

            # Receive 3 demo frames emitted automatically
            received_types = []
            for _ in range(3):
                op, data = client.recv_frame(timeout=2.0)
                self.assertEqual(op, 0x1)
                ev = json.loads(data.decode("utf-8"))
                received_types.append(ev.get("event_type"))

            self.assertEqual(len(received_types), 3)
            valid_types = {
                "task_started", "tool_call", "approval_required", "gate_verdict",
                "security_block", "state_committed", "taryaq_clinical", "grounding_verify"
            }
            for et in received_types:
                self.assertIn(et, valid_types)
            client.close()
        finally:
            # Shutdown demo bridge
            try:
                req = urllib.request.Request(
                    f"http://{TEST_HOST}:{demo_port}/shutdown", data=b"{}", headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=1.0)
            except Exception:
                proc.terminate()
            proc.wait(timeout=3.0)


def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHUDTelemetryBridge)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()