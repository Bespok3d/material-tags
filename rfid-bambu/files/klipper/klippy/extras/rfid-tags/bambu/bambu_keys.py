"""Bambu Mifare-Classic key derivation (pure, stdlib-only, unit-tested).

Clean-room from the PUBLIC Bambu-Research-Group writeup (BambuLabRfid.md): the 16
Mifare-Classic sector keys (key A) are derived per-tag with HKDF-SHA256 over the tag UID.

  PRK = HMAC-SHA256(salt = master key, ikm = tag UID)
  OKM = HKDF-Expand(PRK, info = b"RFID-A\\0", length = 96)
  sector key[i] = OKM[i*6 : i*6+6]

The master key is the same public constant on every consumer Bambu spool, but we do NOT
ship it: the user pastes it into the plugin ``key`` config (see the plugin doc), and we
ship only its SHA-256 hash to validate the paste. HKDF here is the RFC 5869 primitive, so
it is testable against the RFC vectors without any third-party crypto dependency.
"""
import hashlib
import hmac
import logging
from typing import Any, TypeGuard

SECTOR_COUNT = 16
KEY_LEN = 6
HKDF_INFO = b"RFID-A\0"
DERIVE_LENGTH = SECTOR_COUNT * KEY_LEN
MASTER_KEY_LEN = 16
# sha256 of the 16 master-key bytes; the key itself is user-supplied, never shipped.
MASTER_KEY_SHA256 = "19cc3c63cb8802668800c3b3bf3fee05b3c59bf59fc5fd256b68e868084ec304"

_log = logging.getLogger("bespok3d.bambu")

def _value_is_set(value: Any) -> TypeGuard[bytes]:
    if isinstance(value, bytes):
        return True
    return False

def hkdf_sha256(salt: bytes, ikm: bytes, info: bytes, length: int) -> bytes:
    """RFC 5869 HKDF (extract + expand) over SHA-256."""
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    okm = bytearray()
    block = b""
    counter = 1
    while len(okm) < length:
        block = hmac.new(prk, block + info + bytes([counter]), hashlib.sha256).digest()
        okm.extend(block)
        counter += 1
    return bytes(okm[:length])


def derive_sector_keys(uid: bytes, master_key: bytes) -> list[list[int]]:
    """Return the 16 six-byte crypto1 key-A values for a tag, as lists of ints."""
    okm = hkdf_sha256(bytes(master_key), bytes(uid), HKDF_INFO, DERIVE_LENGTH)
    return [list(okm[i * KEY_LEN:(i + 1) * KEY_LEN]) for i in range(SECTOR_COUNT)]


def parse_master_key(text: str) -> bytes | None:
    """Parse a user-pasted 32-hex master key, or None if it is not 16 valid hex bytes."""
    cleaned = \
        (text or "").strip().replace(":", "").replace(" ", "").replace(",", "").replace("0x","")
    try:
        _log.info("Trying to read BBL master key.")
        raw = bytes.fromhex(cleaned)
    except ValueError as e:
        _log.info("Failed to read bytes. %s", e)
        return None
    return raw if len(raw) == MASTER_KEY_LEN else None


def master_key_is_valid(master_key: bytes) -> bool:
    """The pasted key is the expected Bambu master key (checked by hash, not by value)."""
    assert _value_is_set(master_key)
    return hashlib.sha256(bytes(master_key)).hexdigest() == MASTER_KEY_SHA256
