from pathlib import Path
import os

# Data folders: defaults match the extracted archives in ~/Downloads.
# Override with environment variables REFIT_RAW_DIR / REFIT_CLEAN_DIR if needed.
RAW_DIR = Path(os.environ.get("REFIT_RAW_DIR", Path.home() / "Downloads" / "REFIT_RAW_081116"))
CLEAN_DIR = Path(os.environ.get("REFIT_CLEAN_DIR", Path.home() / "Downloads" / "CLEAN_REFIT_081116"))

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "figures"
OUT_DIR = ROOT / "outputs"
FIG_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

# REFIT logger timestamps are UK wall-clock time (see DATA.md)
LOCAL_TZ = "Europe/London"

# House 1 appliance channels, from the REFIT readme
HOUSE1_APPLIANCES = {
    "Appliance1": "Fridge",
    "Appliance2": "Chest Freezer",
    "Appliance3": "Upright Freezer",
    "Appliance4": "Tumble Dryer",
    "Appliance5": "Washing Machine",
    "Appliance6": "Dishwasher",
    "Appliance7": "Computer Site",
    "Appliance8": "Television Site",
    "Appliance9": "Electric Heater",
}

# Plot colours (colourblind-checked categorical palette)
C_RAW = "#9b9a95"      # raw / before
C_CLEAN = "#2a78d6"    # cleaned / after
C_FLAG = "#eb6834"     # flagged / removed
C_ALT = "#1baf7a"
