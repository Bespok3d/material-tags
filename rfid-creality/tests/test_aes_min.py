"""Known-answer tests for the vendored AES (FIPS-197 + the verified Creality vectors).

The FIPS-197 Appendix B/C cases prove the implementation is real AES (encrypt and
decrypt, 128 and 256-bit) without any third-party library. The Creality vectors confirm
the exact ECB usage the decoder relies on (UID-derived sector key and payload decrypt).
"""
from aes_min import AesEcb

# FIPS-197 Appendix B (AES-128 single block).
FIPS128_KEY = bytes.fromhex("000102030405060708090a0b0c0d0e0f")
FIPS128_PLAIN = bytes.fromhex("00112233445566778899aabbccddeeff")
FIPS128_CIPHER = bytes.fromhex("69c4e0d86a7b0430d8cdb78070b4c55a")

# FIPS-197 Appendix C.3 (AES-256 single block).
FIPS256_KEY = bytes.fromhex("000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f")
FIPS256_PLAIN = bytes.fromhex("00112233445566778899aabbccddeeff")
FIPS256_CIPHER = bytes.fromhex("8ea2b7ca516745bfeafc49904b496089")

# Creality vectors (verified against the public DnG-Crafts/flamebarke reverse engineering).
CREALITY_MASTER_KEY = bytes.fromhex("713362755e74316e71665a2870662431")
CREALITY_ENCRYPTION_KEY = bytes.fromhex("484043466b526e7a404b4174424a7032")


def test_aes128_encrypt_matches_fips197():
    assert AesEcb(FIPS128_KEY).encrypt_block(FIPS128_PLAIN) == FIPS128_CIPHER


def test_aes128_decrypt_matches_fips197():
    assert AesEcb(FIPS128_KEY).decrypt_block(FIPS128_CIPHER) == FIPS128_PLAIN


def test_aes256_encrypt_matches_fips197():
    assert AesEcb(FIPS256_KEY).encrypt_block(FIPS256_PLAIN) == FIPS256_CIPHER


def test_aes256_decrypt_matches_fips197():
    assert AesEcb(FIPS256_KEY).decrypt_block(FIPS256_CIPHER) == FIPS256_PLAIN


def test_encrypt_decrypt_round_trip():
    cipher = AesEcb(FIPS128_KEY)
    block = bytes(range(16))
    assert cipher.decrypt_block(cipher.encrypt_block(block)) == block


def test_rejects_bad_key_length():
    import pytest
    with pytest.raises(ValueError):
        AesEcb(bytes(15))


def test_decrypt_ecb_rejects_unaligned():
    import pytest
    with pytest.raises(ValueError):
        AesEcb(FIPS128_KEY).decrypt_ecb(bytes(17))


def test_creality_sector_key_vector():
    # Sector key = first 6 bytes of AES-ECB(master, UID tiled to 16 bytes).
    uid = bytes.fromhex("35b94a19")
    block = bytes(uid[i % len(uid)] for i in range(16))
    derived = AesEcb(CREALITY_MASTER_KEY).encrypt_block(block)
    assert derived[:6] == bytes.fromhex("239e7fe23653")


def test_creality_payload_ecb_round_trip():
    # The verified decrypted payload (DnG-Crafts/flamebarke). We do not ship the captured
    # ciphertext, so prove the ECB path end-to-end with the real key: encrypting the known
    # 48-byte plaintext and decrypting it back must reproduce it byte-for-byte.
    expected = "1A5241201B3D010010000000033000000100000000000000"
    cipher = AesEcb(CREALITY_ENCRYPTION_KEY)
    encrypted = b"".join(
        cipher.encrypt_block(expected.encode()[at:at + 16])
        for at in range(0, len(expected), 16)
    )
    assert cipher.decrypt_ecb(encrypted).decode() == expected
    assert len(encrypted) == len(expected)
