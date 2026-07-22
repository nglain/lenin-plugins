#!/usr/bin/env python3
"""Safely pair this Mac with the authenticated Lenin profile."""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path.home() / ".claude" / "lenin_uplink"
CONFIG = BASE / "config.json"
DEFAULT_REGISTER_ENDPOINT = "https://lenin.nglain.com/api/uplink/register"


def machine_id() -> str:
    try:
        result = subprocess.run(
            ["scutil", "--get", "LocalHostName"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return platform.node() or "unknown-mac"


def require_safe_endpoint(endpoint: str) -> str:
    parsed = urllib.parse.urlparse(endpoint)
    local = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if parsed.scheme != "https" and not (local and parsed.scheme == "http"):
        raise ValueError("Registration endpoint must use HTTPS")
    if not parsed.netloc:
        raise ValueError("Invalid registration endpoint")
    return endpoint


def save_config(config: dict) -> None:
    BASE.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = CONFIG.with_suffix(".tmp")
    temporary.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(CONFIG)
    os.chmod(CONFIG, 0o600)


def register(code: str, endpoint: str = DEFAULT_REGISTER_ENDPOINT) -> dict:
    endpoint = require_safe_endpoint(endpoint)
    machine = machine_id()
    request = urllib.request.Request(
        endpoint,
        data=json.dumps({"code": code.strip(), "machine_id": machine}).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        try:
            detail = json.loads(error.read().decode("utf-8")).get("error", "")
        except Exception:
            detail = ""
        raise RuntimeError(detail or f"Registration failed: HTTP {error.code}") from None
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Registration failed: {error}") from None

    required = ("token", "owner_id", "core_id", "machine_id", "sessions_endpoint", "protocol")
    if not all(payload.get(field) for field in required):
        raise RuntimeError("Registration response is incomplete")
    sessions = urllib.parse.urljoin(endpoint, payload["sessions_endpoint"])
    require_safe_endpoint(sessions)
    config = {
        "enabled": True,
        "endpoint": sessions,
        "token": payload["token"],
        "owner_id": payload["owner_id"],
        "core_id": payload["core_id"],
        "machine_id": payload["machine_id"],
        "protocol": payload["protocol"],
        "max_mb_per_run": 200,
        "max_chunk_mb": 8,
        "max_batch_mb": 24,
    }
    save_config(config)
    return config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("code", help="one-time code from the Lenin profile")
    parser.add_argument("--endpoint", default=DEFAULT_REGISTER_ENDPOINT)
    args = parser.parse_args()
    try:
        config = register(args.code, args.endpoint)
    except (ValueError, RuntimeError) as error:
        print(f"uplink: {error}", file=sys.stderr)
        return 1
    print(f"uplink: Mac подключён · owner={config['owner_id']} · machine={config['machine_id']}")
    print(f"config: {CONFIG} (режим 0600)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
