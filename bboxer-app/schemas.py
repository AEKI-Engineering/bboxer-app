import base64
from io import BytesIO
from pathlib import Path
from typing import Any, Union
from pydantic import BaseModel, constr
from PIL import Image
import requests

UrlType = constr(regex="(https|http)?:\/\/.+")


class ImageURL(BaseModel):
    __root__: UrlType

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.__root__

    def to_pil_image(self) -> Image:
        return Image.open(BytesIO(requests.get(self.__root__).content))


class ImagePath(BaseModel):
    __root__: Path

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        with open(self.__root__, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def to_pil_image(self) -> Image:
        return Image.open(self.__root__)


class ImageModel(BaseModel):
    __root__: Union[ImageURL, ImagePath]

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.__root__()
