"""
Interactive command-line interface for the rover.

Commands typed here are either passed directly to the Arduino or
handled locally on the Pi (CAMERA, START).
"""

from rover.arduino import Arduino, ArduinoError
from rover.camera import Camera
from rover import auto

# Commands that go straight to the Arduino
_ARDUINO_PREFIXES = ("SERVO:", "MOVE:", "PUMP:")

_HELP = """
Commands:
  SERVO:XXX                 Move servo to position 0–100
  MOVE:FORWARD:XXXX         Move forward XXXX steps
  MOVE:BACKWARD:XXXX        Move backward XXXX steps
  PUMP:FORWARD:XX           Pump forward XX seconds
  PUMP:BACKWARD:XX          Pump backward XX seconds
  STOP                      Emergency stop
  CAMERA                    Open live camera feed (press q to close)
  START                     Start autonomous mode (Ctrl-C to stop)
  help                      Show this message
  exit / quit               Leave the CLI
""".strip()


def run(arduino: Arduino, camera: Camera) -> None:
    """Start the interactive REPL. Exits on 'exit', 'quit', or Ctrl-C."""
    print("Rover ready. Type 'help' for commands.\n")

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not raw:
            continue

        cmd = raw.upper()

        if cmd in ("EXIT", "QUIT"):
            print("Exiting.")
            break

        if cmd == "HELP":
            print(_HELP)
            continue

        if cmd == "CAMERA":
            camera.live_feed()
            continue

        if cmd == "START":
            try:
                auto.run(arduino, camera)
            except KeyboardInterrupt:
                print("\nAutonomous mode stopped.")
                try:
                    arduino.send("STOP")
                except ArduinoError:
                    pass
            continue

        if cmd == "STOP" or any(cmd.startswith(p) for p in _ARDUINO_PREFIXES):
            try:
                responses = arduino.send(cmd)
                for line in responses:
                    print(line)
            except ArduinoError as exc:
                print(f"Error: {exc}")
            continue

        print(f"Unknown command: '{raw}'. Type 'help' for available commands.")
