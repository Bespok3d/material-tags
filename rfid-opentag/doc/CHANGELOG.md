# Changelog

## 0.2.0

- A spool with several colors now shows all of them, up to four, instead of only the first.
- Tags in the current OpenTag3D format (version 2) now show the right brand, colors,
  diameter, weight and temperatures, instead of wrong values.
- Tags in a future format this decoder does not know yet are no longer read with wrong values.
- Only the first OpenTag3D record on a tag is read, as the OpenTag3D spec says.
- A version 1 tag that leaves its min or max nozzle temperature or its max bed temperature at 0
  now shows its print or bed temperature for that one, instead of 0.
- A tag whose data type name mixes capital and small letters is now read too.
- Text only: the description and doc now say testing, the channel this plugin is already on,
  instead of experiment.

## 0.1.0

- First release. Clean-room OpenTag3D decoder: unpacks the big-endian binary
  payload from an NDEF `application/opentag3d` record (manufacturer, material,
  color, diameter, weight, core and extended temperatures) into the shared
  `rfid_data.json`. Read-only. Experiment channel until verified on a real tag.
