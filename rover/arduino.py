"""
Blocking serial interface to the Arduino Mega rover firmware.

Opens the serial port, waits for ROVER:READY, then exposes a send()
method that transmits a command and blocks until the Arduino replies
with a terminal response (ACK:...:FINISH, ACK:STOP, or ERR:...).
"""

import time

import serial

import config


class ArduinoError(Exception):
    """Connection failures, timeouts, or serial I/O errors."""


class Arduino:
    def __init__(self):
        self._ser: serial.Serial | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Open the serial port and block until ROVER:READY."""
        port = config.SERIAL_PORT
        print(f"Connecting to Arduino on {port} ...")
        try:
            self._ser = serial.Serial(port, config.SERIAL_BAUD, timeout=1.0)
        except serial.SerialException as exc:
            raise ArduinoError(f"Could not open {port}: {exc}") from exc

        deadline = time.monotonic() + config.SERIAL_CONNECT_TIMEOUT
        while time.monotonic() < deadline:
            line = self._readline()
            if line == "ROVER:READY":
                print("Arduino connected.")
                return

        raise ArduinoError(
            f"Timed out waiting for ROVER:READY after {config.SERIAL_CONNECT_TIMEOUT}s. "
            "Check the port and baud rate in config.py."
        )

    def close(self) -> None:
        """Close the serial port if open."""
        if self._ser and self._ser.is_open:
            self._ser.close()

    # ── Command interface ─────────────────────────────────────────────────────

    def send(self, command: str) -> list[str]:
        """
        Send a command and collect all response lines until a terminal
        response is received.

        Returns the list of response lines.
        Raises ArduinoError on timeout or serial failure.
        """
        if not self._ser or not self._ser.is_open:
            raise ArduinoError("Not connected.")

        self._ser.write((command + "\n").encode("ascii"))
        self._ser.flush()

        responses: list[str] = []
        deadline = time.monotonic() + config.SERIAL_COMMAND_TIMEOUT

        while time.monotonic() < deadline:
            line = self._readline()
            if not line:
                continue
            responses.append(line)
            if self._is_terminal(line):
                return responses

        raise ArduinoError(
            f"Timed out after {config.SERIAL_COMMAND_TIMEOUT}s "
            f"waiting for response to '{command}'."
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _readline(self) -> str:
        """Read one line. Returns '' on timeout."""
        if not self._ser:
            return ""
        try:
            raw = self._ser.readline()
            return raw.decode("ascii", errors="ignore").strip()
        except serial.SerialException as exc:
            raise ArduinoError(f"Serial read error: {exc}") from exc

    @staticmethod
    def _is_terminal(line: str) -> bool:
        """True if the line marks the end of a command cycle."""
        return (
            line.endswith(":FINISH")
            or line == "ACK:STOP"
            or line.startswith("ERR:")
        )
