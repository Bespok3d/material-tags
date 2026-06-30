"""Registers the best-effort generic JSON-over-NDEF decoder with the RFID hub.

Klipper loads this module for the ``[rfid_tag_generic_ndef]`` config section. On
ready it looks up the ``bespok3d_rfid`` hub (shipped by the rfid-ntag plugin) and
registers a payload parser. The parser declines protocol-keyed JSON, so it never
shadows OpenSpool or other protocol mappers; the hub tries parsers first-OK-wins.

Thin relative-import shell: the decode logic lives in the pure, unit-tested
``generic_ndef_fields`` sibling module. ``filament_protocol`` and ``ndef_parser``
resolve as flat ``klippy.extras`` siblings at runtime (placed by rfid-ntag).
"""
import logging

from . import filament_protocol, ndef_parser
from .generic_ndef_fields import build_struct

_log = logging.getLogger("bespok3d.generic_ndef")


class GenericNdefParser:
    def to_filament_protocol(self, raw_bytes):
        error, records, card_uid = ndef_parser.ndef_parse(raw_bytes)
        if error != ndef_parser.NDEF_OK or not records:
            return filament_protocol.FILAMENT_PROTO_ERR, None
        template = dict(filament_protocol.FILAMENT_INFO_STRUCT)
        info = build_struct(records, card_uid, template)
        if info is None:
            return filament_protocol.FILAMENT_PROTO_ERR, None
        _log.info("generic-NDEF: vendor=%s type=%s", info.get("VENDOR"), info.get("MAIN_TYPE"))
        return filament_protocol.FILAMENT_PROTO_OK, info


class RfidTagGenericNdef:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:ready", self._handle_ready)

    def _handle_ready(self):
        hub = self.printer.lookup_object("bespok3d_rfid", None)
        if hub is None:
            _log.warning("bespok3d_rfid not loaded: generic-NDEF support inactive")
            return
        hub.register_payload_parser(GenericNdefParser())
        _log.info("ready: generic-NDEF payload parser registered")


def load_config(config):
    return RfidTagGenericNdef(config)
