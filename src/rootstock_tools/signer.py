"""Environment-key transaction signer. The private key never appears in any output.

Signing requires eth-account (optional [execute] extra); the read-only core
remains stdlib-only.
"""
from __future__ import annotations
import os


class SignerError(ValueError):
    pass


class Signer:
    """Signs EIP-1559 transactions from a hex private key supplied at construction.

    The key is held only in the underlying account object and is never exposed
    through repr(), str(), or any error message.
    """

    def __init__(self, key: str):
        try:
            from eth_account import Account
        except ImportError as exc:
            raise SignerError(
                "Signing requires the optional [execute] extra: "
                "pip install '.[execute]' (eth-account)") from exc
        if not isinstance(key, str):
            raise SignerError("Private key must be a hex string")
        k = key[2:] if key.startswith("0x") else key
        if len(k) != 64:
            raise SignerError("Private key must be a 32-byte hex string (64 hex chars, 0x optional)")
        try:
            int(k, 16)
        except ValueError as exc:
            raise SignerError("Private key must be hexadecimal") from exc
        self._account = Account.from_key("0x" + k)
        self.address = self._account.address

    def __repr__(self):
        return f"Signer(address={self.address})"

    __str__ = __repr__

    @classmethod
    def from_env(cls, var: str = "ROOTSTOCK_SIGNER_KEY") -> "Signer":
        key = os.environ.get(var)
        if not key:
            raise SignerError(f"Signing key environment variable {var} is not set")
        return cls(key)

    def sign_transaction(self, tx: dict) -> str:
        """Sign an EIP-1559 transaction. chainId is mandatory (EIP-155 replay safety)."""
        if not isinstance(tx, dict):
            raise SignerError("Transaction must be a dict")
        if "chainId" not in tx or "nonce" not in tx or "gas" not in tx:
            raise SignerError("Transaction requires chainId, nonce and gas")
        # eth-account requires checksummed addresses; normalize case-insensitive input.
        from eth_utils import to_checksum_address
        tx = dict(tx)
        if isinstance(tx.get("to"), str) and tx["to"]:
            tx["to"] = to_checksum_address(tx["to"])
        signed = self._account.sign_transaction(tx)
        raw = signed.raw_transaction.hex()
        return raw if raw.startswith("0x") else "0x" + raw
