# Changelog

## 0.1.1

- Fix a Klipper load failure that auto-deactivated the plugin on install ("the Python import
  of 'cbor_min' failed"). The `openprinttag_fields` helper imported its `cbor_min` sibling with
  a flat `import cbor_min`, which resolves in the unit tests but not at runtime: Klipper loads
  the placed files into the `extras` package, so the sibling is `extras.cbor_min` and must be
  imported relatively (`from . import cbor_min`), matching every other decoder in this list. The
  unit tests now import the modules through their package, so a future flat-import regression
  fails the suite instead of only the printer.

## 0.1.0

- First release. Clean-room OpenPrintTag (prusa3d) decoder: a minimal vendored pure-python
  CBOR reader (the subset OpenPrintTag uses - ints, byte/text strings, arrays, definite and
  indefinite maps, f16/f32/f64; no native dependency) plus a field map verified against the
  public spec (specs.openprinttag.org / prusa3d/OpenPrintTag) and a real captured Prusament
  payload. Decodes material/brand names, color (RGB/RGBA), diameter, weight, manufacture
  date, and nozzle/bed/drying temperatures into the shared `rfid_data.json`. Registers as a
  payload parser keyed on the `application/vnd.openprinttag` NDEF record type, so it declines
  every other tag. We decode the payload on any readable NTAG21x; Prusa's factory ISO-15693
  spool tags are unreadable on the U1, but that is the tag tech, not the payload. Read-only.
  Experiment channel.
