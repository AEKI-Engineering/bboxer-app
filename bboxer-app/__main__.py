import argparse
import atexit
import json
from pathlib import Path
import sys
import time
from typing import Optional

from PIL import Image
from .utils import convert_normalized_xy, draw_bbox
import numpy as np
from .schemas import ImageModel
import msal

import requests

from .config import settings


def main(args: argparse.Namespace) -> Optional[int]:
    print(":: bboxer-app ::")

    start = time.perf_counter()

    # Define headers
    headers = {"Content-Type": "application/json"}

    # Authenticate only for default URL
    if args.url == settings.API_DEFAULT_URL:
        print(f"Using default endpoint: {settings.API_DEFAULT_URL}")
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
            print("Prompting browser to authenticate...")
            token = app.acquire_token_interactive(settings.AZURE_TOKEN_SCOPES)

        # Safe get access token
        try:
            headers["Authorization"] = "Bearer " + token["access_token"]
            print("Authentication successful.")
        except KeyError:
            print("Failed to authenticate: no access token returned.")
            return 1
    else:
        # Don't use token for overwritten URL
        print(f"Using local endpoint: {args.url}")
        token = None

    if len(args.images) == 1:
        print("Running detection...")
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

            print(
                f"1/1 :: {img.shape[0]}x{img.shape[1]} px, {data['time']} s, {len(data['detections'])} detected objects."
            )

            for detection in data["detections"]:
                bbox = convert_normalized_xy(detection["boundingBox"], img.shape)
                img = draw_bbox(img, bbox, detection["name"], score=detection["score"])

            if not args.no_save:
                i = 1
                while Path(f"{i}.png").exists():
                    i += 1
                print(f"Saving image to '{i}.png'")
                Image.fromarray(img).save(f"{i}.png")
            else:
                # Print response JSON instead
                print("1/1 :: response:")
                print(json.dumps(data, indent=4))

        else:
            print(f"Failed to execute API request, status code: {response.status_code}")
            try:
                print(json.dumps(response.json(), indent=2))
            except Exception:
                # Silently pass since the next instruction is nonzero return
                pass
            return 1

    else:
        # Run batch prediction
        ims = [ImageModel(__root__=image) for image in args.images]

        response = requests.post(
            f"{args.url}{settings.API_ROUTE}{settings.PREDICT_BATCH_ENDPOINT}",
            headers=headers,
            json={"images": [im() for im in ims]},
        )

        if response.status_code == 200:
            data = response.json()

            for result, i in zip(
                data["batchResults"], range(len(data["batchResults"]))
            ):

                img = np.array(ims[i].__root__.to_pil_image())

                print(
                    f"{i + 1}/{len(data['batchResults'])} :: {img.shape[0]}x{img.shape[1]} px, {len(result['detections'])} detected objects."
                )

                for detection in result["detections"]:
                    bbox = convert_normalized_xy(detection["boundingBox"], img.shape)
                    img = draw_bbox(
                        img, bbox, detection["name"], score=detection["score"]
                    )

                if not args.no_save:
                    while Path(f"{i}.png").exists():
                        i += 1
                    print(f"Saving image to '{i}.png'")
                    Image.fromarray(img).save(f"{i}.png")
                else:
                    # Print the corresponding JSON response instead
                    print(f"{i + 1}/{len(data['batchResults'])} :: response:")
                    print(json.dumps(result, indent=4))

            # print(json.dumps(data, indent=2))
        else:
            print(f"Failed to execute API request, status code: {response.status_code}")
            try:
                print(json.dumps(response.json(), indent=2))
            except Exception:
                # Silently pass since the next instruction is nonzero return
                pass
            return 1

    end = time.perf_counter()

    print(f"Done! Finished in {round(end - start, 3)} seconds.")


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
    parser.add_argument(
        "--no-save", action="store_true", help="Do not save resulting images."
    )

    args = parser.parse_args()

    sys.exit(main(args))
