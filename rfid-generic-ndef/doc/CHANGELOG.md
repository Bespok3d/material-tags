# Changelog

## 0.2.0

- A tag whose data type name mixes capital and small letters is now read too.
- Only real hex colors are read (`RRGGBB` or `RRGGBBAA`, with or without `#`). Short forms
  like `F00`, signs and plain numbers no longer turn into a wrong color.
- The main color comes from the first color field that holds a real color, so a bad value in
  one field no longer hides a good one in the next.
- A tag with extra colors but no main color, or a main color that is not a real color, now
  shows its first extra color as the main one, instead of white.
- A tag that lists extra colors now shows all of them, up to five in total, instead of only
  the first.
- Text only: the description no longer says experiment; the plugin is already on the stable
  channel, and the doc now says so.

## 0.1.0

- First release. Best-effort decoder for untagged JSON-over-NDEF filament tags:
  maps common field aliases (brand, type, color, temps, diameter, weight) into the
  shared `rfid_data.json`. Declines protocol-keyed JSON so OpenSpool is never
  shadowed. Read-only. Experiment channel until verified on a real tag.
