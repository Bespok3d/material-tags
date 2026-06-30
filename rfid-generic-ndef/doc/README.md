# Generic NDEF Filament Tag

Reads filament NFC tags that store their data as **plain JSON in an NDEF record**
but do not use a recognized protocol. OpenSpool and other protocol-keyed tags are
handled by their own decoders; this one is the best-effort catch-all for "someone
just wrote some JSON to a tag".

It plugs into the **RFID Spool Reader** (`rfid-ntag`), which it installs for you.
When a tag is read, the detected filament is written to the shared
`rfid_data.json` like every other decoder, so the rest of your stack (Spoolman,
the touchscreen) just knows what spool is loaded.

## What it reads

Any NDEF `application/json` record **without** a `protocol` field. It maps common
field names (first match wins, case-sensitive) into the filament record:

- **Brand / vendor** from `brand`, `vendor`, `manufacturer`, or `make`
- **Material type** from `type`, `material`, or `material_type`
- **Sub-type** from `subtype`, `sub_type`, or `variant`
- **Color** from `color_hex`, `color`, `colour`, or `hex` (`#RRGGBB` or `RRGGBB`)
- **Nozzle min / max** from `min_temp` / `max_temp` (also `nozzle_*`, `hotend_*`, `temp_*`)
- **Bed temp** from `bed_temp`, `bed_max_temp`, `bed_min_temp`, or `bed`
- **Diameter** from `diameter` or `diameter_mm` (mm)
- **Weight** from `weight`, `weight_g`, or `net_weight` (g)

A tag that carries none of the known fields is ignored, so this parser never
claims unrelated JSON. A tag that carries `"protocol": "..."` is left to its own
decoder, so OpenSpool is never shadowed.

## What it does not do

- It does **not** write tags. Read-only.
- It does **not** decode binary or encrypted tags. For a binary open standard use
  the **OpenTag3D** decoder; OpenSpool tags use the **RFID Spool Reader** directly.

## Status

Experiment channel until verified against a real tag on a printer. The decode is
unit-tested against representative payloads.
