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

# House 1 appliance channels, from docs/CLEAN_READ_ME_081116.txt
HOUSE1_APPLIANCES = {
    "Appliance1": "Fridge",
    "Appliance2": "Freezer (1)",
    "Appliance3": "Freezer (2)",
    "Appliance4": "Washer Dryer",
    "Appliance5": "Washing Machine",
    "Appliance6": "Dishwasher",
    "Appliance7": "Computer",
    "Appliance8": "Television Site",
    "Appliance9": "Electric Heater",
}

# Washing-machine channel per house in the CLEAN data (readme appliance list).
# Six houses with one washing machine and no appliance swap noted in the readme.
# Not used: 4 (two washing machines), 13 (machine changed Mar 2015), 1 (used for
# the raw-data section). House 9 has a separate washer-dryer, which stays part
# of the aggregate and is a realistic source of confusion for the model.
WM_CHANNELS = {
    2: "Appliance2",
    5: "Appliance3",
    7: "Appliance5",
    9: "Appliance3",
    15: "Appliance3",
    17: "Appliance4",
}

# Plot colours (colourblind-checked categorical palette)
C_RAW = "#9b9a95"      # raw / before
C_CLEAN = "#2a78d6"    # cleaned / after
C_FLAG = "#eb6834"     # flagged / removed
C_ALT = "#1baf7a"
# fixed categorical order for per-house series
HOUSE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
