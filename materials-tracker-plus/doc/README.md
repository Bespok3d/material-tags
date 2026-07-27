# Materials Tracker Plus

Tap a spool on the reader and the printer knows what it is, how much is left, and what colour it
prints. The full filament-awareness setup in one install.

## What it installs

| Plugin | What it does |
| --- | --- |
| RFID Spool Reader | Reads the tag on the spool and runs the decoder hub |
| Generic NDEF, OpenTag3D, OpenPrintTag, TigerTag | The open tag standards |
| Anycubic, Bambu, Creality, Elegoo | The vendor tags (Bambu and Creality need your own key pasted into their settings; without one they still track the spool by its serial) |
| Spoolman Bridge | Keeps the remaining length of the loaded spool up to date |
| AFC Lite | Four-lane filament tracking and tool-change macros for the U1 |
| U1 G-code Preview Colors | Shows each tool in the preview in the colour actually loaded |

Everything installs together with a single service restart.

## How it differs from "All the Tags"

"All the Tags" is the reading half: the reader, the decoders, and Spoolman. This adds the two pieces
that use what was read, the filament changer lanes and the real colours in the preview. If you do not
have a changer, "All the Tags" is the one you want.

## Experiment channel

The stack is on the experiment channel until it has been verified end to end on a real printer.
