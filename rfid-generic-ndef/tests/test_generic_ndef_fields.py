# ruff: noqa: PLR2004  Tests assert on literal field values by design.
"""Regression tests for the generic JSON-over-NDEF decoder.

These pin the produced FILAMENT_INFO_STRUCT fields for a representative captured
payload, and the decline rules that keep this best-effort parser from shadowing
OpenSpool or claiming unrelated JSON.
"""
import json

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
