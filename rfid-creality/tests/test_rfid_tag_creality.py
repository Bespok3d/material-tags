"""Regression tests for the Creality reader shell (rfid_tag_creality).

The shell is a thin relative-import wrapper: it derives the sector key, drives the hardware
reader, decrypts, and hands the payload to creality_fields.decode. These tests exercise that
wiring end to end against a FakeReader that replays a captured tag payload.

KEYS: this file uses THROWAWAY dummy keys, never Creality's real community keys. Bespok3d
deliberately does not distribute the real keys (the plugin ships only their SHA-256 hashes and
the user pastes the public values). That policy would be undermined if the real keys sat in a
test file in this public repo, so the fixture below is the known filament plaintext re-encrypted
under a dummy key (bytes 0x00..0x0f). The decode plaintext itself is not secret: it is ordinary
filament fields (type id, weight, color) read off a spool. Only the two AES keys are withheld,
and they are absent here. The sector-key derivation test uses a dummy master key (0x10..0x1f);
it proves the tiling + AES wiring, not any real key value.
"""
from creality import aes_min, creality_keys, filament_protocol
from creality import fm175xx_reader as fm_mod
from creality.rfid_tag_creality import CrealityReader

# Real captured UID (not secret) and the known decoded plaintext.
REAL_UID = [0x40, 0x24, 0xC2, 0x6A]
# Fixture cipher = the known plaintext re-encrypted under DUMMY_PAYLOAD_KEY (see module doc).
FIXTURE_CIPHER48 = bytes.fromhex(
    "0647e9392cf454e8df481dd3cf19631e"
    "73ccec97dfd4a07db869a2e12d85394f"
    "9a12cf3b2dbd186e44d9f1b961bf41e6"
)
DUMMY_MASTER_KEY = bytes(range(16, 32))   # 0x10..0x1f, NOT Creality's master key
DUMMY_PAYLOAD_KEY = bytes(range(16))      # 0x00..0x0f, NOT Creality's payload key
# Sector key derived from DUMMY_MASTER_KEY + REAL_UID (proves tiling + AES, not a real value).
EXPECTED_DUMMY_SECTOR_KEY = "9845145718c8"

M1_SAK = 0x08


class FakeReader:
    """Stands in for the fm175xx hardware reader, replaying one captured payload."""

    def __init__(self, sak=M1_SAK, uid=None, cipher=FIXTURE_CIPHER48,
                 reactivate=fm_mod.FM175XX_OK, read_err=fm_mod.FM175XX_OK):
        self._sak = sak
        self._uid = uid if uid is not None else list(REAL_UID)
        self._cipher = cipher
        self._reactivate = reactivate
        self._read_err = read_err
        self.auth_mode_seen = None

    def selected_card_sak(self):
        return self._sak

    def selected_card_uid(self):
        return list(self._uid)

    def reactivate_card(self):
        return self._reactivate

    def read_mifare_classic(self, auth_mode, sector, sector_key, uid, blocks):
        self.auth_mode_seen = auth_mode
        if self._read_err != fm_mod.FM175XX_OK:
            return self._read_err, None
        return fm_mod.FM175XX_OK, list(self._cipher)


def _reader_with_keys():
    return CrealityReader(DUMMY_MASTER_KEY, DUMMY_PAYLOAD_KEY)


def test_claims_only_with_keys_and_m1_sak():
    assert _reader_with_keys().claims(FakeReader()) is True


def test_does_not_claim_without_keys():
    assert CrealityReader(None, None).claims(FakeReader()) is False


def test_does_not_claim_on_wrong_sak():
    assert _reader_with_keys().claims(FakeReader(sak=0x04)) is False


def test_read_hw_tag_returns_uid_and_cipher():
    reader = _reader_with_keys()
    card_type, payload, err = reader.read_hw_tag(FakeReader())
    assert err == fm_mod.FM175XX_OK
    assert card_type == reader.card_type
    uid, cipher = payload
    assert uid == REAL_UID
    assert cipher == FIXTURE_CIPHER48


def test_read_hw_tag_derives_expected_sector_key():
    # The FakeReader records nothing about the key, so assert the derivation directly: the
    # dummy master + real UID must produce the known dummy sector key (tiling + AES wiring).
    sk = creality_keys.derive_sector_key(bytes(REAL_UID), DUMMY_MASTER_KEY, aes_min.AesEcb)
    assert bytes(sk).hex() == EXPECTED_DUMMY_SECTOR_KEY


def test_read_hw_tag_propagates_reactivate_failure():
    reader = _reader_with_keys()
    _card_type, payload, err = reader.read_hw_tag(
        FakeReader(reactivate=fm_mod.FM175XX_CARD_READ_ERR))
    assert payload is None
    assert err == fm_mod.FM175XX_CARD_READ_ERR


def test_read_hw_tag_propagates_read_failure():
    reader = _reader_with_keys()
    _card_type, payload, err = reader.read_hw_tag(
        FakeReader(read_err=fm_mod.FM175XX_CARD_READ_ERR))
    assert payload is None
    assert err == fm_mod.FM175XX_CARD_READ_ERR


def test_full_parse_decodes_confirmed_fields():
    reader = _reader_with_keys()
    _card_type, payload, _err = reader.read_hw_tag(FakeReader())
    status, info = reader.parse(payload)
    assert status == filament_protocol.FILAMENT_PROTO_OK
    assert info["VENDOR"] == "Creality"
    assert info["MANUFACTURER"] == "Creality"
    assert info["SKU"] == "01001"          # Creality slicer: filament_id 01001 = Hyper PLA
    assert info["MAIN_TYPE"] == "PLA"      # resolved from id via creality_types table
    assert info["DIAMETER"] == 1.75        # filled from id (Creality slicer profiles)
    assert info["HOTEND_MIN_TEMP"] == 190
    assert info["HOTEND_MAX_TEMP"] == 240
    assert info["WEIGHT"] == 1000          # physical 1kg spool
    assert info["CARD_UID"] == REAL_UID
    assert info["OFFICIAL"] is True


def test_color_is_present_and_opaque():
    reader = _reader_with_keys()
    _card_type, payload, _err = reader.read_hw_tag(FakeReader())
    _status, info = reader.parse(payload)
    assert info["COLOR_NUMS"] == 1
    assert info["ALPHA"] == 0xFF
    assert info["ARGB_COLOR"] >> 24 == 0xFF


def test_parse_with_wrong_payload_key_fails_cleanly():
    # A different-but-valid-length key decrypts to non-payload bytes; decoder rejects cleanly.
    wrong = CrealityReader(DUMMY_MASTER_KEY, bytes([0xAA] * 16))
    _card_type, payload, _err = wrong.read_hw_tag(FakeReader())
    status, info = wrong.parse(payload)
    assert status == filament_protocol.FILAMENT_PROTO_ERR
    assert info is None
