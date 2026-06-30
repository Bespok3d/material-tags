"""Creality filament-payload decode (pure, stdlib-only, unit-tested).

Clean-room from the PUBLIC Creality reverse engineering (DnG-Crafts/K2-RFID read side,
Bambu-Research-Group CrealityRfid.md). After the shell decrypts blocks 4-6 (AES-128-ECB),
the 48-byte payload is an ASCII string of hex digits with these fixed character fields
(verified self-consistent against K2-RFID's MainForm.cs `Substring` anchors):

    [0:3]   batch number          [3:8]   manufacture date (YY M DD)
    [8:12]  vendor / supplier id  [12:17] material id (Creality enum, not name-mappable)
    [17:18] flag nibble           [18:24] color RRGGBB
    [24:28] weight/length code     [28:34] serial         [34:48] reserved

Creality's tag carries no diameter or temperatures (the printer resolves those from the
material id via its on-device database, which is not published), so this decoder fills the
color, weight, date, and material-id fields and leaves the rest at the template default.
The material id stays a numeric id; its human name needs Creality's unpublished material
database.
"""
import copy
from typing import Any

CREALITY_VENDOR = "Creality"
PAYLOAD_LEN = 48
HEX_ALPHABET = set("0123456789ABCDEF")

DATE_OFFSET = 3
DATE_LEN = 5
MATERIAL_OFFSET = 12
MATERIAL_LEN = 5
COLOR_OFFSET = 18
COLOR_LEN = 6
WEIGHT_OFFSET = 24
WEIGHT_LEN = 4

OPAQUE_ALPHA = 0xFF
ALPHA_SHIFT = 24
HEX_BASE = 16
DEC_BASE = 10
YEAR_BASE = 2000
MIN_MONTH = 1
MAX_MONTH = 12
MIN_DAY = 1
MAX_DAY = 31

# Weight/length code -> grams (K2-RFID Utils.cs bucket map). Creality stores a bucket, not
# free grams.
WEIGHT_GRAMS = {"0082": 250, "0165": 500, "0198": 600, "0247": 750, "0330": 1000}


def _decode_date(field: str) -> str | None:
    """YY M DD -> YYYYMMDD: year/day are 2-digit decimal, month a single hex nibble
    (A/B/C = Oct/Nov/Dec). Returns None for an implausible or malformed field."""
    try:
        year = YEAR_BASE + int(field[0:2], DEC_BASE)
        month = int(field[2], HEX_BASE)
        day = int(field[3:5], DEC_BASE)
    except ValueError:
        return None
    if not (MIN_MONTH <= month <= MAX_MONTH and MIN_DAY <= day <= MAX_DAY):
        return None
    return f"{year:04d}{month:02d}{day:02d}"


def _apply_color(text: str, info: dict[str, Any]) -> None:
    rgb = int(text[COLOR_OFFSET:COLOR_OFFSET + COLOR_LEN], HEX_BASE)
    info["RGB_1"] = rgb
    info["COLOR_NUMS"] = 1
    info["ALPHA"] = OPAQUE_ALPHA
    info["ARGB_COLOR"] = OPAQUE_ALPHA << ALPHA_SHIFT | rgb


def decode(
    payload_text: str | None, card_uid: list[int], template: dict[str, Any],
) -> dict[str, Any] | None:
    """Decode the decrypted Creality payload into a filament struct, or None if invalid."""
    if payload_text is None or len(payload_text) < PAYLOAD_LEN:
        return None
    text = payload_text[:PAYLOAD_LEN].upper()
    if not set(text) <= HEX_ALPHABET:
        return None
    info = copy.deepcopy(template)
    info["VENDOR"] = CREALITY_VENDOR
    info["MANUFACTURER"] = CREALITY_VENDOR
    info["SKU"] = int(text[MATERIAL_OFFSET:MATERIAL_OFFSET + MATERIAL_LEN], HEX_BASE)
    info["WEIGHT"] = WEIGHT_GRAMS.get(text[WEIGHT_OFFSET:WEIGHT_OFFSET + WEIGHT_LEN], 0)
    _apply_color(text, info)
    manufactured = _decode_date(text[DATE_OFFSET:DATE_OFFSET + DATE_LEN])
    if manufactured is not None:
        info["MF_DATE"] = manufactured
    info["CARD_UID"] = list(card_uid)
    info["OFFICIAL"] = True
    return info
