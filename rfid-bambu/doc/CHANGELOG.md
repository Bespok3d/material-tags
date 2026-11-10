# Changelog

## 0.3.0

- A Bambu spool has a tag on each side. With the key set, both sides now carry the same spool
  id. Spoolman Bridge is optional; version 0.1.40 or newer uses that id to keep both sides as
  one spool.
- A two-colour spool now shows both its colours instead of only the first.

## 0.2.1

- Fixed the manifest file publisher field. No functional changes in the plugin.

## 0.2.0

- Second release. This is the first working version of this plugin, verified to be working on a U1 printer.

## 0.1.0

- First release. Decodes Bambu Lab filament tags (encrypted Mifare Classic) into the shared
  rfid_data.json: material, colour, diameter, weight, and nozzle/bed temperatures. The
  master key is user-supplied (see the documentation); with no key, Bambu spools are tracked
  by their tag UID. Requires the RFID Spool Reader, which it installs automatically. Read-only.
  Experiment channel until verified on a real tag.
