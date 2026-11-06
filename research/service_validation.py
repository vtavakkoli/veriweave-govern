"""Run the real HTTP service and its benchmark in one local process environment."""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

from benchmark.runner import request_json, wait_for_service


def run(output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="veriweave-http-") as temp:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        env = {
            **os.environ, "GOVERN_AUDIT_PATH": str(Path(temp) / "audit.jsonl"),
            "GOVERN_SNAPSHOT_DIR": str(Path(temp) / "snapshots"),
            "GOVERN_AUDIT_SIGNING_KEY": "public-local-http-fixture-not-for-deployment",
        }
        env.pop("GOVERN_EVIDENCE_TRUST_CONFIG", None)
        url = f"http://127.0.0.1:{port}"
        with (output / "server.log").open("w") as log:
            server = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
                 "--port", str(port)], env=env, stdout=log, stderr=subprocess.STDOUT,
            )
            try:
                wait_for_service(url, 15)
                benchmark = subprocess.run([
                    sys.executable, "-m", "benchmark.runner", "--base-url", url,
                    "--results-dir", str(output), "--iterations", "10", "--concurrency", "4",
                ], check=False)
                recent = request_json("GET", f"{url}/v1/audit?limit=1")
                record = recent.body["records"][0]
                replay = request_json("POST", f"{url}/v1/replay", {"record_id": record["record_id"]})
                wrong = request_json("POST", f"{url}/v1/replay", {
                    "record_id": record["record_id"], "expected_policy_set_hash": "0" * 64,
                })
                passed = benchmark.returncode == 0 and replay.status == 200 and (
                    replay.body["reproduced"] and wrong.status == 409
                )
                (output / "replay-http.json").write_text(json.dumps({
                    "historical_replay": replay.body, "incorrect_version_status": wrong.status,
                    "passed": passed, "scope": "Local single-instance HTTP, demo metadata verifier",
                }, indent=2))
                return 0 if passed else 1
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("results/revision-2026-11/service"))
    args = parser.parse_args()
    return run(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
