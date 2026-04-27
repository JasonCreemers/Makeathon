"""
Makeathon Rover — entry point.

    cd /home/makeathon/Makethon && source venv/bin/activate && python3 main.py

Make sure the Arduino is connected and SERIAL_PORT in config.py
points to the correct device (e.g. /dev/ttyACM0 or COMx).
"""

import sys

from rover.arduino import Arduino, ArduinoError
from rover.camera import Camera, CameraError
from rover import cli


def main() -> None:
    arduino = Arduino()
    camera = Camera()

    try:
        arduino.connect()
    except ArduinoError as exc:
        print(f"Fatal: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        camera.open()
    except CameraError as exc:
        print(f"Warning: camera unavailable — {exc}")
        print("CAMERA and START will not work this session.\n")

    try:
        cli.run(arduino, camera)
    finally:
        camera.close()
        try:
            arduino.send("STOP")
        except ArduinoError:
            pass
        arduino.close()


if __name__ == "__main__":
    main()
