# Changelog

## 0.2.0

- A tag that lists extra colors now shows all of them, up to five in total, instead of only
  the first.

## 0.1.0

- First release. Best-effort decoder for untagged JSON-over-NDEF filament tags:
  maps common field aliases (brand, type, color, temps, diameter, weight) into the
  shared `rfid_data.json`. Declines protocol-keyed JSON so OpenSpool is never
  shadowed. Read-only. Experiment channel until verified on a real tag.
