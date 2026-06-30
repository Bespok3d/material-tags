"""Registers the OpenPrintTag decoder with the RFID hub.

Klipper loads this module for the ``[rfid_tag_openprinttag]`` config section. OpenPrintTag
data rides an NDEF record of MIME type ``application/vnd.openprinttag``, so this parser only
claims tags carrying that record and never collides with OpenSpool or the other decoders.
It decodes the PAYLOAD on any NTAG the reader can read - Prusa's own factory spools use
ISO-15693 tags the U1 cannot read, but an OpenPrintTag payload written onto a standard
NTAG21x reads and decodes here.

Thin relative-import shell: the decode logic lives in the pure, unit-tested
``openprinttag_fields`` / ``cbor_min`` siblings. ``filament_protocol`` and ``ndef_parser``
resolve as flat ``klippy.extras`` siblings at runtime (placed by rfid-ntag).
"""
import logging

from . import filament_protocol, ndef_parser
from .openprinttag_fields import build_struct

_log = logging.getLogger("bespok3d.openprinttag")


class OpenPrintTagParser:
    def to_filament_protocol(self, raw_bytes):
        error, records, card_uid = ndef_parser.ndef_parse(raw_bytes)
        if error != ndef_parser.NDEF_OK or not records:
            return filament_protocol.FILAMENT_PROTO_ERR, None
        template = dict(filament_protocol.FILAMENT_INFO_STRUCT)
        info = build_struct(records, card_uid, template)
        if info is None:
            return filament_protocol.FILAMENT_PROTO_ERR, None
        _log.info("OpenPrintTag: vendor=%s type=%s", info.get("VENDOR"), info.get("MAIN_TYPE"))
        return filament_protocol.FILAMENT_PROTO_OK, info


class RfidTagOpenPrintTag:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:ready", self._handle_ready)

    def _handle_ready(self):
        hub = self.printer.lookup_object("bespok3d_rfid", None)
        if hub is None:
            _log.warning("bespok3d_rfid not loaded: OpenPrintTag support inactive")
            return
        hub.register_payload_parser(OpenPrintTagParser())
        _log.info("ready: OpenPrintTag payload parser registered")


def load_config(config):
    return RfidTagOpenPrintTag(config)
