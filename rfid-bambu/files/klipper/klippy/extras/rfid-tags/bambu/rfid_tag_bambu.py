"""Registers the Bambu Mifare-Classic decoder with the RFID hub.

Klipper loads this module for the ``[rfid_tag_bambu]`` config section. Bambu spools are
Mifare-Classic cards that share Snapmaker's M1 SAK (0x08), so the rfid-ntag reader routes a
0x08 card the Snapmaker key could not open to *claim handlers* like this one. This shell
claims such a card, derives the 16 sector keys from the tag UID + the user-supplied master
key (``bambu_keys``), re-selects the card (the stock read consumed its crypto session),
reads the data blocks via the reader's ``read_mifare_classic`` primitive, and decodes them
(``bambu_fields``). With no/invalid key it does not claim, so the reader's UID-only fallback
carries (the spool stays trackable by UID).

Thin relative-import shell: the key derivation and decode live in the pure, unit-tested
``bambu_keys`` / ``bambu_fields`` siblings. ``filament_protocol`` and ``fm175xx_reader``
resolve as flat ``klippy.extras`` siblings at runtime (placed by rfid-ntag).
"""
import logging

from . import bambu_fields, bambu_keys, filament_protocol
from . import fm175xx_reader as fm_mod

_log = logging.getLogger("bespok3d.bambu")

M1_SAK = 0x08
BAMBU_CARD_TYPE = 0xBA  # distinct card type so the dedicated Bambu parser owns its data
BAMBU_SECTORS = (0, 1)  # blocks 0-2 (uid/variant/type) + 4-6 (detail/color/temps)
BLOCKS_PER_SECTOR = 4
DATA_BLOCKS_PER_SECTOR = 3
BLOCK_BYTES = 16


class BambuReader:
    sak = M1_SAK
    card_type = BAMBU_CARD_TYPE

    def __init__(self, master_key):
        self._master_key = master_key

    @property
    def has_master_key(self):
        return self._master_key is not None

    def claims(self, reader):
        return self.has_master_key and reader.selected_card_sak() == M1_SAK

    def read_hw_tag(self, reader):
        uid = list(reader.selected_card_uid()[0:4])
        keys = bambu_keys.derive_sector_keys(bytes(uid), self._master_key)
        _log.info("Spool UID: %s",uid)
        if reader.reactivate_card() != fm_mod.FM175XX_OK:
            _log.error("Bambu: could not re-select card after stock read")
            return BAMBU_CARD_TYPE, None, fm_mod.FM175XX_CARD_READ_ERR
        buffer = [0] * (len(BAMBU_SECTORS) * BLOCKS_PER_SECTOR * BLOCK_BYTES)
        for sector in BAMBU_SECTORS:
            err = self._read_sector(reader, sector, keys[sector], uid, buffer)
            if err != fm_mod.FM175XX_OK:
                _log.warning("Err: %s", err)
                return BAMBU_CARD_TYPE, None, err
        return BAMBU_CARD_TYPE, buffer, fm_mod.FM175XX_OK

    def _read_sector(self, reader, sector, key, uid, buffer):
        blocks = [sector * BLOCKS_PER_SECTOR + n for n in range(DATA_BLOCKS_PER_SECTOR)]
        err, data = \
            reader.read_mifare_classic(fm_mod.FM175XX_M1_CARD_AUTH_MODE_A, sector, key, uid, blocks)
        if err != fm_mod.FM175XX_OK:
            _log.warning("Bambu: sector %d auth/read failed (err=%d)", sector, err)
            return err
        for index, block in enumerate(blocks):
            start = block * BLOCK_BYTES
            buffer[start:start + BLOCK_BYTES] = data[index * BLOCK_BYTES:(index + 1) * BLOCK_BYTES]
        return fm_mod.FM175XX_OK

    def parse(self, card_data):
        info = bambu_fields.decode(card_data, dict(filament_protocol.FILAMENT_INFO_STRUCT))
        if info is None:
            return filament_protocol.FILAMENT_PROTO_ERR, None
        _log.info("Bambu: vendor=%s type=%s sub=%s", info.get("VENDOR"),
                  info.get("MAIN_TYPE"), info.get("SUB_TYPE"))
        return filament_protocol.FILAMENT_PROTO_OK, info


class RfidTagBambu:
    def __init__(self, config):
        self.printer = config.get_printer()
        master_key = bambu_keys.parse_master_key(config.get("key", ""))
        if master_key is not None and not bambu_keys.master_key_is_valid(master_key):
            _log.warning("Bambu: configured key is not the expected master key; UID-only mode")
            master_key = None
        self._reader = BambuReader(master_key)
        self.printer.register_event_handler("klippy:ready", self._handle_ready)

    def _handle_ready(self):
        hub = self.printer.lookup_object("bespok3d_rfid", None)
        if hub is None:
            _log.warning("bespok3d_rfid not loaded: Bambu support inactive")
            return
        hub.register_hw_reader(self._reader)
        _log.info("ready: Bambu reader registered (master key configured: %s)",
                  self._reader.has_master_key)


def load_config(config):
    return RfidTagBambu(config)
