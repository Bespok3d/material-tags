# Changelog

## 0.1.0

- First release. Decodes Bambu Lab filament tags (encrypted Mifare Classic) into the shared
  rfid_data.json: material, colour, diameter, weight, and nozzle/bed temperatures. The
  master key is user-supplied (see the documentation); with no key, Bambu spools are tracked
  by their tag UID. Requires the RFID Spool Reader, which it installs automatically. Read-only.
  Experiment channel until verified on a real tag.
