# Changelog

## 0.1.2 - 2026-08-13

- QIDI spools now read. The new QIDI decoder comes with the stack and needs no key from you: QIDI
  leaves its tags on the factory default key every blank card ships with. A QIDI tag carries the
  material, the sub-type, and the colour, and nothing else, so weight, diameter, temperatures, and
  date still come from your slicer profile or from Spoolman.

## 0.1.1 - 2026-07-27

- Say what the Bambu and Creality decoders actually fall back to without a key: the tag's own ID, not
  the spool's serial number.

## 0.1.0 - 2026-07-27

- First release of the "Materials Tracker Plus" collection: the whole RFID tag-reading stack (reader,
  all eight decoders, Spoolman tracking) plus AFC Lite and the U1 G-code preview colours, installed
  in one batch with a single service restart.
- Experiment channel until the full read -> decode -> track stack is verified end to end on a real
  printer.
