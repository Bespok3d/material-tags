"""Creality filament-payload decode (pure, stdlib-only, unit-tested).

Clean-room from the PUBLIC Creality reverse engineering (DnG-Crafts/K2-RFID,
Bambu-Research-Group CrealityRfid.md). After the shell decrypts blocks 4-6 (AES-128-ECB),
the plaintext is an ASCII string of hex-ish characters terminated by '%' (0x25) and padded
with NUL to the 48-byte block. The usable data is the run before the terminator.

Field offsets below are cross-confirmed two ways: against a real tag dump (blue Hyper PLA,
1kg, UID 40:24:c2:6a) AND against an independent third-party reader implementation that
ships real Creality support (m0h31h31/3DPrint-Filament-RFID-Tool, parseCrealityTagString).
That second decoder reads the same values from the same offsets, which is much stronger than
a single-source schema. Note: only the field FACTS (offsets, meanings) are reused; no code
from that project is copied, and it ships without a license file, so it is treated as a
behavioural reference only.

Confirmed:

    [12:17] material id   -> literal 5-char id, e.g. '01001'. Cross-checked: the reference
                            project's material table maps '01001' to "Hyper PLA", which
                            matches the physical spool label. Kept as a STRING: real ids are
                            not all numeric (e.g. 'E4001'), so the earlier int(...,16) parse
                            was wrong (it turned '01001' into 4097 and would mangle letters).
    [24:28] weight bucket -> '0330' = 1000 g, matches the physical 1kg spool.

Color field (confirmed to be plain RGB by five independent sources):

    [18:24] color RGB     -> a straight 6-digit RRGGBB hex value, preceded by a fixed prefix
                            char at [17] (K2 writes it as '0' + RRGGBB). Confirmed by the
                            upstream authority DnG-Crafts/K2-RFID and by SpoolPainter, OpenRFID,
                            the reference Android app, and this decoder: all read [18:24] as RGB
                            the same way. Emitting it as an opaque RGB value is correct.
                            NOTE on the sample tag: its stored RGB is 0A2989 (dark navy) but the
                            physical filament is bright cerulean (#0087BE, colorimeter-measured,
                            CIELAB L*51.73 a*-18.25 b*-40.01). That is a factory data error on
                            that one spool's tag, not a decode problem: every reader shows the
                            same navy. A second differently-colored real tag would confirm that
                            correctly-programmed tags carry sensible RGB.

Deliberately left undecoded (Rule 5), evidence needed named for each:

    date:    offset is probably correct (year [3:5], month nibble [5], day [6:8], as K2 and
             OpenRFID both use). On the sample tag the month nibble is 0 (invalid), the same
             result every implementation gets, so this spool just has an unset/partial date.
             Left undecoded until a tag with a valid date confirms it.
    serial:  reference reads [28:34]; nothing on the spool confirms its meaning.
    vendorId: reference reads [5:9]; unconfirmed, and its purpose is unclear.

Creality's tag itself carries no diameter or temperatures, but this decoder fills them from
the material id via the creality_types table (harvested from Creality's own slicer profiles),
the same way Creality's firmware resolves them from its on-device database. Diameter is
authoritative; hotend temps are nominal defaults the printer may override. Bed temperature is
not filled (it is too printer-dependent to assert from the id). Unknown ids leave all of these
at the template default.
"""
from typing import Any

# NOTE: this import is relative (from . import) even though this module is otherwise a
# "bare-importable" pure module. Klipper loads the shell as extras.rfid_tag_creality, so this
# module is pulled in as extras.creality_fields (a package submodule), NOT as a top-level
# module. klippy/extras is a package on the path, not a sys.path entry, so a bare
# "import creality_types" fails at runtime with ModuleNotFoundError even though the file sits
# right next to this one. A sibling import therefore MUST be relative. Do not "simplify" this
# to a bare import. Standalone tests give this module a package context via the conftest stub
# pattern (same mechanism used for filament_protocol / fm175xx_reader).
from . import creality_types

HUNDREDTHS_PER_MM = 100

CREALITY_VENDOR = "Creality"
PAYLOAD_TERMINATOR = "%"
# The core must be long enough to contain every field we read (through weight at [24:28]).
MIN_CORE_LEN = 28
CORE_ALPHABET = set("0123456789ABCDEF")

MATERIAL_OFFSET = 12
MATERIAL_LEN = 5
COLOR_OFFSET = 18
COLOR_LEN = 6
WEIGHT_OFFSET = 24
WEIGHT_LEN = 4

OPAQUE_ALPHA = 0xFF
ALPHA_SHIFT = 24
HEX_BASE = 16

# Weight/length bucket code -> grams (community schema, cross-confirmed by the reference app).
# The 1000 g entry is confirmed against a real 1kg spool; the rest are unconfirmed against
# hardware but agree across both independent sources.
WEIGHT_GRAMS = {"0082": 250, "0165": 500, "0198": 600, "0247": 750, "0330": 1000}


def _core_text(payload_text: str | None) -> str | None:
    """Return the leading data run of the payload (before the '%' terminator), uppercased,
    or None if the payload is missing, too short, or not the expected hex-ish charset."""
    if payload_text is None:
        return None
    head = payload_text.split(PAYLOAD_TERMINATOR, 1)[0].upper()
    if len(head) < MIN_CORE_LEN or not set(head) <= CORE_ALPHABET:
        return None
    return head


def _apply_color(core: str, info: dict[str, Any]) -> None:
    """Emit the color at [18:24] as an opaque RGB value. Offset is cross-confirmed; the exact
    value semantics are still unconfirmed (see module docstring)."""
    rgb = int(core[COLOR_OFFSET:COLOR_OFFSET + COLOR_LEN], HEX_BASE)
    info["RGB_1"] = rgb
    info["COLOR_NUMS"] = 1
    info["ALPHA"] = OPAQUE_ALPHA
    info["ARGB_COLOR"] = OPAQUE_ALPHA << ALPHA_SHIFT | rgb


def decode(
    payload_text: str | None, card_uid: list[int], template: dict[str, Any],
) -> dict[str, Any] | None:
    """Decode the decrypted Creality payload into a filament struct, or None if invalid.

    Emits fields cross-confirmed against a real tag and an independent reference decoder
    (vendor, material id, weight, color, UID). Date/serial/vendor-id are left at the template
    default until a real tag confirms them.
    """
    core = _core_text(payload_text)
    if core is None:
        return None
    info = dict(template)
    info["VENDOR"] = CREALITY_VENDOR
    info["MANUFACTURER"] = CREALITY_VENDOR
    # Literal 5-char id (not an int): the material table is keyed by this string.
    info["SKU"] = core[MATERIAL_OFFSET:MATERIAL_OFFSET + MATERIAL_LEN]
    material = creality_types.material_for_id(info["SKU"])
    if material is not None:
        # The Creality tag carries no type/diameter/temps; these come from the id lookup
        # (Creality's own slicer profiles). Diameter is authoritative; temps are nominal
        # defaults the printer may override. Only set fields the profile provided.
        info["MAIN_TYPE"] = material.type
        if material.diameter is not None:
            # The table holds millimetres as Creality's profiles write them (1.75); the shared
            # struct wants hundredths of a millimetre (175), as every other decoder and
            # rfid-ntag's own OpenSpool mapper write it.
            info["DIAMETER"] = round(material.diameter * HUNDREDTHS_PER_MM)
        if material.hotend_min is not None:
            info["HOTEND_MIN_TEMP"] = material.hotend_min
        if material.hotend_max is not None:
            info["HOTEND_MAX_TEMP"] = material.hotend_max
    info["WEIGHT"] = WEIGHT_GRAMS.get(core[WEIGHT_OFFSET:WEIGHT_OFFSET + WEIGHT_LEN], 0)
    _apply_color(core, info)
    info["CARD_UID"] = list(card_uid)
    info["OFFICIAL"] = True
    return info
