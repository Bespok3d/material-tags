# ruff: noqa: PLR2004  Tests assert on literal field values/offsets by design.
"""Regression tests for the Bambu decoder.

These build a block-indexed buffer at the public BambuLabRfid.md offsets and pin the
produced FILAMENT_INFO_STRUCT fields, including the float diameter, little-endian
temperatures and the block-16 second colour, plus the too-short / empty guards.
"""
import struct

from bambu_fields import (
    BLOCK_BYTES,
    BLOCK_COLOR,
    BLOCK_EXTRA_COLOR,
    BLOCK_TRAY_UID,
    MIN_BUFFER_LEN,
    TRAY_UID_LEN,
    decode,
)

# Mirrors klippy/extras/filament_protocol.FILAMENT_INFO_STRUCT (the downstream contract).
TEMPLATE = {
    "VERSION": 0, "VENDOR": "NONE", "MANUFACTURER": "NONE", "MAIN_TYPE": "NONE",
    "SUB_TYPE": "NONE", "TRAY": 0, "ALPHA": 0xFF, "MULTI_MODE": 0, "COLOR_NUMS": 1,
    "ARGB_COLOR": 0xFFFFFFFF, "RGB_1": 0xFFFFFF, "RGB_2": 0xFFFFFF, "RGB_3": 0xFFFFFF,
    "RGB_4": 0xFFFFFF, "RGB_5": 0xFFFFFF, "DIAMETER": 0, "WEIGHT": 0, "LENGTH": 0,
    "DRYING_TEMP": 0, "DRYING_TIME": 0, "HOTEND_MAX_TEMP": 0, "HOTEND_MIN_TEMP": 0,
    "BED_TYPE": 0, "BED_TEMP": 0, "FIRST_LAYER_TEMP": 0, "OTHER_LAYER_TEMP": 0,
    "SKU": 0, "MF_DATE": "19700101", "RSA_KEY_VERSION": 0, "OFFICIAL": False, "CARD_UID": 0,
}

UID = [0x04, 0xA1, 0xB2, 0xC3]
TRAY_UID = list(range(0x60, 0x70))
TRAY_UID_START = BLOCK_TRAY_UID * BLOCK_BYTES

# Blocks 5 and 16 of a real two-colour spool, PLA Silk Multi-Color Velvet Eclipse (Black-Red),
# tag 548D23D0 in queengooborg/Bambu-Lab-RFID-Library: black first, red A34342 second.
VELVET_ECLIPSE_COLOR_BLOCK = bytes.fromhex("000000FFE80300000000E03F00000000")
VELVET_ECLIPSE_EXTRA_COLOR_BLOCK = bytes.fromhex("02000200FF4243A30000000000000000")
COLOR_START = BLOCK_COLOR * BLOCK_BYTES
EXTRA_COLOR_START = BLOCK_EXTRA_COLOR * BLOCK_BYTES


def _put_text(buf: list[int], block: int, value: str) -> None:
    chunk = value.encode("ascii")
    buf[block * 16:block * 16 + len(chunk)] = list(chunk)


def _put_u16_le(buf: list[int], block: int, offset: int, value: int) -> None:
    buf[block * 16 + offset] = value & 0xFF
    buf[block * 16 + offset + 1] = (value >> 8) & 0xFF


def build_buffer() -> list[int]:
    buf = [0] * (BLOCK_EXTRA_COLOR + 1) * BLOCK_BYTES  # every block through the extra colour
    buf[0:4] = UID                                  # block 0: UID
    _put_text(buf, 2, "PLA")                        # block 2: filament type
    _put_text(buf, 4, "PLA Basic")                  # block 4: detailed type
    buf[80:84] = [0xFF, 0x80, 0x00, 0xFF]           # block 5: RGBA (orange, opaque)
    _put_u16_le(buf, 5, 4, 1000)                    # block 5+4: weight (g)
    buf[88:92] = list(struct.pack("<f", 1.75))      # block 5+8: diameter float32
    _put_u16_le(buf, 6, 0, 55)                      # block 6: drying temp
    _put_u16_le(buf, 6, 2, 8)                       # block 6+2: drying time
    _put_u16_le(buf, 6, 4, 1)                       # block 6+4: bed type
    _put_u16_le(buf, 6, 6, 60)                      # block 6+6: bed temp
    _put_u16_le(buf, 6, 8, 230)                     # block 6+8: max hotend
    _put_u16_le(buf, 6, 10, 190)                    # block 6+10: min hotend
    buf[TRAY_UID_START:TRAY_UID_START + TRAY_UID_LEN] = TRAY_UID  # block 9: tray UID
    return buf


def build_two_color_buffer() -> list[int]:
    buf = build_buffer()
    buf[COLOR_START:COLOR_START + BLOCK_BYTES] = list(VELVET_ECLIPSE_COLOR_BLOCK)
    buf[EXTRA_COLOR_START:EXTRA_COLOR_START + BLOCK_BYTES] = list(VELVET_ECLIPSE_EXTRA_COLOR_BLOCK)
    return buf


def test_decode_full_tag():
    info = decode(build_buffer(), dict(TEMPLATE))
    assert info is not None
    assert info["VENDOR"] == "Bambu Lab"
    assert info["MANUFACTURER"] == "Bambu Lab"
    assert info["MAIN_TYPE"] == "PLA"
    assert info["SUB_TYPE"] == "Basic"
    assert info["OFFICIAL"] is True
    assert info["CARD_UID"] == UID


def test_both_tags_of_one_spool_carry_the_same_spool_uid():
    first_tag_info = decode(build_buffer(), dict(TEMPLATE))
    opposite_tag_buffer = build_buffer()
    opposite_tag_buffer[0:4] = [0x04, 0x99, 0x88, 0x77]
    opposite_tag_info = decode(opposite_tag_buffer, dict(TEMPLATE))
    assert first_tag_info["SPOOL_UID"] == opposite_tag_info["SPOOL_UID"] == TRAY_UID
    assert first_tag_info["CARD_UID"] != opposite_tag_info["CARD_UID"]


def test_a_read_that_stops_before_the_tray_uid_keeps_the_filament_without_a_spool_uid():
    info = decode(build_buffer()[:MIN_BUFFER_LEN], dict(TEMPLATE))
    assert info["MAIN_TYPE"] == "PLA"
    assert info["HOTEND_MIN_TEMP"] == 190
    assert "SPOOL_UID" not in info


def test_a_blank_tray_uid_gives_no_spool_uid():
    buf = build_buffer()
    buf[TRAY_UID_START:TRAY_UID_START + TRAY_UID_LEN] = [0] * TRAY_UID_LEN
    info = decode(buf, dict(TEMPLATE))
    assert info["MAIN_TYPE"] == "PLA"
    assert "SPOOL_UID" not in info


def test_decode_color():
    info = decode(build_buffer(), dict(TEMPLATE))
    assert info["RGB_1"] == 0xFF8000
    assert info["ALPHA"] == 0xFF
    assert info["ARGB_COLOR"] == 0xFFFF8000
    assert info["COLOR_NUMS"] == 1


def test_decode_dimensions():
    info = decode(build_buffer(), dict(TEMPLATE))
    assert info["WEIGHT"] == 1000
    assert info["DIAMETER"] == 175  # 1.75 mm -> hundredths


def test_decode_temperatures():
    info = decode(build_buffer(), dict(TEMPLATE))
    assert info["DRYING_TEMP"] == 55
    assert info["DRYING_TIME"] == 8
    assert info["BED_TYPE"] == 1
    assert info["BED_TEMP"] == 60
    assert info["HOTEND_MAX_TEMP"] == 230
    assert info["HOTEND_MIN_TEMP"] == 190
    assert info["FIRST_LAYER_TEMP"] == 190
    assert info["OTHER_LAYER_TEMP"] == 190


def test_subtype_is_detailed_type_when_no_main_prefix():
    buf = build_buffer()
    _put_text(buf, 4, "Matte")  # detailed type without the "PLA" prefix
    # block 4 keeps stale "PLA Basic" tail bytes; overwrite the rest to clear them
    buf[4 * 16 + 5:4 * 16 + 16] = [0] * 11
    info = decode(buf, dict(TEMPLATE))
    assert info["SUB_TYPE"] == "Matte"


def test_decode_rejects_short_or_missing_buffer():
    assert decode(None, dict(TEMPLATE)) is None
    assert decode([0] * 16, dict(TEMPLATE)) is None  # only one block: too short
    assert decode(build_buffer()[:MIN_BUFFER_LEN - 1], dict(TEMPLATE)) is None


def test_decode_does_not_mutate_template():
    decode(build_buffer(), TEMPLATE)
    assert TEMPLATE["VENDOR"] == "NONE"
    assert TEMPLATE["OFFICIAL"] is False


def test_decode_second_color_of_a_real_two_color_spool():
    info = decode(build_two_color_buffer(), dict(TEMPLATE))
    assert info["COLOR_NUMS"] == 2
    assert info["RGB_1"] == 0x000000
    assert info["RGB_2"] == 0xA34342
    assert info["RGB_3"] == 0xFFFFFF
    assert info["ARGB_COLOR"] == 0xFF000000
    assert info["WEIGHT"] == 1000
    assert info["DIAMETER"] == 175


def test_block_16_without_the_color_format_keeps_one_color():
    buf = build_two_color_buffer()
    buf[EXTRA_COLOR_START:EXTRA_COLOR_START + 2] = [0x00, 0x00]
    info = decode(buf, dict(TEMPLATE))
    assert info["COLOR_NUMS"] == 1
    assert info["RGB_2"] == 0xFFFFFF


def test_a_color_count_of_one_keeps_one_color():
    buf = build_two_color_buffer()
    buf[EXTRA_COLOR_START + 2] = 0x01
    info = decode(buf, dict(TEMPLATE))
    assert info["COLOR_NUMS"] == 1


def test_a_read_that_stops_before_block_16_keeps_one_color():
    info = decode(build_two_color_buffer()[:EXTRA_COLOR_START], dict(TEMPLATE))
    assert info["COLOR_NUMS"] == 1
    assert info["RGB_2"] == 0xFFFFFF
