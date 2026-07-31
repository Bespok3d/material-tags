# ruff: noqa: PLR2004  Tests assert on literal counts/values by design.
"""Tests for Creality key handling.

The sector-key derivation is checked against a frozen UID->key vector (proving the
AES-ECB-of-tiled-UID math), and the hash validation's match branch is exercised by pointing
a baked hash at a throwaway key. The real Creality keys are never committed: the fixture key
below is obviously fake, and the real-key check runs only when the key is supplied by env var.
"""
import hashlib
import os

import creality_keys
import pytest
from aes_min import AesEcb
from creality_keys import derive_sector_key, key_matches, parse_key

SAMPLE_UID = bytes.fromhex("35b94a19")
FAKE_MASTER_HEX = "00112233445566778899aabbccddeeff"
FAKE_MASTER_KEY = bytes.fromhex(FAKE_MASTER_HEX)
REAL_MASTER_ENV = "B3D_CREALITY_MASTER_KEY"


def test_derive_matches_frozen_vector():
    key = derive_sector_key(SAMPLE_UID, FAKE_MASTER_KEY, AesEcb)
    assert bytes(key) == bytes.fromhex("34e178ac9ecb")
    assert len(key) == 6


def test_derive_is_deterministic():
    once = derive_sector_key(SAMPLE_UID, FAKE_MASTER_KEY, AesEcb)
    again = derive_sector_key(SAMPLE_UID, FAKE_MASTER_KEY, AesEcb)
    assert once == again


def test_derive_depends_on_uid():
    other = derive_sector_key(bytes.fromhex("04000000"), FAKE_MASTER_KEY, AesEcb)
    assert other != derive_sector_key(SAMPLE_UID, FAKE_MASTER_KEY, AesEcb)


def test_derive_rejects_empty_uid():
    with pytest.raises(ValueError):
        derive_sector_key(b"", FAKE_MASTER_KEY, AesEcb)


def test_parse_key_accepts_clean_hex():
    parsed = parse_key(FAKE_MASTER_HEX)
    assert parsed is not None
    assert len(parsed) == 16


def test_parse_key_strips_separators_and_case():
    spaced = parse_key(" 00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF ")
    assert spaced == FAKE_MASTER_KEY


@pytest.mark.skipif(REAL_MASTER_ENV not in os.environ, reason=f"{REAL_MASTER_ENV} not supplied")
def test_supplied_master_key_derives_the_verified_vector():
    supplied = parse_key(os.environ[REAL_MASTER_ENV])
    assert supplied is not None
    assert key_matches(supplied, creality_keys.MASTER_KEY_SHA256) is True
    derived = derive_sector_key(SAMPLE_UID, supplied, AesEcb)
    assert bytes(derived) == bytes.fromhex("239e7fe23653")


def test_parse_key_rejects_bad_input():
    assert parse_key("") is None
    assert parse_key("not-hex!!") is None
    assert parse_key("dead") is None
    assert parse_key("ab" * 17) is None


def test_key_matches_uses_baked_hash(monkeypatch):
    probe = bytes(range(16))
    monkeypatch.setattr(creality_keys, "MASTER_KEY_SHA256", hashlib.sha256(probe).hexdigest())
    assert key_matches(probe, creality_keys.MASTER_KEY_SHA256) is True
    assert key_matches(bytes(16), creality_keys.MASTER_KEY_SHA256) is False


def test_baked_hashes_are_sha256_hexdigests():
    for digest in (creality_keys.MASTER_KEY_SHA256, creality_keys.ENCRYPTION_KEY_SHA256):
        assert len(digest) == 64
        assert all(char in "0123456789abcdef" for char in digest)
