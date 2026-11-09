"""Regression tests for the Bambu reader shell (rfid_tag_bambu).

The shell drives the hardware reader through the sectors of one Bambu tag and hands the blocks to
bambu_fields.decode. These tests replay a tag image built at the public Bambu offsets through a
fake reader that opens a sector only with the key derived from a THROWAWAY master key.
"""
from bambu import fm175xx_reader as fm_mod
from bambu.bambu_fields import BLOCK_BYTES
from bambu.bambu_keys import derive_sector_keys
from bambu.rfid_tag_bambu import M1_SAK, TRAY_UID_SECTOR, BambuReader
from test_bambu_fields import TRAY_UID, build_buffer

DUMMY_MASTER_KEY = bytes(range(16))


class FakeBambuTagReader:
    """Stands in for the fm175xx hardware reader, serving blocks from one tag image."""

    def __init__(self, tag_image, locked_sectors=()):
        self._tag_image = tag_image
        self._locked_sectors = locked_sectors
        self._sector_keys = derive_sector_keys(bytes(tag_image[0:4]), DUMMY_MASTER_KEY)

    def selected_card_sak(self):
        return M1_SAK

    def selected_card_uid(self):
        return list(self._tag_image[0:4])

    def reactivate_card(self):
        return fm_mod.FM175XX_OK

    def read_mifare_classic(self, auth_mode, sector, sector_key, uid, blocks):
        if not self._opens(auth_mode, sector, sector_key):
            return fm_mod.FM175XX_CARD_AUTH_ERR, None
        return fm_mod.FM175XX_OK, [
            tag_byte for block in blocks
            for tag_byte in self._tag_image[block * BLOCK_BYTES:(block + 1) * BLOCK_BYTES]
        ]

    def _opens(self, auth_mode, sector, sector_key):
        return (
            sector not in self._locked_sectors
            and auth_mode == fm_mod.FM175XX_M1_CARD_AUTH_MODE_A
            and list(sector_key) == self._sector_keys[sector]
        )


def _read_and_decode(tag_reader):
    bambu_reader = BambuReader(DUMMY_MASTER_KEY)
    _card_type, card_data, read_result = bambu_reader.read_hw_tag(tag_reader)
    assert read_result == fm_mod.FM175XX_OK
    _parse_result, info = bambu_reader.parse(card_data)
    return info


def test_a_read_tag_hands_on_the_tray_uid_as_the_spool_uid():
    info = _read_and_decode(FakeBambuTagReader(build_buffer()))
    assert info["MAIN_TYPE"] == "PLA"
    assert info["SPOOL_UID"] == TRAY_UID


def test_a_tray_uid_that_cannot_be_read_still_gives_the_filament_without_a_spool_uid():
    info = _read_and_decode(FakeBambuTagReader(build_buffer(), {TRAY_UID_SECTOR}))
    assert info["MAIN_TYPE"] == "PLA"
    assert "SPOOL_UID" not in info
