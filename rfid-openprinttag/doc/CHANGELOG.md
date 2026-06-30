# Changelog

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
