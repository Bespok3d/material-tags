# ruff: noqa: PLR2004  Tests assert on literal field values/offsets by design.
"""Regression tests for the QIDI Mifare-Classic decoder.

These build sector-1 payload blocks in the layout read off physical QIDI spools (material
code, colour code, manufacturer code, then thirteen zero bytes) and pin the produced
FILAMENT_INFO_STRUCT fields, the code tables, and the decline rules.

The four code triples in KNOWN_SPOOLS are the ones confirmed on real spools, so a table
edit that loses one of them fails here.
"""
from qidi_fields import decode, looks_like_qidi

BLOCK_BYTES = 16
CARD_UID = [0x8B, 0xD5, 0x4F, 0xF4]

TEMPLATE = {
    "VERSION": 0, "VENDOR": "NONE", "MANUFACTURER": "NONE", "MAIN_TYPE": "NONE",
    "SUB_TYPE": "NONE", "TRAY": 0, "ALPHA": 0xFF, "MULTI_MODE": 0, "COLOR_NUMS": 1,
    "ARGB_COLOR": 0xFFFFFFFF, "RGB_1": 0xFFFFFF, "RGB_2": 0xFFFFFF, "RGB_3": 0xFFFFFF,
    "RGB_4": 0xFFFFFF, "RGB_5": 0xFFFFFF, "DIAMETER": 0, "WEIGHT": 0, "LENGTH": 0,
    "DRYING_TEMP": 0, "DRYING_TIME": 0, "HOTEND_MAX_TEMP": 0, "HOTEND_MIN_TEMP": 0,
    "BED_TYPE": 0, "BED_TEMP": 0, "FIRST_LAYER_TEMP": 0, "OTHER_LAYER_TEMP": 0,
    "SKU": 0, "MF_DATE": "19700101", "RSA_KEY_VERSION": 0, "OFFICIAL": False, "CARD_UID": 0,
}

QIDI_MAKER = 0x01

# material code, colour code, expected material, expected sub-type, expected RGB.
KNOWN_SPOOLS = (
    (0x02, 0x01, "PLA", "Matte", 0xFFFFFF),
    (0x29, 0x0B, "PETG", "", 0x1714B0),
    (0x29, 0x12, "PETG", "", 0xFF362D),
    (0x29, 0x14, "PETG", "", 0x898F9B),
)


def build_block(material_code: int, color_code: int, maker_code: int = QIDI_MAKER) -> bytes:
    """A QIDI payload block: three codes, then the all-zero tail that is its signature."""
    return bytes((material_code, color_code, maker_code)).ljust(BLOCK_BYTES, b"\x00")


def test_decodes_every_confirmed_spool() -> None:
    for material_code, color_code, material, sub_type, rgb in KNOWN_SPOOLS:
        info = decode(build_block(material_code, color_code), CARD_UID, dict(TEMPLATE))
        assert info is not None
        assert info["MAIN_TYPE"] == material
        assert info["SUB_TYPE"] == sub_type
        assert info["RGB_1"] == rgb
        assert info["ARGB_COLOR"] == 0xFF000000 | rgb
        assert info["COLOR_NUMS"] == 1


def test_qidi_maker_code_reads_as_genuine() -> None:
    info = decode(build_block(0x02, 0x01), CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["VENDOR"] == "QIDI"
    assert info["MANUFACTURER"] == "QIDI"
    assert info["OFFICIAL"] is True
    assert info["CARD_UID"] == CARD_UID


def test_other_maker_code_reads_as_compatible() -> None:
    info = decode(build_block(0x02, 0x01, maker_code=0x07), CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["VENDOR"] == "QIDI-compatible"
    assert info["MANUFACTURER"] == "QIDI-compatible"
    assert info["OFFICIAL"] is False


def test_unknown_material_code_is_reported_not_guessed() -> None:
    info = decode(build_block(0x7E, 0x01), CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["MAIN_TYPE"] == "UNKNOWN"
    assert info["SUB_TYPE"] == "QIDI material 0x7e"


def test_unknown_color_code_leaves_the_colour_alone() -> None:
    info = decode(build_block(0x02, 0x7E), CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["RGB_1"] == TEMPLATE["RGB_1"]
    assert info["ARGB_COLOR"] == TEMPLATE["ARGB_COLOR"]


def test_a_qidi_tag_carries_no_sku_or_weight() -> None:
    """A material code is not a SKU: writing it there matched the spool to a foreign filament."""
    info = decode(build_block(0x02, 0x01), CARD_UID, dict(TEMPLATE))
    assert info is not None
    assert info["SKU"] == 0
    assert info["WEIGHT"] == 0
    assert info["DIAMETER"] == 0
    assert info["HOTEND_MIN_TEMP"] == 0
    assert info["MF_DATE"] == "19700101"


def test_block_with_a_written_tail_is_declined() -> None:
    foreign = bytearray(build_block(0x02, 0x01))
    foreign[8] = 0x42
    assert decode(bytes(foreign), CARD_UID, dict(TEMPLATE)) is None


def test_block_with_a_zero_code_is_declined() -> None:
    assert decode(build_block(0x00, 0x01), CARD_UID, dict(TEMPLATE)) is None
    assert decode(build_block(0x02, 0x00), CARD_UID, dict(TEMPLATE)) is None
    assert decode(build_block(0x02, 0x01, maker_code=0x00), CARD_UID, dict(TEMPLATE)) is None


def test_short_block_is_declined() -> None:
    assert decode(build_block(0x02, 0x01)[:8], CARD_UID, dict(TEMPLATE)) is None
    assert not looks_like_qidi(build_block(0x02, 0x01)[:15])


def test_missing_block_is_declined() -> None:
    assert decode(None, CARD_UID, dict(TEMPLATE)) is None


def test_the_template_is_not_mutated() -> None:
    template = dict(TEMPLATE)
    decode(build_block(0x02, 0x01), CARD_UID, template)
    assert template == TEMPLATE
