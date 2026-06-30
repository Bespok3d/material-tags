# ruff: noqa: PLR2004  Tests assert on literal field values by design.
"""Regression tests for the OpenPrintTag CBOR decoder.

The primary fixture is a REAL OpenPrintTag payload (Prusament PLA Galaxy Black, captured in
prusa3d/OpenPrintTag tests/encode_decode/01_info.yaml), so the decode is pinned against
ground truth. A synthetic payload covers the fields that one happens not to carry (filament
diameter, material abbreviation, an alpha color channel, drying).
"""
from openprinttag_fields import OPENPRINTTAG_MIME_TYPE, build_struct

# Real Prusament payload = meta map {2: 210} + the main map + an empty aux map.
META = "a10218d2"
MAIN = (
    "bf041b000007d0fcab45f9056a33333463353466303838080009000a76504c41"
    "2050727573612047616c61787920426c61636b0b6950727573616d656e740e1a"
    "68d3c7d7101903e8111903f41219011813443d3e3dff181c9f17ff181df93cf6"
    "182218cd182318e1182418aa182518281826183c18271218281828182914182a"
    "1840182b18c8182c1864182d183418389f0001ff183b831832fa4134cccdfa43"
    "014ccd183c69323730203330203230ff"
)
AUX = "a0"
PRUSAMENT_PAYLOAD = bytes.fromhex(META + MAIN + AUX)

# Synthetic main map (no meta -> main begins after an empty meta map): material abbreviation
# "PETG", color 11 22 33 with alpha 80, diameter 1.75 mm (f32), drying 65 C / 240 min.
SYNTHETIC_PAYLOAD = bytes.fromhex(
    "a0"  # empty meta map -> main starts at offset 1
    "a5"
    "1834" "64" "50455447"      # 52 material_abbreviation = "PETG"
    "13" "44" "11223380"        # 19 primary_color = R11 G22 B33 A80
    "181e" "fa" "3fe00000"      # 30 filament_diameter = 1.75 (f32)
    "1839" "1841"               # 57 drying_temperature = 65
    "183a" "18f0"               # 58 drying_time = 240
)

UID = [0x04, 0x11, 0x22, 0x44, 0x55, 0x66, 0x77]

TEMPLATE = {
    "VERSION": 0, "VENDOR": "NONE", "MANUFACTURER": "NONE", "MAIN_TYPE": "NONE",
    "SUB_TYPE": "NONE", "TRAY": 0, "ALPHA": 0xFF, "MULTI_MODE": 0, "COLOR_NUMS": 1,
    "ARGB_COLOR": 0xFFFFFFFF, "RGB_1": 0xFFFFFF, "RGB_2": 0xFFFFFF, "RGB_3": 0xFFFFFF,
    "RGB_4": 0xFFFFFF, "RGB_5": 0xFFFFFF, "DIAMETER": 0, "WEIGHT": 0, "LENGTH": 0,
    "DRYING_TEMP": 0, "DRYING_TIME": 0, "HOTEND_MAX_TEMP": 0, "HOTEND_MIN_TEMP": 0,
    "BED_TYPE": 0, "BED_TEMP": 0, "FIRST_LAYER_TEMP": 0, "OTHER_LAYER_TEMP": 0,
    "SKU": 0, "MF_DATE": "19700101", "RSA_KEY_VERSION": 0, "OFFICIAL": False, "CARD_UID": 0,
}


def _records(payload: bytes, mime: str = OPENPRINTTAG_MIME_TYPE):
    return [{"mime_type": mime, "payload": payload}]


def test_decodes_real_prusament_identity():
    info = build_struct(_records(PRUSAMENT_PAYLOAD), UID, dict(TEMPLATE))
    assert info is not None
    assert info["VENDOR"] == "Prusament"
    assert info["MANUFACTURER"] == "Prusament"
    assert info["MAIN_TYPE"] == "PLA Prusa Galaxy Black"
    assert info["OFFICIAL"] is True
    assert info["CARD_UID"] == UID


def test_decodes_real_prusament_color():
    info = build_struct(_records(PRUSAMENT_PAYLOAD), UID, dict(TEMPLATE))
    assert info["RGB_1"] == 0x3D3E3D
    assert info["ALPHA"] == 0xFF
    assert info["ARGB_COLOR"] == 0xFF3D3E3D


def test_decodes_real_prusament_weight_and_temps():
    info = build_struct(_records(PRUSAMENT_PAYLOAD), UID, dict(TEMPLATE))
    assert info["WEIGHT"] == 1000
    assert info["HOTEND_MIN_TEMP"] == 205
    assert info["HOTEND_MAX_TEMP"] == 225
    assert info["FIRST_LAYER_TEMP"] == 205
    assert info["BED_TEMP"] == 60


def test_decodes_real_prusament_date():
    # manufactured_date = 1758709719 (UNIX seconds) -> 2025-09-24 UTC.
    info = build_struct(_records(PRUSAMENT_PAYLOAD), UID, dict(TEMPLATE))
    assert info["MF_DATE"] == "20250924"


def test_synthetic_diameter_abbrev_alpha_drying():
    info = build_struct(_records(SYNTHETIC_PAYLOAD), UID, dict(TEMPLATE))
    assert info is not None
    assert info["MAIN_TYPE"] == "PETG"          # abbreviation preferred over name
    assert info["DIAMETER"] == 175              # 1.75 mm -> hundredths
    assert info["RGB_1"] == 0x112233
    assert info["ALPHA"] == 0x80
    assert info["ARGB_COLOR"] == 0x80112233
    assert info["DRYING_TEMP"] == 65
    assert info["DRYING_TIME"] == 240


def test_declines_non_openprinttag_mime():
    records = _records(PRUSAMENT_PAYLOAD, mime="application/json")
    assert build_struct(records, UID, dict(TEMPLATE)) is None


def test_declines_when_no_records():
    assert build_struct([], UID, dict(TEMPLATE)) is None


def test_declines_garbage_payload():
    # A record that claims to be OpenPrintTag but holds non-CBOR bytes must be declined.
    records = _records(b"\xff\xff\xff\xff\xff")
    assert build_struct(records, UID, dict(TEMPLATE)) is None


def test_does_not_mutate_template():
    build_struct(_records(PRUSAMENT_PAYLOAD), UID, TEMPLATE)
    assert TEMPLATE["VENDOR"] == "NONE"
    assert TEMPLATE["OFFICIAL"] is False
