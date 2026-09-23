"""Registers the Elegoo decoder with the RFID hub as a payload parser. PLUGIN-ONLY, no reader.

A factory Elegoo tag is an NFC Type 2 tag with a cascaded 7-byte UID, so the stock NTAG reader
(SAK 0x04, rfid-ntag's NtagReader) already activates it and reads its pages. Confirmed on a real
U1 (2026-09-23): the tag arrived through NtagReader as card_type 0x00 and reached this parser via
the hub's payload parsers. This plugin therefore registers no hardware handler of its own; it only
turns those pages into a FILAMENT_INFO_STRUCT.

The read depends on rfid-ntag 0.1.15 or newer: NtagReader asks for 132 pages, a factory Elegoo tag
has 44, and before 0.1.15's ChunkedType2PageReader the refused chunk past the end discarded the
whole read. The ready handler warns when that reader is missing.
"""
import logging

from . import filament_protocol
from .elegoo_fields import build_struct

_log = logging.getLogger("bespok3d.elegoo")


class ElegooParser:
    def to_filament_protocol(self, raw_bytes):
        if not raw_bytes:
            return filament_protocol.FILAMENT_PROTO_ERR, None
        info = build_struct(bytes(raw_bytes), dict(filament_protocol.FILAMENT_INFO_STRUCT))
        if info is None:
            _log.info("Elegoo: no EEEEEEEE signature in %d bytes, declining", len(raw_bytes))
            return filament_protocol.FILAMENT_PROTO_ERR, None
        _log.info(
            "Elegoo: uid=%s type=%s color=%06X nozzle=%s-%s diameter=%s weight=%s",
            _uid_as_hex(info.get("CARD_UID")), info.get("MAIN_TYPE"), info.get("RGB_1", 0),
            info.get("HOTEND_MIN_TEMP"), info.get("HOTEND_MAX_TEMP"),
            info.get("DIAMETER"), info.get("WEIGHT"),
        )
        return filament_protocol.FILAMENT_PROTO_OK, info


class RfidTagElegoo:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:ready", self._handle_ready)

    def _handle_ready(self):
        hub = self.printer.lookup_object("bespok3d_rfid", None)
        if hub is None:
            _log.warning("bespok3d_rfid missing: Elegoo support inactive")
            return
        _warn_if_page_reader_too_old()
        hub.register_payload_parser(ElegooParser())
        _log.info("ready: Elegoo payload parser registered")


def _uid_as_hex(card_uid):
    """Colon-separated hex, as phone tag readers print a UID, so the two compare at a glance."""
    return ":".join(format(uid_byte, "02X") for uid_byte in card_uid or [])


def _warn_if_page_reader_too_old():
    try:
        from . import ntag_reader
    except ImportError:
        _log.warning("elegoo: ntag_reader not found, so no Elegoo tag can be read")
        return
    if not hasattr(ntag_reader, "ChunkedType2PageReader"):
        _log.warning("elegoo: rfid-ntag is older than 0.1.15, so Elegoo tags will fail to read")


def load_config(config):
    return RfidTagElegoo(config)
