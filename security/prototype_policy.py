#!/usr/bin/env python3
"""OFFLINE READ-ONLY POLICY DEMONSTRATOR — not a production authorization gateway.

This script only classifies JSON proposals. It DOES NOT call tools, authenticate
agents, authorize wallets, hold secrets, simulate transactions, or grant permissions.
The executing tool host must independently prevent all side effects.
"""
import json
import re
import sys
from typing import Any

CHAINS = {8453, 84532}
OPERATIONS = {
    "rootstock.deployments.inspect": {"manifest"},
    "rootstock.pools.list": {"limit"},
    "orchard.observations.inspect": {"observation_id"},
    "rootstock.source.audit": {"source"},
}
ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._:-]{0,63}\Z")
MANIFEST = {8453: "deployments/base.json", 84532: "deployments/base-sepolia.json"}


def evaluate(proposal: Any) -> dict[str, Any]:
    """Return deterministic DENY or ALLOW_READ label; host must recheck all inputs."""
    def deny(code: str) -> dict[str, Any]:
        return {"decision": "DENY", "reason": code, "executable": False}

    if not isinstance(proposal, dict):
        return deny("invalid_request_shape")
    if set(proposal) != {"operation", "chain_id", "arguments"}:
        return deny("unexpected_or_missing_request_fields")
    op = proposal["operation"]
    chain = proposal["chain_id"]
    args = proposal["arguments"]
    if not isinstance(op, str) or op not in OPERATIONS:
        return deny("operation_not_readonly_allowlisted")
    if type(chain) is not int or chain not in CHAINS:
        return deny("unsupported_chain")
    if not isinstance(args, dict) or any(type(key) is not str for key in args):
        return deny("invalid_arguments_shape")
    if not set(args).issubset(OPERATIONS[op]):
        return deny("unrecognized_tool_argument")
    if op == "rootstock.pools.list":
        limit = args.get("limit", 20)
        if type(limit) is not int or not 1 <= limit <= 100:
            return deny("invalid_limit")
    elif op in ("rootstock.deployments.inspect", "rootstock.source.audit"):
        if set(args) != ({"manifest"} if op.endswith("inspect") else {"source"}):
            return deny("registry_reference_required")
        source = args.get("manifest", args.get("source"))
        if source != MANIFEST[chain]:
            return deny("chain_registry_mismatch")
    elif op == "orchard.observations.inspect":
        obs = args.get("observation_id")
        if not isinstance(obs, str) or not ID.fullmatch(obs):
            return deny("invalid_observation_id")
    return {
        "decision": "ALLOW_READ",
        "reason": "offline_allowlist_classification_only",
        "operation": op,
        "chain_id": chain,
        "executable": False,
        "warning": "NOT runtime authorization; no execution or authenticated identity",
    }


def main() -> int:
    try:
        obj = json.load(sys.stdin)
    except (ValueError, UnicodeError):
        print(json.dumps({"decision": "DENY", "reason": "invalid_json", "executable": False}))
        return 2
    output = evaluate(obj)
    print(json.dumps(output, sort_keys=True))
    return 0 if output["decision"] == "ALLOW_READ" else 1


if __name__ == "__main__":
    raise SystemExit(main())
