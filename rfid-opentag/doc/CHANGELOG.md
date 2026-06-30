# Changelog

## 0.1.0

- First release. Clean-room OpenTag3D decoder: unpacks the big-endian binary
  payload from an NDEF `application/opentag3d` record (manufacturer, material,
  color, diameter, weight, core and extended temperatures) into the shared
  `rfid_data.json`. Read-only. Experiment channel until verified on a real tag.
