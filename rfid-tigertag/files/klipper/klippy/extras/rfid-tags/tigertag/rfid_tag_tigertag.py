"""Registers the TigerTag raw-page decoder with the RFID hub.

Klipper loads this module for the ``[rfid_tag_tigertag]`` config section. TigerTag rides a
standard NTAG21x (SAK 0x04), which the stock rfid-ntag reader already page-reads, so this
plugin needs no reader change: it registers a payload parser that scans the raw page dump
for TigerTag's magic and decodes the block. Parsers are first-OK-wins, so a non-TigerTag
tag (no magic) is declined and the next parser tries.

Thin relative-import shell: the decode logic lives in the pure, unit-tested
``tigertag_fields`` sibling. ``filament_protocol`` resolves as a flat ``klippy.extras``
sibling at runtime (placed by rfid-ntag).
"""
import logging

from . import filament_protocol
from .tigertag_fields import build_struct

_log = logging.getLogger("bespok3d.tigertag")


class TigerTagParser:
    def to_filament_protocol(self, raw_bytes):
        if not raw_bytes:
            return filament_protocol.FILAMENT_PROTO_ERR, None
        info = build_struct(bytes(raw_bytes), dict(filament_protocol.FILAMENT_INFO_STRUCT))
        if info is None:
            return filament_protocol.FILAMENT_PROTO_ERR, None
        _log.info("TigerTag: color=%06X diameter=%s weight=%s",
                  info.get("RGB_1", 0), info.get("DIAMETER"), info.get("WEIGHT"))
        return filament_protocol.FILAMENT_PROTO_OK, info


class RfidTagTigerTag:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:ready", self._handle_ready)

    def _handle_ready(self):
        hub = self.printer.lookup_object("bespok3d_rfid", None)
        if hub is None:
            _log.warning("bespok3d_rfid not loaded: TigerTag support inactive")
            return
        hub.register_payload_parser(TigerTagParser())
        _log.info("ready: TigerTag payload parser registered")


def load_config(config):
    return RfidTagTigerTag(config)
