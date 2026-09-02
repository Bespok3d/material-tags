# Changelog

## 0.2.0

- Corrected a wrong foundational assumption: Anycubic ACE tags are a plaintext Mifare
  Ultralight C card, not generic NTAG21x. Ultralight C has a smaller page count, and the
  magic scan now tolerates that: it looks for a `7B 00` prefix followed by a one-byte format
  version (`0x64` or `0x65` confirmed so far, both sharing the same field layout) and a
  trailing zero, instead of matching one fixed four-byte value.
- Decodes SKU, brand (correctly falls back to Anycubic when the field is blank, confirmed
  on a real tag), material, color, diameter, length, weight, nozzle temperature, bed
  temperature (both minimum and maximum), and print speed when the tag carries it. Previously
  only brand, material, and nozzle/bed maximum temperature decoded.
- Corrected the color byte order: it is alpha, then blue, green, red, not alpha, red, green,
  blue. The first sample tested (black) could not distinguish the two orders, since its red
  and blue channels are identical, and looked confirmed when it was not. A second,
  non-symmetric sample (peach pink) broke the tie, independently reinforced by that same tag's
  own SKU, which names the same color through an unrelated field.
- Settled two of the three field disputes the original public reverse engineering
  (DnG-Crafts/ACE-RFID, SimplyPrint) left open: page 31 is the weight in grams, not unused,
  and the color byte order above. The third, the SKU field's width (12 vs 16 bytes), stays
  open: every confirmed sample so far null-pads well short of either boundary.
- Every newly decoded field is confirmed against three independently sourced real tag dumps
  spanning three product lines (PLA+, PLA Spezial, ASA), not synthetic data alone. Weight,
  diameter, and length reproduce identically (1000g, 1.75mm, 330m) on all three, which
  confirms their position but not yet their scale, all three happen to be a standard spool
  size.
- Test suite now includes three regression tests that replay those exact real dumps byte for
  byte, pinning the confirmed output, alongside field-by-field synthetic coverage for every
  decoded value, the version scan, the decline paths, and the blank-brand and blank-SKU cases.
- Promoted from the experiment channel to the release candidate channel.

## 0.1.0

- First release. Clean-room Anycubic ACE decoder for the plaintext (no key) NTAG21x layout:
  finds the block by the `7B 00 65 00` magic (version 0x65) and decodes the dispute-free
  fields - brand, material, and nozzle/bed temperatures (little-endian) - into the shared
  `rfid_data.json`. Color, diameter, and weight are deliberately NOT decoded: the public
  sources (DnG-Crafts/ACE-RFID, SimplyPrint) disagree on the SKU length, the color byte order,
  and page 31, and no real tag dump has been published to settle them, so guessing is avoided.
  One tester dump unlocks those three. No key, no reader change (payload parser). Read-only.
  Experiment channel.
