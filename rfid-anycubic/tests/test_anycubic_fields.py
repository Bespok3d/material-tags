# ruff: noqa: PLR2004  Tests assert on literal field values/offsets by design.
"""Regression tests for the Anycubic ACE raw-page decoder.

These build a page dump at the agreed-across-sources NTAG offsets (magic + ASCII
brand/material + LE temps), pin the produced FILAMENT_INFO_STRUCT fields, and confirm the
deliberately-omitted disputed fields (color, diameter, weight) stay at the template default,
plus the decline rules (no magic / truncated).
"""
from anycubic_fields import MAGIC, build_struct

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
    return bytes((value & 0xFF, (value >> 8) & 0xFF))   # little-endian


def build_block(brand: str = "AC", material: str = "PLA") -> bytes:
    block = bytearray(120)                       # magic..page30 = 30 pages = 120 bytes
    block[0:4] = MAGIC                            # +0   magic 7B 00 65 00
    block[24:24 + len(brand)] = brand.encode()   # +24  brand (page 10)
    block[44:44 + len(material)] = material.encode()  # +44 material (page 15)
    block[80:82] = _u16(205)                     # +80  nozzle min (page 24)
    block[82:84] = _u16(245)                     # +82  nozzle max
    block[100:102] = _u16(50)                    # +100 bed min (page 29)
    block[102:104] = _u16(60)                    # +102 bed max
    return bytes(block)


def test_decodes_brand_material_temps():
    dump = UID_HEADER + build_block(brand="Anycubic", material="PETG")
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    assert info["VENDOR"] == "Anycubic"
    assert info["MAIN_TYPE"] == "PETG"
    assert info["HOTEND_MIN_TEMP"] == 205
    assert info["HOTEND_MAX_TEMP"] == 245
    assert info["FIRST_LAYER_TEMP"] == 205
    assert info["BED_TEMP"] == 60
    assert info["CARD_UID"] == EXPECTED_UID
    assert info["OFFICIAL"] is True


def test_disputed_fields_left_at_default():
    # color / diameter / weight are NOT decoded (sources disagree, no real dump).
    info = build_struct(UID_HEADER + build_block(), dict(TEMPLATE))
    assert info["RGB_1"] == 0xFFFFFF
    assert info["DIAMETER"] == 0
    assert info["WEIGHT"] == 0


def test_default_vendor_when_brand_blank():
    info = build_struct(UID_HEADER + build_block(brand=""), dict(TEMPLATE))
    assert info["VENDOR"] == "Anycubic"


def test_magic_found_at_any_offset():
    dump = UID_HEADER + bytes(8) + build_block()
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    assert info["HOTEND_MAX_TEMP"] == 245


def test_no_magic_declines():
    assert build_struct(UID_HEADER + bytes(120), dict(TEMPLATE)) is None


def test_truncated_block_declines():
    # Cut into the block so bed temp (magic+104) no longer fits.
    assert build_struct((UID_HEADER + build_block())[:-20], dict(TEMPLATE)) is None


def test_does_not_mutate_template():
    build_struct(UID_HEADER + build_block(), TEMPLATE)
    assert TEMPLATE["VENDOR"] == "NONE"
    assert TEMPLATE["OFFICIAL"] is False
