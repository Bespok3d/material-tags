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

- Material type (PLA, PETG, ABS, and so on)
- Filament diameter
- Hotend temperature range (nominal; the printer may override)
- Color (RGB)
- Net weight (Creality stores a bucket: 250 / 500 / 600 / 750 / 1000 g)
- Material id (a Creality numeric id)

The tag itself carries only the material id, color, and weight bucket. The material type,
diameter, and temperatures are resolved from the material id using a table built from
Creality's own published slicer profiles, the same way Creality's firmware looks them up from
its on-device database. Diameter is authoritative; the temperatures are nominal defaults.
Creality's material-id to human-name map is not published, so the material id itself stays a
number here.

## A note on color

Color is decoded from the tag as an RGB value. On the spool used to verify this plugin, the
tag stored a color that did not match the physical filament, a data error written to that
spool at the factory. So the color the plugin reports comes straight from the tag and may not
always match what is actually loaded.

## Status

rc channel. The decryption math is verified against the public reverse engineering
(AES-128-ECB throughout, both the UID to card-key derivation and the payload), with no native
crypto dependency: a tiny AES is vendored into the plugin. The decoder has been verified
against a real Creality tag (blue Hyper PLA, 1kg) for material type, diameter, temperature
range, and weight. Other material ids are resolved from Creality's slicer profiles but have
not yet been seen on hardware. Requires the RFID Spool Reader (installed automatically).