# ruff: noqa: PLR2004  Tests assert on literal field values/offsets by design.
"""Regression tests for the OpenTag3D decoder.

These build OpenTag3D payloads at the spec's verified byte offsets and pin the
produced FILAMENT_INFO_STRUCT fields, including the core-only vs extended
temperature paths and the MIME-type gating.
"""
from opentag_fields import build_struct

OPENTAG_MIME_TYPE = "application/opentag3d"
CARD_UID = [0x04, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66]
CORE_ONLY_LENGTH = 0x62  # bed-temp offset (0x61) + 1: the shortest core payload
EXTENDED_LENGTH = 0xBB

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

DEFAULT_FIELDS = {
    "material": "PLA", "modifiers": "CF", "manufacturer": "Polymaker",
    "rgba": (0x10, 0x20, 0x30, 0xFF), "diameter_um": 1750, "weight_g": 1000,
    "print_temp_c": 210, "bed_temp_c": 60, "ext_min_c": 200, "ext_max_c": 220, "ext_bed_c": 60,
}


def _put_text(buf: bytearray, offset: int, value: str, length: int) -> None:
    chunk = value.encode("utf-8")[:length]
    buf[offset:offset + len(chunk)] = chunk


def _put_u16_be(buf: bytearray, offset: int, value: int) -> None:
    buf[offset:offset + 2] = bytes(((value >> 8) & 0xFF, value & 0xFF))


def build_payload(size: int, fields: dict[str, object]) -> bytes:
    buf = bytearray(size)
    _put_text(buf, 0x02, str(fields["material"]), 5)
    _put_text(buf, 0x07, str(fields["modifiers"]), 5)
    _put_text(buf, 0x1B, str(fields["manufacturer"]), 16)
    buf[0x4B:0x4F] = bytes(fields["rgba"])
    _put_u16_be(buf, 0x5C, int(fields["diameter_um"]))
    _put_u16_be(buf, 0x5E, int(fields["weight_g"]))
    buf[0x60] = int(fields["print_temp_c"]) // 5
    buf[0x61] = int(fields["bed_temp_c"]) // 5
    if size > 0xB7:
        buf[0xB4] = int(fields["ext_min_c"]) // 5
        buf[0xB5] = int(fields["ext_max_c"]) // 5
        buf[0xB7] = int(fields["ext_bed_c"]) // 5
    return bytes(buf)


def opentag_record(payload: bytes) -> dict[str, object]:
    return {"mime_type": OPENTAG_MIME_TYPE, "payload": payload}


def test_decodes_extended_payload() -> None:
    record = opentag_record(build_payload(EXTENDED_LENGTH, DEFAULT_FIELDS))
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["VENDOR"] == "Polymaker"
    assert info["MANUFACTURER"] == "Polymaker"
    assert info["MAIN_TYPE"] == "PLA"
    assert info["SUB_TYPE"] == "CF"
    assert info["RGB_1"] == 0x102030
    assert info["ALPHA"] == 0xFF
    assert info["ARGB_COLOR"] == 0xFF102030
    assert info["DIAMETER"] == 175
    assert info["WEIGHT"] == 1000
    assert info["HOTEND_MIN_TEMP"] == 200
    assert info["HOTEND_MAX_TEMP"] == 220
    assert info["FIRST_LAYER_TEMP"] == 200
    assert info["BED_TEMP"] == 60
    assert info["CARD_UID"] == CARD_UID
    assert info["OFFICIAL"] is True


def test_core_only_payload_uses_single_print_temp() -> None:
    record = opentag_record(build_payload(CORE_ONLY_LENGTH, DEFAULT_FIELDS))
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["HOTEND_MIN_TEMP"] == 210
    assert info["HOTEND_MAX_TEMP"] == 210
    assert info["BED_TEMP"] == 60


def test_color_channels_are_distinct() -> None:
    fields = {**DEFAULT_FIELDS, "rgba": (0xAB, 0xCD, 0xEF, 0x80)}
    record = opentag_record(build_payload(EXTENDED_LENGTH, fields))
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["RGB_1"] == 0xABCDEF
    assert info["ALPHA"] == 0x80
    assert info["ARGB_COLOR"] == 0x80ABCDEF


def test_ignores_non_opentag_mime() -> None:
    record = {"mime_type": "application/json", "payload": b'{"type":"PLA"}'}
    assert build_struct([record], CARD_UID, dict(TEMPLATE)) is None


def test_ignores_payload_shorter_than_core() -> None:
    record = opentag_record(bytes(0x40))
    assert build_struct([record], CARD_UID, dict(TEMPLATE)) is None
