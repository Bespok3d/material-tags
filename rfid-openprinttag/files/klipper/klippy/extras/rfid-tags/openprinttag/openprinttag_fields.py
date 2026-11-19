"""Clean-room OpenPrintTag (prusa3d) CBOR payload decoder.

OpenPrintTag rides an NDEF MIME record ``application/vnd.openprinttag``. Its payload is three
concatenated CBOR maps - meta, main, aux - with integer keys. This decoder reads the meta map
to find the main region, decodes the main map, and maps the documented fields to a
FILAMENT_INFO_STRUCT. The keys and units below are verified against the public spec
(specs.openprinttag.org / prusa3d/OpenPrintTag data/main_fields.yaml):

    9  material_type (enum)   10 material_name (str)    11 brand_name (str)
    14 manufactured_date (s)  16 nominal weight (g)     19 primary_color (R,G,B[,A] bstr)
    20-24 secondary_color_0..4 (same format as primary_color)
    30 filament_diameter (mm) 34/35 nozzle min/max (C)  37/38 bed min/max (C)
    52 material_abbreviation  57 drying_temp (C)         58 drying_time (min)

We decode the PAYLOAD, not Prusa's hardware: Prusa's own factory spools use ISO-15693 tags the
U1 reader cannot read, but an OpenPrintTag payload written onto a standard NTAG21x reads fine
and decodes here. The brand/material name strings are used directly (no enum table needed).

Pure helper: stdlib + the vendored cbor_min sibling, imported relatively so it resolves at
runtime as a flat ``klippy.extras`` sibling (Klipper loads the placed files into the ``extras``
package); the tests reach it through the same ``openprinttag`` package.
"""
import copy
import datetime
from typing import Any, TypeGuard

from . import cbor_min

OPENPRINTTAG_MIME_TYPE = "application/vnd.openprinttag"

META_MAIN_OFFSET_KEY = 0

KEY_MATERIAL_NAME = 10
KEY_BRAND_NAME = 11
KEY_MANUFACTURED_DATE = 14
KEY_NETTO_WEIGHT = 16
KEY_PRIMARY_COLOR = 19
KEY_SECONDARY_COLORS = (20, 21, 22, 23, 24)
KEY_DIAMETER = 30
KEY_MIN_PRINT_TEMP = 34
KEY_MAX_PRINT_TEMP = 35
KEY_MAX_BED_TEMP = 38
KEY_MATERIAL_ABBREV = 52
KEY_DRYING_TEMP = 57
KEY_DRYING_TIME = 58

DIAMETER_SCALE = 100   # the struct uses hundredths of a mm; the spec stores mm
OPAQUE_ALPHA = 0xFF
ALPHA_SHIFT = 24
RED_SHIFT = 16
GREEN_SHIFT = 8
RGB_BYTES = 3
RGBA_BYTES = 4
MAX_COLORS = 5   # the printer shows at most five colors per spool

Record = dict[str, Any]


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


def _is_openprinttag_record(record: Record) -> bool:
    # RFC 2045: MIME types compare case-insensitively.
    return str(record.get("mime_type", "")).lower() == OPENPRINTTAG_MIME_TYPE


def select_openprinttag_payload(records: list[Record]) -> bytes | None:
    matches = (
        bytes(record.get("payload") or b"")
        for record in records
        if _is_openprinttag_record(record)
    )
    return next((payload for payload in matches if payload), None)


def _decode_main_map(payload: bytes) -> dict[Any, Any] | None:
    meta, after_meta = cbor_min.load_at(payload, 0)
    if not isinstance(meta, dict):
        return None
    main_offset = meta.get(META_MAIN_OFFSET_KEY, after_meta)
    if not isinstance(main_offset, int) or not 0 <= main_offset < len(payload):
        return None
    main, _ = cbor_min.load_at(payload, main_offset)
    return main if isinstance(main, dict) else None


def _text(main: dict[Any, Any], key: int) -> str | None:
    value = main.get(key)
    return value if isinstance(value, str) and value else None


def _apply_identity(main: dict[Any, Any], info: dict[str, Any]) -> None:
    brand = _text(main, KEY_BRAND_NAME)
    if brand is not None:
        info["VENDOR"] = brand
        info["MANUFACTURER"] = brand
    main_type = _text(main, KEY_MATERIAL_ABBREV) or _text(main, KEY_MATERIAL_NAME)
    if main_type is not None:
        info["MAIN_TYPE"] = main_type


def _is_color(value: Any) -> TypeGuard[bytes | bytearray]:
    return isinstance(value, (bytes, bytearray)) and len(value) >= RGB_BYTES


def _rgb(color: bytes) -> int:
    return (color[0] << RED_SHIFT) | (color[1] << GREEN_SHIFT) | color[2]


def _spool_colors(main: dict[Any, Any]) -> list[bytes]:
    color_keys = (KEY_PRIMARY_COLOR, *KEY_SECONDARY_COLORS)
    colors = [main.get(key) for key in color_keys]
    return [bytes(color) for color in colors if _is_color(color)][:MAX_COLORS]


def _apply_color(main: dict[Any, Any], info: dict[str, Any]) -> None:
    # The spec omits primary_color on rainbow and coextruded spools, so the first color present
    # leads, whichever key holds it.
    colors = _spool_colors(main)
    if not colors:
        return
    first_color = colors[0]
    alpha = first_color[3] if len(first_color) >= RGBA_BYTES else OPAQUE_ALPHA
    info.update({f"RGB_{slot}": _rgb(color) for slot, color in enumerate(colors, start=1)})
    info["ALPHA"] = alpha
    info["COLOR_NUMS"] = len(colors)
    info["ARGB_COLOR"] = alpha << ALPHA_SHIFT | _rgb(first_color)


def _apply_int(main: dict[Any, Any], key: int, info: dict[str, Any], field: str) -> None:
    value = _as_number(main.get(key))
    if value is not None:
        info[field] = round(value)


def _apply_dimensions(main: dict[Any, Any], info: dict[str, Any]) -> None:
    diameter = _as_number(main.get(KEY_DIAMETER))
    if diameter is not None:
        info["DIAMETER"] = round(diameter * DIAMETER_SCALE)
    _apply_int(main, KEY_NETTO_WEIGHT, info, "WEIGHT")


def _apply_temperatures(main: dict[Any, Any], info: dict[str, Any]) -> None:
    _apply_int(main, KEY_MIN_PRINT_TEMP, info, "HOTEND_MIN_TEMP")
    _apply_int(main, KEY_MAX_PRINT_TEMP, info, "HOTEND_MAX_TEMP")
    _apply_int(main, KEY_MAX_BED_TEMP, info, "BED_TEMP")
    _apply_int(main, KEY_DRYING_TEMP, info, "DRYING_TEMP")
    _apply_int(main, KEY_DRYING_TIME, info, "DRYING_TIME")
    info["FIRST_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]
    info["OTHER_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]


def _apply_date(main: dict[Any, Any], info: dict[str, Any]) -> None:
    seconds = main.get(KEY_MANUFACTURED_DATE)
    if not isinstance(seconds, int) or isinstance(seconds, bool) or seconds <= 0:
        return
    moment = datetime.datetime.fromtimestamp(seconds, datetime.UTC)
    info["MF_DATE"] = moment.strftime("%Y%m%d")


def build_struct(
    records: list[Record], card_uid: list[int], template: dict[str, Any],
) -> dict[str, Any] | None:
    payload = select_openprinttag_payload(records)
    if payload is None:
        return None
    try:
        main = _decode_main_map(payload)
    except cbor_min.CborError:
        return None
    if main is None:
        return None
    info = copy.deepcopy(template)
    _apply_identity(main, info)
    _apply_color(main, info)
    _apply_dimensions(main, info)
    _apply_temperatures(main, info)
    _apply_date(main, info)
    info["CARD_UID"] = card_uid
    info["OFFICIAL"] = True
    return info
