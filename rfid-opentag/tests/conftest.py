import sys
from pathlib import Path

EXTRAS = (
    Path(__file__).resolve().parent.parent
    / "files" / "klipper" / "klippy" / "extras" / "rfid-tags" / "opentag"
)
sys.path.insert(0, str(EXTRAS))
