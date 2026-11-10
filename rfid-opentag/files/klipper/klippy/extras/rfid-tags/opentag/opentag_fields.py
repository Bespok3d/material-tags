"""Clean-room OpenTag3D (queengooborg) payload decoder.

OpenTag3D stores filament data as a big-endian binary block inside an NDEF record
of MIME type ``application/opentag3d``. This module decodes that payload into a
FILAMENT_INFO_STRUCT. Read-only. Field offsets are payload-relative and taken
verbatim from the public OpenTag3D spec (opentag3d.info/spec.html, _data/spec.json),
implemented clean-room from the documented layout (no third-party code reused).
Spec v1 and v2 tags are decoded, each from its own layout. A tag of a newer major
version is not parsed, as the spec's reader guidelines require, and comes back as a
read error; a newer minor version is read without the warning the spec asks for.

Pure helper module: stdlib only, no relative imports, so it is unit-testable in
isolation. The registration shell (``rfid_tag_opentag.py``) supplies the
FILAMENT_INFO_STRUCT template at runtime.
"""
import copy
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

Record = dict[str, Any]
FilamentInfo = dict[str, Any]

OPENTAG_MIME_TYPE = "application/opentag3d"

# Payload-relative byte offsets, big-endian. Every spec version keeps the version and material here.
TAG_VERSION_OFFSET = 0x00
TAG_VERSION_LEN = 2
VERSION_PER_MAJOR = 1000      # the tag version has three implied decimals: 2004 is v2.004
BASE_MATERIAL_OFFSET = 0x02
BASE_MATERIAL_LEN = 5
MATERIAL_MODIFIERS_OFFSET = 0x07
MATERIAL_MODIFIERS_LEN = 5
MANUFACTURER_LEN = 16

# Spec v1 layout. Colors 2..4 of a multi-color spool follow color 1; unused ones are
# transparent black.
V1_MANUFACTURER_OFFSET = 0x1B
V1_COLOR_OFFSETS = (0x4B, 0x50, 0x54, 0x58)
V1_DIAMETER_OFFSET = 0x5C
V1_WEIGHT_OFFSET = 0x5E
V1_PRINT_TEMP_OFFSET = 0x60
V1_BED_TEMP_OFFSET = 0x61
V1_MIN_PRINT_TEMP_OFFSET = 0xB4
V1_MAX_PRINT_TEMP_OFFSET = 0xB5
V1_MAX_BED_TEMP_OFFSET = 0xB7
# Shortest payload that still carries every core field this decoder reads (through bed temp).
V1_CORE_MIN_LENGTH = V1_BED_TEMP_OFFSET + 1
# A v1 tag without the extended block (NTAG213) has not set its min/max temperatures, the same
# as one that leaves them at 0, so the missing bytes read as 0 up to the last one decoded.
V1_ZERO_FILLED_LENGTH = V1_MAX_BED_TEMP_OFFSET + 1

# Spec v2 layout (v2.000 moved every field after the material modifiers).
V2_MANUFACTURER_OFFSET = 0x0C
V2_COLOR_OFFSETS = (0x3C, 0x40, 0x44, 0x48)
V2_DIAMETER_OFFSET = 0x8C
V2_PRINT_TEMP_OFFSET = 0x90
V2_MIN_PRINT_TEMP_OFFSET = 0x91
V2_MAX_PRINT_TEMP_OFFSET = 0x92
V2_BED_TEMP_OFFSET = 0x94
V2_WEIGHT_OFFSET = 0x9E
# Weight is the last required v2 field. Missing bytes read as 0x00, so a payload that ends
# before the weight leaves it unset, while one that ends inside it only dropped a zero low byte.
V2_MIN_LENGTH = V2_WEIGHT_OFFSET + 1
# The spec reads every byte missing from the end of the payload, up to address 0xDF, as 0x00.
V2_ZERO_FILLED_LENGTH = 0xE0

TEMP_SCALE = 5                # spec stores temperatures as degrees Celsius / 5
MICROMETRE_PER_CENTI_MM = 10  # spec stores diameter in micrometres; the struct uses centi-mm
BITS_PER_BYTE = 8
ALPHA_SHIFT = 24
RED_SHIFT = 16
GREEN_SHIFT = 8
RGBA_BYTES = 4
ALPHA_INDEX = 3
TRANSPARENT_BLACK = bytes(RGBA_BYTES)


@dataclass(frozen=True)
class TagLayout:
    manufacturer_offset: int
    color_offsets: tuple[int, ...]
    diameter_offset: int
    weight_offset: int
    min_length: int
    zero_filled_length: int
    apply_temperatures: Callable[[bytes, FilamentInfo], None]


def _text(payload: bytes, offset: int, length: int) -> str:
    raw = payload[offset:offset + length]
    return raw.decode("utf-8", errors="ignore").rstrip("\x00").strip()


def _u16_be(payload: bytes, offset: int) -> int:
    return (payload[offset] << BITS_PER_BYTE) | payload[offset + 1]


def _temperature(payload: bytes, offset: int) -> int:
    return payload[offset] * TEMP_SCALE


def _apply_v1_temperatures(payload: bytes, info: FilamentInfo) -> None:
    print_temp = _temperature(payload, V1_PRINT_TEMP_OFFSET)
    bed_temp = _temperature(payload, V1_BED_TEMP_OFFSET)
    # The extended temperatures are optional and read 0 when unset.
    info["HOTEND_MIN_TEMP"] = _temperature(payload, V1_MIN_PRINT_TEMP_OFFSET) or print_temp
    info["HOTEND_MAX_TEMP"] = _temperature(payload, V1_MAX_PRINT_TEMP_OFFSET) or print_temp
    info["BED_TEMP"] = _temperature(payload, V1_MAX_BED_TEMP_OFFSET) or bed_temp
    info["FIRST_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]
    info["OTHER_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]


def _apply_v2_temperatures(payload: bytes, info: FilamentInfo) -> None:
    print_temp = _temperature(payload, V2_PRINT_TEMP_OFFSET)
    # The min and max print temperatures are optional and read 0 when unset.
    info["HOTEND_MIN_TEMP"] = _temperature(payload, V2_MIN_PRINT_TEMP_OFFSET) or print_temp
    info["HOTEND_MAX_TEMP"] = _temperature(payload, V2_MAX_PRINT_TEMP_OFFSET) or print_temp
    info["BED_TEMP"] = _temperature(payload, V2_BED_TEMP_OFFSET)
    info["FIRST_LAYER_TEMP"] = print_temp
    info["OTHER_LAYER_TEMP"] = print_temp


V1_LAYOUT = TagLayout(
    manufacturer_offset=V1_MANUFACTURER_OFFSET,
    color_offsets=V1_COLOR_OFFSETS,
    diameter_offset=V1_DIAMETER_OFFSET,
    weight_offset=V1_WEIGHT_OFFSET,
    min_length=V1_CORE_MIN_LENGTH,
    zero_filled_length=V1_ZERO_FILLED_LENGTH,
    apply_temperatures=_apply_v1_temperatures,
)
V2_LAYOUT = TagLayout(
    manufacturer_offset=V2_MANUFACTURER_OFFSET,
    color_offsets=V2_COLOR_OFFSETS,
    diameter_offset=V2_DIAMETER_OFFSET,
    weight_offset=V2_WEIGHT_OFFSET,
    min_length=V2_MIN_LENGTH,
    zero_filled_length=V2_ZERO_FILLED_LENGTH,
    apply_temperatures=_apply_v2_temperatures,
)
# Versions below 1.000 were read as v1 before this decoder checked the version; they keep that.
LAYOUT_BY_MAJOR_VERSION = {0: V1_LAYOUT, 1: V1_LAYOUT, 2: V2_LAYOUT}


def _layout_of(payload: bytes) -> TagLayout | None:
    if len(payload) < TAG_VERSION_LEN:
        return None
    major_version = _u16_be(payload, TAG_VERSION_OFFSET) // VERSION_PER_MAJOR
    return LAYOUT_BY_MAJOR_VERSION.get(major_version)


def _decodable(payload: bytes) -> tuple[bytes, TagLayout] | None:
    layout = _layout_of(payload)
    if layout is None or len(payload) < layout.min_length:
        return None
    return payload.ljust(layout.zero_filled_length, b"\x00"), layout


def _is_opentag_record(record: Record) -> bool:
    # RFC 2045: MIME types compare case-insensitively.
    return str(record.get("mime_type", "")).lower() == OPENTAG_MIME_TYPE


def decodable_opentag_payload(records: list[Record]) -> tuple[bytes, TagLayout] | None:
    # The spec has the reader load only the first OpenTag3D record; it holds all the tag data.
    first_record = next((record for record in records if _is_opentag_record(record)), None)
    if first_record is None:
        return None
    return _decodable(bytes(first_record.get("payload") or b""))


def _apply_identity(payload: bytes, layout: TagLayout, info: FilamentInfo) -> None:
    manufacturer = _text(payload, layout.manufacturer_offset, MANUFACTURER_LEN)
    main_type = _text(payload, BASE_MATERIAL_OFFSET, BASE_MATERIAL_LEN).upper()
    sub_type = _text(payload, MATERIAL_MODIFIERS_OFFSET, MATERIAL_MODIFIERS_LEN)
    info["VENDOR"] = manufacturer or info["VENDOR"]
    info["MANUFACTURER"] = manufacturer or info["MANUFACTURER"]
    info["MAIN_TYPE"] = main_type or info["MAIN_TYPE"]
    info["SUB_TYPE"] = sub_type or info["SUB_TYPE"]


def _rgba(payload: bytes, offset: int) -> bytes:
    return payload[offset:offset + RGBA_BYTES]


def _rgb(rgba: bytes) -> int:
    red, green, blue, _alpha = rgba
    return (red << RED_SHIFT) | (green << GREEN_SHIFT) | blue


def _spool_colors(payload: bytes, layout: TagLayout) -> list[bytes]:
    primary_offset, *secondary_offsets = layout.color_offsets
    secondaries = [_rgba(payload, offset) for offset in secondary_offsets]
    used_secondaries = [rgba for rgba in secondaries if rgba != TRANSPARENT_BLACK]
    return [_rgba(payload, primary_offset), *used_secondaries]


def _apply_color(payload: bytes, layout: TagLayout, info: FilamentInfo) -> None:
    colors = _spool_colors(payload, layout)
    first_color = colors[0]
    alpha = first_color[ALPHA_INDEX]
    info.update({f"RGB_{slot}": _rgb(color) for slot, color in enumerate(colors, start=1)})
    info["ALPHA"] = alpha
    info["COLOR_NUMS"] = len(colors)
    info["ARGB_COLOR"] = alpha << ALPHA_SHIFT | _rgb(first_color)


def _apply_dimensions(payload: bytes, layout: TagLayout, info: FilamentInfo) -> None:
    info["DIAMETER"] = _u16_be(payload, layout.diameter_offset) // MICROMETRE_PER_CENTI_MM
    info["WEIGHT"] = _u16_be(payload, layout.weight_offset)


def build_struct(
    records: list[Record], card_uid: list[int], template: FilamentInfo,
) -> FilamentInfo | None:
    match = decodable_opentag_payload(records)
    if match is None:
        return None
    payload, layout = match
    info = copy.deepcopy(template)
    _apply_identity(payload, layout, info)
    _apply_color(payload, layout, info)
    _apply_dimensions(payload, layout, info)
    layout.apply_temperatures(payload, info)
    info["CARD_UID"] = card_uid
    info["OFFICIAL"] = True
    return info
