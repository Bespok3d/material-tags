"""Clean-room Elegoo filament decoder, verified against a real factory Centauri spool.

Elegoo writes a binary filament block into the tag's user memory, separate from the tag's NDEF
message (a factory spool carries a single https://www.elegoo.com URI record in front of it). The
block opens with a 0x36 header byte and Elegoo's 4-byte 0xEEEEEEEE manufacturer marker, and every
field after that starts on a 4-byte page boundary, zero-padded, as the "Data Alignment Rules" note
in ELEGOO's published guide requires. Pages are counted from the header page:

    +0, +1  header 0x36, marker EEEEEEEE, then 00 00 00
    +2      material, 4 bytes, one letter per byte in decimal-digit form (below)
    +4      color RGB888 in bytes 0 to 2 (byte 3 is 0xFF on the sample; meaning unconfirmed)
    +5      nozzle minimum then nozzle maximum, u16 big-endian each, degrees C
    +7      diameter u16 big-endian (hundredths of a mm), then weight u16 big-endian (grams)

Confirmed field by field against one real tag, read with NXP TagInfo, whose label gives: PLA,
"Sea Green", 1.75 mm, 1 kg, printing temperature 190 to 230 C. Two things in the guide do NOT
match factory tags, so do not "correct" this decoder back to it:
  * its field table packs the fields byte against byte (material at marker + 6 and so on);
    factory tags follow the guide's own alignment note instead, which moves every field;
  * it documents no temperatures, but factory tags carry the nozzle range on page +5.

Material encoding: each byte's two hex digits are the DECIMAL ASCII code of one letter, so 0x80
reads as "80", which is "P", and PLA is 00 80 76 65. That rule reproduces all nine codes in the
guide's material table and the real tag. The guide's other examples spell material in plain ASCII
(0x504C4120) instead, which no factory tag has been seen to use, so a code that does not come out
as capital letters is left undecoded rather than guessed.

Left at the template default on purpose, because nothing confirms them yet: the sub-type (page +3
is all zeros on the sample, and the guide shows two encodings for it), the filament code in page
+1, pages +6 and +8, and the production date (the guide's YYMM field is not where it says, and the
sample spool's printed code 1-2602-0206 appears nowhere in its memory).

Pure helper: stdlib only, no relative imports, unit-testable. The registration shell supplies the
FILAMENT_INFO_STRUCT template.
"""
import copy
from typing import Any

ELEGOO_VENDOR = "Elegoo"
BLOCK_SIGNATURE = bytes((0x36, 0xEE, 0xEE, 0xEE, 0xEE))
BYTES_PER_PAGE = 4

# Page indexes counted from the header page.
MATERIAL_PAGE = 2
COLOR_PAGE = 4
NOZZLE_TEMP_PAGE = 5
DIAMETER_WEIGHT_PAGE = 7
BLOCK_LEN = (DIAMETER_WEIGHT_PAGE + 1) * BYTES_PER_PAGE

U16_LEN = 2
RGB_LEN = 3
PADDING_BYTE = 0x00
FIRST_CAPITAL = "A"
LAST_CAPITAL = "Z"
CARD_UID_INDEXES = (0, 1, 2, 4, 5, 6, 7)
CARD_UID_MIN_BYTES = 8
OPAQUE_ALPHA = 0xFF
ALPHA_SHIFT = 24


def _page(dump: bytes, block_start: int, page_index: int) -> bytes:
    offset = block_start + page_index * BYTES_PER_PAGE
    return dump[offset:offset + BYTES_PER_PAGE]


def _u16_be(page: bytes, offset: int) -> int:
    return int.from_bytes(page[offset:offset + U16_LEN], "big")


def _card_uid(dump: bytes) -> list[int]:
    if len(dump) < CARD_UID_MIN_BYTES:
        return []
    return [dump[index] for index in CARD_UID_INDEXES]


def _decimal_digit_letter(code: int) -> str:
    """Read one material byte: 0x80 is "80", ASCII 80 is "P". Empty if it is not a capital."""
    digits = f"{code:02X}"
    if not digits.isdigit():
        return ""
    letter = chr(int(digits))
    return letter if FIRST_CAPITAL <= letter <= LAST_CAPITAL else ""


def decode_material(material_page: bytes) -> str | None:
    codes = [code for code in material_page if code != PADDING_BYTE]
    letters = [_decimal_digit_letter(code) for code in codes]
    if not codes or not all(letters):
        return None
    return "".join(letters)


def find_block_start(dump: bytes) -> int | None:
    """Locate the block by its signature; it must start a page and be present in full."""
    start = dump.find(BLOCK_SIGNATURE)
    if start < 0 or start % BYTES_PER_PAGE or start + BLOCK_LEN > len(dump):
        return None
    return start


def _apply_color(color_page: bytes, info: dict[str, Any]) -> None:
    rgb = int.from_bytes(color_page[:RGB_LEN], "big")
    info["RGB_1"] = rgb
    info["COLOR_NUMS"] = 1
    info["ALPHA"] = OPAQUE_ALPHA
    info["ARGB_COLOR"] = OPAQUE_ALPHA << ALPHA_SHIFT | rgb


def build_struct(dump: bytes, template: dict[str, Any]) -> dict[str, Any] | None:
    block_start = find_block_start(dump)
    if block_start is None:
        return None
    info = copy.deepcopy(template)
    info["VENDOR"] = ELEGOO_VENDOR
    info["MANUFACTURER"] = ELEGOO_VENDOR
    material = decode_material(_page(dump, block_start, MATERIAL_PAGE))
    info["MAIN_TYPE"] = material or info["MAIN_TYPE"]
    _apply_color(_page(dump, block_start, COLOR_PAGE), info)
    nozzle_page = _page(dump, block_start, NOZZLE_TEMP_PAGE)
    info["HOTEND_MIN_TEMP"] = _u16_be(nozzle_page, 0)
    info["HOTEND_MAX_TEMP"] = _u16_be(nozzle_page, U16_LEN)
    spool_page = _page(dump, block_start, DIAMETER_WEIGHT_PAGE)
    info["DIAMETER"] = _u16_be(spool_page, 0)
    info["WEIGHT"] = _u16_be(spool_page, U16_LEN)
    info["CARD_UID"] = _card_uid(dump)
    info["OFFICIAL"] = True
    return info
