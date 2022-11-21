from typing import Dict, List, Tuple, Union
import cv2

import numpy as np


def convert_normalized_xy(
    xy: List[Dict[str, float]], shape: Tuple[int, int]
) -> List[int]:
    """Convert normalized xy coordinates

    Convert list of normalized xy bounding box points to list of x_min, y_min,
    x_max, y_max.

    Parameters
    ----------
    xy: List[Dict[str, float]]
        List of bounding box normalized coordinates, where each item is a
        dictionary with keys: "x", "y"
    shape: Tuple[int, int]
        Shape of the original image (x,y)

    Returns
    -------
    List[int]
        list of coordinates representing bounding box: x_min, y_min, x_max,
        y_max
    """
    return [
        int(min([v["x"] for v in xy]) * shape[1]),
        int(min([v["y"] for v in xy]) * shape[0]),
        int(max([v["x"] for v in xy]) * shape[1]),
        int(max([v["y"] for v in xy]) * shape[0]),
    ]


def draw_bbox(
    img: np.ndarray,
    bbox: List[Union[int, float]],
    label: str,
    score: Union[None, int],
    bbox_color: Tuple[int, int, int] = (255, 255, 255),
    bbox_thickness: int = 3,
    text_color: Tuple[int, int, int] = (0, 0, 0),
) -> np.ndarray:
    output = img.copy()

    # Draw rectangle
    cv2.rectangle(
        output, (bbox[0], bbox[1]), (bbox[2], bbox[3]), bbox_color, bbox_thickness
    )

    # Add label
    text = label if not score else f"{label} {score:.2f}"
    text_width = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0][0]

    label_bg = [bbox[0], bbox[1], bbox[0] + text_width, bbox[1] - 30]
    cv2.rectangle(
        output,
        (label_bg[0], label_bg[1]),
        (label_bg[2] + 5, label_bg[3]),
        bbox_color,
        -1,
    )
    cv2.putText(
        output,
        text,
        (bbox[0] + 5, bbox[1] - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        text_color,
        2,
        cv2.LINE_AA,
    )
    return output
