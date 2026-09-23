# Materials Tracker Plus

Tap a spool on the reader and the printer knows what it is, how much is left, and what colour it
prints. The full filament-awareness setup in one install.

## What it installs

- **RFID Spool Reader**: reads the tag on the spool and runs the decoder hub.
- **Generic NDEF, OpenTag3D, OpenPrintTag, TigerTag**: the open tag standards.
- **Anycubic, Bambu, Creality, Elegoo, QIDI**: the vendor tags. Anycubic and Creality decode fully
  against real tags (type, colour, weight, and more); Bambu and Creality need your own key pasted
  into their settings, and without one they track the spool by the tag's own ID; QIDI needs no key.
  The Creality decoder is a recent release candidate, so its colour may not match every spool yet.
  Elegoo reads factory spools, confirmed on one U1 so far, if you hold the tag against the centre of
  the spool holder while the filament feeds (its tag is small and sits further out than the reader reaches).
- **Spoolman Bridge**: keeps the remaining length of the loaded spool up to date.
- **AFC Lite**: four-lane filament tracking and tool-change macros for the U1.
- **U1 G-code Preview Colors**: shows each tool in the preview in the colour actually loaded.

Everything installs together with a single service restart.

## How it differs from "All the Tags"

"All the Tags" is the reading half: the reader, the decoders, and Spoolman. This adds the two pieces
that use what was read, the filament changer lanes and the real colours in the preview. If you do not
have a changer, "All the Tags" is the one you want.

## Status

Early-access (testing) channel until the stack has been verified end to end on a real printer.
The decoders are read-only; none of them ever writes a tag.
