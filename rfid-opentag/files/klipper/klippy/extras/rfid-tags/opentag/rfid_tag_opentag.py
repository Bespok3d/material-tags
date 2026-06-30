"""Registers the OpenTag3D decoder with the RFID hub.

Klipper loads this module for the ``[rfid_tag_opentag]`` config section. On ready
it looks up the ``bespok3d_rfid`` hub (shipped by the rfid-ntag plugin) and
registers a payload parser. OpenTag3D data rides an NDEF record of MIME type
``application/opentag3d``, so this parser only claims tags carrying that record
and never collides with OpenSpool or the generic JSON decoder.

Thin relative-import shell: the decode logic lives in the pure, unit-tested
``opentag_fields`` sibling module. ``filament_protocol`` and ``ndef_parser``
resolve as flat ``klippy.extras`` siblings at runtime (placed by rfid-ntag).
"""
import logging

from . import filament_protocol, ndef_parser
from .opentag_fields import build_struct

_log = logging.getLogger("bespok3d.opentag")


class OpenTagParser:
    def to_filament_protocol(self, raw_bytes):
        error, records, card_uid = ndef_parser.ndef_parse(raw_bytes)
        if error != ndef_parser.NDEF_OK or not records:
            return filament_protocol.FILAMENT_PROTO_ERR, None
        template = dict(filament_protocol.FILAMENT_INFO_STRUCT)
        info = build_struct(records, card_uid, template)
        if info is None:
            return filament_protocol.FILAMENT_PROTO_ERR, None
        _log.info("OpenTag3D: vendor=%s type=%s", info.get("VENDOR"), info.get("MAIN_TYPE"))
        return filament_protocol.FILAMENT_PROTO_OK, info


class RfidTagOpenTag:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:ready", self._handle_ready)

    def _handle_ready(self):
        hub = self.printer.lookup_object("bespok3d_rfid", None)
        if hub is None:
            _log.warning("bespok3d_rfid not loaded: OpenTag3D support inactive")
            return
        hub.register_payload_parser(OpenTagParser())
        _log.info("ready: OpenTag3D payload parser registered")


def load_config(config):
    return RfidTagOpenTag(config)
