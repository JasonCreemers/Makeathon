"""
Roboflow stem detection via the serverless hosted API.

Sends a base64-encoded image and returns instance segmentation results
with polygon points for each detected stem.
"""

import base64
from pathlib import Path

import requests

import config


class DetectionError(Exception):
    """Raised when the API call fails."""


def detect_stems(image_path: str | Path) -> tuple[list[dict], int, int]:
    """
    Run stem instance segmentation on an image.

    Returns:
        (detections, image_width, image_height)

        Each detection dict has:
            x, y          — bounding box centre
            width, height — bounding box size
            confidence    — float 0–1
            points        — list of {"x": float, "y": float} polygon vertices

        Sorted by confidence descending.
        Returns ([], 0, 0) on any error.
    """
    if not config.ROBOFLOW_API_KEY:
        print("Warning: ROBOFLOW_API_KEY not set.")
        return [], 0, 0

    try:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        url = f"{config.ROBOFLOW_URL}/{config.ROBOFLOW_MODEL_ID}"

        resp = requests.post(
            url,
            params={
                "api_key": config.ROBOFLOW_API_KEY,
                "confidence": config.ROBOFLOW_CONFIDENCE,
                "response_mask_format": "polygon",
            },
            data=img_b64,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        resp.raise_for_status()
        result = resp.json()

        image_info = result.get("image", {})
        img_w = image_info.get("width", 0)
        img_h = image_info.get("height", 0)

        detections = []
        for pred in result.get("predictions", []):
            detections.append({
                "x": pred.get("x", 0),
                "y": pred.get("y", 0),
                "width": pred.get("width", 0),
                "height": pred.get("height", 0),
                "confidence": pred.get("confidence", 0),
                "points": pred.get("points", []),
            })

        detections.sort(key=lambda d: d["confidence"], reverse=True)
        return detections, img_w, img_h

    except Exception as exc:
        print(f"Detection error: {exc}")
        return [], 0, 0
