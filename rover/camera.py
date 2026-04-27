"""
Raspberry Pi camera interface (IMX708 via picamera2).

Provides still capture and a live OpenCV preview window.
The camera is mounted upside-down, so vflip is applied.
"""

import time
from datetime import datetime
from pathlib import Path

import config


class CameraError(Exception):
    """Camera open/capture failures."""


class Camera:
    def __init__(self):
        self._cam = None

    def open(self) -> None:
        """Initialise and start the camera."""
        try:
            from picamera2 import Picamera2
            from libcamera import Transform

            self._cam = Picamera2()
            transform = Transform(vflip=True) if config.CAMERA_VFLIP else Transform()
            cfg = self._cam.create_still_configuration(transform=transform)
            self._cam.configure(cfg)
            self._cam.start()
            time.sleep(1)  # let auto-exposure settle
            print("Camera ready.")
        except Exception as exc:
            raise CameraError(f"Could not open camera: {exc}") from exc

    def close(self) -> None:
        """Stop and release the camera."""
        if self._cam:
            try:
                self._cam.stop()
                self._cam.close()
            except Exception:
                pass
        self._cam = None

    def capture(self) -> Path:
        """
        Capture a still image, save to data/, return the path.

        Raises CameraError if the camera isn't open or capture fails.
        """
        if not self._cam:
            raise CameraError("Camera is not open.")

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = config.DATA_DIR / f"{timestamp}.jpg"

        try:
            self._cam.capture_file(str(path))
        except Exception as exc:
            raise CameraError(f"Capture failed: {exc}") from exc

        return path

    def live_feed(self) -> None:
        """
        Show a live camera preview in an OpenCV window.
        Press 'q' or ESC to close.
        """
        if not self._cam:
            print("Camera is not open.")
            return

        import cv2

        print("Live feed — press 'q' or ESC to close.")

        try:
            while True:
                frame = self._cam.capture_array()
                cv2.imshow("Rover Camera", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q") or key == 27:  # q or ESC
                    break
        finally:
            cv2.destroyAllWindows()
