# Anycubic ACE Filament Tag decoder

Decodes Anycubic ACE filament tags on stock firmware and writes the filament into the shared
`rfid_data.json`, so the touchscreen and Spoolman treat the spool like a Snapmaker one.
Read-only: it never writes a tag.

## No key needed

Anycubic ACE tags are plaintext NTAG21x - no encryption, no key. The standard NTAG reader
reads them directly, and this decoder finds the data block by Anycubic's `7B 00 65 00` magic
(the `0x65` byte is the ACE format version).

## Partial by design - and why

The public reverse engineering (DnG-Crafts/ACE-RFID, SimplyPrint) **agrees** on the magic,
the version, the ASCII brand and material fields, and the nozzle/bed temperatures. It
**disagrees** on three things, and no real captured tag dump has been published to settle
them:

- the SKU field length (12 vs 16 bytes),
- the color byte order (ARGB vs ABGR at page 20),
- whether page 31 holds the weight or is unused.

Rather than guess and show a wrong color or a 10x-off weight, this decoder ships only the
fields the sources agree on:

- Brand
- Material
- Nozzle temperature (min and max)
- Bed temperature

Color, diameter, and weight are **left undecoded** until one tester captures a real Anycubic
ACE tag. The moment that dump exists, those three fields are a small, mechanical addition.

## Help finish it

If you have an Anycubic ACE spool, tap it on a phone (NFC Tools / NXP TagInfo) and share the
raw page dump - that pins the SKU length, color order, and page 31, and unlocks the rest.

## Status

Experiment channel. Brand/material/temps decode from the agreed layout (NTAG21x,
little-endian). Requires the RFID Spool Reader (installed automatically).
