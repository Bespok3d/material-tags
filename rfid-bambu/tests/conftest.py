"""Loads the Bambu decoder modules as package 'bambu', the way Klipper loads them.

tests_support/decoder_package.py explains the package setup. The two runtime-only siblings that
rfid-ntag places at install time are stubbed with the values the reader shell relies on.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tests_support"))

# The shared helper lives outside this decoder's dir, so it imports only after the path insert.
from decoder_package import register_decoder_package, stub_runtime_sibling  # noqa: E402

BAMBU_DIR = (
    REPO_ROOT / "rfid-bambu" / "files" / "klipper" / "klippy" / "extras" / "rfid-tags" / "bambu"
)

stub_runtime_sibling("bambu", "filament_protocol", {
    "FILAMENT_PROTO_OK": 0,
    "FILAMENT_PROTO_ERR": -1,
    "FILAMENT_INFO_STRUCT": {
        "VENDOR": "NONE", "MANUFACTURER": "NONE", "MAIN_TYPE": "NONE", "SUB_TYPE": "NONE",
        "CARD_UID": [], "OFFICIAL": False,
    },
})
stub_runtime_sibling("bambu", "fm175xx_reader", {
    "FM175XX_OK": 0,
    "FM175XX_CARD_AUTH_ERR": -28,
    "FM175XX_CARD_READ_ERR": -29,
    "FM175XX_M1_CARD_AUTH_MODE_A": 0,
})
register_decoder_package("bambu", BAMBU_DIR, ("bambu_keys", "bambu_fields"))
