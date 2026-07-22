#!/usr/bin/env python3
"""Focused tests for safe pairing and revocation handling."""
from __future__ import annotations

import gzip
import importlib.util
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent


class Handler(BaseHTTPRequestHandler):
    mode = "register"
    requests = []

    def log_message(self, *_args):
        return

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(length)
        if self.mode == "register":
            body = json.loads(raw_body)
            response = {
                "token": "lu1_secret",
                "owner_id": "larry",
                "core_id": "lenin-test-mac-abc",
                "machine_id": body["machine_id"],
                "sessions_endpoint": "/v1/uplink/sessions",
                "protocol": "teamon-uplink/1",
            }
            raw = json.dumps(response).encode()
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        if self.mode == "sync":
            body = json.loads(gzip.decompress(raw_body))
            self.requests.append(body)
            raw = json.dumps({"accepted": True, "files": {}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        self.send_response(403)
        self.end_headers()


class UplinkTests(unittest.TestCase):
    def setUp(self):
        Handler.requests = []
        self.home = tempfile.TemporaryDirectory()
        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()
        self.home.cleanup()

    def load(self, name):
        with patch.dict(os.environ, {"HOME": self.home.name}):
            spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

    def test_registration_writes_private_config_without_printing_token(self):
        Handler.mode = "register"
        module = self.load("register")
        endpoint = f"http://127.0.0.1:{self.server.server_port}/api/uplink/register"
        with patch.object(module, "machine_id", return_value="Test-Mac"):
            config = module.register("lsc_once", endpoint)
        self.assertEqual(config["endpoint"], f"http://127.0.0.1:{self.server.server_port}/v1/uplink/sessions")
        self.assertEqual(config["protocol"], "teamon-uplink/1")
        self.assertEqual(module.CONFIG.stat().st_mode & 0o777, 0o600)

    def test_http_403_disables_future_sync(self):
        Handler.mode = "revoke"
        module = self.load("session_uplink")
        module.PROJECTS.mkdir(parents=True)
        session = module.PROJECTS / "project" / "session.jsonl"
        session.parent.mkdir()
        session.write_text('{"type":"user"}\n', encoding="utf-8")
        module.save_json(module.CONFIG_F, {
            **module.DEFAULT_CONFIG,
            "enabled": True,
            "endpoint": f"http://127.0.0.1:{self.server.server_port}/v1/uplink/sessions",
            "token": "revoked",
            "owner_id": "larry",
            "core_id": "lenin-test",
        })
        self.assertEqual(module.run(False, 1), 1)
        self.assertFalse(json.loads(module.CONFIG_F.read_text())["enabled"])

    def test_uplink_reports_its_installed_version(self):
        module = self.load("session_uplink")
        self.assertIn("uplink 1.1.0", module.lenin_version())

    def test_empty_run_sends_versioned_heartbeat(self):
        Handler.mode = "sync"
        module = self.load("session_uplink")
        module.save_json(module.CONFIG_F, {
            **module.DEFAULT_CONFIG,
            "enabled": True,
            "endpoint": f"http://127.0.0.1:{self.server.server_port}/v1/uplink/sessions",
            "token": "active",
            "owner_id": "larry",
            "core_id": "lenin-test",
        })
        self.assertEqual(module.run(False, 1), 0)
        self.assertEqual(len(Handler.requests), 1)
        self.assertEqual(Handler.requests[0]["chunks"], [])
        self.assertIn("uplink 1.1.0", Handler.requests[0]["lenin_version"])
        self.assertTrue(json.loads(module.STATE_F.read_text())["last_ok"])


if __name__ == "__main__":
    unittest.main()
