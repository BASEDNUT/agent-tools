#!/usr/bin/env python3
"""Dogfood: live ROOTSTOCK ecosystem snapshot for BASED NUT ops.

Uses the toolkit SDK (read-only) to produce the daily report Peanutoshi
actually consumes: ROOTSTOCK mainnet pools census + treasury workbench
balances. No fabricated USD: raw balances + metadata only.

Usage: python3 examples/ecosystem_report.py   (ROOTSTOCK_ARCHIVE_RPC overrides the archive gateway)
"""
import json
import os
import sys

from rootstock_tools import Toolchain

WORKBENCH = "0x135b208ac2480B0d876944416De16E7a3B9A1F65"
TREASURY_TOKENS = [
    "0xb8de15fb529d98c93c749de63c749d48d25a30df",  # NUT
    "0xAC130701aa31c284c36609E2489f150F419AD7AD",  # SNUT
    "0xBA5ED46e31F80dafF307cbf60bd422a6f62E3dd3",  # wNUT
    "0x3f2327221dd4f0bae660172606d6b288a1cf8ad9",  # PIPS
    "0x833589fCD5eDb6E6fa2CAb1B97BaD1B63f34E4d1",  # USDC
    "0x4200000000000000000000000000000000000006",  # WETH
]


def main():
    # Two read-only clients: default public RPC for live state reads;
    # archive gateway for deep historical event windows (public endpoints
    # wall archive ranges).
    kit = Toolchain()
    archive = Toolchain(rpc_overrides={8453: os.environ.get("ROOTSTOCK_ARCHIVE_RPC",
        "https://base.gateway.tenderly.co")})

    health = kit.run("rpc.get_health", {"chain_id": 8453})
    print(f"# ROOTSTOCK live snapshot — head {health['head_block']}")
    print()

    balances = kit.run("accounts.balances", {
        "chain_id": 8453, "wallet": WORKBENCH, "tokens": TREASURY_TOKENS})
    print("## Workbench balances (block-atomic)")
    for a in balances["assets"]:
        m = a["metadata"]
        print(f"- {m['symbol']}: raw {a['balance_raw']} ({m['decimals']}d)")
    print()

    # Known registration bands (baked-registry truth): newest pools first.
    bands = [
        (53119690, 53119705), (53118280, 53118295), (53119000, 53119015),
        (53083710, 53083720), (53082560, 53082945), (53077270, 53077280),
        (53076185, 53076200), (53014430, 53014455), (52908190, 52908210),
        (52707735, 52707835),
    ]
    pools = {}
    import time
    from rootstock_tools.rpc import ChainError
    for lo, hi in bands:
        for attempt in range(4):
            try:
                res = archive.run("pools.list", {"chain_id": 8453,
                                                 "from_block": lo, "to_block": hi,
                                                 "limit": 100})
                break
            except ChainError:
                if attempt == 3:
                    raise
                time.sleep(5 * (attempt + 1))  # provider rate-limit backoff
        for e in res["events"]:
            pools[e["pool"]] = e
        time.sleep(1.5)  # pace archive gateway
    print(f"## ROOTSTOCK pools discovered: {len(pools)}")
    for addr, e in sorted(pools.items(), key=lambda kv: kv[1]["block_number"]):
        print(f"- {addr} {e['pool_math_type']} @ block {e['block_number']}")


if __name__ == "__main__":
    main()
