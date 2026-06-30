# ruff: noqa: PLR2004  Tests assert on literal field values/offsets by design.
"""Regression tests for the Bambu decoder.

These build a block-indexed buffer at the public BambuLabRfid.md offsets and pin the
produced FILAMENT_INFO_STRUCT fields, including the float diameter and little-endian
temperatures, plus the too-short / empty guards.
"""
import struct

from bambu_fields import decode

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


def _put_text(buf: list[int], block: int, value: str) -> None:
    chunk = value.encode("ascii")
    buf[block * 16:block * 16 + len(chunk)] = list(chunk)


def _put_u16_le(buf: list[int], block: int, offset: int, value: int) -> None:
    buf[block * 16 + offset] = value & 0xFF
    buf[block * 16 + offset + 1] = (value >> 8) & 0xFF


def build_buffer() -> list[int]:
    buf = [0] * 128  # 2 sectors x 4 blocks x 16 bytes
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


def test_decode_does_not_mutate_template():
    decode(build_buffer(), TEMPLATE)
    assert TEMPLATE["VENDOR"] == "NONE"
    assert TEMPLATE["OFFICIAL"] is False
