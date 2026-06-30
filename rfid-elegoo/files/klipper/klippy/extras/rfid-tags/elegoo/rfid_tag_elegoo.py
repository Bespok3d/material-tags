"""Registers the Elegoo reader + decoder with the RFID hub - PLUGIN-ONLY, no rfid-ntag change.

On ready it looks up the hub (`bespok3d_rfid`) and the reader (`fm175xx_reader`), then uses
the reader's EXISTING `register_card_type_handler` delegate to claim the SAKs a Feiju Elegoo
chip can present, and `read_nfc_type2_pages` to read it (via `ElegooReader`). Bytes flow to
the hub's payload parsers (card_type 0x00, the NTAG path), where `ElegooParser` decodes them.
"""
import logging

from . import filament_protocol
from .elegoo_fields import build_struct
from .elegoo_reader import CANDIDATE_SAKS, ElegooReader

_log = logging.getLogger("bespok3d.elegoo")


class ElegooParser:
    def to_filament_protocol(self, raw_bytes):
        if not raw_bytes:
            return filament_protocol.FILAMENT_PROTO_ERR, None
        info = build_struct(bytes(raw_bytes), dict(filament_protocol.FILAMENT_INFO_STRUCT))
        if info is None:
            return filament_protocol.FILAMENT_PROTO_ERR, None
        _log.info("Elegoo: type=%s color=%06X", info.get("MAIN_TYPE"), info.get("RGB_1", 0))
        return filament_protocol.FILAMENT_PROTO_OK, info


class RfidTagElegoo:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:ready", self._handle_ready)

    def _handle_ready(self):
        hub = self.printer.lookup_object("bespok3d_rfid", None)
        fm_reader = self.printer.lookup_object("fm175xx_reader", None)
        if hub is None or fm_reader is None:
            _log.warning("bespok3d_rfid or fm175xx_reader missing: Elegoo support inactive")
            return
        reader = ElegooReader()
        for sak in CANDIDATE_SAKS:
            fm_reader.register_card_type_handler(sak, reader.read_hw_tag)
        hub.register_payload_parser(ElegooParser())
        _log.info("ready: Elegoo reader+parser registered for SAKs %s",
                  [hex(sak) for sak in CANDIDATE_SAKS])


def load_config(config):
    return RfidTagElegoo(config)
