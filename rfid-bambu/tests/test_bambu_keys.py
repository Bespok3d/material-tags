# ruff: noqa: PLR2004  Tests assert on literal counts/values by design.
"""Tests for Bambu key derivation.

The HKDF primitive is checked against the RFC 5869 SHA-256 test vector (so the crypto is
provably correct without a third-party library), and the sector-key wiring is checked
against that primitive. The real Bambu master key is never committed; the validation's
match branch is exercised by pointing the baked hash at a throwaway key via monkeypatch.
"""
import hashlib

import bambu_keys
from bambu_keys import (
    derive_sector_keys,
    hkdf_sha256,
    master_key_is_valid,
    parse_master_key,
)

# RFC 5869, Appendix A, Test Case 1 (HKDF SHA-256).
RFC_IKM = bytes.fromhex("0b" * 22)
RFC_SALT = bytes.fromhex("000102030405060708090a0b0c")
RFC_INFO = bytes.fromhex("f0f1f2f3f4f5f6f7f8f9")
RFC_OKM = bytes.fromhex(
    "3cb25f25faacd57a90434f64d0362f2a"
    "2d2d0a90cf1a5a4c5db02d56ecc4c5bf"
    "34007208d5b887185865"
)

SAMPLE_UID = bytes([0x04, 0xA1, 0xB2, 0xC3])
DUMMY_MASTER = bytes(range(16))  # NOT the Bambu key; only exercises the wiring


def test_hkdf_matches_rfc5869_vector():
    assert hkdf_sha256(RFC_SALT, RFC_IKM, RFC_INFO, 42) == RFC_OKM


def test_derive_returns_sixteen_six_byte_keys():
    keys = derive_sector_keys(SAMPLE_UID, DUMMY_MASTER)
    assert len(keys) == 16
    assert all(len(key) == 6 for key in keys)
    assert all(0 <= byte <= 255 for key in keys for byte in key)


def test_derive_is_deterministic():
    once = derive_sector_keys(SAMPLE_UID, DUMMY_MASTER)
    again = derive_sector_keys(SAMPLE_UID, DUMMY_MASTER)
    assert once == again


def test_derive_depends_on_uid():
    other_uid = bytes([0x04, 0x00, 0x00, 0x00])
    sample = derive_sector_keys(SAMPLE_UID, DUMMY_MASTER)
    other = derive_sector_keys(other_uid, DUMMY_MASTER)
    assert sample != other


def test_derive_wires_salt_uid_ikm_master():
    # The spec: PRK = HMAC(salt=UID, ikm=master); keys are the expand output split by six.
    okm = hkdf_sha256(DUMMY_MASTER, SAMPLE_UID, bambu_keys.HKDF_INFO, bambu_keys.DERIVE_LENGTH)
    expected = [list(okm[i * 6:(i + 1) * 6]) for i in range(16)]
    assert derive_sector_keys(SAMPLE_UID, DUMMY_MASTER) == expected


def test_parse_master_key_accepts_clean_hex():
    parsed = parse_master_key("00112233445566778899aabbccddeeff")
    assert parsed is not None
    assert len(parsed) == 16


def test_parse_master_key_strips_separators_and_case():
    spaced = parse_master_key(" 00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF ")
    tight = parse_master_key("00112233445566778899aabbccddeeff")
    assert spaced == tight


def test_parse_master_key_rejects_bad_input():
    assert parse_master_key("") is None
    assert parse_master_key("not-hex-at-all!!") is None
    assert parse_master_key("dead") is None  # too short
    assert parse_master_key("ab" * 17) is None  # too long


def test_validation_matches_baked_hash(monkeypatch):
    probe = bytes(range(16))
    monkeypatch.setattr(bambu_keys, "MASTER_KEY_SHA256", hashlib.sha256(probe).hexdigest())
    assert master_key_is_valid(probe) is True
    assert master_key_is_valid(bytes(16)) is False


def test_baked_hash_is_a_sha256_hexdigest():
    assert len(bambu_keys.MASTER_KEY_SHA256) == 64
    assert all(char in "0123456789abcdef" for char in bambu_keys.MASTER_KEY_SHA256)
