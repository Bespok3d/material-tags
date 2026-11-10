# ruff: noqa: PLR2004  Tests assert on literal field values by design.
"""Regression tests for the generic JSON-over-NDEF decoder.

These pin the produced FILAMENT_INFO_STRUCT fields for a representative captured
payload, and the decline rules that keep this best-effort parser from shadowing
OpenSpool or claiming unrelated JSON.
"""
import json

import pytest
from generic_ndef_fields import build_struct, select_filament_json

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
CARD_UID = [0x04, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66]
NOT_A_HEX_COLOR = [
    "", None, "zz", "F00", "+12345", "-12345", " 112233", "0x1122", "##112233", "1122334",
    "112233ZZ", 112233,
]


def json_record(payload: dict[str, object]) -> dict[str, object]:
    return {"mime_type": "application/json", "payload": json.dumps(payload).encode("utf-8")}


def test_decodes_untagged_json_into_struct() -> None:
    tag = {
        "brand": "Polymaker", "type": "petg", "subtype": "Matte", "color_hex": "#1A2B3C",
        "min_temp": 230, "max_temp": 250, "bed_temp": 80, "diameter": 1.75, "weight": 1000,
    }
    info = build_struct([json_record(tag)], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["VENDOR"] == "Polymaker"
    assert info["MAIN_TYPE"] == "PETG"
    assert info["SUB_TYPE"] == "Matte"
    assert info["RGB_1"] == 0x1A2B3C
    assert info["HOTEND_MIN_TEMP"] == 230
    assert info["HOTEND_MAX_TEMP"] == 250
    assert info["FIRST_LAYER_TEMP"] == 230
    assert info["BED_TEMP"] == 80
    assert info["DIAMETER"] == 175
    assert info["WEIGHT"] == 1000
    assert info["CARD_UID"] == CARD_UID
    assert info["OFFICIAL"] is True


def test_resolves_alternate_field_aliases() -> None:
    tag = {"vendor": "Sunlu", "material": "PLA", "color": "FF0000", "nozzle_max_temp": "215"}
    info = build_struct([json_record(tag)], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["VENDOR"] == "Sunlu"
    assert info["MAIN_TYPE"] == "PLA"
    assert info["RGB_1"] == 0xFF0000
    assert info["HOTEND_MAX_TEMP"] == 215


def test_declines_protocol_tagged_json() -> None:
    openspool = {"protocol": "openspool", "type": "PLA", "color_hex": "#FFFFFF"}
    assert build_struct([json_record(openspool)], CARD_UID, dict(TEMPLATE)) is None
    assert select_filament_json([json_record(openspool)]) is None


def test_declines_json_without_any_known_field() -> None:
    unrelated = {"note": "hello", "count": 3}
    assert build_struct([json_record(unrelated)], CARD_UID, dict(TEMPLATE)) is None


def test_matches_the_json_mime_type_in_any_case() -> None:
    # RFC 2045: MIME types compare case-insensitively.
    record = json_record({"type": "PLA"}) | {"mime_type": "Application/JSON"}
    info = build_struct([record], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["MAIN_TYPE"] == "PLA"


def test_ignores_non_json_records() -> None:
    text_record = {"mime_type": "text/plain", "payload": b"PLA"}
    assert build_struct([text_record], CARD_UID, dict(TEMPLATE)) is None


def test_falls_back_to_defaults_for_missing_numbers() -> None:
    tag = {"brand": "Generic", "type": "ABS"}
    info = build_struct([json_record(tag)], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["HOTEND_MIN_TEMP"] == 0
    assert info["DIAMETER"] == 175
    assert info["RGB_1"] == 0xFFFFFF


def test_decodes_additional_colors() -> None:
    # Same field and format as OpenSpool: extra hex strings after color_hex.
    tag = {"type": "PLA", "color_hex": "AFAFAF", "additional_color_hexes": ["EEFFEE", "#FF00FF"]}
    info = build_struct([json_record(tag)], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["COLOR_NUMS"] == 3
    assert [info["RGB_1"], info["RGB_2"], info["RGB_3"]] == [0xAFAFAF, 0xEEFFEE, 0xFF00FF]
    assert info["RGB_4"] == 0xFFFFFF
    assert info["ARGB_COLOR"] == 0xFFAFAFAF


def test_keeps_at_most_five_colors_in_all() -> None:
    extra_hexes = ["010101", "020202", "030303", "040404", "050505"]
    tag = {"type": "PLA", "color_hex": "000000", "additional_color_hexes": extra_hexes}
    info = build_struct([json_record(tag)], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["COLOR_NUMS"] == 5
    assert info["RGB_5"] == 0x040404


def test_ignores_additional_colors_that_are_not_a_list() -> None:
    tag = {"type": "PLA", "color_hex": "AFAFAF", "additional_color_hexes": "EEFFEE"}
    info = build_struct([json_record(tag)], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["COLOR_NUMS"] == 1
    assert info["RGB_2"] == 0xFFFFFF


def test_skips_additional_colors_that_are_not_hex() -> None:
    extra_hexes = [*NOT_A_HEX_COLOR, "EEFFEE"]
    tag = {"type": "PLA", "color_hex": "AFAFAF", "additional_color_hexes": extra_hexes}
    info = build_struct([json_record(tag)], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["COLOR_NUMS"] == 2
    assert info["RGB_2"] == 0xEEFFEE


@pytest.mark.parametrize("color_value", NOT_A_HEX_COLOR)
def test_main_color_that_is_not_a_hex_color_reads_as_white(color_value: object) -> None:
    tag = {"type": "PLA", "color_hex": color_value}
    info = build_struct([json_record(tag)], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["COLOR_NUMS"] == 1
    assert info["RGB_1"] == 0xFFFFFF
    assert info["ARGB_COLOR"] == 0xFFFFFFFF


def test_reads_an_rrggbbaa_color_as_its_rgb() -> None:
    tag = {"type": "PLA", "color_hex": "#11223344", "additional_color_hexes": ["55667788"]}
    info = build_struct([json_record(tag)], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert [info["RGB_1"], info["RGB_2"]] == [0x112233, 0x556677]
    assert info["ARGB_COLOR"] == 0xFF112233


def test_first_additional_color_stands_in_for_a_missing_main_color() -> None:
    tag = {"type": "PLA", "additional_color_hexes": ["112233", "445566"]}
    info = build_struct([json_record(tag)], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["COLOR_NUMS"] == 2
    assert [info["RGB_1"], info["RGB_2"]] == [0x112233, 0x445566]
    assert info["ARGB_COLOR"] == 0xFF112233


def test_five_additional_colors_fill_every_slot_when_the_main_color_is_missing() -> None:
    extra_hexes = ["010101", "020202", "030303", "040404", "050505", "060606"]
    tag = {"type": "PLA", "additional_color_hexes": extra_hexes}
    info = build_struct([json_record(tag)], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["COLOR_NUMS"] == 5
    assert [info["RGB_1"], info["RGB_5"]] == [0x010101, 0x050505]


def test_main_color_comes_from_the_first_alias_with_a_valid_color() -> None:
    tag = {"type": "PLA", "color_hex": "F00", "color": "FF0000"}
    info = build_struct([json_record(tag)], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["RGB_1"] == 0xFF0000


def test_first_additional_color_stands_in_for_an_invalid_main_color() -> None:
    tag = {"type": "PLA", "color_hex": "zz", "additional_color_hexes": ["112233"]}
    info = build_struct([json_record(tag)], CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["COLOR_NUMS"] == 1
    assert info["RGB_1"] == 0x112233
