# Creality Filament Tag decoder

Decodes Creality CFS filament spool tags on stock firmware and writes the filament into
the shared `rfid_data.json`, so the touchscreen and Spoolman see a Creality spool the same
way they see a Snapmaker one. Read-only: it never writes a tag.

## You must supply two keys

Creality CFS tags are encrypted Mifare Classic cards. To decode them the plugin needs two
AES keys that Creality embeds in its own software. They are **public** (the 3D-printing
community recovered them), but Bespok3d does **not** ship them - you paste them into this
plugin's config:

- **Creality master key** - derives the card key from the tag UID.
- **Creality payload key** - decrypts the filament data block.

Where to get them: the community RFID research, e.g. the Bambu-Research-Group
RFID-Tag-Guide (`CrealityRfid.md`) and the DnG-Crafts / K2-RFID project. Paste each as 32
hex characters. The plugin validates each paste against a stored SHA-256 hash, so a typo is
rejected rather than silently producing garbage.

Without the keys (or with the wrong keys), a Creality spool is still **tracked by its tag
UID** - it just is not decoded into material/color. Bind that UID to a spool in Spoolman
(via the RFID Spool Reader) and every future tap is identified.

## What it decodes

- Color (RGB)
- Net weight (Creality stores a bucket: 250 / 500 / 600 / 750 / 1000 g)
- Manufacture date
- Material id (a Creality numeric id; its human name lives in Creality's unpublished
  material database, so it stays a number here)

Creality's tag does **not** carry filament diameter or nozzle/bed temperatures - the
printer looks those up from the material id in its own database - so this decoder leaves
those fields at their defaults.

## Status

Experiment channel. The decryption math is verified against the public reverse engineering
(AES-128-ECB throughout, both the UID->card-key derivation and the payload), with no native
crypto dependency - a tiny AES is vendored into the plugin. The on-tag field positions
follow the K2-RFID community schema. Real-spool decoding is verified by testers; if a real
tag exposes a key-slot or field difference, the plugin degrades to UID-only tracking rather
than failing. Requires the RFID Spool Reader (installed automatically).
