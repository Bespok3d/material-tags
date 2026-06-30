# Elegoo Filament Tag (EXPERIMENTAL)

> **Status: the factory Elegoo Centauri spool tags do NOT read on the Snapmaker U1 today, and
> the cause is the U1's reader hardware, not this decoder.** This is the corrected conclusion
> after a full hardware investigation on a real U1 (2026-06-29); it supersedes the earlier
> "ISO 14443-4 / IsoDep locked tag" guess. See [Findings](#findings-2026-06-29-real-u1) and the
> [call to action](#call-to-action) below. This decoder is correct and ready for the day the
> reader can wake those tags (or for any Elegoo tag re-written to the published NTAG layout).

Decoder for Elegoo's published NTAG EPC-256 tag layout. On a tag using that layout, the
filament data lives on the tag in the clear, with no vendor key, so no reverse-engineered
secret is needed to read it.

It plugs into the **RFID Spool Reader** (`rfid-ntag`), which it installs for you. When
an Elegoo tag is read, the detected filament is written to the shared `rfid_data.json`
like every other decoder, so Spoolman and the touchscreen just know what spool is
loaded.

## How it works

Unlike OpenSpool or OpenTag3D, Elegoo data is **not** NDEF: it is a raw binary
EPC-256 block written directly to the NTAG pages. This decoder finds the block by
Elegoo's **manufacturer signature** (the header byte `0x36` immediately followed by
the `0xEEEEEEEE` "ELEGOO" code) anywhere in the tag, then reads the fields that follow:

- **Material type** from the 4-byte ASCII material name (PLA, PETG...)
- **Sub-type** from the 4-byte ASCII modifier (CF, Silk...)
- **Color** from the 3-byte RGB value
- **Diameter** from the 2-byte value (hundredths of a mm; `0x00AF` = 1.75 mm)
- **Weight** from the 2-byte value (grams)

Vendor is set to `Elegoo`. Finding the block by its signature means the decoder does
not depend on exactly which NTAG page the data starts on.

## What it does not do

- It does **not** write tags. Read-only.
- It does **not** set temperatures: Elegoo tags carry no nozzle or bed temperature, so
  those come from your slicer profile or Spoolman, not the tag.

## Findings (2026-06-29, real U1)

A full hardware investigation on a real U1 (printer "junior") settled what is and is not the
problem. Corrections to earlier guesses are called out, because they matter.

- **The data is NOT locked.** Elegoo's official guide documents a plain **NTAG213** with the
  filament data in **open, unencrypted user memory** (no key, no auth). The earlier "ISO 14443-4 /
  IsoDep, locked behind a vendor key" claim was wrong: it came from a phone only reading the tag's
  NDEF (a single `elegoo.com` URL), while the filament data sits in raw pages a normal reader reads.
- **The factory tag does not answer the U1's reader at the RF layer.** On a real U1 the reader's
  wake-up (WUPA) gets zero response from the factory Elegoo tag, so it never reaches anticollision,
  never selects, and this decoder never sees bytes. Meanwhile Snapmaker M1 and standard NTAG tags
  (including NTAG on the same coil) read every time.
- **It is not software-fixable on the U1, as far as we can reach.** We swept the reader's *entire*
  configurable register space, validated by a real (BCC-checked) UID so receiver noise cannot fake a
  hit: receiver gain, demodulator, threshold, RX timing; transmit drive strength, modulation depth;
  both antenna coils; tag pressed flat AND with a ~1cm gap. Every combination: nothing from the
  Elegoo tag, while M1/NTAG kept reading.
- **It is not exotic hardware and not field strength.** A phone (a *smaller* antenna than the U1's
  ~10cm coil) reads these tags, and so does Elegoo's own ~50-euro Canvas reader. So the tag is a
  normal, wakeable ISO 14443-A tag; the gap is specifically the **U1 reader's antenna/matching
  coupling** with this particular tag, which is below what any reader register can change.

**Net:** the factory Elegoo Centauri tags are a reader-hardware wall on the U1 specifically. Other
readers wake them; the U1's does not, by any setting or position we could find.

### Workaround that works today

Stick a small **NTAG213 / OpenSpool** sticker on the spool, **on the opposite side of the spool
ring** from the factory Elegoo tag (separation avoids the two tags detuning/colliding; covering the
factory tag with foil tape also works), write it with OpenSpool, and bind it in Spoolman. This reads
first time, every time on the U1.

### Call to action

We want to know whether *some* U1 units / firmware / antenna revisions can wake these tags, and if
any reader setting does it on hardware we have not tried. Help us collect data:

- Run the reader debug tools in `plugins/u1-enhanced-rfid/tools/` on your U1 (they do a validated,
  real-UID sweep across channels and are safe: volatile registers only, reader restored on Klipper
  restart). Report your firmware version, what the sweep finds for your Elegoo spools, and your
  tag's UID/chip from a phone (NXP TagInfo: the "IC manufacturer" and UID first byte tell us genuine
  NXP NTAG213 vs a clone).
- If you have a tag that DOES read on a U1, the register combo + firmware that worked is the prize.

Enough comparable data across machines may turn today's "works by luck of position" into a real,
reproducible answer.

## Status

Experiment channel. The decode is unit-tested against blocks built to Elegoo's published EPC-256
layout (field order/lengths from the public spec, signature-anchored so it does not depend on the
start page). It is correct for any tag that presents that layout; the blocker is purely the U1
reader waking the factory tag (see Findings).
