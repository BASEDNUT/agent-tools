#!/usr/bin/env python3
"""Check EVERY changed SDK address in the Rootstock pnpm patch against deployment registries.

This verifies source consistency ONLY. It cannot prove that pnpm applied the patch,
that deployed code is authentic, or that a call routed to the correct contract.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rootstock_tools.registry import RegistryError, git_blob_sha, load_registry

PATCH_PIN = "1e0bc67d5bed6b0830db9a4845714bd9eb3e371c"
P_KEY = re.compile(r"^[ +]?\s*([A-Za-z][A-Za-z0-9]+): \{$")
P_ADDRESS = re.compile(r'^\+\s+\[(8453|84532)\s*/\*.*?\*/\]:\s*"(0x[0-9a-fA-F]{40})"')


def extract_entries(patch_text: str) -> list[dict]:
    target_file = None
    contract = None
    entries: list[dict] = []
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            target_file = line.split(" b/", 1)[-1]
            contract = None
        head = P_KEY.match(line)
        if head:
            contract = head.group(1)
        match = P_ADDRESS.match(line)
        if match:
            if contract is None or target_file is None:
                raise RegistryError("Unattributed patch address: unsupported or changed patch format")
            entries.append({"file": target_file, "chain_id": int(match.group(1)), "contract": contract, "address": match.group(2)})
    return entries


def compare(entries: list[dict], registries: dict[int, object]) -> dict:
    if not entries:
        raise RegistryError("No patched address records found; fail closed")
    checks = []
    by_key: dict[tuple, set] = defaultdict(set)
    for row in entries:
        reg = registries[row["chain_id"]]
        addresses = {item["address"].lower(): item["task"] for item in reg.candidates(row["contract"])}
        addr = row["address"].lower()
        checks.append({**row, "match": addr in addresses, "source_task": addresses.get(addr)})
        by_key[(row["chain_id"], row["contract"])].add(addr)
    divergent = [f"{key}" for key, addrs in by_key.items() if len(addrs) > 1]
    failures = [x for x in checks if not x["match"]]
    return {"checked_entries": len(entries), "matches": len(checks)-len(failures), "mismatches": failures, "bundle_divergences": divergent, "files": sorted({x["file"] for x in entries}), "chains": sorted({x["chain_id"] for x in entries}), "unique_chain_contracts": len(by_key), "ok": not failures and not divergent}


def main(argv=None):
    ap=argparse.ArgumentParser(description="Audit patch-to-registry source alignment, no transactions")
    ap.add_argument("--patch", type=Path, required=True)
    ap.add_argument("--registry-dir", type=Path, required=True)
    ap.add_argument("--allow-unpinned", action="store_true", help="Offline research only; not a source authenticity claim")
    args=ap.parse_args(argv)
    try:
        data=args.patch.read_bytes()
        patch_blob=git_blob_sha(data)
        if patch_blob!=PATCH_PIN and not args.allow_unpinned:
            raise RegistryError(f"Patch source blob not pinned: {patch_blob}")
        registries={k:load_registry(args.registry_dir / filename,allow_unpinned=args.allow_unpinned) for k,filename in ((8453,"base.json"),(84532,"base-sepolia.json"))}
        out=compare(extract_entries(data.decode("utf-8")),registries)
        out["patch_blob_sha"]=patch_blob
        out["sources_pinned"]=patch_blob==PATCH_PIN and all(r.verified_against_pinned_blob for r in registries.values())
        out["patch_applied_at_runtime_verified"]=False
        out["onchain_verified"]=False
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0 if out["ok"] else 2
    except (RegistryError,OSError,UnicodeError) as e:
        print(json.dumps({"ok":False,"error":str(e)}), file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
