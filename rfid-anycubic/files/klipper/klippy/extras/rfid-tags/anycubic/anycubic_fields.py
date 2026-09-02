"""Clean-room Anycubic ACE decoder, the agreed-across-sources NTAG21x fields only.

Anycubic ACE writes a plaintext (no key) little-endian block into NTAG21x user memory,
anchored by a `7B 00` prefix at page 4, followed by a one-byte format version and a
trailing zero (0x65 confirmed repeatedly, 0x64 confirmed via independent research, both
appear to share the same field layout through at least the weight field at page 31). This
decoder ships the fields settled by public reverse engineering (DnG-Crafts/ACE-RFID,
SimplyPrint) plus SKU, weight, diameter, color, length, bed minimum temperature, and print
speed, confirmed across three independently sourced tags spanning two different materials
(PLA+ and ASA) and three different SKUs:

    page 4        magic 7B 00 <version> 00 (version currently 0x64 or 0x65, scan anchored)
    page 5 to 9   SKU     ASCII, null-padded
    page 10       brand   ASCII, null-padded, blank on at least one confirmed SKU
    page 15       material ASCII, null-padded
    page 20       alpha, B, G, R           (4 bytes, R is the LAST byte, not the first)
    page 23       print speed min/max      (u16 LE pair, mm/s)
    page 24       nozzle temp min/max      (u16 LE pair, degC)
    page 29       bed temp min/max         (u16 LE pair, degC)
    page 30       diameter, length         (u16 LE pair: hundredths of a millimeter, meters)
    page 31       weight                   (u16 LE, grams)

SKU is decoded, but the field length dispute (12 vs 16 bytes) is only moot, not resolved:
every confirmed sample so far null pads well before either boundary, so a future tag whose
SKU fills the full 12 or 16 bytes with no trailing null could still decode short or long.
Treat the string as reliable, not the byte count backing it.

The specific dump that would settle this is known: Anycubic's PLA+ Refill line uses SKUs
of the form AHPLP<color>-A108, exactly 12 characters with no slack (per the independent
SKU/color-code catalog at github.com/Molodos/anycubic-nfc-filament/issues/15). A Refill
tag, any color, is the one sample that actually distinguishes the two hypotheses: if the
real field is 12 bytes, that SKU fills it with zero bytes of null padding, and reading it
with SKU_MAX = 16 would pull 4 bytes from whatever follows into the decoded string. If the
real field is 16 bytes, the same tag decodes clean.

Color's byte order was corrected after a second, independently sourced tag broke a tie the
first sample could not: a black spool's R and B channels are identical, so a straight
alpha-R-G-B read and a reversed alpha-B-G-R read produced the same output and looked
confirmed when it was not. A non-symmetric color (peach pink) showed the reversed order is
the one that matches, off by one least-significant bit against the marketing hex, within
normal swatch-to-tag rounding. That correction is independently reinforced by the same
tag's own SKU, whose embedded color code names the same color the corrected byte order
decodes. A third sample (ASA, green flash) has symmetric R and B again and so cannot add
further confirmation either way, same limitation as the original black spool. If a
non-symmetric third sample ever contradicts the fix, trust it over this comment.

Nozzle and bed temperature ranges are now confirmed against two materials with genuinely
different, physically plausible values: PLA/PLA+ at 190 to 230 nozzle, 55 to 65 bed, and
ASA at 240 to 280 nozzle, 90 to 110 bed. That is a stronger confirmation than repeating the
same material would give, since the offsets track a real material difference correctly
rather than a static default. Print speed (page 23) reproduced the documented 50 to 200
mm/s range on the original PLA+ sample, but reads zero on both other confirmed samples
(PLA Spezial, ASA), so it may not be populated across every product line.

Weight, diameter, and length have reproduced identically (1000g, 1.75mm, 330m) across all
three confirmed samples, spanning three different SKUs and two materials. That confirms the
offsets are right, but not yet the scale factors: identical values across every sample so
far are consistent with this simply being Anycubic's standard spool size for most of their
catalog, not with a genuinely varying field having been exercised. A spool with a different
weight or length (a refill pouch, a mini spool, anything not 1kg/330m) is still the one
sample that would actually prove the scale factors generalize.

Bed minimum temperature and print speed are both new keys on the returned dict (BED_MIN_TEMP,
PRINT_SPEED_MIN, PRINT_SPEED_MAX) that have not been confirmed to already exist in
filament_protocol.FILAMENT_INFO_STRUCT. They decode correctly from the tag either way, but
whether anything downstream reads them is an open question outside this file.

Brand can legitimately be blank (an all-zero field), the code already falls back to the
generic Anycubic vendor name in that case, confirmed against two real tags with no brand
data (PLA Spezial, and separately the friend-sourced sample), and populated brand ("AC")
confirmed on both PLA+ and ASA samples.

A fixed marker byte (0xBD) sits at the last byte of page 41 in this project's own PLA+
sample (AHPLPBK-108), confirmed reproducible across two independent reads of that tag. Two
other independently sourced samples from different product lines (PLA Spezial, ASA) place
the same marker one page earlier, at page 40. This was initially suspected to be a
transcription artifact in one of the pastes, but a clean re-read ruled that out: the most
likely explanation now is that the PLA+ line carries one extra 4-byte field somewhere
between weight (page 31) and this trailer that the other lines do not, since every byte in
that gap reads zero on every sample seen so far. Still undecoded either way. Does not
affect any field above, all of which sit before page 32 and have been confirmed identical
in position across all three product lines.

Pure helper: stdlib only, no relative imports, unit testable. The registration shell
supplies the FILAMENT_INFO_STRUCT template.
"""
import copy
from typing import Any

ANYCUBIC_VENDOR = "Anycubic"
MAGIC_PREFIX = bytes((0x7B, 0x00))
KNOWN_VERSIONS = (0x65, 0x64)  # 0x65 confirmed repeatedly, 0x64 via independent research

# Offsets RELATIVE to the magic prefix at page 4 (each NTAG page is 4 bytes), little-endian.
SKU_OFFSET = 4               # page 5, every sample null pads well short of either width guess
SKU_MAX = 16
BRAND_OFFSET = 24            # page 10, blank on some confirmed samples, populated on others
BRAND_MAX = 16
MATERIAL_OFFSET = 44         # page 15, confirmed on PLA+ and ASA
MATERIAL_MAX = 32
COLOR_OFFSET = 64            # page 20: alpha, B, G, R, R last, confirmed on two spools
PRINT_SPEED_MIN_OFFSET = 76  # page 23, u16 LE, mm/s, not populated on every sample seen
PRINT_SPEED_MAX_OFFSET = 78
NOZZLE_MIN_OFFSET = 80       # page 24, u16 LE, confirmed on two materials
NOZZLE_MAX_OFFSET = 82
BED_MIN_OFFSET = 100         # page 29, u16 LE, no confirmed template slot yet
BED_MAX_OFFSET = 102         # confirmed on two materials with different values
DIAMETER_OFFSET = 104        # page 30, u16 LE, hundredths of a millimeter, same on all samples
LENGTH_OFFSET = 106          # page 30 second half, u16 LE, meters, same on all samples
WEIGHT_OFFSET = 108          # page 31, u16 LE, grams, same on all samples
BLOCK_LEN = 112              # bytes past the magic this decoder reads (through weight)

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
    search_from = 0
    while True:
        candidate = dump.find(MAGIC_PREFIX, search_from)
        if candidate < 0:
            return None
        version_index = candidate + 2
        trailer_index = candidate + 3
        if trailer_index < len(dump) and dump[trailer_index] == 0x00 \
                and dump[version_index] in KNOWN_VERSIONS \
                and candidate + BLOCK_LEN <= len(dump):
            return candidate
        search_from = candidate + 1


def _apply_identity(dump: bytes, magic: int, info: dict[str, Any]) -> None:
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


def _apply_temperatures(dump: bytes, magic: int, info: dict[str, Any]) -> None:
    info["HOTEND_MIN_TEMP"] = _u16_le(dump, magic + NOZZLE_MIN_OFFSET)
    info["HOTEND_MAX_TEMP"] = _u16_le(dump, magic + NOZZLE_MAX_OFFSET)
    info["FIRST_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]
    info["OTHER_LAYER_TEMP"] = info["HOTEND_MIN_TEMP"]
    info["BED_MIN_TEMP"] = _u16_le(dump, magic + BED_MIN_OFFSET)
    info["BED_TEMP"] = _u16_le(dump, magic + BED_MAX_OFFSET)


def _apply_physical_properties(dump: bytes, magic: int, info: dict[str, Any]) -> None:
    info["DIAMETER"] = _u16_le(dump, magic + DIAMETER_OFFSET) / DIAMETER_SCALE
    info["LENGTH"] = _u16_le(dump, magic + LENGTH_OFFSET)
    info["WEIGHT"] = _u16_le(dump, magic + WEIGHT_OFFSET)


def _apply_print_speed(dump: bytes, magic: int, info: dict[str, Any]) -> None:
    info["PRINT_SPEED_MIN"] = _u16_le(dump, magic + PRINT_SPEED_MIN_OFFSET)
    info["PRINT_SPEED_MAX"] = _u16_le(dump, magic + PRINT_SPEED_MAX_OFFSET)


def _apply_color(dump: bytes, magic: int, info: dict[str, Any]) -> None:
    # Byte order is alpha, B, G, R, confirmed by a second, non-symmetric-color sample,
    # independently reinforced by that same tag's own SKU color code. See the module
    # docstring for why the first and third samples alone could not prove this.
    offset = magic + COLOR_OFFSET
    alpha, blue, green, red = dump[offset], dump[offset + 1], dump[offset + 2], dump[offset + 3]
    info["ALPHA"] = alpha
    info["ARGB_COLOR"] = (alpha << 24) | (red << 16) | (green << 8) | blue
    info["RGB_1"] = (red << 16) | (green << 8) | blue


def build_struct(dump: bytes, template: dict[str, Any]) -> dict[str, Any] | None:
    magic = find_block_start(dump)
    if magic is None:
        return None
    info = copy.deepcopy(template)
    info["VERSION"] = dump[magic + 2]
    _apply_identity(dump, magic, info)
    _apply_temperatures(dump, magic, info)
    _apply_physical_properties(dump, magic, info)
    _apply_print_speed(dump, magic, info)
    _apply_color(dump, magic, info)
    info["CARD_UID"] = _card_uid(dump)
    info["OFFICIAL"] = True
    return info
