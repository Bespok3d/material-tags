# ruff: noqa: PLR2004  Tests assert on literal field values/offsets by design.
"""Regression tests for the OpenTag3D decoder.

These build OpenTag3D payloads at the spec's verified byte offsets and pin the
produced FILAMENT_INFO_STRUCT fields, including the v1 core temperatures and the
optional extended nozzle min and max, the v2 layout, the version gate and the MIME-type gating.
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
    "print_temp_c": 210, "bed_temp_c": 60, "ext_min_c": 200, "ext_max_c": 220, "ext_max_bed_c": 70,
}


def _put_text(buf: bytearray, offset: int, value: str, length: int) -> None:
    chunk = value.encode("utf-8")[:length]
    buf[offset:offset + len(chunk)] = chunk


def _put_u16_be(buf: bytearray, offset: int, value: int) -> None:
    buf[offset:offset + 2] = bytes(((value >> 8) & 0xFF, value & 0xFF))


def build_payload(size: int, fields: dict[str, object]) -> bytes:
    buf = bytearray(size)
    _put_u16_be(buf, 0x00, int(fields.get("tag_version", 1000)))
    _put_text(buf, 0x02, str(fields["material"]), 5)
    _put_text(buf, 0x07, str(fields["modifiers"]), 5)
    _put_text(buf, 0x1B, str(fields["manufacturer"]), 16)
    buf[0x4B:0x4F] = bytes(fields["rgba"])
    for offset, rgba in zip((0x50, 0x54, 0x58), fields.get("secondary_rgba", ())):
        buf[offset:offset + 4] = bytes(rgba)
    _put_u16_be(buf, 0x5C, int(fields["diameter_um"]))
    _put_u16_be(buf, 0x5E, int(fields["weight_g"]))
    buf[0x60] = int(fields["print_temp_c"]) // 5
    buf[0x61] = int(fields["bed_temp_c"]) // 5
    if size > 0xB7:
        buf[0xB4] = int(fields["ext_min_c"]) // 5
        buf[0xB5] = int(fields["ext_max_c"]) // 5
        buf[0xB7] = int(fields["ext_max_bed_c"]) // 5
    return bytes(buf)


def opentag_record(payload: bytes) -> dict[str, object]:
    return {"mime_type": OPENTAG_MIME_TYPE, "payload": payload}


def test_decodes_extended_payload() -> None:
    # Spec v1: Print Temperature (0x60) and Bed Temperature (0x61) are the recommended targets;
    # the extended block only bounds the nozzle, and its max bed is a limit, not a target.
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
    assert info["FIRST_LAYER_TEMP"] == 210
    assert info["OTHER_LAYER_TEMP"] == 210
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


def test_extended_nozzle_temperatures_left_at_zero_fall_back_to_the_print_temp() -> None:
    # Spec reader: an optional int left at 0 is not set.
    fields = {**DEFAULT_FIELDS, "ext_min_c": 0, "ext_max_c": 0}
    record = opentag_record(build_payload(EXTENDED_LENGTH, fields))
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["HOTEND_MIN_TEMP"] == 210
    assert info["HOTEND_MAX_TEMP"] == 210
    assert info["FIRST_LAYER_TEMP"] == 210
    assert info["OTHER_LAYER_TEMP"] == 210
    assert info["BED_TEMP"] == 60


def test_each_extended_temperature_falls_back_on_its_own() -> None:
    fields = {**DEFAULT_FIELDS, "ext_max_c": 0}
    record = opentag_record(build_payload(EXTENDED_LENGTH, fields))
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["HOTEND_MIN_TEMP"] == 200
    assert info["HOTEND_MAX_TEMP"] == 210


def test_pre_1000_tag_version_keeps_v1_reading() -> None:
    fields = {**DEFAULT_FIELDS, "tag_version": 20}
    record = opentag_record(build_payload(CORE_ONLY_LENGTH, fields))
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["MAIN_TYPE"] == "PLA"
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


def test_matches_the_opentag_mime_type_in_any_case() -> None:
    # RFC 2045: MIME types compare case-insensitively.
    record = opentag_record(build_payload(EXTENDED_LENGTH, DEFAULT_FIELDS))
    record["mime_type"] = "Application/OpenTag3D"
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["VENDOR"] == "Polymaker"


def test_ignores_non_opentag_mime() -> None:
    record = {"mime_type": "application/json", "payload": b'{"type":"PLA"}'}
    assert build_struct([record], CARD_UID, dict(TEMPLATE)) is None


def test_ignores_payload_shorter_than_core() -> None:
    record = opentag_record(bytes(0x40))
    assert build_struct([record], CARD_UID, dict(TEMPLATE)) is None


def test_decodes_secondary_colors() -> None:
    # Spec v1.000: color_2..color_4 are RGBA at 0x50, 0x54, 0x58; an unused one is 00000000.
    secondaries = ((0x40, 0x50, 0x60, 0xFF), (0, 0, 0, 0), (0x70, 0x80, 0x90, 0xFF))
    fields = {**DEFAULT_FIELDS, "secondary_rgba": secondaries}
    record = opentag_record(build_payload(CORE_ONLY_LENGTH, fields))
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["COLOR_NUMS"] == 3
    assert [info["RGB_1"], info["RGB_2"], info["RGB_3"]] == [0x102030, 0x405060, 0x708090]
    assert info["RGB_4"] == 0xFFFFFF
    assert info["ARGB_COLOR"] == 0xFF102030


def test_single_color_spool_keeps_one_color() -> None:
    record = opentag_record(build_payload(EXTENDED_LENGTH, DEFAULT_FIELDS))
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["COLOR_NUMS"] == 1
    assert info["RGB_2"] == 0xFFFFFF


V2_FULL_LENGTH = 0xE0  # spec v2.004 address range 0x00..0xDF
V2_FIELDS = {
    "tag_version": 2004, "material": "PETG", "modifiers": "HF", "manufacturer": "Example Brand",
    "color_rgba": ((0xFF, 0xA6, 0x4D, 0xFF), (0x11, 0x22, 0x33, 0xFF)),
    "serial": "SN-2026-000042-ROLL-0007", "diameter_um": 1750, "weight_g": 750,
    "print_temp_c": 240, "min_print_temp_c": 230, "max_print_temp_c": 250,
    "bed_temp_c": 80, "min_bed_temp_c": 70, "max_bed_temp_c": 90,
}


def _put_temperature(buf: bytearray, offset: int, fields: dict[str, object], key: str) -> None:
    buf[offset] = int(fields.get(key, 0)) // 5


def build_v2_payload(size: int, fields: dict[str, object]) -> bytes:
    # Spec v2.004 memory map (_data/spec.json); bytes past `size` are cut, as a short tag would.
    buf = bytearray(V2_FULL_LENGTH)
    _put_u16_be(buf, 0x00, int(fields["tag_version"]))
    _put_text(buf, 0x02, str(fields["material"]), 5)
    _put_text(buf, 0x07, str(fields["modifiers"]), 5)
    _put_text(buf, 0x0C, str(fields["manufacturer"]), 16)
    for offset, rgba in zip((0x3C, 0x40, 0x44, 0x48), fields["color_rgba"]):
        buf[offset:offset + 4] = bytes(rgba)
    _put_text(buf, 0x4C, str(fields.get("serial", "")), 32)
    _put_u16_be(buf, 0x8C, int(fields["diameter_um"]))
    for offset, key in ((0x90, "print_temp_c"), (0x91, "min_print_temp_c"),
                        (0x92, "max_print_temp_c"), (0x94, "bed_temp_c"),
                        (0x95, "min_bed_temp_c"), (0x96, "max_bed_temp_c")):
        _put_temperature(buf, offset, fields, key)
    _put_u16_be(buf, 0x9E, int(fields["weight_g"]))
    return bytes(buf[:size])


def test_decodes_v2_tag_from_its_own_layout() -> None:
    record = opentag_record(build_v2_payload(V2_FULL_LENGTH, V2_FIELDS))
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["MANUFACTURER"] == "Example Brand"
    assert info["VENDOR"] == "Example Brand"
    assert info["MAIN_TYPE"] == "PETG"
    assert info["SUB_TYPE"] == "HF"
    assert info["COLOR_NUMS"] == 2
    assert [info["RGB_1"], info["RGB_2"]] == [0xFFA64D, 0x112233]
    assert info["RGB_3"] == 0xFFFFFF
    assert info["ARGB_COLOR"] == 0xFFFFA64D
    assert info["DIAMETER"] == 175
    assert info["WEIGHT"] == 750
    assert info["HOTEND_MIN_TEMP"] == 230
    assert info["HOTEND_MAX_TEMP"] == 250
    assert info["FIRST_LAYER_TEMP"] == 240
    assert info["OTHER_LAYER_TEMP"] == 240
    assert info["BED_TEMP"] == 80
    assert info["OFFICIAL"] is True


def test_v2_tag_without_min_max_print_temps_uses_the_target() -> None:
    fields = {**V2_FIELDS, "min_print_temp_c": 0, "max_print_temp_c": 0}
    record = opentag_record(build_v2_payload(V2_FULL_LENGTH, fields))
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["HOTEND_MIN_TEMP"] == 240
    assert info["HOTEND_MAX_TEMP"] == 240
    assert info["BED_TEMP"] == 80


def test_v2_payload_ending_right_after_its_weight_decodes() -> None:
    record = opentag_record(build_v2_payload(0xA0, V2_FIELDS))
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["MANUFACTURER"] == "Example Brand"
    assert info["WEIGHT"] == 750
    assert info["HOTEND_MAX_TEMP"] == 250


def test_v2_payload_ending_inside_its_weight_reads_the_low_byte_as_zero() -> None:
    fields = {**V2_FIELDS, "weight_g": 512}
    record = opentag_record(build_v2_payload(0x9F, fields))
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["WEIGHT"] == 512


def test_declines_v2_payload_that_ends_before_its_weight() -> None:
    record = opentag_record(build_v2_payload(0x9E, V2_FIELDS))
    assert build_struct([record], CARD_UID, dict(TEMPLATE)) is None


def test_declines_tag_of_a_newer_major_version() -> None:
    fields = {**V2_FIELDS, "tag_version": 3000}
    record = opentag_record(build_v2_payload(V2_FULL_LENGTH, fields))
    assert build_struct([record], CARD_UID, dict(TEMPLATE)) is None


def test_newer_v2_minor_version_still_decodes() -> None:
    fields = {**V2_FIELDS, "tag_version": 2999}
    record = opentag_record(build_v2_payload(V2_FULL_LENGTH, fields))
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["MANUFACTURER"] == "Example Brand"


def test_only_the_first_opentag_record_is_read() -> None:
    newer_major_fields = {**V2_FIELDS, "tag_version": 3000}
    newer_major = opentag_record(build_v2_payload(V2_FULL_LENGTH, newer_major_fields))
    supported = opentag_record(build_v2_payload(V2_FULL_LENGTH, V2_FIELDS))
    assert build_struct([newer_major, supported], CARD_UID, dict(TEMPLATE)) is None
