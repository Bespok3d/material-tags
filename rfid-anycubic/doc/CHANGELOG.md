# Changelog

## 0.1.0

- First release. Clean-room Anycubic ACE decoder for the plaintext (no key) NTAG21x layout:
  finds the block by the `7B 00 65 00` magic (version 0x65) and decodes the dispute-free
  fields - brand, material, and nozzle/bed temperatures (little-endian) - into the shared
  `rfid_data.json`. Color, diameter, and weight are deliberately NOT decoded: the public
  sources (DnG-Crafts/ACE-RFID, SimplyPrint) disagree on the SKU length, the color byte order,
  and page 31, and no real tag dump has been published to settle them, so guessing is avoided.
  One tester dump unlocks those three. No key, no reader change (payload parser). Read-only.
  Experiment channel.
