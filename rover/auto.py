"""
Autonomous fertilization loop.

Camera is mounted on the LEFT side of the rover, facing LEFT.
As the rover moves FORWARD, the scene shifts right-to-left in the image.

Cycle:
  1. Servo to scanning position (left).
  2. Search forward in small steps until a stem is detected.
  3. Centre the stem on the image X-axis using decreasing nudge sizes.
  4. Deploy nozzle (servo centre), pump forward, pump backward, stow.
  5. Repeat for the next plant.
"""

from rover.arduino import Arduino, ArduinoError
from rover.camera import Camera, CameraError
from rover.detection import detect_stems
import config


def _send(arduino: Arduino, cmd: str) -> list[str]:
    """Send a command and print each response line."""
    responses = arduino.send(cmd)
    for line in responses:
        print(f"  {line}")
    return responses


def _stem_x_midpoint(detection: dict) -> float:
    """
    Compute the X-axis midpoint of a segmentation polygon.

    Projects all polygon points onto the X axis and returns
    the midpoint between the leftmost and rightmost vertices.
    """
    points = detection.get("points", [])
    if not points:
        # Fall back to bounding box centre
        return detection.get("x", 0)
    xs = [p["x"] for p in points]
    return (min(xs) + max(xs)) / 2.0


def _center_on_stem(arduino: Arduino, camera: Camera) -> bool:
    """
    Nudge the rover forward/backward with decreasing step sizes until
    the best-detected stem is within CENTER_TOLERANCE of the image centre.

    Returns True if centred successfully, False if the stem was lost.
    """
    step_size = config.CENTER_START_STEPS

    while True:
        # Capture and detect
        try:
            path = camera.capture()
            print(f"  Photo: {path.name}")
        except CameraError as exc:
            print(f"  Camera error: {exc}")
            return False

        detections, img_w, _ = detect_stems(str(path))

        if not detections:
            print("  Stem lost during centering.")
            return False

        best = detections[0]
        stem_x = _stem_x_midpoint(best)
        center_x = img_w / 2.0
        offset = (stem_x - center_x) / img_w

        print(
            f"  stem_x={stem_x:.0f}  center={center_x:.0f}  "
            f"offset={offset * 100:+.1f}%  step={step_size}"
        )

        if abs(offset) <= config.CENTER_TOLERANCE:
            print("  Stem centred.")
            return True

        # If we're at minimum step size and still not centred, close enough
        if step_size <= config.CENTER_MIN_STEPS:
            print("  Close enough at minimum step size.")
            return True

        # Direction: camera faces LEFT, scene shifts right-to-left as rover goes forward
        #   stem right of centre → rover hasn't reached it → FORWARD
        #   stem left of centre  → rover passed it         → BACKWARD
        direction = "FORWARD" if offset > 0 else "BACKWARD"
        print(f"  Nudging {direction} {step_size} steps...")

        try:
            _send(arduino, f"MOVE:{direction}:{step_size:04d}")
        except ArduinoError as exc:
            print(f"  Arduino error: {exc}")
            return False

        # Halve step size for next iteration
        step_size = max(step_size // 2, config.CENTER_MIN_STEPS)


def run(arduino: Arduino, camera: Camera) -> None:
    """
    Main autonomous loop. Runs until KeyboardInterrupt (Ctrl-C).

    Called by the CLI when the user types START.
    """
    print("Autonomous mode started. Press Ctrl-C to stop.\n")

    # Move servo to scanning position
    print("Servo → scanning position (left)...")
    _send(arduino, f"SERVO:{config.SERVO_LEFT:03d}")

    while True:
        # ── Search: capture and look for stems ────────────────────────────
        try:
            path = camera.capture()
            print(f"Photo: {path.name}")
        except CameraError as exc:
            print(f"Camera error: {exc}")
            return

        detections, _, _ = detect_stems(str(path))

        if not detections:
            print(f"No stems. Moving forward {config.SEARCH_STEPS} steps...")
            try:
                _send(arduino, f"MOVE:FORWARD:{config.SEARCH_STEPS:04d}")
            except ArduinoError as exc:
                print(f"Arduino error: {exc}")
                return
            continue

        print(f"Stem detected (confidence {detections[0]['confidence']:.0%}).")

        # ── Centre on the stem ────────────────────────────────────────────
        if not _center_on_stem(arduino, camera):
            print("Centering failed. Continuing search...\n")
            continue

        # ── Fertilize ─────────────────────────────────────────────────────
        print("Deploying nozzle (servo → centre)...")
        _send(arduino, f"SERVO:{config.SERVO_CENTER:03d}")

        print(f"Pump forward {config.PUMP_FORWARD_SEC}s...")
        _send(arduino, f"PUMP:FORWARD:{config.PUMP_FORWARD_SEC:02d}")

        print(f"Pump backward {config.PUMP_BACKWARD_SEC}s...")
        _send(arduino, f"PUMP:BACKWARD:{config.PUMP_BACKWARD_SEC:02d}")

        print("Stowing nozzle (servo → left)...")
        _send(arduino, f"SERVO:{config.SERVO_LEFT:03d}")

        print("Plant fertilized. Searching for next plant...\n")
