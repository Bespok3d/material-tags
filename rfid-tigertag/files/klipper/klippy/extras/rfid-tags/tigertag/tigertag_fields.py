"""Clean-room TigerTag decoder - the published NTAG21x raw-page layout.

TigerTag (tigertag.io) writes a 144-byte big-endian block into NTAG213 user memory
(pages 0x04-0x27). The block is anchored by a 4-byte "ID TigerTag" magic at its head
(payload offset +0), so this decoder finds the block by scanning the raw page dump for
the magic and reads every field at a fixed offset relative to it. Layout per the public
TigerTag-RFID-Guide spec:

    +0  u32  magic         0x5BF59264 standard / 0xBC0FCB97 plus (0x6C41A2E1 = blank)
    +4  u32  id_product
    +8  u16  id_material   (numeric id; name map is TigerTag's GPLv3 table - not shipped)
    +10 u8   id_aspect1 / +11 u8 id_aspect2   Bicolor, Tricolor, Rainbow set the colour count
    +13 u8   id_diameter   enum: 0x38 -> 1.75 mm, 0xDD -> 2.85 mm
    +14 u16  id_brand      (numeric id; name map not shipped)
    +16 4    color1        RGBA, byte order R, G, B, A
    +20 u24  measure       net quantity at manufacture (grams for filament)
    +24 u16  nozzle_temp_min / +26 nozzle_temp_max   degC
    +28 u8   dry_temp / +29 dry_time(hours)
    +30 u8   bed_temp_min / +31 bed_temp_max         degC
    +36 3    color2        RGB / +40 3 color3 RGB

TigerTag stores brand and material as numeric ids whose human-name maps are GPLv3, so
this decoder ships the numeric/physical fields (color, diameter, temperatures, weight)
and leaves the brand/material name strings at the struct template default rather than
vendoring a GPL table. id_product is surfaced as the struct SKU.

Pure helper: stdlib only, no relative imports, unit-testable. The registration shell
supplies the FILAMENT_INFO_STRUCT template.
"""
import copy
from typing import Any

TIGERTAG_VENDOR = "TigerTag"
MAGIC_STANDARD = bytes((0x5B, 0xF5, 0x92, 0x64))
MAGIC_PLUS = bytes((0xBC, 0x0F, 0xCB, 0x97))

# Offsets RELATIVE to the magic at the head of the block, big-endian.
ID_PRODUCT_OFFSET = 4
ASPECT_1_OFFSET = 10
ASPECT_2_OFFSET = 11
DIAMETER_OFFSET = 13
COLOR_OFFSET = 16           # 4 bytes R, G, B, A
MEASURE_OFFSET = 20         # u24 net quantity (grams for filament)
NOZZLE_MIN_OFFSET = 24      # u16
NOZZLE_MAX_OFFSET = 26      # u16
DRY_TEMP_OFFSET = 28        # u8
DRY_TIME_OFFSET = 29        # u8
BED_MAX_OFFSET = 31         # u8
BLOCK_LEN = 32              # bytes past the magic this decoder reads (through bed temp)
COLOR_2_OFFSET = 36         # 3 bytes R, G, B
COLOR_3_OFFSET = 40         # 3 bytes R, G, B
RGB_BYTES = 3
COLOR_OFFSETS = (COLOR_OFFSET, COLOR_2_OFFSET, COLOR_3_OFFSET)

# Diameter is an enumerated byte, not a scaled value; map the two documented codes to
# the struct's hundredths-of-a-millimetre unit.
DIAMETER_CODES = {0x38: 175, 0xDD: 285}

# The aspect ids whose color_count is above one in TigerTag's id_aspect.json (CC0). Every
# other aspect means a single colour.
ASPECT_BICOLOR = 252
ASPECT_TRICOLOR = 24
ASPECT_RAINBOW = 145
ASPECT_COLOR_COUNTS = {ASPECT_BICOLOR: 2, ASPECT_TRICOLOR: 3, ASPECT_RAINBOW: 3}
SINGLE_COLOR = 1

CARD_UID_INDEXES = (0, 1, 2, 4, 5, 6, 7)
CARD_UID_MIN_BYTES = 8
RED_SHIFT = 16
GREEN_SHIFT = 8
ALPHA_SHIFT = 24


def _u16_be(dump: bytes, offset: int) -> int:
    return (dump[offset] << GREEN_SHIFT) | dump[offset + 1]


def _u24_be(dump: bytes, offset: int) -> int:
    return (dump[offset] << RED_SHIFT) | (dump[offset + 1] << GREEN_SHIFT) | dump[offset + 2]


def _u32_be(dump: bytes, offset: int) -> int:
    return (_u16_be(dump, offset) << RED_SHIFT) | _u16_be(dump, offset + 2)


def _card_uid(dump: bytes) -> list[int]:
    if len(dump) < CARD_UID_MIN_BYTES:
        return []
    return [dump[index] for index in CARD_UID_INDEXES]


def find_block_start(dump: bytes) -> int | None:
    for magic in (MAGIC_STANDARD, MAGIC_PLUS):
        start = dump.find(magic)
        if start >= 0 and start + BLOCK_LEN <= len(dump):
            return start
    return None


def _aspect_color_count(dump: bytes, magic: int) -> int:
    # The spec says to check Aspect 2 first for the multi-colour mode, then Aspect 1.
    aspect_2 = ASPECT_COLOR_COUNTS.get(dump[magic + ASPECT_2_OFFSET])
    return aspect_2 or ASPECT_COLOR_COUNTS.get(dump[magic + ASPECT_1_OFFSET], SINGLE_COLOR)


def _held_color_offsets(dump: bytes, magic: int) -> tuple[int, ...]:
    wanted_offsets = COLOR_OFFSETS[:_aspect_color_count(dump, magic)]
    return tuple(offset for offset in wanted_offsets if magic + offset + RGB_BYTES <= len(dump))


def _apply_color(dump: bytes, magic: int, info: dict[str, Any]) -> None:
    color_offsets = _held_color_offsets(dump, magic)
    colors = [_u24_be(dump, magic + offset) for offset in color_offsets]
    alpha = dump[magic + COLOR_OFFSET + RGB_BYTES]
    info.update({f"RGB_{slot}": rgb for slot, rgb in enumerate(colors, start=1)})
    info["COLOR_NUMS"] = len(colors)
    info["ALPHA"] = alpha
    info["ARGB_COLOR"] = alpha << ALPHA_SHIFT | colors[0]


def _apply_temperatures(dump: bytes, magic: int, info: dict[str, Any]) -> None:
    info["HOTEND_MIN_TEMP"] = _u16_be(dump, magic + NOZZLE_MIN_OFFSET)
    info["HOTEND_MAX_TEMP"] = _u16_be(dump, magic + NOZZLE_MAX_OFFSET)
    info["FIRST_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]
    info["OTHER_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]
    info["BED_TEMP"] = dump[magic + BED_MAX_OFFSET]
    info["DRYING_TEMP"] = dump[magic + DRY_TEMP_OFFSET]
    info["DRYING_TIME"] = dump[magic + DRY_TIME_OFFSET]


def build_struct(dump: bytes, template: dict[str, Any]) -> dict[str, Any] | None:
    magic = find_block_start(dump)
    if magic is None:
        return None
    info = copy.deepcopy(template)
    info["VENDOR"] = TIGERTAG_VENDOR
    info["MANUFACTURER"] = TIGERTAG_VENDOR
    info["SKU"] = _u32_be(dump, magic + ID_PRODUCT_OFFSET)
    info["DIAMETER"] = DIAMETER_CODES.get(dump[magic + DIAMETER_OFFSET], 0)
    info["WEIGHT"] = _u24_be(dump, magic + MEASURE_OFFSET)
    _apply_color(dump, magic, info)
    _apply_temperatures(dump, magic, info)
    info["CARD_UID"] = _card_uid(dump)
    info["OFFICIAL"] = True
    return info
