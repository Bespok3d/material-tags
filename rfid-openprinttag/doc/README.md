# OpenPrintTag Filament Tag decoder

Decodes the **OpenPrintTag** data format on stock firmware and writes the filament into the
shared `rfid_data.json`, so the touchscreen and Spoolman treat the spool like a Snapmaker
one. Read-only: it never writes a tag.

## We decode the payload, not the hardware

OpenPrintTag (by Prusa) is an open, CBOR-encoded filament data format. This plugin decodes
that **payload**. There is no key.

One caveat worth stating plainly: Prusa's own factory spools carry the OpenPrintTag payload
on **ISO-15693** tags, which the U1's NFC reader cannot read (it is ISO-14443A only). That
is a hardware-tech choice, not a payload limitation. The same OpenPrintTag payload written
onto a **standard NTAG21x** (which the U1 reads perfectly) decodes here just fine. So this
plugin is for anyone who wants to use the OpenPrintTag data model on NTAG tags.

## What it decodes

- Material and brand (the human-readable names from the payload)
- Color (RGB or RGBA)
- Filament diameter
- Net weight
- Nozzle temperature (min and max) and bed temperature
- Drying temperature and time
- Manufacture date

It declines any tag that is not an OpenPrintTag record (it keys off the
`application/vnd.openprinttag` NDEF record type), so it never shadows OpenSpool, OpenTag3D,
or the generic JSON decoder.

## Status

Experiment channel. The CBOR reader is a minimal, vendored, pure-python decoder (no native
dependency) covering exactly the subset OpenPrintTag uses, and the field map is verified
against the public spec (specs.openprinttag.org / prusa3d/OpenPrintTag) and a real captured
Prusament payload. Verified end-to-end by testers (write an OpenPrintTag payload to an
NTAG215 and tap it). Requires the RFID Spool Reader (installed automatically).
