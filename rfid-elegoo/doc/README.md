# Elegoo Filament Tag (EXPERIMENTAL)

> **Status: factory Elegoo spools read on a Snapmaker U1, with one extra step when loading.**
> Elegoo's tag is an NTAG-type tag inside the cardboard, further out than the U1's reader reaches
> for that kind of tag, so a spool sitting on its holder is not read. Hold the tag over the reader
> while the filament feeds, as described in [Loading an Elegoo spool](#loading-an-elegoo-spool),
> and it reads. Confirmed on one printer and one spool so far; see the
> [call to action](#call-to-action).

Decoder for the filament data on factory Elegoo (Centauri) spool tags. The data lives on the tag
in the clear, with no vendor key, so no reverse-engineered secret is needed to read it.

It plugs into the **RFID Spool Reader** (`rfid-ntag`), which it installs for you, and needs
version **0.1.15 or newer** of it. When an Elegoo tag is read, the detected filament is written to
the shared `rfid_data.json` like every other decoder, so Spoolman and the touchscreen just know
what spool is loaded.

## How it works

The RFID Spool Reader reads a factory Elegoo tag the same way it reads any NTAG sticker, and hands
the tag's memory to this decoder. The tag holds two things: a small NDEF message (just a link to
elegoo.com) and, after it, a raw binary filament block that is **not** NDEF. This decoder finds
that block by Elegoo's **manufacturer signature** (the header byte `0x36` followed by
`0xEEEEEEEE`), then reads the fields that follow it:

- **Material type** (PLA, PETG, ABS...)
- **Color**, as an RGB value
- **Nozzle temperature range**, minimum and maximum
- **Diameter** (`175` = 1.75 mm)
- **Weight** in grams

Vendor is set to `Elegoo`, and the tag's UID is recorded so Spoolman can track the spool. A factory
spool carries **two** tags, one on each side, with different UIDs and the same filament data, so
the UID Spoolman sees depends on which side the printer read.

**The layout is not the one in ELEGOO's published table.** On a factory tag every field starts on
its own 4-byte page, as the guide's own alignment note says, rather than packed byte against byte
as its field table shows, and the tag also carries a nozzle temperature range the guide does not
mention. This decoder follows the factory tag.

## Loading an Elegoo spool

The U1 reads a spool's tag through a reader in the spool holder, and how far out it reaches
depends on the tag. On the printer tested, Snapmaker, Bambu and Creality tags read from 13 mm to
43.5 mm out from the edge of the spool's centre hole, but NTAG-type tags have to be closer: a
plain NTAG sticker read at 22.5 mm, and at 35 mm it was found but could not be read. A factory
Elegoo tag is an NTAG-type tag, inside the cardboard side, about 35 mm out (on the sample spool it sat
under the printed ELEGOO logo), and a spool sitting on its holder is not read, however it is
turned. The fix is to hold the tag against the centre of the holder for the moment the printer
reads it:

1. **Unwind a little filament**, enough slack for the feeder to pull while you hold the spool.
2. **Hold the spool so its tag sits against the centre of the spool holder.** There is a tag in
   each side of the spool, so either side works.
3. **Feed the filament on that lane** as usual, keeping the spool held there until the lane shows
   the Elegoo spool.
4. **Mount the spool on the holder.** The lane keeps the spool from then on: a later read that
   finds no tag does not replace a spool the printer already knows. Unloading the filament clears
   it, so repeat these steps on the next load.

Holding the tag there and running `DETECT_SPOOLS` works too, if the filament is already loaded.

If it still does not read:

- **Check the RFID Spool Reader version.** Older than 0.1.15, the reader throws the whole tag read
  away, because the tag is smaller than the area it asks for. The printer's log says so at startup.
- Or use one of the other ways below, which need no holding at all.

## Other ways to get it read

Each of these puts a tag where the reader looks, so the spool reads like any tagged spool, with no
holding.

### A sticker at the reader spot

Stick a small **NTAG213 / OpenSpool** sticker on the side of the spool that faces the holder,
**close to the centre hole, about 13 to 20 mm from its edge** (a Snapmaker spool's tag sits at about 13 mm). Not as far out as the factory tag:
at 35 mm a sticker is found but cannot be read. Write it with
OpenSpool and bind it in Spoolman. It then reads first time every time. It carries what you write on
it rather than Elegoo's own data.

### A copy of the Elegoo tag on a sticker

The factory tag has no password, so its filament data can be copied onto a blank NTAG213 or NTAG215
sticker placed at the same reader spot. The copy is then read by this plugin with Elegoo's own
material, color and temperatures.

1. Scan the original tag with NXP TagInfo and note pages `0x10` to `0x18`: that is the filament
   block. **Copy your own spool's pages**; every filament and color has its own values.
2. Write those nine pages, unchanged, to the same page numbers on the blank sticker, with a phone
   app that can send raw NFC-A commands (NFC Tools has one under its "Other" tab) or a USB reader.
   The NTAG write command is `A2`, then the page number, then that page's four bytes. Each
   successful write answers `0A`.
3. **Write nothing to pages below `0x10`, or to the configuration pages at the end of the
   sticker's memory.** They hold the UID, lock bits, settings and password, and some of those bits
   can only ever be set, so one wrong write can lock the sticker for good.
4. Scan the sticker with TagInfo and check that the nine pages match.
5. Stick it close to the centre hole, about 13 to 20 mm from its edge, on the side that faces the holder.

The copy reports the sticker's own UID, not Elegoo's, so bind that UID in Spoolman.

For example, the PLA "Sea Green" 1 kg spool this was tested with gives these nine writes:

```text
A21036EEEEEE
A211EE000000
A21200807665
A21300000000
A21409C299FF
A21500BE00E6
A21600000000
A21700AF03E8
A2180036C800
```

Confirmed on a U1 (2026-09-23): a copy on a blank NTAG215 sticker read in full and decoded as PLA,
`#09C299`, 190 to 230 C, 1.75 mm, 1000 g, under the sticker's own UID.

### Moving the original tag (not yet tested)

Cut out the piece of cardboard that holds the tag and glue it close to the centre hole, about 13 to 20 mm from its edge, on the side
that faces the holder. No respooling needed. Take care: the tag's coil is
thin, and a tear kills it.

### Respooling onto another spool

Move the tag, or a copy, along with the filament, to about 13 to 20 mm from the new spool's centre
hole.
If the new spool has a tag of its own (a Snapmaker spool does), remove or cover it; with two tags in
front of the reader, which one gets read is unpredictable.

### External spool holders

If the spool does not sit on the printer's own holder, a tag fixed at the reader identifies the
**lane**, not the spool. When you change spools, change the tag too, or the lane keeps reporting the
old spool and Spoolman charges its usage to the wrong one.

## What it does not do

- It does **not** write tags. Read-only.
- It does **not** set a sub-type (Silk, CF...) or a production date yet. Neither is confirmed on
  a real tag: the sample spool's sub-type is empty, and its date is not where the guide puts it.
  Both stay blank rather than risk showing a wrong value.
- It does **not** set a bed temperature: none has been found on the tag.

## Findings (2026-09-23, real factory spool)

A factory Elegoo PLA "Sea Green" 1 kg spool was read with a phone (NXP TagInfo), compared field by
field with its label, then loaded on a U1.

- **The tag is open.** It is an NFC Type 2 tag with NTAG213-style memory and no password, made
  by Shanghai Feiju. It is **not** a locked ISO 14443-4 / IsoDep chip, which an earlier note
  claimed.
- **Every decoded field matches the label:** PLA, 1.75 mm, 1000 g, 190 to 230 C, and a teal
  green color (`#09C299`) for "Sea Green".
- **There are two tags,** one on each side of the spool, with different UIDs. The phone read one;
  the U1 read the other. Both carry the same filament data.
- **The U1 read it, once the tag was close to the reader.** Mounted on the holder, the spool read
  only twice in many attempts, and never while sitting still, at any of eight angles. Measured from
  the edge of the centre hole, the Elegoo tag sits at about 35 mm; tags that do read with the spool
  mounted sat at 13 mm (Snapmaker), 22.5 mm (an NTAG sticker), 27.2 mm (Bambu) and 43.5 mm
  (Creality). A plain NTAG sticker taped at 35 mm was found by the reader but could not be read, so
  for NTAG-type tags that distance is the edge of the reader's range; the buried Elegoo tag
  did not answer at all. Held with the tag against the centre of the holder, it read in full on every lane
  tried (three of the four; one needed a second try), including once while the filament fed.
  Every field matched the label each time.

## Findings (2026-06-29, real U1)

> Kept for the record. Its conclusion that the U1 cannot read these tags at all was overturned
> on 2026-09-23: the U1 reads them once the tag is close to its reader. The tag is an NTAG-type
> tag inside the cardboard, further out than the reader reaches for that kind of tag, which is most
> likely why a spool pressed against the reader here never answered; see the findings above.

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

## Call to action

One spool on one printer is not enough to call this done. If you have factory Elegoo spools and a
U1, please report:

- whether the spool was identified, on which lane, and whether you held it as described in
  [Loading an Elegoo spool](#loading-an-elegoo-spool), or used one of the other ways;
- if you can measure it: how far your spool's tag sits from the edge of the centre hole (a phone
  finds the spot), so we know whether every Elegoo spool puts it in the same place;
- the log line this plugin writes when it decodes a spool (it starts `Elegoo: uid=`), next to a
  photo of the spool's label, so every field can be checked;
- for a material or color we have not seen yet (anything but PLA "Sea Green"), a phone scan with
  NXP TagInfo: its text export holds the tag's full memory, which is what confirms the parts of
  the layout that are still open (sub-type, production date).

## Status

Experiment channel. The decode is unit-tested against the complete memory of a real factory spool,
every decoded field matches that spool's label, and the spool reads on a real U1 once its tag is
held over the reader. It stays on the experiment channel until more spools, materials and printers
confirm it.
