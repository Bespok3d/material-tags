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
- **QIDI (`rfid-qidi`)** - full QIDI payload decode, and no key to supply: QIDI leaves its tags on
  the factory default key every blank card ships with. A QIDI tag carries only the material, the
  sub-type, and the colour, so weight, diameter, temperatures, and date keep coming from your slicer
  profile or Spoolman.
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

Snapmaker's own spools work that way too, verified on a Snapmaker U1 running stock firmware with two
genuine Snapmaker spools: the firmware exposes each card's own hardware UID, and binding that UID to
a spool in Spoolman makes the lane resolve by the card itself. With the filament's **Article Number**
cleared in Spoolman, so no SKU match was possible, unloading and reloading the spool still resolved
to the bound spool. Bind with `SH_BIND_CARD_UID CHANNEL=<lane> SPOOL=<spoolman id>`. Two spools on
one firmware were tested: that is what those spools do, not a claim about every Snapmaker spool, and
nothing is claimed about other vendors' tags.

## What a tag does not fix

Reading a tag tells the printer what is on the lane. It does not make your slicer agree. Snapmaker
Orca's **Sync Filament Information** only ever matches filaments Snorca/Orca ships itself, so anything else
syncs its colour and falls back to `Generic <material>`. That is Snorca/Orca's own behaviour and nothing
here changes it.

A tag also has to resolve to a spool that exists in Spoolman. Spools themselves come back after a
reboot on their own, tagged or not: the tag data is kept on the printer and read back at startup, and
a spool picked by hand on an untagged lane is kept the same way. What a tag cannot do is land on a
spool that is not there. While it resolves to nothing the lane shows what the tag says with no
Spoolman spool behind it, and a spool picked by hand for that lane is not kept, because on a tagged
lane the tag is what persists. Give the tag
something to land on once and it stops: bind it (`SH_BIND_CARD_UID CHANNEL={0..3} SPOOL=<id>`), or
fill the SKU the tag reports into the filament's **Article Number** in Spoolman. Either one is
enough, and the Article Number route is the one to reach for whenever the tag reports a SKU. When a
lane looks wrong for any other reason, `DETECT_SPOOLS` is the last line of defence: it re-reads every
lane on the spot, so you can force the detection without rebooting and without pulling the spool off
the printer and putting it back on.

The Spoolman Bridge doc covers both under "Limits worth knowing about".

## Status

Stable channel. The decoders are read-only; none of them ever writes a tag.
