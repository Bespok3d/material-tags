# ruff: noqa: PLR2004  Tests assert on literal field values/offsets by design.
"""Regression tests for the TigerTag raw-page decoder.

These build a TigerTag block behind a page-0 UID header at the published NTAG offsets
and pin the produced FILAMENT_INFO_STRUCT fields, the magic-anchoring (standard + plus),
the diameter enum, and the decline rules (blank/init magic, no magic, truncated).
"""
from tigertag_fields import MAGIC_PLUS, MAGIC_STANDARD, build_struct

# Page-0 dump prefix: 7-byte UID (BCC at index 3) then lock/CC pages.
UID_HEADER = bytes((0x04, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77,
                    0x00, 0x00, 0x00, 0x00, 0xE1, 0x10, 0x12, 0x00))
EXPECTED_UID = [0x04, 0x11, 0x22, 0x44, 0x55, 0x66, 0x77]

TEMPLATE = {
    "VERSION": 0, "VENDOR": "NONE", "MANUFACTURER": "NONE", "MAIN_TYPE": "NONE",
    "SUB_TYPE": "NONE", "TRAY": 0, "ALPHA": 0xFF, "MULTI_MODE": 0, "COLOR_NUMS": 1,
    "ARGB_COLOR": 0xFFFFFFFF, "RGB_1": 0xFFFFFF, "RGB_2": 0xFFFFFF, "RGB_3": 0xFFFFFF,
    "RGB_4": 0xFFFFFF, "RGB_5": 0xFFFFFF, "DIAMETER": 0, "WEIGHT": 0, "LENGTH": 0,
    "DRYING_TEMP": 0, "DRYING_TIME": 0, "HOTEND_MAX_TEMP": 0, "HOTEND_MIN_TEMP": 0,
    "BED_TYPE": 0, "BED_TEMP": 0, "FIRST_LAYER_TEMP": 0, "OTHER_LAYER_TEMP": 0,
    "SKU": 0, "MF_DATE": "19700101", "RSA_KEY_VERSION": 0, "OFFICIAL": False, "CARD_UID": 0,
}


def _u16(value: int) -> bytes:
    return bytes(((value >> 8) & 0xFF, value & 0xFF))


def build_block(magic: bytes, diameter_code: int = 0x38) -> bytes:
    block = bytearray(magic)              # +0  magic
    block += bytes((0x12, 0x34, 0x56, 0x78))  # +4  id_product
    block += _u16(0x0042)                 # +8  id_material
    block += bytes((0x01, 0x00))          # +10 aspect 1/2
    block += bytes((0x8E,))               # +12 id_type (filament)
    block += bytes((diameter_code,))      # +13 id_diameter
    block += _u16(0x0007)                 # +14 id_brand
    block += bytes((0xFF, 0x80, 0x00, 0xC0))  # +16 color RGBA
    block += bytes((0x00, 0x03, 0xE8))    # +20 measure u24 = 1000
    block += bytes((0x01,))               # +23 id_unit
    block += _u16(205)                    # +24 nozzle min
    block += _u16(245)                    # +26 nozzle max
    block += bytes((55,))                 # +28 dry temp
    block += bytes((8,))                  # +29 dry time
    block += bytes((50,))                 # +30 bed min
    block += bytes((60,))                 # +31 bed max
    return bytes(block)


def test_decodes_standard_tag():
    dump = UID_HEADER + build_block(MAGIC_STANDARD)
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    assert info["VENDOR"] == "TigerTag"
    assert info["SKU"] == 0x12345678
    assert info["DIAMETER"] == 175
    assert info["WEIGHT"] == 1000
    assert info["CARD_UID"] == EXPECTED_UID
    assert info["OFFICIAL"] is True


def test_decodes_color_rgba():
    info = build_struct(UID_HEADER + build_block(MAGIC_STANDARD), dict(TEMPLATE))
    assert info["RGB_1"] == 0xFF8000
    assert info["ALPHA"] == 0xC0
    assert info["ARGB_COLOR"] == 0xC0FF8000


def test_decodes_temperatures():
    info = build_struct(UID_HEADER + build_block(MAGIC_STANDARD), dict(TEMPLATE))
    assert info["HOTEND_MIN_TEMP"] == 205
    assert info["HOTEND_MAX_TEMP"] == 245
    assert info["FIRST_LAYER_TEMP"] == 205
    assert info["BED_TEMP"] == 60
    assert info["DRYING_TEMP"] == 55
    assert info["DRYING_TIME"] == 8


def test_diameter_enum():
    standard = build_struct(UID_HEADER + build_block(MAGIC_STANDARD, 0x38), dict(TEMPLATE))
    assert standard["DIAMETER"] == 175
    wide = build_struct(UID_HEADER + build_block(MAGIC_STANDARD, 0xDD), dict(TEMPLATE))
    assert wide["DIAMETER"] == 285
    unknown = build_struct(UID_HEADER + build_block(MAGIC_STANDARD, 0x99), dict(TEMPLATE))
    assert unknown["DIAMETER"] == 0


def test_plus_magic_decodes():
    info = build_struct(UID_HEADER + build_block(MAGIC_PLUS), dict(TEMPLATE))
    assert info is not None
    assert info["WEIGHT"] == 1000


def test_magic_found_at_any_offset():
    dump = UID_HEADER + bytes(20) + build_block(MAGIC_STANDARD) + bytes(8)
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    assert info["WEIGHT"] == 1000


def test_blank_init_magic_declines():
    # The TigerTag-Init blank marker is not a decodable tag.
    blank = UID_HEADER + bytes((0x6C, 0x41, 0xA2, 0xE1)) + bytes(40)
    assert build_struct(blank, dict(TEMPLATE)) is None


def test_no_magic_declines():
    assert build_struct(UID_HEADER + bytes(48), dict(TEMPLATE)) is None


def test_truncated_block_declines():
    truncated = (UID_HEADER + build_block(MAGIC_STANDARD))[:-6]
    assert build_struct(truncated, dict(TEMPLATE)) is None


def test_does_not_mutate_template():
    build_struct(UID_HEADER + build_block(MAGIC_STANDARD), TEMPLATE)
    assert TEMPLATE["VENDOR"] == "NONE"
    assert TEMPLATE["OFFICIAL"] is False
