"""Registers the Creality Mifare-Classic decoder with the RFID hub.

Klipper loads this module for the ``[rfid_tag_creality]`` config section. Creality CFS
spools are Mifare-Classic cards that share Snapmaker's M1 SAK (0x08), so the rfid-ntag
reader routes a 0x08 card the Snapmaker key could not open to *claim handlers* like this
one. This shell claims such a card, derives the crypto1 sector key from the tag UID + the
user-supplied master key (``creality_keys`` over the vendored ``aes_min``), re-selects the
card, reads blocks 4-6 with that key (loaded as Key B), AES-ECB-decrypts the payload with
the user-supplied encryption key, and decodes it (``creality_fields``). With no/invalid
keys it does not claim, so the reader's UID-only fallback carries.

Thin relative-import shell: the AES, key derivation, and decode live in the pure,
unit-tested ``aes_min`` / ``creality_keys`` / ``creality_fields`` siblings. ``filament_protocol``
and ``fm175xx_reader`` resolve as flat ``klippy.extras`` siblings at runtime (placed by
rfid-ntag).
"""
import logging

from . import aes_min, creality_fields, creality_keys, filament_protocol
from . import fm175xx_reader as fm_mod

_log = logging.getLogger("bespok3d.creality")

M1_SAK = 0x08
CREALITY_CARD_TYPE = 0xC0  # distinct card type so the dedicated Creality parser owns its data
CREALITY_SECTOR = 1
CREALITY_BLOCKS = (4, 5, 6)
PAYLOAD_BYTES = 48
UID_LEN = 4


class CrealityReader:
    card_type = CREALITY_CARD_TYPE

    def __init__(self, master_key, encryption_key):
        self._master_key = master_key
        self._encryption_key = encryption_key

    @property
    def has_keys(self):
        return self._master_key is not None and self._encryption_key is not None

    def claims(self, reader):
        return self.has_keys and reader.selected_card_sak() == M1_SAK

    def read_hw_tag(self, reader):
        uid = list(reader.selected_card_uid()[0:UID_LEN])
        sector_key = creality_keys.derive_sector_key(bytes(uid), self._master_key, aes_min.AesEcb)
        if reader.reactivate_card() != fm_mod.FM175XX_OK:
            _log.error("Creality: could not re-select card after stock read")
            return CREALITY_CARD_TYPE, None, fm_mod.FM175XX_CARD_READ_ERR
        err, data = reader.read_mifare_classic(
            fm_mod.FM175XX_M1_CARD_AUTH_MODE_B, CREALITY_SECTOR, sector_key,
            uid, list(CREALITY_BLOCKS))
        if err != fm_mod.FM175XX_OK or not data:
            _log.warning("Creality: sector %d auth/read failed (err=%s)", CREALITY_SECTOR, err)
            return CREALITY_CARD_TYPE, None, err
        return CREALITY_CARD_TYPE, (uid, bytes(data)), fm_mod.FM175XX_OK

    def parse(self, card_data):
        uid, cipher = card_data
        plaintext = aes_min.AesEcb(self._encryption_key).decrypt_ecb(cipher[:PAYLOAD_BYTES])
        text = plaintext.decode("ascii", "ignore")
        info = creality_fields.decode(text, uid, dict(filament_protocol.FILAMENT_INFO_STRUCT))
        if info is None:
            _log.error("Creality: payload did not decode (wrong key?)")
            return filament_protocol.FILAMENT_PROTO_ERR, None
        _log.info("Creality: weight=%s color=%06X date=%s",
                  info.get("WEIGHT"), info.get("RGB_1", 0), info.get("MF_DATE"))
        return filament_protocol.FILAMENT_PROTO_OK, info


class RfidTagCreality:
    def __init__(self, config):
        self.printer = config.get_printer()
        master_key = self._load_key(config, "key", creality_keys.MASTER_KEY_SHA256, "master")
        encryption_key = self._load_key(
            config, "encryption_key", creality_keys.ENCRYPTION_KEY_SHA256, "encryption")
        self._reader = CrealityReader(master_key, encryption_key)
        self.printer.register_event_handler("klippy:ready", self._handle_ready)

    def _load_key(self, config, option, expected_sha256, label):
        key = creality_keys.parse_key(config.get(option, ""))
        if key is not None and not creality_keys.key_matches(key, expected_sha256):
            _log.warning("Creality: configured %s key is not expected; UID-only mode", label)
            return None
        return key

    def _handle_ready(self):
        hub = self.printer.lookup_object("bespok3d_rfid", None)
        if hub is None:
            _log.warning("bespok3d_rfid not loaded: Creality support inactive")
            return
        hub.register_hw_reader(self._reader)
        _log.info("ready: Creality reader registered (keys configured: %s)",
                  self._reader.has_keys)


def load_config(config):
    return RfidTagCreality(config)
