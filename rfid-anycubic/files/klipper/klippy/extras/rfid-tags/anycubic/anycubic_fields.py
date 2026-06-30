"""Clean-room Anycubic ACE decoder - the agreed-across-sources NTAG21x fields only.

Anycubic ACE writes a plaintext (no key) little-endian block into NTAG21x user memory,
anchored by a 4-byte magic `7B 00 65 00` at page 4 (the 0x65 byte is the ACE format
version). This decoder ships ONLY the fields that the public reverse engineering
(DnG-Crafts/ACE-RFID and SimplyPrint) agrees on:

    page 4   magic 7B 00 65 00         (found by scan; offsets below are relative to it)
    page 10  brand   ASCII, null-padded
    page 15  material ASCII, null-padded
    page 24  nozzle temp min/max       (u16 LE pair, degC)
    page 29  bed temp min/max          (u16 LE pair, degC)

Three fields are DELIBERATELY NOT decoded because the public sources disagree and there is
no published real dump to break the tie: the SKU field length (12 vs 16 bytes), the color
byte order (ARGB vs ABGR at page 20), and page 31 (weight vs unknown). Decoding those would
be guessing; they wait for one tester dump. So this decoder yields brand, material, and
temperatures - the dispute-free core - and leaves color/diameter/weight at the template
default.

Pure helper: stdlib only, no relative imports, unit-testable. The registration shell
supplies the FILAMENT_INFO_STRUCT template.
"""
import copy
from typing import Any

ANYCUBIC_VENDOR = "Anycubic"
MAGIC = bytes((0x7B, 0x00, 0x65, 0x00))

# Offsets RELATIVE to the magic at page 4 (each NTAG page is 4 bytes), little-endian.
BRAND_OFFSET = 24           # page 10
BRAND_MAX = 16
MATERIAL_OFFSET = 44        # page 15
MATERIAL_MAX = 32
NOZZLE_MIN_OFFSET = 80      # page 24, u16 LE
NOZZLE_MAX_OFFSET = 82
BED_MIN_OFFSET = 100        # page 29, u16 LE
BED_MAX_OFFSET = 102
BLOCK_LEN = 104             # bytes past the magic this decoder reads (through bed temp)

CARD_UID_INDEXES = (0, 1, 2, 4, 5, 6, 7)
CARD_UID_MIN_BYTES = 8
PRINTABLE_MIN = 0x20
PRINTABLE_MAX = 0x7F


def _u16_le(dump: bytes, offset: int) -> int:
    return dump[offset] | (dump[offset + 1] << 8)


def _ascii(dump: bytes, offset: int, limit: int) -> str:
    raw = dump[offset:offset + limit].split(b"\x00", 1)[0]
    return "".join(chr(byte) for byte in raw if PRINTABLE_MIN <= byte < PRINTABLE_MAX).strip()


def _card_uid(dump: bytes) -> list[int]:
    if len(dump) < CARD_UID_MIN_BYTES:
        return []
    return [dump[index] for index in CARD_UID_INDEXES]


def find_block_start(dump: bytes) -> int | None:
    start = dump.find(MAGIC)
    if start < 0 or start + BLOCK_LEN > len(dump):
        return None
    return start


def _apply_temperatures(dump: bytes, magic: int, info: dict[str, Any]) -> None:
    info["HOTEND_MIN_TEMP"] = _u16_le(dump, magic + NOZZLE_MIN_OFFSET)
    info["HOTEND_MAX_TEMP"] = _u16_le(dump, magic + NOZZLE_MAX_OFFSET)
    info["FIRST_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]
    info["OTHER_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]
    info["BED_TEMP"] = _u16_le(dump, magic + BED_MAX_OFFSET)


def build_struct(dump: bytes, template: dict[str, Any]) -> dict[str, Any] | None:
    magic = find_block_start(dump)
    if magic is None:
        return None
    info = copy.deepcopy(template)
    info["VENDOR"] = ANYCUBIC_VENDOR
    info["MANUFACTURER"] = ANYCUBIC_VENDOR
    brand = _ascii(dump, magic + BRAND_OFFSET, BRAND_MAX)
    if brand:
        info["VENDOR"] = brand
    material = _ascii(dump, magic + MATERIAL_OFFSET, MATERIAL_MAX).upper()
    if material:
        info["MAIN_TYPE"] = material
    _apply_temperatures(dump, magic, info)
    info["CARD_UID"] = _card_uid(dump)
    info["OFFICIAL"] = True
    return info
