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
`application/opentag3d`** as big-endian binary. This decoder reads the first such
record (the spec puts all the tag data in it), reads the tag version, unpacks the
documented field offsets of that version, and maps them into the filament record:

- **Brand / manufacturer** from Filament Manufacturer (16 bytes)
- **Material type** from Base Material Name (PLA, PETG...)
- **Sub-type** from Material Modifiers (CF, Silk...)
- **Color** from Color 1 (RGBA), plus Colors 2 to 4 on multi-color spools (an unused slot,
  transparent black, is skipped)
- **Diameter** from Target Diameter in v1, Filament Diameter in v2 (stored in micrometres,
  read as centi-mm)
- **Weight** from Target Weight (grams)
- **Nozzle min / max** and **bed temp**, see below

Version 2 tags (the current format) keep the version and material where v1 has them
and move every later field. The nozzle min / max come from Minimum / Maximum Print
Temperature, or the target Print Temperature when the tag leaves them unset; the bed
temp is the target Bed Temperature. A tag that stops early is read with the missing
bytes as zero, as the spec says, but it must reach at least the weight field.

Version 1 tags, and older ones below version 1.000, keep the v1 layout. Core-only v1
tags (NTAG213) carry a single print temperature; the decoder uses it for both the min
and max. Tags with the extended block (NTAG215/216) carry explicit min/max nozzle and
bed temperatures, which are preferred when present.

A tag of a newer major version (3 or later) is not read, so it is never shown with
wrong data.

## What it does not do

- It does **not** write tags. Read-only.
- OpenSpool (JSON) tags are read by the **RFID Spool Reader** directly, not here.

## Programming tags

Use any OpenTag3D-compatible writer (see [opentag3d.info](https://opentag3d.info/))
with NTAG215/216 tags. A version 2 tag is longer than the 144 bytes an NTAG213 holds, so
NTAG213 only fits the version 1 format.

## Status

Experiment channel until verified against a real OpenTag3D tag on a printer. The
decode is unit-tested against spec-constructed payloads at the documented offsets.
