"""Clean-room OpenTag3D (queengooborg) payload decoder.

OpenTag3D stores filament data as a big-endian binary block inside an NDEF record
of MIME type ``application/opentag3d``. This module decodes that payload into a
FILAMENT_INFO_STRUCT. Read-only. Field offsets are payload-relative and taken
verbatim from the public OpenTag3D spec (opentag3d.info/spec.html, _data/spec.json),
implemented clean-room from the documented layout (no third-party code reused).

Pure helper module: stdlib only, no relative imports, so it is unit-testable in
isolation. The registration shell (``rfid_tag_opentag.py``) supplies the
FILAMENT_INFO_STRUCT template at runtime.
"""
import copy
from typing import Any

Record = dict[str, Any]

OPENTAG_MIME_TYPE = "application/opentag3d"

# Payload-relative byte offsets, big-endian, per the public OpenTag3D spec v1.
TAG_VERSION_OFFSET = 0x00
BASE_MATERIAL_OFFSET = 0x02
BASE_MATERIAL_LEN = 5
MATERIAL_MODIFIERS_OFFSET = 0x07
MATERIAL_MODIFIERS_LEN = 5
MANUFACTURER_OFFSET = 0x1B
MANUFACTURER_LEN = 16
COLOR_1_OFFSET = 0x4B
# Colours 2..4 of a multi-colour spool; a single-colour spool leaves them transparent black.
SECONDARY_COLOR_OFFSETS = (0x50, 0x54, 0x58)
# Spec v2.000 moved every field; on a v2 tag the v1 colour 2..4 bytes hold its serial number.
FIRST_V2_TAG_VERSION = 2000
DIAMETER_OFFSET = 0x5C
WEIGHT_OFFSET = 0x5E
PRINT_TEMP_OFFSET = 0x60
BED_TEMP_OFFSET = 0x61
MIN_PRINT_TEMP_OFFSET = 0xB4
MAX_PRINT_TEMP_OFFSET = 0xB5
MAX_BED_TEMP_OFFSET = 0xB7

# Shortest payload that still carries every core field this decoder reads (through bed temp).
CORE_MIN_LENGTH = BED_TEMP_OFFSET + 1
# Shortest payload that carries the extended min/max temperatures (through max bed temp).
EXTENDED_TEMP_MIN_LENGTH = MAX_BED_TEMP_OFFSET + 1

TEMP_SCALE = 5                # spec stores temperatures as degrees Celsius / 5
MICROMETRE_PER_CENTI_MM = 10  # spec stores diameter in micrometres; the struct uses centi-mm
RGB_MASK = 0xFFFFFF
ALPHA_SHIFT = 24
RED_SHIFT = 16
GREEN_SHIFT = 8
RGBA_BYTES = 4
ALPHA_INDEX = 3
TRANSPARENT_BLACK = bytes(RGBA_BYTES)


def _text(payload: bytes, offset: int, length: int) -> str:
    raw = payload[offset:offset + length]
    return raw.decode("utf-8", errors="ignore").rstrip("\x00").strip()


def _u16_be(payload: bytes, offset: int) -> int:
    return (payload[offset] << GREEN_SHIFT) | payload[offset + 1]


def select_opentag_payload(records: list[Record]) -> bytes | None:
    matches = (
        bytes(record.get("payload") or b"")
        for record in records
        if record.get("mime_type") == OPENTAG_MIME_TYPE
    )
    long_enough = (payload for payload in matches if len(payload) >= CORE_MIN_LENGTH)
    return next(long_enough, None)


def _apply_identity(payload: bytes, info: dict[str, Any]) -> None:
    manufacturer = _text(payload, MANUFACTURER_OFFSET, MANUFACTURER_LEN)
    main_type = _text(payload, BASE_MATERIAL_OFFSET, BASE_MATERIAL_LEN).upper()
    sub_type = _text(payload, MATERIAL_MODIFIERS_OFFSET, MATERIAL_MODIFIERS_LEN)
    info["VENDOR"] = manufacturer or info["VENDOR"]
    info["MANUFACTURER"] = manufacturer or info["MANUFACTURER"]
    info["MAIN_TYPE"] = main_type or info["MAIN_TYPE"]
    info["SUB_TYPE"] = sub_type or info["SUB_TYPE"]


def _rgba(payload: bytes, offset: int) -> bytes:
    return payload[offset:offset + RGBA_BYTES]


def _rgb(rgba: bytes) -> int:
    return (rgba[0] << RED_SHIFT) | (rgba[1] << GREEN_SHIFT) | rgba[2]


def _secondary_colors(payload: bytes) -> list[bytes]:
    if _u16_be(payload, TAG_VERSION_OFFSET) >= FIRST_V2_TAG_VERSION:
        return []
    secondaries = [_rgba(payload, offset) for offset in SECONDARY_COLOR_OFFSETS]
    return [rgba for rgba in secondaries if rgba != TRANSPARENT_BLACK]


def _spool_colors(payload: bytes) -> list[bytes]:
    return [_rgba(payload, COLOR_1_OFFSET), *_secondary_colors(payload)]


def _apply_color(payload: bytes, info: dict[str, Any]) -> None:
    colors = _spool_colors(payload)
    first_color = colors[0]
    alpha = first_color[ALPHA_INDEX]
    info.update({f"RGB_{slot}": _rgb(color) for slot, color in enumerate(colors, start=1)})
    info["ALPHA"] = alpha
    info["COLOR_NUMS"] = len(colors)
    info["ARGB_COLOR"] = alpha << ALPHA_SHIFT | _rgb(first_color)


def _apply_dimensions(payload: bytes, info: dict[str, Any]) -> None:
    info["DIAMETER"] = _u16_be(payload, DIAMETER_OFFSET) // MICROMETRE_PER_CENTI_MM
    info["WEIGHT"] = _u16_be(payload, WEIGHT_OFFSET)


def _apply_temperatures(payload: bytes, info: dict[str, Any]) -> None:
    if len(payload) >= EXTENDED_TEMP_MIN_LENGTH:
        info["HOTEND_MIN_TEMP"] = payload[MIN_PRINT_TEMP_OFFSET] * TEMP_SCALE
        info["HOTEND_MAX_TEMP"] = payload[MAX_PRINT_TEMP_OFFSET] * TEMP_SCALE
        info["BED_TEMP"] = payload[MAX_BED_TEMP_OFFSET] * TEMP_SCALE
    else:
        print_temp = payload[PRINT_TEMP_OFFSET] * TEMP_SCALE
        info["HOTEND_MIN_TEMP"] = print_temp
        info["HOTEND_MAX_TEMP"] = print_temp
        info["BED_TEMP"] = payload[BED_TEMP_OFFSET] * TEMP_SCALE
    info["FIRST_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]
    info["OTHER_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]


def build_struct(
    records: list[Record], card_uid: list[int], template: dict[str, Any],
) -> dict[str, Any] | None:
    payload = select_opentag_payload(records)
    if payload is None:
        return None
    info = copy.deepcopy(template)
    _apply_identity(payload, info)
    _apply_color(payload, info)
    _apply_dimensions(payload, info)
    _apply_temperatures(payload, info)
    info["CARD_UID"] = card_uid
    info["OFFICIAL"] = True
    return info
