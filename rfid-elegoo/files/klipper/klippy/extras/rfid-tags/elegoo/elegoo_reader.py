"""HW reader for Elegoo (Feiju) filament tags - does what OpenRFID does (page read).

The Feiju Elegoo chip presents a SAK the stock NTAG reader (SAK 0x04) does not claim, so the
U1 never page-reads it. This reader claims EVERY SAK except the stock NTAG (0x04) and Mifare
M1 (0x08) ones, logs the actual SAK the chip presents, then does a plain NTAG/Type-2 page read
(cmd 0x30) like OpenRFID - all via the EXISTING reader delegate, so this is a PLUGIN-ONLY add.
The broad SAK claim is diagnostic: once the real Feiju SAK is known it can be narrowed.
"""
import logging

from . import fm175xx_reader as fm_mod

_log = logging.getLogger("bespok3d.elegoo_reader")

ELEGOO_CARD_TYPE = getattr(fm_mod, "FM175XX_MIFARE_CARD_TYPE_NTAG", 0x00)
PAGE_COUNT = 32
HEX_PREVIEW_BYTES = 128
STOCK_NTAG_SAK = 0x04
MIFARE_M1_SAK = 0x08
SAK_SPACE = 256

# Claim every SAK except the stock NTAG and M1 readers' so the Feiju chip - whatever SAK it
# presents - reaches this handler.
CANDIDATE_SAKS = tuple(
    sak for sak in range(SAK_SPACE) if sak not in (STOCK_NTAG_SAK, MIFARE_M1_SAK)
)


def _selected_sak(reader: object) -> int:
    picc = getattr(reader, "_Fm175xxReader__picc_a", None)
    if picc is None:
        return -1
    return picc.SAK[0]


class ElegooReader:
    card_type = ELEGOO_CARD_TYPE

    def read_hw_tag(self, reader):
        _log.info("elegoo read_hw_tag fired: SAK=0x%02X", _selected_sak(reader))
        err, data = reader.read_nfc_type2_pages(0, PAGE_COUNT)
        byte_count = len(data) if data else 0
        _log.info("elegoo read_hw_tag: err=%d bytes=%d", err, byte_count)
        if data:
            preview = " ".join(format(byte, "02x") for byte in data[:HEX_PREVIEW_BYTES])
            _log.info("elegoo raw pages 0+%d: %s", PAGE_COUNT, preview)
        if err == fm_mod.FM175XX_OK and data:
            return ELEGOO_CARD_TYPE, data, fm_mod.FM175XX_OK
        return ELEGOO_CARD_TYPE, None, fm_mod.FM175XX_CARD_READ_ERR
