#!/usr/bin/env bash
# Wait for Redis, backend, and Taskiq worker readiness before a benchmark.
set -euo pipefail

HOST="${CONCEPTCAST_HOST:-127.0.0.1}"
REDIS_PORT="${CONCEPTCAST_REDIS_PORT:-6379}"
BACKEND_URL="${CONCEPTCAST_BACKEND_URL:-http://${HOST}:8000/health}"
TIMEOUT="${CONCEPTCAST_STARTUP_TIMEOUT:-120}"

python3 - "$HOST" "$REDIS_PORT" "$BACKEND_URL" "$TIMEOUT" <<'PY'
import socket
import sys
import time
import urllib.error
import urllib.request

host, redis_port, backend_url, timeout = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
deadline = time.monotonic() + timeout
last = "not checked"

while time.monotonic() < deadline:
    try:
        with socket.create_connection((host, redis_port), timeout=2) as sock:
            sock.sendall(b"*1\r\n$4\r\nPING\r\n")
            if b"PONG" not in sock.recv(64):
                raise RuntimeError("Redis did not return PONG")

        with urllib.request.urlopen(backend_url, timeout=3) as response:
            if response.status >= 500:
                raise RuntimeError(f"backend returned HTTP {response.status}")

        # The worker has no HTTP endpoint; the systemd unit is the readiness
        # boundary. Redis + backend health means the queue can be reached.
        print("ConceptCast dependencies ready: Redis PONG and backend health OK")
        raise SystemExit(0)
    except Exception as exc:
        last = str(exc)
        time.sleep(2)

print(f"ConceptCast dependencies did not become ready within {timeout}s: {last}", file=sys.stderr)
raise SystemExit(1)
PY
