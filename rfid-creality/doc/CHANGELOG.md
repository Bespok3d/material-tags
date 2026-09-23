# Changelog

## 0.2.2

- Diameter is now reported in hundredths of a millimetre (`175` for 1.75 mm), the unit the shared
  filament record uses and the other decoders report. This decoder reported `1.75`, so anything
  reading `rfid_data.json` saw a different unit for Creality spools than for most other brands.
- The plugin's homepage link now opens the Creality page of the RFID Tag Guide
  (`CrealityRfid.md`) instead of the guide's front page.

## 0.2.1

- Fixed the manifest file publisher field. No functional changes in the plugin.

## 0.2.0

- Verified against a real Creality tag (blue Hyper PLA, 1kg). The decoder now fills, from the
  material id, the fields Creality stores off-tag in its own database: material type, filament
  diameter, and hotend temperature range. These come from a table (`creality_types.py`)
  harvested from Creality's own published slicer profiles (CrealityOfficial/CrealityPrint), not
  from any third-party reader project.
- Payload framing corrected to the real on-tag format (a hex core terminated by '%', then NUL
  padding), which is what let the decoder read a real tag at all.
- Material id is now emitted as its literal id string (for example "01001"), not parsed as an
  integer, so ids that contain letters are handled and the value matches Creality's id scheme.
- Weight bucket confirmed against hardware (1000 g).
- Color is decoded from the tag as RGB. Known rough edge: on the sample spool the tag stored a
  color that does not match the physical filament (a factory write error on that spool), so the
  reported color may not always match the real filament. Every independent reader shows the same
  on-tag value.
- Test keys scrubbed: the unit tests no longer contain the real community keys. They use
  throwaway dummy keys and a dummy-encrypted fixture, so the public repository does not
  distribute the keys (the plugin still ships only their SHA-256 hashes).
- Promoted to the rc channel. Rough edges: validated against one real tag so far (other material
  ids are resolved from Creality's profiles but not yet seen on hardware), and the color caveat
  above.

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