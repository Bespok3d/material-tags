# Changelog

## 0.1.0

- First release. Clean-room Creality CFS decoder on the rfid-ntag crypto1 substrate:
  derives the card key from the tag UID (AES-128-ECB of the tiled UID, master key
  user-supplied), authenticates sector 1 (Key B), reads blocks 4-6, and AES-128-ECB-decrypts
  the 48-byte payload with a second user-supplied key. Decodes color, weight bucket,
  manufacture date, and the numeric material id into the shared `rfid_data.json`. AES is
  vendored (pure python, no native dependency) and verified against the FIPS-197 vectors;
  key derivation + ECB mode verified against the public DnG-Crafts/flamebarke reverse
  engineering. Both keys are user-supplied; we ship only their SHA-256 hashes, never the
  keys. No/invalid key -> UID-only tracking. Read-only. Experiment channel.
- Known open item for device verification: implementations load the derived key as Key B
  (this plugin does too); if a real tag needs Key A, that is a one-line change. Creality's
  tag carries no diameter/temperatures, and the material-id name map is not published.
