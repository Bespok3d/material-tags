"""QIDI filament-tag decode (pure, stdlib-only, unit-tested).

A QIDI spool tag is a Mifare Classic 1K left on its factory default key, and the whole
payload sits in the first data block of sector 1: material code, colour code, manufacturer
code, then thirteen zero bytes. Nothing else on the card is written, so weight, diameter,
temperatures, dates and a SKU are simply not present on a QIDI tag; they stay at the
template default here rather than being invented. The material code in particular is NOT a
SKU: putting it in that field made Spoolman match the spool to an unrelated filament.

The thirteen zero bytes are the format signature: a Mifare card that opens with the default
key but has anything else in that tail is not a QIDI spool, and is declined so the next
vendor handler gets its turn.

The code tables hold only pairings confirmed against physical spools. An unrecognised code
is reported as its number, never guessed, so an unknown spool still tracks and still says
what QIDI wrote on it. doc/README.md points at the community list for wider coverage.
"""
import copy
from typing import Any

QIDI_VENDOR = "QIDI"
COMPATIBLE_VENDOR = "QIDI-compatible"
UNKNOWN_MATERIAL = "UNKNOWN"

BLOCK_BYTES = 16
MATERIAL_INDEX = 0
COLOR_INDEX = 1
MANUFACTURER_INDEX = 2
SIGNATURE_START = 3
QIDI_MANUFACTURER_CODE = 0x01
OPAQUE_ALPHA = 0xFF
ALPHA_SHIFT = 24

# Confirmed against physical spools only. Extend as real tags are read.
MATERIALS = {
    0x02: ("PLA", "Matte"),
    0x29: ("PETG", ""),
}

COLORS = {
    0x01: 0xFFFFFF,
    0x0B: 0x1714B0,
    0x12: 0xFF362D,
    0x14: 0x898F9B,
}


def looks_like_qidi(block: bytes) -> bool:
    """True when the block carries three non-zero codes and QIDI's all-zero tail."""
    if len(block) < BLOCK_BYTES:
        return False
    codes = (block[MATERIAL_INDEX], block[COLOR_INDEX], block[MANUFACTURER_INDEX])
    if 0x00 in codes:
        return False
    return not any(block[SIGNATURE_START:BLOCK_BYTES])


def _material_names(material_code: int) -> tuple[str, str]:
    known = MATERIALS.get(material_code)
    if known is None:
        return UNKNOWN_MATERIAL, f"QIDI material {material_code:#04x}"
    return known


def _apply_color(color_code: int, info: dict[str, Any]) -> None:
    """Paint the struct only when the colour code is one we have confirmed on a spool."""
    rgb = COLORS.get(color_code)
    if rgb is None:
        return
    info["RGB_1"] = rgb
    info["COLOR_NUMS"] = 1
    info["ALPHA"] = OPAQUE_ALPHA
    info["ARGB_COLOR"] = OPAQUE_ALPHA << ALPHA_SHIFT | rgb


def decode(
    block: bytes | None, card_uid: list[int], template: dict[str, Any],
) -> dict[str, Any] | None:
    """Decode sector 1's first data block into a filament struct, or None if not QIDI."""
    if block is None or not looks_like_qidi(block):
        return None
    manufacturer_code = block[MANUFACTURER_INDEX]
    is_qidi_brand = manufacturer_code == QIDI_MANUFACTURER_CODE
    info = copy.deepcopy(template)
    info["MAIN_TYPE"], info["SUB_TYPE"] = _material_names(block[MATERIAL_INDEX])
    info["VENDOR"] = QIDI_VENDOR if is_qidi_brand else COMPATIBLE_VENDOR
    info["MANUFACTURER"] = info["VENDOR"]
    info["OFFICIAL"] = is_qidi_brand
    info["CARD_UID"] = list(card_uid)
    _apply_color(block[COLOR_INDEX], info)
    return info
