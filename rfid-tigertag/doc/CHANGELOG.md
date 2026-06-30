# Changelog

## 0.1.0

- First release. Clean-room TigerTag decoder for the open NTAG21x raw-page layout: finds
  the data block by TigerTag's magic header (standard `0x5BF59264` and Plus `0xBC0FCB97`;
  the blank/init marker is declined) and decodes color (RGBA), diameter (from the diameter
  code), nozzle min/max + bed + drying temperatures, weight, and product id (as SKU) into the
  shared `rfid_data.json`. Offsets follow the official TigerTag-RFID-Guide spec (NTAG213,
  big-endian). No key, no reader change - registers as a payload parser on the standard NTAG
  path. Brand and material are kept as numeric ids (their name maps are GPLv3, not vendored).
  Read-only. Experiment channel.
