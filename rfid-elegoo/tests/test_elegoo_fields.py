"""Regression tests for the Elegoo decoder, anchored on a real factory spool.

REAL_TAG_PAGES is the complete memory of one factory Elegoo Centauri spool (Feiju chip, UID
53:CD:83:09:30:00:04) as read by NXP TagInfo, byte for byte. Its label says: PLA, "Sea Green",
1.75 mm, 1 kg, printing temperature 190 to 230 C. Every expectation below that names a field value
comes from that label, not from the decoder.

0.1.3 decoded this same tag as MAIN_TYPE '\\x00\\x00V', DIAMETER 39423, WEIGHT 190, because it
followed the published guide's byte-packed field table; the factory tag is page-aligned instead.
test_real_factory_spool_matches_its_label fails on 0.1.3 and passes from 0.1.4.
"""
import pytest
from elegoo_fields import build_struct, decode_material

REAL_TAG_PAGES = (
    "53 CD 83 95", "09 30 00 04", "3D 48 00 00", "E1 10 12 00",  # 0x00 UID, lock, CC
    "01 03 A0 0C", "34 03 0F D1", "01 0B 55 02", "65 6C 65 67",  # 0x04 NDEF: elegoo.com URI
    "6F 6F 2E 63", "6F 6D FE 00", "00 00 00 00", "00 00 00 00",  # 0x08
    "00 00 00 00", "00 00 00 00", "00 00 00 00", "00 00 00 00",  # 0x0C
    "36 EE EE EE", "EE 00 00 00", "00 80 76 65", "00 00 00 00",  # 0x10 Elegoo block
    "09 C2 99 FF", "00 BE 00 E6", "00 00 00 00", "00 AF 03 E8",  # 0x14
    "00 36 C8 00", "00 00 00 00", "00 00 00 00", "00 00 00 00",  # 0x18
    "00 00 00 00", "00 00 00 00", "00 00 00 00", "00 00 00 00",  # 0x1C
    "00 00 00 00", "00 00 00 00", "00 00 00 00", "00 00 00 00",  # 0x20
    "00 00 00 00", "00 00 00 00", "00 00 00 00", "00 00 00 00",  # 0x24
    "00 00 00 BD", "04 00 00 FF", "00 05 00 00", "00 00 00 00",  # 0x28 NTAG213-style config
)
REAL_BLOCK_PAGE = 0x10
REAL_UID = [0x53, 0xCD, 0x83, 0x09, 0x30, 0x00, 0x04]
PAGE_BYTES = 4

TEMPLATE = {
    "VERSION": 0, "VENDOR": "NONE", "MANUFACTURER": "NONE", "MAIN_TYPE": "NONE",
    "SUB_TYPE": "NONE", "TRAY": 0, "ALPHA": 0xFF, "MULTI_MODE": 0, "COLOR_NUMS": 1,
    "ARGB_COLOR": 0xFFFFFFFF, "RGB_1": 0xFFFFFF, "RGB_2": 0xFFFFFF, "RGB_3": 0xFFFFFF,
    "RGB_4": 0xFFFFFF, "RGB_5": 0xFFFFFF, "DIAMETER": 0, "WEIGHT": 0, "LENGTH": 0,
    "DRYING_TEMP": 0, "DRYING_TIME": 0, "HOTEND_MAX_TEMP": 0, "HOTEND_MIN_TEMP": 0,
    "BED_TYPE": 0, "BED_TEMP": 0, "FIRST_LAYER_TEMP": 0, "OTHER_LAYER_TEMP": 0,
    "SKU": 0, "MF_DATE": "19700101", "RSA_KEY_VERSION": 0, "OFFICIAL": False, "CARD_UID": 0,
}

# ELEGOO's published material table, which the decimal-digit rule must reproduce exactly.
GUIDE_MATERIAL_CODES = (
    ("00 80 76 65", "PLA"), ("80 69 84 71", "PETG"), ("00 65 66 83", "ABS"),
    ("00 84 80 85", "TPU"), ("00 00 80 65", "PA"), ("00 67 80 69", "CPE"),
    ("00 00 80 67", "PC"), ("00 80 86 65", "PVA"), ("00 65 83 65", "ASA"),
)


def _dump(pages=REAL_TAG_PAGES) -> bytes:
    return b"".join(bytes.fromhex(page) for page in pages)


def _with_page(page_number: int, page_hex: str) -> bytes:
    pages = list(REAL_TAG_PAGES)
    pages[page_number] = page_hex
    return _dump(pages)


def _decode(dump: bytes) -> dict:
    info = build_struct(dump, dict(TEMPLATE))
    assert info is not None
    return info


def test_real_factory_spool_matches_its_label() -> None:
    info = _decode(_dump())
    assert info["VENDOR"] == "Elegoo"
    assert info["MANUFACTURER"] == "Elegoo"
    assert info["MAIN_TYPE"] == "PLA"
    assert info["RGB_1"] == 0x09C299
    assert info["ARGB_COLOR"] == 0xFF09C299
    assert info["HOTEND_MIN_TEMP"] == 190
    assert info["HOTEND_MAX_TEMP"] == 230
    assert info["DIAMETER"] == 175
    assert info["WEIGHT"] == 1000
    assert info["OFFICIAL"] is True


def test_card_uid_skips_the_bcc_byte() -> None:
    assert _decode(_dump())["CARD_UID"] == REAL_UID


def test_unconfirmed_fields_keep_the_template_default() -> None:
    info = _decode(_dump())
    assert info["SUB_TYPE"] == "NONE"
    assert info["MF_DATE"] == "19700101"
    assert info["BED_TEMP"] == 0


def test_a_nonzero_subtype_page_is_still_not_decoded() -> None:
    # The guide encodes sub-type two ways and no real tag has shown one yet.
    info = _decode(_with_page(REAL_BLOCK_PAGE + 3, "00 00 43 46"))
    assert info["SUB_TYPE"] == "NONE"


@pytest.mark.parametrize(("material_page", "material"), GUIDE_MATERIAL_CODES)
def test_decimal_digit_rule_reproduces_the_guide_table(material_page: str, material: str) -> None:
    assert decode_material(bytes.fromhex(material_page)) == material


def test_plain_ascii_material_is_left_undecoded_not_guessed() -> None:
    # The guide's other example spells "PLA " in plain ASCII; no factory tag does.
    info = _decode(_with_page(REAL_BLOCK_PAGE + 2, "50 4C 41 20"))
    assert info["MAIN_TYPE"] == "NONE"
    assert info["WEIGHT"] == 1000


def test_empty_material_page_is_left_undecoded() -> None:
    assert decode_material(bytes(PAGE_BYTES)) is None


def test_block_is_found_on_the_page_the_guide_names() -> None:
    # The guide puts the block at page 0x04; factory tags put it after the NDEF message.
    header_pages = REAL_TAG_PAGES[:4]
    block_pages = REAL_TAG_PAGES[REAL_BLOCK_PAGE:REAL_BLOCK_PAGE + 8]
    info = _decode(_dump(header_pages + block_pages))
    assert info["MAIN_TYPE"] == "PLA"
    assert info["WEIGHT"] == 1000


# The first five pages of a real blank NTAG215 sticker (non-genuine NXP), as read by NXP TagInfo
# before and after the Elegoo block was copied onto it: UID, lock bytes, capability container, and
# an empty NDEF TLV. The copy read on a real U1 (2026-09-23) under this UID.
CLONE_STICKER_HEAD = ("04 AA 91 B7", "2B 47 59 80", "B5 48 00 00", "E1 10 3E 00", "03 00 FE 00")
CLONE_UID = [0x04, 0xAA, 0x91, 0x2B, 0x47, 0x59, 0x80]
NTAG215_READ_PAGES = 132
BLOCK_PAGES_COPIED = 9  # pages 0x10 to 0x18, the nine written to the sticker


def test_a_copy_on_an_ntag215_sticker_decodes_under_its_own_uid() -> None:
    blank_pages = NTAG215_READ_PAGES - len(CLONE_STICKER_HEAD)
    pages = list(CLONE_STICKER_HEAD) + ["00 00 00 00"] * blank_pages
    for page in range(REAL_BLOCK_PAGE, REAL_BLOCK_PAGE + BLOCK_PAGES_COPIED):
        pages[page] = REAL_TAG_PAGES[page]
    info = _decode(_dump(tuple(pages)))
    assert info["CARD_UID"] == CLONE_UID
    assert info["MAIN_TYPE"] == "PLA"
    assert info["RGB_1"] == 0x09C299
    assert info["HOTEND_MIN_TEMP"] == 190
    assert info["HOTEND_MAX_TEMP"] == 230
    assert info["DIAMETER"] == 175
    assert info["WEIGHT"] == 1000


def test_no_signature_returns_none() -> None:
    assert build_struct(_dump(REAL_TAG_PAGES[:REAL_BLOCK_PAGE]), dict(TEMPLATE)) is None


def test_truncated_block_returns_none() -> None:
    truncated = _dump()[:REAL_BLOCK_PAGE * PAGE_BYTES + 31]
    assert build_struct(truncated, dict(TEMPLATE)) is None


def test_signature_off_a_page_boundary_returns_none() -> None:
    shifted = bytes(1) + _dump()
    assert build_struct(shifted, dict(TEMPLATE)) is None
