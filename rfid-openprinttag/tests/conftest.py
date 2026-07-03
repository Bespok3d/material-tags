import sys
from pathlib import Path

RFID_TAGS = (
    Path(__file__).resolve().parent.parent
    / "files" / "klipper" / "klippy" / "extras" / "rfid-tags"
)
sys.path.insert(0, str(RFID_TAGS))
