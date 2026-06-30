"""Clean-room Elegoo filament decoder - the published EPC-256 / OpenRFID NTAG layout.

Elegoo writes a binary filament block into the NTAG user memory (data block at page 4,
byte 0x04), anchored by Elegoo's 4-byte 0xEEEEEEEE manufacturer marker that follows a
0x36 header. The fields below are at fixed offsets RELATIVE to that marker, big-endian,
per Elegoo's published spec and the OpenRFID/ELG-RFID layout:

    0x04 header 0x36
    0x05 marker EEEEEEEE        (found by scan; the offsets below are relative to it)
    0x09 product code (u16)
    0x0B material ASCII (4)     == marker + 6
    0x0F sub-type ASCII (4)     == marker + 10
    0x13 color RGB888 (3)       == marker + 14
    0x16 diameter u16 /100mm    == marker + 17
    0x18 weight u16 grams       == marker + 19

Elegoo's EPC-256 tags carry no temperatures, so this decoder fills only the fields the
layout actually has; everything else keeps the struct template default.

Pure helper: stdlib only, no relative imports, unit-testable. The registration shell
supplies the FILAMENT_INFO_STRUCT template.
"""
import copy
from typing import Any

ELEGOO_VENDOR = "Elegoo"
SIGNATURE = bytes((0xEE, 0xEE, 0xEE, 0xEE))

# Offsets RELATIVE to the 0xEEEEEEEE marker start, big-endian.
MATERIAL_OFFSET = 6
MATERIAL_LEN = 4
SUBTYPE_OFFSET = 10
SUBTYPE_LEN = 4
COLOR_OFFSET = 14           # 3 bytes R, G, B
DIAMETER_OFFSET = 17        # u16, hundredths-mm == the struct's centi-mm
WEIGHT_OFFSET = 19          # u16, grams
BLOCK_LEN = 21              # bytes past the marker this decoder reads (through weight)

CARD_UID_INDEXES = (0, 1, 2, 4, 5, 6, 7)
CARD_UID_MIN_BYTES = 8
RED_SHIFT = 16
GREEN_SHIFT = 8
OPAQUE_ALPHA = 0xFF
ALPHA_SHIFT = 24


def _u16_be(dump: bytes, offset: int) -> int:
    return (dump[offset] << GREEN_SHIFT) | dump[offset + 1]


def _ascii(dump: bytes, offset: int, length: int) -> str:
    return dump[offset:offset + length].decode("ascii", errors="ignore").rstrip("\x00").strip()


def _card_uid(dump: bytes) -> list[int]:
    if len(dump) < CARD_UID_MIN_BYTES:
        return []
    return [dump[index] for index in CARD_UID_INDEXES]


def find_block_start(dump: bytes) -> int | None:
    start = dump.find(SIGNATURE)
    if start < 0 or start + BLOCK_LEN > len(dump):
        return None
    return start


def _apply_color(dump: bytes, marker: int, info: dict[str, Any]) -> None:
    base = marker + COLOR_OFFSET
    rgb = (dump[base] << RED_SHIFT) | (dump[base + 1] << GREEN_SHIFT) | dump[base + 2]
    info["RGB_1"] = rgb
    info["COLOR_NUMS"] = 1
    info["ALPHA"] = OPAQUE_ALPHA
    info["ARGB_COLOR"] = OPAQUE_ALPHA << ALPHA_SHIFT | rgb


def build_struct(dump: bytes, template: dict[str, Any]) -> dict[str, Any] | None:
    marker = find_block_start(dump)
    if marker is None:
        return None
    info = copy.deepcopy(template)
    material = _ascii(dump, marker + MATERIAL_OFFSET, MATERIAL_LEN).upper()
    sub_type = _ascii(dump, marker + SUBTYPE_OFFSET, SUBTYPE_LEN)
    info["VENDOR"] = ELEGOO_VENDOR
    info["MANUFACTURER"] = ELEGOO_VENDOR
    info["MAIN_TYPE"] = material or info["MAIN_TYPE"]
    info["SUB_TYPE"] = sub_type or info["SUB_TYPE"]
    _apply_color(dump, marker, info)
    info["DIAMETER"] = _u16_be(dump, marker + DIAMETER_OFFSET)
    info["WEIGHT"] = _u16_be(dump, marker + WEIGHT_OFFSET)
    info["CARD_UID"] = _card_uid(dump)
    info["OFFICIAL"] = True
    return info
