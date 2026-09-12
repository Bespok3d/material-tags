# ruff: noqa: PLR2004  Tests assert on literal field values/offsets by design.
"""Regression tests for the Creality payload decoder.

Pins the field slicing (material id, color, weight) and the payload framing (hex core before
the '%' terminator, NUL padding after). Field offsets are cross-confirmed against the upstream
K2-RFID layout and a real tag dump. Only fields the decoder actually emits are asserted:
material id (as a literal string), MAIN_TYPE (looked up from the id), weight bucket, color,
vendor, and UID. Date/serial are intentionally not decoded (see creality_fields docstring).
"""
from creality_fields import decode

# A valid decrypted payload in the real on-tag format: 40 hex chars, then '%' + NUL padding.
# material [12:17]=01001 (-> PLA), color [18:24]=0000FF, weight [24:28]=0330 (1000 g).
EXAMPLE = "3C6260276A210100100000FF0330000001000000" + "%" + "\x00" * 7
UID = [0x40, 0x24, 0xC2, 0x6A]

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
    info = decode(EXAMPLE, UID, dict(TEMPLATE))
    assert info["RGB_1"] == 0x0000FF
    assert info["ALPHA"] == 0xFF
    assert info["ARGB_COLOR"] == 0xFF0000FF


def test_decodes_material_id_as_string():
    # material id [12:17] = "01001", kept as a literal string (ids are not all numeric).
    assert decode(EXAMPLE, UID, dict(TEMPLATE))["SKU"] == "01001"


def test_resolves_main_type_from_material_id():
    # 01001 -> PLA via the creality_types table (sourced from Creality slicer profiles).
    assert decode(EXAMPLE, UID, dict(TEMPLATE))["MAIN_TYPE"] == "PLA"


def test_fills_diameter_and_temps_from_material_id():
    # 01001 -> 1.75 mm, hotend 190 to 240 (from Creality slicer profiles via creality_types).
    info = decode(EXAMPLE, UID, dict(TEMPLATE))
    assert info["DIAMETER"] == 1.75
    assert info["HOTEND_MIN_TEMP"] == 190
    assert info["HOTEND_MAX_TEMP"] == 240


def test_unknown_material_id_leaves_type_and_temps_default():
    # A material id not in the table leaves type, diameter, and temps at the template default.
    unknown = EXAMPLE[:12] + "99999" + EXAMPLE[17:]
    info = decode(unknown, UID, dict(TEMPLATE))
    assert info is not None
    assert info["SKU"] == "99999"
    assert info["MAIN_TYPE"] == "NONE"
    assert info["DIAMETER"] == 0
    assert info["HOTEND_MIN_TEMP"] == 0
    assert info["HOTEND_MAX_TEMP"] == 0


def test_accepts_core_with_terminator_and_padding():
    # The real framing (hex core, then '%' then NULs) must decode.
    assert decode(EXAMPLE, UID, dict(TEMPLATE)) is not None


def test_rejects_too_short_core():
    # A core that does not reach the end of the weight field [24:28] is invalid.
    assert decode("3C6260276A21" + "%", UID, dict(TEMPLATE)) is None
    assert decode(None, UID, dict(TEMPLATE)) is None


def test_rejects_non_hex_core():
    assert decode("Z" * 40 + "%", UID, dict(TEMPLATE)) is None


def test_does_not_mutate_template():
    decode(EXAMPLE, UID, TEMPLATE)
    assert TEMPLATE["VENDOR"] == "NONE"
    assert TEMPLATE["OFFICIAL"] is False
    assert TEMPLATE["SKU"] == 0
