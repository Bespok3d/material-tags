# Anycubic ACE Filament Tag decoder

Decodes Anycubic ACE filament tags on stock firmware and writes the filament into the shared
`rfid_data.json`, so the touchscreen and Spoolman treat the spool like a Snapmaker one.
Read-only: it never writes a tag.

## No key needed

Anycubic ACE tags are a plaintext Mifare Ultralight C card, no encryption, no key (earlier
research assumed generic NTAG21x, a real tag dump showed it is actually Ultralight C, a
smaller-capacity chip in the same family). The stock reader's page-read handles them
directly, since Ultralight C shares the same read command as NTAG21x, and this decoder finds
the data block by scanning for Anycubic's `7B 00` magic prefix, followed by a one-byte format
version (`0x64` or `0x65` confirmed so far) and a trailing zero.

## What decodes today

Confirmed against three independently sourced tags, spanning PLA+, PLA Spezial, and ASA:

- SKU
- Brand (can be blank on some tags; falls back to Anycubic)
- Material
- Color
- Nozzle temperature (min and max)
- Bed temperature (min and max)
- Diameter
- Length
- Weight
- Print speed (min and max), when the tag carries it: populated on the PLA+ sample tested,
  reads zero on the other two, so it may not be written for every product line

The original public reverse engineering (DnG-Crafts/ACE-RFID, SimplyPrint) settled the magic,
the version byte, and the ASCII brand and material fields, and disagreed on three others with
no real tag dump published to settle them. Two are now settled, from real tags:

- the color byte order is alpha, then blue, green, red, not the more common
  alpha-red-green-blue order (confirmed against a tag where red and blue actually differ; the
  first tag tested was black, where the two orders happen to look identical),
- page 31 is the weight, in grams, not unused.

One is still open:

- the SKU field length (12 vs 16 bytes): every tag decoded so far has a short enough SKU that
  it null-pads well clear of either boundary, so the two possibilities still decode the same
  string either way.

## Still open

- **SKU field length.** Settling this needs a tag whose SKU actually reaches the boundary.
  Anycubic's PLA+ Refill line uses SKUs of the form `AHPLP<color>-A108`, exactly 12 characters
  with no slack, that is the one dump that would prove it either way.
- **Weight, diameter, and length scale factors.** Confirmed correct in position on three
  tags, but all three happen to be a standard 1kg, 1.75mm, 330m spool. A tag with a genuinely
  different weight or length (a refill pouch, a mini spool) is the one sample that would prove
  the scale factors hold generally, not just for the standard size.
- An unidentified fixed byte sits right after the decoded fields, at a different page
  depending on product line. It does not affect anything decoded above.

## Help finish it

If you have an Anycubic ACE spool, especially a PLA+ Refill pack or anything that is not a
standard 1kg, 330m spool, tap it on a phone (NFC Tools / NXP TagInfo) and share the raw page
dump. That is what would close out the two open items above.

## Status

Experiment channel. SKU, brand, material, color, temperatures, diameter, length, and weight
decode from the confirmed layout (Mifare Ultralight C, little-endian); print speed decodes
when the tag carries it. Requires the RFID Spool Reader (installed automatically).