# Bambu Filament Tag (EXPERIMENTAL)

Reads **Bambu Lab** filament spool tags on the Snapmaker U1 and decodes the full
filament, the same way a Bambu printer does: material, colour, diameter, weight, and
nozzle/bed temperatures, written to the shared `rfid_data.json` so Spoolman and the
touchscreen just know what spool is loaded.

It installs the **RFID Spool Reader** (`rfid-ntag`) for you and plugs into it; no firmware
reader changes are needed beyond what that plugin already ships.

## You must supply a key

Bambu tags are **encrypted**. Snapmaker's reader cannot open them with its own key, so this
plugin needs the **public Bambu master key** to derive each tag's keys and read it.

**We do not ship the key.** You paste it in once:

1. Get the master key from the community project that documents it: the
   **Bambu-Research-Group RFID-Tag-Guide** (`https://github.com/Bambu-Research-Group/RFID-Tag-Guide`).
   It is a single 32-character hex string, the same on every consumer Bambu spool.
2. Open this plugin's **Config** and paste it into **Bambu master key (hex)**.
3. Save. The plugin validates the key by its hash; if it matches, Bambu tags decode on the
   next tap.

Leave the key empty and Bambu spools are still **tracked by their tag UID** (so you can bind
them to a Spoolman spool by UID); they just are not decoded into material/colour/temps.

## How it works

- Bambu tags are Mifare-Classic cards whose SAK (0x08) is the same as Snapmaker's own M1
  filament tags. When the stock Snapmaker key cannot open a 0x08 card, the reader offers it
  to this plugin.
- The 16 Mifare sector keys are derived from the tag UID with HKDF-SHA256 over the master
  key (clean-room from the public spec), exactly as a Bambu printer does.
- The plugin authenticates and reads the data blocks through the reader's
  `read_mifare_classic` primitive, then decodes the plaintext blocks into the filament
  fields. The encrypted RSA signature blocks are ignored (we only read).

## What it does not do

- It does **not** write tags. Read-only.
- It does **not** decrypt or forge anything you do not already have the public key for, and
  it never stores or transmits your key anywhere off the printer.

## Status

Experiment channel. The key derivation is verified against the RFC 5869 HKDF test vector and
the decode is unit-tested against blocks built to the public Bambu memory map. End-to-end
reading of a real Bambu spool is pending device verification on the U1 bench.
