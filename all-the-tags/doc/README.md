# All the Tags

One collection that installs the whole RFID filament-tag reading stack for your printer: the
reader, every tag-standard decoder, and Spoolman tracking. Tap a spool and, if its tag is one
Bespok3d can read, it is identified and tracked automatically.

"Install all" installs only the members you do not already have, in a single batch (one service
restart, not one per plugin). The members are ordinary plugins afterward; you can manage or remove
each on its own. The collection itself is not installed and has nothing to uninstall.

## What each member does

- **RFID Spool Reader (`rfid-ntag`)** - the reader and hub. Reads NTAG/OpenSpool tags and routes
  every tag to the right decoder. Required by all the decoders; installed first.
- **Generic NDEF JSON (`rfid-generic-ndef`)** - best-effort decoder for untagged `application/json`
  filament tags. Open, no key.
- **OpenTag3D (`rfid-opentag`)** - the OpenTag3D open standard (NDEF binary). Open, no key.
- **OpenPrintTag (`rfid-openprinttag`)** - the OpenPrintTag CBOR payload on any readable NTAG. Open,
  no key. (Prusa's own factory spools use an ISO-15693 tag the printer cannot read; the payload
  decoder still works on a tag you write yourself.)
- **TigerTag (`rfid-tigertag`)** - the TigerTag open NTAG21x layout. Open, no key. Brand and material
  are kept as numeric ids (their public name maps are not bundled).
- **Anycubic ACE (`rfid-anycubic`)** - plaintext Anycubic NTAG. PARTIAL: the dispute-free fields
  (brand, material, nozzle and bed temperatures) decode today; color, diameter, and weight wait for
  one real tester dump.
- **Bambu (`rfid-bambu`)** - full Bambu payload decode. Needs YOUR Bambu master key pasted into the
  plugin's config; without a key it falls back to UID-only tracking. We ship only the key's checksum,
  never the key.
- **Creality (`rfid-creality`)** - full Creality CFS payload decode. Needs YOUR two Creality keys in
  the plugin's config; without them it falls back to UID-only tracking. Keys are validated by
  checksum, never shipped.
- **Elegoo (`rfid-elegoo`)** - the published Elegoo NTAG layout. Note: current factory Elegoo
  (Centauri) spools use an IsoDep chip the printer's reader cannot wake, so those read UID-only; this
  decoder covers the documented NTAG layout.
- **Spoolman (`spoolman`)** - closes the loop: it tracks the identified spool in your Spoolman server,
  by tag UID as well as by SKU, so a tag you have bound to a spool is recognized on every tap.

## Getting keys for the proprietary tags

Bambu and Creality tags are encrypted. The keys are community-known but not ours to ship, so you
paste them into each plugin's config yourself (see that plugin's own documentation for where to get
the key and exactly what to enter). With no key, the spool is still tracked by its hardware UID once
you bind that UID to a spool in Spoolman.

## Status

Experiment channel until the whole stack is verified end to end on a real printer. The decoders are
read-only; none of them ever writes a tag.
