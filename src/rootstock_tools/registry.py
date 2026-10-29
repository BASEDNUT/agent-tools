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
    "base.json": "3999774121968bef9f6d5abca9748a4c62b14f10",
    "base-sepolia.json": "825ecb8dedab18d5867068572bd82cd85adceed7",
}

# S113-fix (2026-10-05) superseded deployments — defective upstream owners / zero
# sequencer feed. Hardcoded defense-in-depth: a registry that lists any of these
# addresses under a resolvable task fails closed at load time, whatever the pin.
KNOWN_SUPERSEDED = {
    # Base mainnet (7)
    "0xb3d9a369b6b7a354ccb81c68b975830103aebd59": "TokenPairRegistry: upstream-owner defect (superseded 2026-10-05)",
    "0x9614ea13c468c2c4fc830ecedb0741d1f54a5147": "CowSwapFeeBurner: upstream-owner defect",
    "0xc9e85699bc45c62bccfda6e23cca05dc76d090b6": "ERC4626CowSwapFeeBurner: upstream-owner defect",
    "0xe6c1ea38b26a29093858d57c257bc73cee79e22d": "BalancerFeeBurner: upstream-owner defect",
    "0x27969e016f144c266fdab2de60c90bd1e172eb5c": "WeightedLPOracleFactory: zero sequencer uptime feed",
    "0x1da76dcd3b1dc39ed82a96257dfad54cada7b733": "StableLPOracleFactory: zero sequencer uptime feed",
    "0x86d328be82b8713bfddde54ceacab0fbbfa9a7437": "EclpLPOracleFactory: zero sequencer uptime feed",
    # Base Sepolia (4)
    "0x43dbb8f3bb9f6277e350f37adf240518c0964f06": "TokenPairRegistry: upstream-owner defect",
    "0xf51efd4762d5ebdcba49472c266a5c37dc4ddd5a": "CowSwapFeeBurner: upstream-owner defect",
    "0xe9fcba7bf13dce9a146d02adfb2ad5ec036f0b35": "ERC4626CowSwapFeeBurner: upstream-owner defect",
    "0x67cf3d0223e191ac2c423ca1b27c0b688b1a1e35": "BalancerFeeBurner: upstream-owner defect",
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
    superseded: dict[str, dict[str, Any]]
    reported_contracts_total: int | None

    def is_superseded(self, address: str) -> bool:
        """True for known-superseded addresses and registry-declared superseded map keys."""
        key = address.lower() if isinstance(address, str) else ""
        return key in KNOWN_SUPERSEDED or key in self.superseded

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
        dead = [c for c in matches if self.is_superseded(c["address"])]
        if dead:
            listed = ", ".join(f"{c['task']}:{c['address']}" for c in dead)
            raise RegistryError(
                f"SUPERSEDED deployment listed as resolvable on chain {self.chain_id} for {name!r}: {listed}. "
                "Superseded contracts are provenance records of defective deployments — never resolve, approve, or use them."
            )
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
    task_addresses: set[str] = set()
    for task, contracts in tasks.items():
        if not isinstance(task, str) or not task or not isinstance(contracts, dict):
            raise RegistryError("Invalid task structure")
        for name, addr in contracts.items():
            if not isinstance(name, str) or not name or not isinstance(addr, str) or not ADDRESS.fullmatch(addr):
                raise RegistryError(f"Invalid deployment entry in {task}: {name!r}={addr!r}")
            key = addr.lower()
            if key in KNOWN_SUPERSEDED:
                raise RegistryError(
                    f"known-superseded deployment address present in tasks ({task}/{name}: {addr}) — "
                    f"{KNOWN_SUPERSEDED[key]}. Refusing to load a registry that makes a dead deployment resolvable."
                )
            task_addresses.add(key)
    superseded_raw = data.get("superseded", {})
    if superseded_raw is None:
        superseded_raw = {}
    if not isinstance(superseded_raw, dict):
        raise RegistryError("Invalid superseded map: expected object")
    superseded: dict[str, dict[str, Any]] = {}
    for old_addr, meta in superseded_raw.items():
        if not isinstance(old_addr, str) or not ADDRESS.fullmatch(old_addr):
            raise RegistryError(f"Invalid superseded map key: {old_addr!r}")
        if not isinstance(meta, dict):
            raise RegistryError(f"Invalid superseded map entry for {old_addr}")
        name = meta.get("name")
        replacement = meta.get("superseded_by")
        if not isinstance(name, str) or not name:
            raise RegistryError(f"Invalid superseded map entry for {old_addr}: name required")
        if not isinstance(replacement, str) or not ADDRESS.fullmatch(replacement):
            raise RegistryError(f"Invalid superseded map entry for {old_addr}: superseded_by must be an address")
        if replacement.lower() not in task_addresses:
            raise RegistryError(
                f"Invalid superseded map entry for {old_addr}: superseded_by {replacement} is not deployed in tasks"
            )
        if "never_use" in meta and meta["never_use"] is not True:
            raise RegistryError(f"Invalid superseded map entry for {old_addr}: never_use must be true")
        superseded[old_addr.lower()] = meta
    total = data.get("contracts_total")
    if total is not None and (type(total) is not int or total < 0):
        raise RegistryError("Invalid contract count")
    return Registry(chain_id, network, str(path), blob, pinned, tasks, superseded, total)
