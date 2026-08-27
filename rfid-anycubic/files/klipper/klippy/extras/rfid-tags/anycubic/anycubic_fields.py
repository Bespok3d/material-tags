"""Clean-room Anycubic ACE decoder, the agreed-across-sources NTAG21x fields only.

Anycubic ACE writes a plaintext (no key) little-endian block into NTAG21x user memory,
anchored by a 4-byte magic `7B 00 65 00` at page 4 (the 0x65 byte is the ACE format
version). This decoder ships the fields settled by public reverse engineering
(DnG-Crafts/ACE-RFID, SimplyPrint) plus SKU, weight, diameter, color, and length, all
confirmed against one real tag matched to its box and seller listing:

    page 4        magic 7B 00 65 00        (found by scan, offsets below are relative to it)
    page 5 to 9   SKU     ASCII, null-padded
    page 10       brand   ASCII, null-padded
    page 15       material ASCII, null-padded
    page 20       alpha, R, G, B           (4 bytes, stored in that order, no byte swap)
    page 24       nozzle temp min/max      (u16 LE pair, degC)
    page 29       bed temp min/max         (u16 LE pair, degC, min currently unused downstream)
    page 30       diameter, length         (u16 LE pair: hundredths of a millimeter, meters)
    page 31       weight                   (u16 LE, grams)

PENDING CONFIRMATION ON MORE SPOOLS: SKU, color, diameter, length, and weight were all
pinned down against a single tag (one Anycubic PLA+ black spool, box-matched). Brand,
material, and temperatures carry over from the public reverse engineering sources, which
already cross-checked multiple tags, those are not part of this caveat. SKU's field-width
dispute (12 vs 16 bytes) also stays open regardless of sample count, see below, that is a
different, permanent caveat, not one more spools resolves by default.

Everything under PENDING gets re-checked as more spools come in: same brand and material
first, since offsets should hold; a different color or a fractional weight next, since
those are the values most likely to expose a wrong offset or scale factor if page 20, 30,
or 31 turn out not to be fixed-layout across the whole ACE tag family.

SKU is decoded, but the field length dispute (12 vs 16 bytes) is only moot, not resolved:
the sample this was confirmed against happens to null pad well before either boundary, so a
future tag whose SKU fills the full 12 or 16 bytes with no trailing null could still decode
short or long. Treat the string as reliable, not the byte count backing it.

Pure helper: stdlib only, no relative imports, unit testable. The registration shell
supplies the FILAMENT_INFO_STRUCT template.
"""
import copy
from typing import Any

ANYCUBIC_VENDOR = "Anycubic"
MAGIC = bytes((0x7B, 0x00, 0x65, 0x00))

# Offsets RELATIVE to the magic at page 4 (each NTAG page is 4 bytes), little-endian.
SKU_OFFSET = 4              # page 5, null padded well before page 10 in the sample tag
SKU_MAX = 16                # PENDING: width unresolved regardless of sample count, see docstring
BRAND_OFFSET = 24           # page 10, from public reverse engineering sources
BRAND_MAX = 16
MATERIAL_OFFSET = 44        # page 15, from public reverse engineering sources
MATERIAL_MAX = 32
COLOR_OFFSET = 64           # page 20: alpha, R, G, B. PENDING: confirmed on one spool only
NOZZLE_MIN_OFFSET = 80      # page 24, u16 LE, from public reverse engineering sources
NOZZLE_MAX_OFFSET = 82
BED_MIN_OFFSET = 100        # page 29, u16 LE, matches seller spec but not surfaced downstream
BED_MAX_OFFSET = 102
DIAMETER_OFFSET = 104       # page 30, u16 LE, hundredths of a millimeter. PENDING: one spool only
LENGTH_OFFSET = 106         # page 30, second half, u16 LE, meters. PENDING: one spool only
WEIGHT_OFFSET = 108         # page 31, u16 LE, grams. PENDING: one spool only
BLOCK_LEN = 112             # bytes past the magic this decoder reads (through weight)

CARD_UID_INDEXES = (0, 1, 2, 4, 5, 6, 7)
CARD_UID_MIN_BYTES = 8
PRINTABLE_MIN = 0x20
PRINTABLE_MAX = 0x7F
DIAMETER_SCALE = 100  # stored value is millimeters times 100


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

def _apply_physical_properties(dump: bytes, magic: int, info: dict[str, Any]) -> None:
    # PENDING CONFIRMATION: diameter, length, and weight all reproduced exactly against one
    # spool's box and listing. Re-check against a spool with a different weight or a
    # fractional weight (not an even 1000g) once one comes in, an even number can hide a
    # wrong scale factor or a swapped field that a fractional value would expose.
    info["DIAMETER"] = _u16_le(dump, magic + DIAMETER_OFFSET) / DIAMETER_SCALE
    info["LENGTH"] = _u16_le(dump, magic + LENGTH_OFFSET)
    info["WEIGHT"] = _u16_le(dump, magic + WEIGHT_OFFSET)

def _apply_color(dump: bytes, magic: int, info: dict[str, Any]) -> None:
    # PENDING CONFIRMATION: byte order (alpha, R, G, B) confirmed against one black spool.
    # Black and white can't fully exercise a byte-order bug the way a spool with three
    # distinct R/G/B values would, re-check against a saturated color once one comes in.
    offset = magic + COLOR_OFFSET
    alpha, red, green, blue = dump[offset], dump[offset + 1], dump[offset + 2], dump[offset + 3]
    info["ALPHA"] = alpha
    info["ARGB_COLOR"] = (alpha << 24) | (red << 16) | (green << 8) | blue
    info["RGB_1"] = (red << 16) | (green << 8) | blue


def build_struct(dump: bytes, template: dict[str, Any]) -> dict[str, Any] | None:
    magic = find_block_start(dump)
    if magic is None:
        return None
    info = copy.deepcopy(template)
    info["VENDOR"] = ANYCUBIC_VENDOR
    info["MANUFACTURER"] = ANYCUBIC_VENDOR
    sku = _ascii(dump, magic + SKU_OFFSET, SKU_MAX)
    if sku:
        info["SKU"] = sku
    brand = _ascii(dump, magic + BRAND_OFFSET, BRAND_MAX)
    if brand:
        info["VENDOR"] = brand
    material = _ascii(dump, magic + MATERIAL_OFFSET, MATERIAL_MAX).upper()
    if material:
        info["MAIN_TYPE"] = material
    _apply_temperatures(dump, magic, info)
    _apply_physical_properties(dump, magic, info)
    _apply_color(dump, magic, info)
    info["CARD_UID"] = _card_uid(dump)
    info["OFFICIAL"] = True
    return info