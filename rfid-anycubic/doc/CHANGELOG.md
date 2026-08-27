# Changelog

## 0.2.0

- Decodes five fields previously left at template defaults: SKU, color, diameter,
  length, and weight, all confirmed against a real Anycubic PLA+ spool matched to its box
  and seller listing (SKU "AHPLPBK-108", color #212721, 1.75mm, 330m, 1000g), settling two
  of the original three disputes along the way: color is alpha/R/G/B in that stored order
  (no ARGB/ABGR swap), and page 31 is weight in grams, not unused. Diameter and length were
  new finds past what the original dispute even named. SKU decodes correctly but its field
  width (12 vs 16 bytes) stays an open question regardless of sample count, since the
  confirmed tag null pads well short of either boundary. Color, diameter, length, and weight
  are all pending confirmation on further spools, one tag is not enough to rule out a wrong
  offset or scale factor that happens to read plausibly on this one; flagged inline in
  anycubic_fields.py against what a second spool should specifically stress (a fractional
  weight, a saturated non-gray color). Added raw page dump and parsed-field logging to the
  registration shell so a failed or partial decode can be diagnosed from the log alone. No
  key, no reader change, still read-only. Experiment channel.

## 0.1.0

- First release. Clean-room Anycubic ACE decoder for the plaintext (no key) NTAG21x layout:
  finds the block by the `7B 00 65 00` magic (version 0x65) and decodes the dispute-free
  fields - brand, material, and nozzle/bed temperatures (little-endian) - into the shared
  `rfid_data.json`. Color, diameter, and weight are deliberately NOT decoded: the public
  sources (DnG-Crafts/ACE-RFID, SimplyPrint) disagree on the SKU length, the color byte order,
  and page 31, and no real tag dump has been published to settle them, so guessing is avoided.
  One tester dump unlocks those three. No key, no reader change (payload parser). Read-only.
  Experiment channel.
