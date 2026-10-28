"""Registry-only Rootstock deployments resolver.

No Balancer addresses, no network access, no private keys, no execution.
Read-only source inputs are explicit and validated; ambiguity never resolves by guess.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any

CANONICAL_BLOBS = {
    "base.json": "0348ff1e5ae37e25f43a337ff75cf9f2b8d2857a",
    "base-sepolia.json": "7efb0c38bd29cfa6c92b6cd74ee0c867e81d05c3",
}
CHAIN_IDS = {8453: "base.json", 84532: "base-sepolia.json"}
ADDRESS = re.compile(r"^0x[0-9a-fA-F]{40}$")
ZERO_ADDRESS = "0x" + "0" * 40


class RegistryError(ValueError):
    """Invalid, untrusted, ambiguous or unavailable deployment source."""


def git_blob_sha(raw: bytes) -> str:
    """Reproduce Git's blob-object identifier (not a signature)."""
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


@dataclass(frozen=True)
class Registry:
    chain_id: int
    network: str
    source: str
    blob_sha: str
    verified_against_pinned_blob: bool
    tasks: dict[str, dict[str, str]]
    reported_contracts_total: int | None

    def candidates(self, name: str) -> list[dict[str, str]]:
        if not name or not name.strip():
            raise RegistryError("Contract name required")
        return [
            {"name": contract, "address": addr, "task": task}
            for task, contracts in self.tasks.items()
            for contract, addr in contracts.items()
            if contract == name and addr.lower() != ZERO_ADDRESS
        ]

    def resolve(self, name: str, task: str | None = None) -> dict[str, Any]:
        matches = self.candidates(name)
        if task is not None:
            matches = [c for c in matches if c["task"] == task]
        if not matches:
            raise RegistryError(f"Not found on chain {self.chain_id}: {name!r} (task={task!r})")
        by_addr: dict[str, list[str]] = {}
        casing: dict[str, str] = {}
        for c in matches:
            key = c["address"].lower()
            by_addr.setdefault(key, []).append(c["task"])
            casing.setdefault(key, c["address"])
        if len(by_addr) != 1:
            choices = ", ".join(f"{c['task']}:{c['address']}" for c in matches)
            raise RegistryError(f"Ambiguous {name} on {self.chain_id}; specify --task. Candidates: {choices}")
        key = next(iter(by_addr))
        return {
            "chain_id": self.chain_id,
            "network": self.network,
            "name": name,
            "address": casing[key],
            "tasks": sorted(set(by_addr[key])),
            "source_blob_sha": self.blob_sha,
            "source_pinned": self.verified_against_pinned_blob,
            "source": self.source,
            "onchain_code_verified": False,
        }


def load_registry(path: Path, *, allow_unpinned: bool = False) -> Registry:
    if path.name not in CANONICAL_BLOBS:
        raise RegistryError(f"Unexpected registry filename: {path.name}")
    raw = path.read_bytes()
    blob = git_blob_sha(raw)
    pinned = blob == CANONICAL_BLOBS[path.name]
    if not pinned and not allow_unpinned:
        raise RegistryError(
            f"Registry blob differs from pinned canonical source ({path.name}: {blob}). "
            "Review upstream changes and update the source lock through review, "
            "or explicitly use --allow-unpinned for read-only local research."
        )
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise RegistryError("Malformed deployment JSON") from exc
    if not isinstance(data, dict):
        raise RegistryError("Expected registry object")
    expected_chain = 8453 if path.name == "base.json" else 84532
    chain_id = data.get("chainId")
    if type(chain_id) is not int or chain_id != expected_chain:
        raise RegistryError(f"Chain ID mismatch in registry: expected {expected_chain}, got {chain_id!r}")
    network = data.get("network")
    if network != ("base" if expected_chain == 8453 else "baseSepolia"):
        raise RegistryError(f"Network label mismatch: {network!r}")
    tasks = data.get("tasks")
    if not isinstance(tasks, dict) or not tasks:
        raise RegistryError("No deployment tasks")
    for task, contracts in tasks.items():
        if not isinstance(task, str) or not task or not isinstance(contracts, dict):
            raise RegistryError("Invalid task structure")
        for name, addr in contracts.items():
            if not isinstance(name, str) or not name or not isinstance(addr, str) or not ADDRESS.fullmatch(addr):
                raise RegistryError(f"Invalid deployment entry in {task}: {name!r}={addr!r}")
    total = data.get("contracts_total")
    if total is not None and (type(total) is not int or total < 0):
        raise RegistryError("Invalid contract count")
    return Registry(chain_id, network, str(path), blob, pinned, tasks, total)
