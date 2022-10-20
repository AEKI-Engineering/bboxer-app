import argparse
import atexit
from functools import cache
import json
from pathlib import Path
import sys
from typing import Optional
import msal

import requests

from .config import settings


def main(args: argparse.Namespace) -> Optional[int]:
    headers = {"Content-Type": "application/json"}

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

    # Authenticate only for default URL
    if args.url == settings.API_DEFAULT_URL:
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
        response = requests.post(
            f"{args.url}{settings.API_ROUTE}{settings.PREDICT_ONE_ENDPOINT}",
            headers=headers,
            json={"image": args.images[0]},
        )
    else:
        # Run batch prediction
        response = requests.post(
            f"{args.url}{settings.API_ROUTE}{settings.PREDICT_BATCH_ENDPOINT}",
            headers=headers,
            json={"images": args.images},
        )

    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print("Failed api call")
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

    args = parser.parse_args()

    sys.exit(main(args))
