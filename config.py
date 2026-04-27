"""
Makeathon Rover — all tunable constants in one place.

Adjust these values during hardware bring-up and trial-and-error.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Serial ────────────────────────────────────────────────────────────────────

SERIAL_PORT = os.environ.get("SERIAL_PORT", "/dev/ttyACM0")
SERIAL_BAUD = 115200
SERIAL_CONNECT_TIMEOUT = 10   # seconds to wait for ROVER:READY
SERIAL_COMMAND_TIMEOUT = 30   # seconds to wait for a command to finish

# ── Servo positions (0–100, adjust through trial and error) ───────────────────

SERVO_LEFT = 0       # nozzle toward camera side (scanning position)
SERVO_CENTER = 50    # nozzle aligned with stem (dispensing position)
SERVO_MAX = 75       # max servo position (capped)

# ── Motor ─────────────────────────────────────────────────────────────────────

SEARCH_STEPS = 100   # steps forward between search frames

# ── Centering ─────────────────────────────────────────────────────────────────

CENTER_START_STEPS = 200   # initial nudge size
CENTER_MIN_STEPS = 25      # smallest nudge before we call it good enough
CENTER_TOLERANCE = 0.15    # 15% of image width

# ── Pump ──────────────────────────────────────────────────────────────────────

PUMP_FORWARD_SEC = 10
PUMP_BACKWARD_SEC = 10

# ── Camera ────────────────────────────────────────────────────────────────────

CAMERA_VFLIP = True

# ── Roboflow ──────────────────────────────────────────────────────────────────

ROBOFLOW_API_KEY = os.environ.get("ROBOFLOW_API_KEY", "")
ROBOFLOW_MODEL_ID = "stem_detection-qeoi4/1"
ROBOFLOW_CONFIDENCE = 40   # integer 0–100
ROBOFLOW_URL = "https://serverless.roboflow.com"

# ── Data ──────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
