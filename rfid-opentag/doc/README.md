# OpenTag3D Filament Tag

Reads **OpenTag3D** filament NFC tags. OpenTag3D is an open, vendor-neutral
standard (queengooborg) that stores the full filament profile, manufacturer,
material, color, diameter, weight, and temperatures, as a compact binary block on
an NTAG. No vendor key, no cloud lookup: the data lives on the tag in the clear.

It plugs into the **RFID Spool Reader** (`rfid-ntag`), which it installs for you.
When an OpenTag3D tag is read, the detected filament is written to the shared
`rfid_data.json` like every other decoder, so Spoolman and the touchscreen just
know what spool is loaded.

## How it works

OpenTag3D stores its payload inside an **NDEF record of MIME type
`application/opentag3d`** as big-endian binary. This decoder locates that record,
unpacks the documented field offsets, and maps them into the filament record:

- **Brand / manufacturer** from Filament Manufacturer (16 bytes)
- **Material type** from Base Material Name (PLA, PETG...)
- **Sub-type** from Material Modifiers (CF, Silk...)
- **Color** from Color 1 (RGBA)
- **Diameter** from Target Diameter (micrometres, stored as centi-mm)
- **Weight** from Target Weight (grams)
- **Nozzle min / max** from Extended Min/Max Print Temp, or the core Print Temp
- **Bed temp** from Extended Max Bed Temp, or the core Bed Temp

Core-only tags (NTAG213) carry a single print temperature; the decoder uses it for
both the min and max. Tags with the extended block (NTAG215/216) carry explicit
min/max nozzle and bed temperatures, which are preferred when present.

## What it does not do

- It does **not** write tags. Read-only.
- It does **not** decode multi-color slots beyond the primary color yet (the
  primary color is mapped; additional color slots are a future enhancement).
- OpenSpool (JSON) tags are read by the **RFID Spool Reader** directly, not here.

## Programming tags

Use any OpenTag3D-compatible writer (see [opentag3d.info](https://opentag3d.info/))
with NTAG213/215/216 tags. NTAG215/216 are recommended so the extended temperature
fields fit.

## Status

Experiment channel until verified against a real OpenTag3D tag on a printer. The
decode is unit-tested against spec-constructed payloads at the documented offsets.
