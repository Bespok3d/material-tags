# ruff: noqa: PLR2004  Tests assert on literal field values/offsets by design.
"""Regression tests for the Anycubic ACE raw-page decoder.

Two layers of coverage:

- Synthetic tests build a page dump field by field, using the module's own offset
  constants, and pin the produced FILAMENT_INFO_STRUCT output for each field in isolation
  (including the version scan and decline rules).
- Regression tests replay the exact raw dumps captured from real tags during this plugin's
  development (one first-party read, two independently sourced), byte for byte, and pin the
  full decoded output against what was manually verified at the time against the physical
  spool's box, seller listing, and an independent SKU/color catalog. These exist to catch
  any future change that would silently alter a real, already-confirmed decode.
"""
from anycubic_fields import (
    BED_MAX_OFFSET,
    BED_MIN_OFFSET,
    BLOCK_LEN,
    BRAND_OFFSET,
    COLOR_OFFSET,
    DIAMETER_OFFSET,
    LENGTH_OFFSET,
    MAGIC_PREFIX,
    MATERIAL_OFFSET,
    NOZZLE_MAX_OFFSET,
    NOZZLE_MIN_OFFSET,
    PRINT_SPEED_MAX_OFFSET,
    PRINT_SPEED_MIN_OFFSET,
    SKU_OFFSET,
    WEIGHT_OFFSET,
    build_struct,
    find_block_start,
)

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


def _set(block: bytearray, offset: int, data: bytes) -> None:
    block[offset:offset + len(data)] = data


def build_block(
    version: int = 0x65,
    sku: str = "",
    brand: str = "AC",
    material: str = "PLA",
    color_rgb: tuple[int, int, int] = (0xFF, 0xFF, 0xFF),
    alpha: int = 0xFF,
    print_speed: tuple[int, int] = (0, 0),
    nozzle: tuple[int, int] = (205, 245),
    bed: tuple[int, int] = (50, 60),
    diameter_mm: float = 0.0,
    length_m: int = 0,
    weight_g: int = 0,
) -> bytes:
    block = bytearray(BLOCK_LEN)
    _set(block, 0, MAGIC_PREFIX)
    block[2] = version
    block[3] = 0x00
    if sku:
        _set(block, SKU_OFFSET, sku.encode())
    if brand:
        _set(block, BRAND_OFFSET, brand.encode())
    if material:
        _set(block, MATERIAL_OFFSET, material.encode())
    red, green, blue = color_rgb
    _set(block, COLOR_OFFSET, bytes((alpha, blue, green, red)))
    _set(block, PRINT_SPEED_MIN_OFFSET, _u16(print_speed[0]))
    _set(block, PRINT_SPEED_MAX_OFFSET, _u16(print_speed[1]))
    _set(block, NOZZLE_MIN_OFFSET, _u16(nozzle[0]))
    _set(block, NOZZLE_MAX_OFFSET, _u16(nozzle[1]))
    _set(block, BED_MIN_OFFSET, _u16(bed[0]))
    _set(block, BED_MAX_OFFSET, _u16(bed[1]))
    _set(block, DIAMETER_OFFSET, _u16(round(diameter_mm * 100)))
    _set(block, LENGTH_OFFSET, _u16(length_m))
    _set(block, WEIGHT_OFFSET, _u16(weight_g))
    return bytes(block)


def _dump_from_hex(page_groups: str) -> bytes:
    """Rebuilds a raw dump from the same space-separated per-page hex format logged by
    rfid_tag_anycubic.py, so regression fixtures can be pasted straight from a captured
    log line."""
    return b"".join(bytes.fromhex(group) for group in page_groups.split())


# --- synthetic, field-by-field coverage -------------------------------------------------

def test_decodes_brand_material_temps():
    dump = UID_HEADER + build_block(brand="Anycubic", material="PETG", nozzle=(205, 245),
                                     bed=(50, 60))
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    assert info["VENDOR"] == "Anycubic"
    assert info["MAIN_TYPE"] == "PETG"
    assert info["HOTEND_MIN_TEMP"] == 205
    assert info["HOTEND_MAX_TEMP"] == 245
    assert info["FIRST_LAYER_TEMP"] == 205
    assert info["OTHER_LAYER_TEMP"] == 205
    assert info["BED_MIN_TEMP"] == 50
    assert info["BED_TEMP"] == 60
    assert info["CARD_UID"] == EXPECTED_UID
    assert info["OFFICIAL"] is True


def test_decodes_version_byte():
    dump = UID_HEADER + build_block(version=0x64)
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    assert info["VERSION"] == 0x64


def test_accepts_both_known_versions():
    for version in (0x65, 0x64):
        dump = UID_HEADER + build_block(version=version)
        assert build_struct(dump, dict(TEMPLATE)) is not None


def test_rejects_unknown_version():
    dump = UID_HEADER + build_block(version=0x99)
    assert build_struct(dump, dict(TEMPLATE)) is None


def test_skips_false_positive_prefix_before_real_magic():
    # A stray 7B 00 with a bad trailer byte should not be mistaken for the real block.
    false_positive = bytes((0x7B, 0x00, 0x65, 0x01))
    dump = UID_HEADER + false_positive + build_block()
    magic = find_block_start(dump)
    assert magic is not None
    assert magic == len(UID_HEADER) + len(false_positive)


def test_decodes_color_argb_and_rgb():
    # Peach pink, the real non-symmetric sample that settled the byte order dispute.
    dump = UID_HEADER + build_block(color_rgb=(0xFE, 0xC1, 0x96), alpha=0xFF)
    info = build_struct(dump, dict(TEMPLATE))
    assert info["ALPHA"] == 0xFF
    assert info["ARGB_COLOR"] == 0xFFFEC196
    assert info["RGB_1"] == 0xFEC196


def test_decodes_diameter_length_weight():
    dump = UID_HEADER + build_block(diameter_mm=1.75, length_m=330, weight_g=1000)
    info = build_struct(dump, dict(TEMPLATE))
    assert info["DIAMETER"] == 1.75
    assert info["LENGTH"] == 330
    assert info["WEIGHT"] == 1000


def test_decodes_print_speed():
    dump = UID_HEADER + build_block(print_speed=(50, 200))
    info = build_struct(dump, dict(TEMPLATE))
    assert info["PRINT_SPEED_MIN"] == 50
    assert info["PRINT_SPEED_MAX"] == 200


def test_print_speed_defaults_to_zero_when_unpopulated():
    # Confirmed on two real samples (PLA Spezial, ASA): the field can legitimately be zero.
    dump = UID_HEADER + build_block()
    info = build_struct(dump, dict(TEMPLATE))
    assert info["PRINT_SPEED_MIN"] == 0
    assert info["PRINT_SPEED_MAX"] == 0


def test_sku_decoded_when_present():
    dump = UID_HEADER + build_block(sku="AHPLPBK-108")
    info = build_struct(dump, dict(TEMPLATE))
    assert info["SKU"] == "AHPLPBK-108"


def test_sku_left_at_default_when_blank():
    dump = UID_HEADER + build_block(sku="")
    info = build_struct(dump, dict(TEMPLATE))
    assert info["SKU"] == 0


def test_default_vendor_when_brand_blank():
    info = build_struct(UID_HEADER + build_block(brand=""), dict(TEMPLATE))
    assert info["VENDOR"] == "Anycubic"


def test_magic_found_at_any_offset():
    dump = UID_HEADER + bytes(8) + build_block()
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    assert info["HOTEND_MAX_TEMP"] == 245


def test_no_magic_declines():
    assert build_struct(UID_HEADER + bytes(BLOCK_LEN), dict(TEMPLATE)) is None


def test_truncated_block_declines():
    # Cut into the block so weight (the last decoded field) no longer fits.
    assert build_struct((UID_HEADER + build_block())[:-4], dict(TEMPLATE)) is None


def test_does_not_mutate_template():
    build_struct(UID_HEADER + build_block(), TEMPLATE)
    assert TEMPLATE["VENDOR"] == "NONE"
    assert TEMPLATE["OFFICIAL"] is False


# --- regression tests against real captured dumps ---------------------------------------

def test_regression_first_party_pla_plus_black():
    # AHPLPBK-108, black PLA+, box-matched: SKU, color (#212721), 1.75mm/330m/1000g,
    # 190-230 nozzle, 55-65 bed, 50-200 print speed. Version 0x65.
    dump = _dump_from_hex(
        "5330bd56 ad950001 39480000 e1101200 7b006500 4148504c 50424b2d 31303800 "
        "00000000 00000000 41430000 00000000 00000000 00000000 00000000 504c412b "
        "00000000 00000000 00000000 00000000 ff212721 00000000 00000000 3200c800 "
        "be00e600 00000000 00000000 00000000 00000000 37004100 af004a01 e8030000 "
        "00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 "
        "000000bd 04000004 47000000 00000000 00000000 5330bd56 ad950001 39480000"
    )
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    assert info["VERSION"] == 0x65
    assert info["SKU"] == "AHPLPBK-108"
    assert info["VENDOR"] == "AC"
    assert info["MAIN_TYPE"] == "PLA+"
    assert info["ALPHA"] == 0xFF
    assert info["ARGB_COLOR"] == 0xFF212721
    assert info["RGB_1"] == 0x212721
    assert info["DIAMETER"] == 1.75
    assert info["LENGTH"] == 330
    assert info["WEIGHT"] == 1000
    assert info["HOTEND_MIN_TEMP"] == 190
    assert info["HOTEND_MAX_TEMP"] == 230
    assert info["BED_MIN_TEMP"] == 55
    assert info["BED_TEMP"] == 65
    assert info["PRINT_SPEED_MIN"] == 50
    assert info["PRINT_SPEED_MAX"] == 200
    assert info["CARD_UID"] == [0x53, 0x30, 0xBD, 0xAD, 0x95, 0x00, 0x01]


def test_regression_third_party_pla_spezial_peach_pink():
    # HPL16-102, peach pink PLA Spezial, from independent German-language tag research.
    # Blank brand, version 0x64, print speed unpopulated (zero).
    pages = [
        "5313945c", "d3720001", "a0480000", "e1101200", "7b006400", "48504c31",
        "362d3130", "32000000", "00000000", "00000000", "00000000", "00000000",
        "00000000", "00000000", "00000000", "504c4100", "00000000", "00000000",
        "00000000", "00000000", "ff96c1fe", "00000000", "00000000", "00000000",
        "c800d200", "00000000", "00000000", "00000000", "00000000", "32003c00",
        "af004a01", "e8030000",
    ]
    dump = _dump_from_hex(" ".join(pages))
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    assert info["VERSION"] == 0x64
    assert info["SKU"] == "HPL16-102"
    assert info["VENDOR"] == "Anycubic"  # brand field is blank on this sample
    assert info["MAIN_TYPE"] == "PLA"
    assert info["ALPHA"] == 0xFF
    assert info["ARGB_COLOR"] == 0xFFFEC196
    assert info["RGB_1"] == 0xFEC196
    assert info["DIAMETER"] == 1.75
    assert info["LENGTH"] == 330
    assert info["WEIGHT"] == 1000
    assert info["HOTEND_MIN_TEMP"] == 200
    assert info["HOTEND_MAX_TEMP"] == 210
    assert info["BED_MIN_TEMP"] == 50
    assert info["BED_TEMP"] == 60
    assert info["PRINT_SPEED_MIN"] == 0
    assert info["PRINT_SPEED_MAX"] == 0
    assert info["CARD_UID"] == [0x53, 0x13, 0x94, 0xD3, 0x72, 0x00, 0x01]


def test_regression_third_party_asa_green_flash():
    # HASGF-106, ASA, from the independently sourced AnycubicNFCTaggerQT5 reference dump.
    # Higher-temperature material, version 0x65, print speed unpopulated (zero).
    pages = [
        "1d72f512", "610f1080", "fec00000", "e1101200", "7b006500", "48415347",
        "462d3130", "36000000", "00000000", "00000000", "41430000", "00000000",
        "00000000", "00000000", "00000000", "41534100", "00000000", "00000000",
        "00000000", "00000000", "ff008000", "00000000", "00000000", "00000000",
        "f0001801", "00000000", "00000000", "00000000", "00000000", "5a006e00",
        "af004a01", "e8030000",
    ]
    dump = _dump_from_hex(" ".join(pages))
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    assert info["VERSION"] == 0x65
    assert info["SKU"] == "HASGF-106"
    assert info["VENDOR"] == "AC"
    assert info["MAIN_TYPE"] == "ASA"
    assert info["ALPHA"] == 0xFF
    assert info["ARGB_COLOR"] == 0xFF008000
    assert info["RGB_1"] == 0x008000
    assert info["DIAMETER"] == 1.75
    assert info["LENGTH"] == 330
    assert info["WEIGHT"] == 1000
    assert info["HOTEND_MIN_TEMP"] == 240
    assert info["HOTEND_MAX_TEMP"] == 280
    assert info["BED_MIN_TEMP"] == 90
    assert info["BED_TEMP"] == 110
    assert info["PRINT_SPEED_MIN"] == 0
    assert info["PRINT_SPEED_MAX"] == 0
    assert info["CARD_UID"] == [0x1D, 0x72, 0xF5, 0x61, 0x0F, 0x10, 0x80]
