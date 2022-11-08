import argparse
import atexit
import json
from pathlib import Path
import sys
from typing import Optional

from PIL import Image
import bbox_visualizer as bbv
from .utils import convert_normalized_xy
import cv2
import numpy as np
from .schemas import ImageModel
import msal

import requests

from .config import settings


def main(args: argparse.Namespace) -> Optional[int]:
    headers = {"Content-Type": "application/json"}

    # Authenticate only for default URL
    if args.url == settings.API_DEFAULT_URL:
        # Register persistent token cache
        # Note: Seems like MSAL is not capable of managing token cache for
        # short-lived applications. To investigate further
        token_cache = msal.SerializableTokenCache()
        if Path(".token.cache").exists():
            token_cache.deserialize(open(".token.cache", "r").read())

        # Update token cache
        atexit.register(
            lambda: open(".token.cache", "w").write(token_cache.serialize())
            if token_cache.has_state_changed
            else None
        )

        app = msal.PublicClientApplication(
            settings.AZURE_APP_CLIENT_ID,
            authority=settings.AZURE_AAD_AUTHORITY,
            token_cache=token_cache,
        )

        # Try to get token from cache
        token = app.acquire_token_silent(settings.AZURE_TOKEN_SCOPES, account=None)

        if not token:
            # If no token in cache found, authenticate user with browser
            print("Prompting browser")
            token = app.acquire_token_interactive(settings.AZURE_TOKEN_SCOPES)

        # Safe get access token
        try:
            headers["Authorization"] = "Bearer " + token["access_token"]
        except KeyError:
            print("Failed to authenticate: no access token returned")
            return 1
    else:
        # Don't use token for overwritten URL
        token = None

    if len(args.images) == 1:
        # Run single image prediction
        im = ImageModel(__root__=args.images[0])

        response = requests.post(
            f"{args.url}{settings.API_ROUTE}{settings.PREDICT_ONE_ENDPOINT}",
            headers=headers,
            json={"image": im()},
        )

        if response.status_code == 200:
            data = response.json()

            img = np.array(im.__root__.to_pil_image())

            for detection in data["detections"]:
                bbox = convert_normalized_xy(detection["boundingBox"], img.shape)

                img = bbv.bbox_visualizer.draw_rectangle(img, bbox=bbox)
                img = bbv.add_label(
                    img, label=f"{detection['name']} {detection['score']}", bbox=bbox
                )

            Image.fromarray(img).save("1.png")

    else:
        # Run batch prediction
        ims = [ImageModel(__root__=image)() for image in args.images]

        response = requests.post(
            f"{args.url}{settings.API_ROUTE}{settings.PREDICT_BATCH_ENDPOINT}",
            headers=headers,
            json={"images": ims},
        )

    if response.status_code == 200:
        data = response.json()

        # print(json.dumps(data, indent=2))
    else:
        print("Failed api call")
        print(json.dumps(response.json(), indent=2))
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Detect objects from images.", prog="bboxer-app"
    )

    parser.add_argument("images", nargs="+", help="HTTP/HTTPS URLs or paths to images.")
    parser.add_argument(
        "--url",
        "-u",
        default=settings.API_DEFAULT_URL,
        help="Base URL (with port, if applies) to overwrite.",
    )
    parser.add_argument("--no-save", help="Do not save resulting images.")

    args = parser.parse_args()

    sys.exit(main(args))
