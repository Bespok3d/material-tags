# QIDI Filament Tag decoder

Decodes QIDI filament spool tags on stock firmware and writes the filament into the shared
`rfid_data.json`, so the touchscreen and Spoolman treat a QIDI spool like a Snapmaker one.
Read-only: it never writes a tag.

## No key needed, and none shipped

QIDI leaves its spool tags on the **Mifare factory default key** (`FF FF FF FF FF FF`), the
key every blank Mifare Classic card ships with. There is nothing for you to paste into a
config, nothing for anyone to obtain, and nothing secret in this package. That is the whole
difference from the Bambu and Creality decoders, which do need a key you supply.

The printer's stock reader tries its own Snapmaker key on the card first and fails, which is
normal and harmless: the reader then hands the card to this decoder, which opens it.

## What is on the card, and what is not

The entire QIDI payload is the first data block of sector 1: **three bytes**, then thirteen
zeros.

| Byte | Meaning |
| --- | --- |
| 0 | material code |
| 1 | colour code |
| 2 | manufacturer code (`0x01` is QIDI itself) |

So a QIDI tag identifies the filament and nothing else. It carries **no weight, no diameter,
no nozzle or bed temperature, no manufacture date and no SKU**. Those fields are left at their
defaults here rather than invented, and keep coming from your slicer profile or from Spoolman.

A spool whose manufacturer code is not QIDI's own reads as `QIDI-compatible` rather than
`QIDI`, so a third-party spool using the format is still identified and still says so.

## Unknown codes are reported, never guessed

The material and colour tables hold **only pairings confirmed against a physical spool**. QIDI
publishes no list, and a wrong guess would show you the wrong material or the wrong colour.

When a spool carries a code that is not in the tables, the spool still tracks: the material
reads as `UNKNOWN` with the raw code beside it, the colour is left alone, and the log line
says exactly which code was unmapped:

```text
QIDI: tag read, code not in the tables: material 0x1f, colour 0x33
```

That line is the whole contribution: send it with what the spool actually is, and the pairing
joins the tables in the next release. The community keeps wider code lists, notably
[OpenRFID](https://github.com/suchmememanyskill/OpenRFID); this decoder deliberately ships only
what it has seen on real cards rather than importing a list it cannot verify.

## Not QIDI? Nothing breaks

A Mifare card that opens on the default key but does not have QIDI's shape (three non-zero
codes, then an all-zero tail) is handed back to the reader untouched, which carries on to the
next decoder and finally to its UID-only fallback. Any card is at worst tracked by its tag UID.

## Status

Stable channel. The decode is unit-tested, and the read is verified end to end on a real
Snapmaker U1 against physical QIDI spools (PLA Matte and PETG). Requires the RFID Spool Reader,
which is installed automatically.
