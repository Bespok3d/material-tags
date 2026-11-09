"""Loads the Creality decoder modules as package 'creality', the way Klipper loads them.

tests_support/decoder_package.py explains the package setup. The two runtime-only siblings that
rfid-ntag places at install time are stubbed with the values the reader shell relies on.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tests_support"))

# The shared helper lives outside this decoder's dir, so it imports only after the path insert.
from decoder_package import register_decoder_package, stub_runtime_sibling  # noqa: E402

CREALITY_DIR = (
    REPO_ROOT / "rfid-creality" / "files" / "klipper" / "klippy" / "extras" / "rfid-tags"
    / "creality"
)

stub_runtime_sibling("creality", "filament_protocol", {
    "FILAMENT_PROTO_OK": 0,
    "FILAMENT_PROTO_ERR": -1,
    "FILAMENT_INFO_STRUCT": {
        "VENDOR": "NONE", "MANUFACTURER": "NONE", "MAIN_TYPE": "NONE", "SUB_TYPE": "NONE",
        "WEIGHT": 0, "SKU": 0, "RGB_1": 0, "COLOR_NUMS": 0, "ALPHA": 0, "ARGB_COLOR": 0,
        "DIAMETER": 0, "HOTEND_MIN_TEMP": 0, "HOTEND_MAX_TEMP": 0,
        "CARD_UID": [], "OFFICIAL": False, "MF_DATE": "",
    },
})
stub_runtime_sibling("creality", "fm175xx_reader", {
    "FM175XX_OK": 0,
    "FM175XX_CARD_READ_ERR": -29,
    "FM175XX_M1_CARD_AUTH_MODE_B": 1,
})
register_decoder_package(
    "creality", CREALITY_DIR, ("aes_min", "creality_keys", "creality_types", "creality_fields"),
)
