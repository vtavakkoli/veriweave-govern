from __future__ import annotations

import hashlib
import hmac
import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.models import AuditEnvelope


class AuditLedger:
    """Append-only JSONL audit chain with optional HMAC signatures.

    The ledger is a single-process writer. Its current chain head is cached in memory so
    appending a new record is O(1) with respect to ledger length instead of rescanning the
    complete JSONL file for every governance decision. The head is reconstructed once when
    the process starts, preserving continuity across restarts.
    """

    def __init__(self, path: Path, signing_key: str | None = None) -> None:
        self.path = path
        self.signing_key = signing_key.encode("utf-8") if signing_key else None
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)
        self._head_hash = self._read_head_hash()
        verification = self.verify()
        if not verification["valid"]:
            raise ValueError(f"refusing to append to corrupt audit history: {verification}")

    def _read_head_hash(self) -> str:
        """Read the persisted chain head once, primarily during process startup."""
        last = ""
        self._record_count = 0
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    last = json.loads(line)["record_hash"]
                    self._record_count += 1
        return last or "0" * 64

    def append(self, payload: dict[str, Any]) -> AuditEnvelope:
        with self._lock:
            previous_hash = self._head_hash
            created_at = datetime.now(UTC)
            record_id = str(uuid4())
            body = {
                "record_id": record_id,
                "created_at": created_at.isoformat(),
                "previous_hash": previous_hash,
                "payload": payload,
            }
            canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
            record_hash = hashlib.sha256((previous_hash + canonical).encode("utf-8")).hexdigest()
            signature = (
                hmac.new(self.signing_key, record_hash.encode("utf-8"), hashlib.sha256).hexdigest()
                if self.signing_key
                else None
            )
            record = {**body, "record_hash": record_hash, "signature": signature}
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True, default=str) + "\n")

            # Update only after the append succeeds. A failed write must never advance the
            # in-memory chain head beyond durable ledger state.
            self._head_hash = record_hash
            self._record_count += 1

            return AuditEnvelope(
                record_id=record_id,
                created_at=created_at,
                record_hash=record_hash,
                previous_hash=previous_hash,
                signature=signature,
            )

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with self._lock, self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return list(reversed(rows[-limit:]))

    def checkpoint(self) -> dict[str, Any]:
        """Export for storage outside this mutable ledger; this is not itself a signature."""
        with self._lock:
            return {"head_hash": self._head_hash, "records": self._record_count}

    def checked_record(self, record_id: str) -> dict[str, Any]:
        with self._lock:
            verification = self.verify()
            if not verification["valid"]:
                raise ValueError("audit integrity verification failed")
            with self.path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        record = json.loads(line)
                        if record["record_id"] == record_id:
                            return record
            raise ValueError("audit record unavailable")

    def verify(
        self, *, expected_head_hash: str | None = None, expected_records: int | None = None,
    ) -> dict[str, Any]:
        # Verification takes a consistent snapshot relative to this process's appends.
        with self._lock:
            previous_hash = "0" * 64
            count = 0
            with self.path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                        if not isinstance(record, dict) or set(record) != {
                            "record_id", "created_at", "previous_hash", "payload",
                            "record_hash", "signature",
                        }:
                            raise ValueError("invalid audit record schema")
                        body = {
                            "record_id": record["record_id"],
                            "created_at": record["created_at"],
                            "previous_hash": record["previous_hash"],
                            "payload": record["payload"],
                        }
                    except (ValueError, TypeError, KeyError):
                        return {"valid": False, "records": count,
                                "failed_at_line": line_number, "reason": "malformed audit record"}
                    canonical = json.dumps(
                        body,
                        sort_keys=True,
                        separators=(",", ":"),
                        default=str,
                    )
                    expected_hash = hashlib.sha256(
                        (previous_hash + canonical).encode("utf-8")
                    ).hexdigest()
                    if (
                        record["previous_hash"] != previous_hash
                        or record["record_hash"] != expected_hash
                    ):
                        return {"valid": False, "records": count, "failed_at_line": line_number,
                                "reason": "hash chain mismatch"}
                    if self.signing_key:
                        expected_signature = hmac.new(
                            self.signing_key,
                            expected_hash.encode("utf-8"),
                            hashlib.sha256,
                        ).hexdigest()
                        signature = record.get("signature")
                        if not isinstance(signature, str) or not hmac.compare_digest(
                            signature.encode("utf-8"), expected_signature.encode("utf-8")
                        ):
                            return {
                                "valid": False,
                                "records": count,
                                "failed_at_line": line_number,
                                "reason": "invalid signature",
                            }
                    previous_hash = record["record_hash"]
                    count += 1
            # The cached head detects truncation while this process is alive. After a
            # restart a protected external checkpoint is required to detect suffix loss.
            head = expected_head_hash if expected_head_hash is not None else self._head_hash
            records = expected_records if expected_records is not None else self._record_count
            if previous_hash != head or count != records:
                return {"valid": False, "records": count, "head_hash": previous_hash,
                        "reason": "checkpoint mismatch"}
            return {"valid": True, "records": count, "head_hash": previous_hash}
