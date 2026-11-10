"""Best-effort decoder for untagged JSON-over-NDEF filament tags.

A filament tag that stores its data as an NDEF ``application/json`` record but
carries NO recognized ``protocol`` field (OpenSpool and other protocol-keyed
tags own that path) is mapped here against a generous field-alias table. This
keeps any reasonable "just write some JSON" tag readable without a dedicated
decoder. Read-only: it produces a FILAMENT_INFO_STRUCT and never writes a tag.

Pure helper module: stdlib only, no relative imports, so it is unit-testable in
isolation. The registration shell (``rfid_tag_generic_ndef.py``) supplies the
FILAMENT_INFO_STRUCT template and the OK/ERR sentinels at runtime.
"""
import copy
import json
import string
from typing import Any

Record = dict[str, Any]
Json = dict[str, Any]

JSON_MIME_TYPE = "application/json"
PROTOCOL_FIELD = "protocol"

DEFAULT_DIAMETER_CENTI_MM = 175
WHITE_RGB = 0xFFFFFF
OPAQUE_ALPHA = 0xFF
ALPHA_SHIFT = 24
HEX_RADIX = 16
RGB_HEX_DIGITS = 6
# RRGGBBAA: the trailing alpha pair is read past.
RGBA_HEX_DIGITS = 8
HEX_COLOR_PREFIX = "#"
CENTI_MM_PER_MM = 100

# Destination struct key -> ordered source aliases. First present, non-empty alias wins.
STRING_ALIASES: dict[str, tuple[str, ...]] = {
    "VENDOR": ("brand", "vendor", "manufacturer", "make"),
    "MANUFACTURER": ("manufacturer", "brand", "vendor"),
    "MAIN_TYPE": ("type", "material", "material_type"),
    "SUB_TYPE": ("subtype", "sub_type", "variant"),
    "SPOOL_ID": ("spool_id", "id"),
}
TEMPERATURE_ALIASES: dict[str, tuple[str, ...]] = {
    "HOTEND_MIN_TEMP": ("min_temp", "nozzle_min_temp", "hotend_min_temp", "temp_min"),
    "HOTEND_MAX_TEMP": ("max_temp", "nozzle_max_temp", "hotend_max_temp", "temp_max"),
}
WEIGHT_ALIASES = ("weight", "weight_g", "net_weight")
DIAMETER_ALIASES = ("diameter", "diameter_mm")
COLOR_ALIASES = ("color_hex", "color", "colour", "hex")
# The OpenSpool name for a multi-color spool's extra colors: a list of hex strings.
EXTRA_COLORS_FIELD = "additional_color_hexes"
MAX_COLORS = 5   # the printer shows at most five colors per spool
BED_ALIASES = ("bed_temp", "bed_max_temp", "bed_min_temp", "bed")
KNOWN_FIELDS = (
    "brand", "vendor", "type", "material", "color_hex", "color", "min_temp", "max_temp",
)


def _first_alias(data: Json, aliases: tuple[str, ...]) -> Any:
    present = (data[alias] for alias in aliases if data.get(alias) not in (None, ""))
    return next(present, None)


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _diameter_centi_mm(value: Any) -> int:
    try:
        return int(round(float(value) * CENTI_MM_PER_MM))
    except (TypeError, ValueError):
        return DEFAULT_DIAMETER_CENTI_MM


def _is_hex_color(digits: str) -> bool:
    has_color_length = len(digits) in (RGB_HEX_DIGITS, RGBA_HEX_DIGITS)
    return has_color_length and all(digit in string.hexdigits for digit in digits)


def _hex_rgb(value: Any) -> int | None:
    if not isinstance(value, str):
        return None
    digits = value.removeprefix(HEX_COLOR_PREFIX)
    if not _is_hex_color(digits):
        return None
    return int(digits[:RGB_HEX_DIGITS], HEX_RADIX)


def _first_hex_color(data: Json, aliases: tuple[str, ...]) -> int | None:
    parsed_colors = (_hex_rgb(data.get(alias)) for alias in aliases)
    return next((rgb for rgb in parsed_colors if rgb is not None), None)


def _has_known_field(data: Json) -> bool:
    return any(field in data for field in KNOWN_FIELDS)


def _is_json_record(record: Record) -> bool:
    # RFC 2045: MIME types compare case-insensitively.
    return str(record.get("mime_type", "")).lower() == JSON_MIME_TYPE


def _decode_untagged_json(record: Record) -> Json | None:
    if not _is_json_record(record):
        return None
    try:
        parsed = json.loads(record.get("payload") or b"")
    except (ValueError, TypeError):
        return None
    if not isinstance(parsed, dict) or PROTOCOL_FIELD in parsed:
        return None
    return parsed


def select_filament_json(records: list[Record]) -> Json | None:
    candidates = (_decode_untagged_json(record) for record in records)
    usable = (data for data in candidates if data is not None and _has_known_field(data))
    return next(usable, None)


def _apply_strings(data: Json, info: dict[str, Any]) -> None:
    for dest_key, aliases in STRING_ALIASES.items():
        value = _first_alias(data, aliases)
        if value is not None:
            info[dest_key] = str(value)
    main_type = info.get("MAIN_TYPE")
    if isinstance(main_type, str):
        info["MAIN_TYPE"] = main_type.upper()


def _apply_numbers(data: Json, info: dict[str, Any]) -> None:
    for dest_key, aliases in TEMPERATURE_ALIASES.items():
        info[dest_key] = _as_int(_first_alias(data, aliases), info[dest_key])
    info["WEIGHT"] = _as_int(_first_alias(data, WEIGHT_ALIASES), info["WEIGHT"])
    info["DIAMETER"] = _diameter_centi_mm(_first_alias(data, DIAMETER_ALIASES))
    info["BED_TEMP"] = _as_int(_first_alias(data, BED_ALIASES), info["BED_TEMP"])
    info["FIRST_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]
    info["OTHER_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]


def _extra_colors(data: Json) -> list[int]:
    extra_hexes = data.get(EXTRA_COLORS_FIELD)
    if not isinstance(extra_hexes, list):
        return []
    parsed_colors = (_hex_rgb(extra_hex) for extra_hex in extra_hexes)
    return [rgb for rgb in parsed_colors if rgb is not None]


def _spool_colors(data: Json) -> list[int]:
    listed_colors = (_first_hex_color(data, COLOR_ALIASES), *_extra_colors(data))
    valid_colors = [rgb for rgb in listed_colors if rgb is not None]
    return valid_colors[:MAX_COLORS] or [WHITE_RGB]


def _apply_color(data: Json, info: dict[str, Any]) -> None:
    colors = _spool_colors(data)
    info.update({f"RGB_{slot}": color for slot, color in enumerate(colors, start=1)})
    info["COLOR_NUMS"] = len(colors)
    info["ALPHA"] = OPAQUE_ALPHA
    info["ARGB_COLOR"] = OPAQUE_ALPHA << ALPHA_SHIFT | colors[0]


def build_struct(
    records: list[Record], card_uid: list[int], template: dict[str, Any],
) -> dict[str, Any] | None:
    data = select_filament_json(records)
    if data is None:
        return None
    info = copy.deepcopy(template)
    _apply_strings(data, info)
    _apply_numbers(data, info)
    _apply_color(data, info)
    info["CARD_UID"] = card_uid
    info["OFFICIAL"] = True
    return info
