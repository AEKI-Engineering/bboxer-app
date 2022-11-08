from typing import Dict, List, Tuple


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
        int(min([v["x"] for v in xy]) * shape[0]),
        int(min([v["y"] for v in xy]) * shape[0]),
        int(max([v["x"] for v in xy]) * shape[0]),
        int(max([v["y"] for v in xy]) * shape[0]),
    ]
