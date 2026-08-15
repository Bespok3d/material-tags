"""Registers the QIDI Mifare-Classic decoder with the RFID hub.

Klipper loads this module for the ``[rfid_tag_qidi]`` config section. QIDI spools are Mifare
Classic cards sharing Snapmaker's M1 SAK (0x08), so the rfid-ntag reader routes a 0x08 card
the Snapmaker key could not open to *claim handlers* like this one. QIDI leaves its tags on
the Mifare factory default key, so there is no key for anyone to supply and none to ship:
this shell re-selects the card, reads sector 1 with the default key, and decodes the block
(``qidi_fields``).

A card that is not QIDI-shaped is handed back as a read error rather than a bad decode, so
the reader carries on to the next vendor handler and finally to its UID-only fallback.

Thin relative-import shell: the decode lives in the pure, unit-tested ``qidi_fields``
sibling. ``filament_protocol`` and ``fm175xx_reader`` resolve as flat ``klippy.extras``
siblings at runtime (placed by rfid-ntag).
"""
import logging

from . import filament_protocol, qidi_fields
from . import fm175xx_reader as fm_mod

_log = logging.getLogger("bespok3d.qidi")

M1_SAK = 0x08
QIDI_CARD_TYPE = 0x91  # distinct card type so the dedicated QIDI parser owns its data
QIDI_SECTOR = 1
QIDI_PAYLOAD_BLOCK = 4
MIFARE_DEFAULT_KEY = [0xFF] * 6
UID_LEN = 4


def _report_unmapped_codes(block):
    """A spool whose codes are not in the tables reads as UNKNOWN or plain white, which looks
    like a broken tag. Say the codes out loud so the tables can be extended from a real spool."""
    material_code = block[qidi_fields.MATERIAL_INDEX]
    colour_code = block[qidi_fields.COLOR_INDEX]
    unmapped = []
    if material_code not in qidi_fields.MATERIALS:
        unmapped.append(f"material {material_code:#04x}")
    if colour_code not in qidi_fields.COLORS:
        unmapped.append(f"colour {colour_code:#04x}")
    if unmapped:
        _log.warning("QIDI: tag read, code not in the tables: %s", ", ".join(unmapped))


class QidiReader:
    card_type = QIDI_CARD_TYPE

    def claims(self, reader):
        return reader.selected_card_sak() == M1_SAK

    def read_hw_tag(self, reader):
        uid = list(reader.selected_card_uid()[0:UID_LEN])
        if reader.reactivate_card() != fm_mod.FM175XX_OK:
            _log.error("QIDI: could not re-select card after stock read")
            return QIDI_CARD_TYPE, None, fm_mod.FM175XX_CARD_READ_ERR
        err, data = reader.read_mifare_classic(
            fm_mod.FM175XX_M1_CARD_AUTH_MODE_A, QIDI_SECTOR, MIFARE_DEFAULT_KEY, uid,
            [QIDI_PAYLOAD_BLOCK])
        if err != fm_mod.FM175XX_OK or not data:
            _log.info("QIDI: sector %d did not open with the default key", QIDI_SECTOR)
            return QIDI_CARD_TYPE, None, err
        block = bytes(data)
        if not qidi_fields.looks_like_qidi(block):
            _log.info("QIDI: default key opened the card but the block is not QIDI-shaped")
            return QIDI_CARD_TYPE, None, fm_mod.FM175XX_CARD_READ_ERR
        return QIDI_CARD_TYPE, (uid, block), fm_mod.FM175XX_OK

    def parse(self, card_data):
        uid, block = card_data
        info = qidi_fields.decode(block, uid, dict(filament_protocol.FILAMENT_INFO_STRUCT))
        if info is None:
            return filament_protocol.FILAMENT_PROTO_ERR, None
        _report_unmapped_codes(block)
        _log.info("QIDI: type=%s sub=%s color=%06X", info.get("MAIN_TYPE"),
                  info.get("SUB_TYPE"), info.get("RGB_1", 0))
        return filament_protocol.FILAMENT_PROTO_OK, info


class RfidTagQidi:
    def __init__(self, config):
        self.printer = config.get_printer()
        self._reader = QidiReader()
        self.printer.register_event_handler("klippy:ready", self._handle_ready)

    def _handle_ready(self):
        hub = self.printer.lookup_object("bespok3d_rfid", None)
        if hub is None:
            _log.warning("bespok3d_rfid not loaded: QIDI support inactive")
            return
        hub.register_hw_reader(self._reader)
        _log.info("ready: QIDI reader registered")


def load_config(config):
    return RfidTagQidi(config)
