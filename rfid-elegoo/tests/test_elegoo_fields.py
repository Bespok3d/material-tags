# ruff: noqa: PLR2004  Tests assert on literal field values/offsets by design.
"""Regression tests for the Elegoo raw-page decoder.

These build Elegoo EPC-256 blocks behind a page-0 UID header and pin the produced
FILAMENT_INFO_STRUCT fields, the signature-anchoring (block found at any offset),
and the decline rules (no signature / truncated block).

The fixture's block matches the published EPC-256 / OpenRFID layout (0x36 header,
EEEEEEEE marker, u16 code, material@+6, subtype@+10, RGB888@+14, diameter@+17,
weight@+19 - all marker-relative), which elegoo_fields now decodes byte-for-byte.
"""
from elegoo_fields import build_struct

SIGNATURE = bytes((0x36, 0xEE, 0xEE, 0xEE, 0xEE))
# Page-0 dump prefix: 7-byte UID (BCC at index 3) then lock/CC pages, before user memory at byte 16.
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

DEFAULT_FIELDS = {
    "material": "PLA", "subtype": "CF", "rgb": (0xFF, 0x37, 0x00),
    "diameter": 175, "weight": 1000, "code": 0x0001, "date": 0x09C6,
}


def _u16(value: int) -> bytes:
    return bytes(((value >> 8) & 0xFF, value & 0xFF))


def build_block(fields: dict[str, object]) -> bytes:
    block = bytearray(SIGNATURE)
    block += _u16(int(fields["code"]))
    block += str(fields["material"]).encode("ascii").ljust(4, b"\x00")[:4]
    block += str(fields["subtype"]).encode("ascii").ljust(4, b"\x00")[:4]
    block += bytes(fields["rgb"])
    block += _u16(int(fields["diameter"]))
    block += _u16(int(fields["weight"]))
    block += _u16(int(fields["date"]))
    return bytes(block)


def test_decodes_elegoo_block() -> None:
    dump = UID_HEADER + build_block(DEFAULT_FIELDS)
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    assert info["VENDOR"] == "Elegoo"
    assert info["MANUFACTURER"] == "Elegoo"
    assert info["MAIN_TYPE"] == "PLA"
    assert info["SUB_TYPE"] == "CF"
    assert info["RGB_1"] == 0xFF3700
    assert info["ARGB_COLOR"] == 0xFFFF3700
    assert info["DIAMETER"] == 175
    assert info["WEIGHT"] == 1000
    assert info["CARD_UID"] == EXPECTED_UID
    assert info["OFFICIAL"] is True
    assert info["HOTEND_MIN_TEMP"] == 0  # Elegoo tags carry no temperatures


def test_signature_is_found_at_any_offset() -> None:
    dump = UID_HEADER + bytes(20) + build_block(DEFAULT_FIELDS) + bytes(8)
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    assert info["MAIN_TYPE"] == "PLA"
    assert info["WEIGHT"] == 1000


def test_distinct_color_channels() -> None:
    dump = UID_HEADER + build_block({**DEFAULT_FIELDS, "rgb": (0x12, 0x34, 0x56)})
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    assert info["RGB_1"] == 0x123456
    assert info["ARGB_COLOR"] == 0xFF123456


def test_no_signature_returns_none() -> None:
    assert build_struct(UID_HEADER + bytes(32), dict(TEMPLATE)) is None


def test_truncated_block_returns_none() -> None:
    truncated = (UID_HEADER + build_block(DEFAULT_FIELDS))[:-6]
    assert build_struct(truncated, dict(TEMPLATE)) is None
