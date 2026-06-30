# TigerTag Filament Tag decoder

Decodes TigerTag filament tags on stock firmware and writes the filament into the shared
`rfid_data.json`, so the touchscreen and Spoolman treat a TigerTag spool like a Snapmaker
one. Read-only: it never writes a tag.

## No key needed

TigerTag is an **open** standard on a plain NTAG21x. There is no encryption and no key to
paste - the standard NTAG reader reads it directly, and this decoder finds TigerTag's data
block by its magic header and reads the documented fields.

## What it decodes

- Color (RGBA)
- Filament diameter (from TigerTag's diameter code: 1.75 mm or 2.85 mm)
- Nozzle temperature (min and max)
- Bed temperature
- Drying temperature and time
- Weight (TigerTag's net-quantity field)
- Product id (surfaced as the SKU)

## Brand and material stay as ids

A TigerTag stores the brand and material as **numeric ids**. The tables that turn those ids
into human names ("PLA", "Polymaker", ...) are published by TigerTag under **GPLv3**, so
vendoring them into this plugin would force the plugin to GPL. To keep the plugin's license
clean, this decoder **keeps brand and material as numeric ids** and decodes only the
physical fields above. (TigerTag also runs a free public lookup API; a future, optional
online name-resolution step could use it without bundling any GPL data.)

## Status

Experiment channel. Both the standard (`0x5BF59264`) and Plus (`0xBC0FCB97`) magic are
decoded; a blank/init tag is declined. Field offsets follow the official TigerTag-RFID-Guide
spec (NTAG213, pages 0x04-0x27, big-endian). Verified by testers on real tags. Requires the
RFID Spool Reader (installed automatically).
