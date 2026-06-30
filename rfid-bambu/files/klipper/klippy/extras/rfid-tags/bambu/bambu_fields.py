"""Bambu filament-tag decode (pure, stdlib-only, unit-tested).

Clean-room from the PUBLIC Bambu-Research-Group memory map (BambuLabRfid.md). The reader
shell authenticates each sector with a derived key (see ``bambu_keys``) and hands this
module a block-indexed byte buffer: ``card_data[block * 16 + offset]`` is the same layout
the tag uses, so the offsets below read like the spec. All multi-byte numbers are
little-endian; the diameter is an IEEE-754 float32.

The struct fields and their units mirror the stock Snapmaker M1 parser (diameter in
hundredths of a millimetre, weight in grams, temperatures in Celsius), so the touchscreen
and Spoolman treat a Bambu spool exactly like a Snapmaker one.
"""
import struct
from typing import Any

VENDOR = "Bambu Lab"
MIN_BUFFER_LEN = 7 * 16  # through block 6 (temperatures)

BLOCK_UID = 0
BLOCK_FILAMENT_TYPE = 2
BLOCK_DETAILED_TYPE = 4
BLOCK_COLOR = 5
BLOCK_TEMPS = 6

UID_LEN = 4
DIAMETER_SCALE = 100  # mm float -> hundredths of a mm (1.75 -> 175)


def _u16_le(buf: list[int], offset: int) -> int:
    return buf[offset] | (buf[offset + 1] << 8)


def _f32_le(buf: list[int], offset: int) -> float:
    return float(struct.unpack("<f", bytes(buf[offset:offset + 4]))[0])


def _ascii(buf: list[int], offset: int, length: int) -> str:
    return bytes(buf[offset:offset + length]).decode("ascii", "ignore").rstrip("\x00").strip()


def _block(block: int, offset: int = 0) -> int:
    return block * 16 + offset


def _apply_identity(buf: list[int], info: dict[str, Any]) -> None:
    main_type = _ascii(buf, _block(BLOCK_FILAMENT_TYPE), 16).upper()
    if main_type:
        info["MAIN_TYPE"] = main_type
    detailed = _ascii(buf, _block(BLOCK_DETAILED_TYPE), 16)
    if detailed.upper().startswith(main_type):
        sub_type = detailed[len(main_type):].strip()
    else:
        sub_type = detailed
    if sub_type:
        info["SUB_TYPE"] = sub_type


def _apply_color(buf: list[int], info: dict[str, Any]) -> None:
    red, green, blue, alpha = buf[_block(BLOCK_COLOR)], buf[_block(BLOCK_COLOR, 1)], \
        buf[_block(BLOCK_COLOR, 2)], buf[_block(BLOCK_COLOR, 3)]
    info["RGB_1"] = (red << 16) | (green << 8) | blue
    info["ALPHA"] = alpha
    info["COLOR_NUMS"] = 1
    info["ARGB_COLOR"] = (alpha << 24) | info["RGB_1"]


def _apply_dimensions(buf: list[int], info: dict[str, Any]) -> None:
    info["WEIGHT"] = _u16_le(buf, _block(BLOCK_COLOR, 4))
    info["DIAMETER"] = round(_f32_le(buf, _block(BLOCK_COLOR, 8)) * DIAMETER_SCALE)


def _apply_temperatures(buf: list[int], info: dict[str, Any]) -> None:
    info["DRYING_TEMP"] = _u16_le(buf, _block(BLOCK_TEMPS, 0))
    info["DRYING_TIME"] = _u16_le(buf, _block(BLOCK_TEMPS, 2))
    info["BED_TYPE"] = _u16_le(buf, _block(BLOCK_TEMPS, 4))
    info["BED_TEMP"] = _u16_le(buf, _block(BLOCK_TEMPS, 6))
    info["HOTEND_MAX_TEMP"] = _u16_le(buf, _block(BLOCK_TEMPS, 8))
    info["HOTEND_MIN_TEMP"] = _u16_le(buf, _block(BLOCK_TEMPS, 10))
    info["FIRST_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]
    info["OTHER_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]


def decode(card_data: list[int] | None, template: dict[str, Any]) -> dict[str, Any] | None:
    """Decode a Bambu block buffer into a filament struct, or None if it is too short."""
    if card_data is None or len(card_data) < MIN_BUFFER_LEN:
        return None
    info = dict(template)
    info["VENDOR"] = VENDOR
    info["MANUFACTURER"] = VENDOR
    _apply_identity(card_data, info)
    _apply_color(card_data, info)
    _apply_dimensions(card_data, info)
    _apply_temperatures(card_data, info)
    info["CARD_UID"] = list(card_data[_block(BLOCK_UID):_block(BLOCK_UID) + UID_LEN])
    info["OFFICIAL"] = True
    return info
