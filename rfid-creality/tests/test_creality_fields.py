# ruff: noqa: PLR2004  Tests assert on literal field values/offsets by design.
"""Regression tests for the Creality payload decoder.

These pin the field slicing against the verified decrypted example string and the
weight-bucket map, plus the date unpacking and the reject paths (short / non-hex).
"""
from creality_fields import decode

# The verified decrypted 48-char payload (DnG-Crafts/flamebarke).
EXAMPLE = "1A5241201B3D010010000000033000000100000000000000"
UID = [0x35, 0xB9, 0x4A, 0x19]

TEMPLATE = {
    "VERSION": 0, "VENDOR": "NONE", "MANUFACTURER": "NONE", "MAIN_TYPE": "NONE",
    "SUB_TYPE": "NONE", "TRAY": 0, "ALPHA": 0xFF, "MULTI_MODE": 0, "COLOR_NUMS": 1,
    "ARGB_COLOR": 0xFFFFFFFF, "RGB_1": 0xFFFFFF, "RGB_2": 0xFFFFFF, "RGB_3": 0xFFFFFF,
    "RGB_4": 0xFFFFFF, "RGB_5": 0xFFFFFF, "DIAMETER": 0, "WEIGHT": 0, "LENGTH": 0,
    "DRYING_TEMP": 0, "DRYING_TIME": 0, "HOTEND_MAX_TEMP": 0, "HOTEND_MIN_TEMP": 0,
    "BED_TYPE": 0, "BED_TEMP": 0, "FIRST_LAYER_TEMP": 0, "OTHER_LAYER_TEMP": 0,
    "SKU": 0, "MF_DATE": "19700101", "RSA_KEY_VERSION": 0, "OFFICIAL": False, "CARD_UID": 0,
}


def test_decodes_example_identity():
    info = decode(EXAMPLE, UID, dict(TEMPLATE))
    assert info is not None
    assert info["VENDOR"] == "Creality"
    assert info["MANUFACTURER"] == "Creality"
    assert info["OFFICIAL"] is True
    assert info["CARD_UID"] == UID


def test_decodes_weight_bucket():
    # Weight code 0330 -> 1000 g (the example).
    assert decode(EXAMPLE, UID, dict(TEMPLATE))["WEIGHT"] == 1000


def test_weight_bucket_map():
    def weight_for(code: str) -> int:
        payload = EXAMPLE[:24] + code + EXAMPLE[28:]
        return decode(payload, UID, dict(TEMPLATE))["WEIGHT"]
    assert weight_for("0082") == 250
    assert weight_for("0165") == 500
    assert weight_for("0247") == 750
    assert weight_for("FFFF") == 0  # unknown bucket -> 0


def test_decodes_color():
    blue = EXAMPLE[:18] + "0000FF" + EXAMPLE[24:]
    info = decode(blue, UID, dict(TEMPLATE))
    assert info["RGB_1"] == 0x0000FF
    assert info["ALPHA"] == 0xFF
    assert info["ARGB_COLOR"] == 0xFF0000FF


def test_decodes_material_id_as_number():
    # material id [12:17] = "01001" -> 0x01001.
    assert decode(EXAMPLE, UID, dict(TEMPLATE))["SKU"] == 0x01001


def test_decodes_manufacture_date():
    # date [3:8] = "24120" -> 2024, month 1, day 20.
    assert decode(EXAMPLE, UID, dict(TEMPLATE))["MF_DATE"] == "20240120"


def test_keeps_default_date_when_implausible():
    # All-zero date field -> month 0, day 0 -> implausible -> keep template default.
    zero_date = EXAMPLE[:3] + "00000" + EXAMPLE[8:]
    assert decode(zero_date, UID, dict(TEMPLATE))["MF_DATE"] == "19700101"


def test_decodes_october_month_letter():
    # Month nibble A = October.
    october = EXAMPLE[:3] + "24A15" + EXAMPLE[8:]
    assert decode(october, UID, dict(TEMPLATE))["MF_DATE"] == "20241015"


def test_rejects_short_payload():
    assert decode(EXAMPLE[:40], UID, dict(TEMPLATE)) is None
    assert decode(None, UID, dict(TEMPLATE)) is None


def test_rejects_non_hex_payload():
    # A bad key produces non-hex bytes; the decoder must decline rather than mis-decode.
    assert decode("Z" * 48, UID, dict(TEMPLATE)) is None


def test_does_not_mutate_template():
    decode(EXAMPLE, UID, TEMPLATE)
    assert TEMPLATE["VENDOR"] == "NONE"
    assert TEMPLATE["OFFICIAL"] is False
