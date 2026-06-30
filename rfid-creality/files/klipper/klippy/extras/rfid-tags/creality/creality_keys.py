"""Creality Mifare-Classic key handling (pure, stdlib-only, unit-tested).

Clean-room from the PUBLIC Creality reverse engineering (Bambu-Research-Group
CrealityRfid.md, DnG-Crafts/K2-RFID, flamebarke). Creality's CFS tag is a Mifare Classic
1K whose data lives in sector 1 (blocks 4-6) behind a per-tag crypto1 key, and whose
payload is a second AES layer. Two AES-128 keys are involved, BOTH user-supplied:

  * the master key derives the crypto1 sector key from the tag UID:
        sector_key = AES-128-ECB-encrypt(master_key, UID tiled to 16 bytes)[:6]
  * the encryption key decrypts the 48-byte block 4-6 payload (AES-128-ECB, no IV).

Both keys are published in the community sources, but we do NOT ship them: the user pastes
each into the plugin config, and we ship only their SHA-256 hashes to validate the paste.
The AES primitive is injected so this module stays pure and bare-importable for tests.
"""
import hashlib
from collections.abc import Callable
from typing import Protocol

MASTER_KEY_LEN = 16
SECTOR_KEY_LEN = 6
UID_BLOCK_LEN = 16
HEX_DIGITS = "0123456789abcdef"

# SHA-256 of the 16 master-key bytes and the 16 payload-key bytes; the keys themselves are
# user-supplied, never shipped. (Computed from the published community key material.)
MASTER_KEY_SHA256 = "e544d94feb16159bbd7bc227df1e283eca1f38f2bb2015dfcc6161b74473b5c2"
ENCRYPTION_KEY_SHA256 = "acec2106007458579ba522b25610b2cf509ae59d7879cb975f65c45228e5c9a1"


class BlockEncryptor(Protocol):
    def encrypt_block(self, block: bytes) -> bytes: ...


def parse_key(text: str) -> bytes | None:
    """Parse a user-pasted 32-hex AES key, or None if it is not 16 valid hex bytes."""
    cleaned = (text or "").strip().replace(":", "").replace(" ", "")
    try:
        raw = bytes.fromhex(cleaned)
    except ValueError:
        return None
    return raw if len(raw) == MASTER_KEY_LEN else None


def key_matches(key: bytes, expected_sha256: str) -> bool:
    """The pasted key is the expected key (checked by hash, not by value)."""
    return hashlib.sha256(bytes(key)).hexdigest() == expected_sha256


def derive_sector_key(
    uid: bytes, master_key: bytes, make_cipher: Callable[[bytes], BlockEncryptor],
) -> list[int]:
    """Return the 6-byte crypto1 sector key for a tag (AES-ECB of the tiled UID)."""
    if not uid:
        raise ValueError("UID must be non-empty")
    block = bytes(uid[index % len(uid)] for index in range(UID_BLOCK_LEN))
    cipher_text = make_cipher(bytes(master_key)).encrypt_block(block)
    return list(cipher_text[:SECTOR_KEY_LEN])
