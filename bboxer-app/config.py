from typing import List
from pydantic import BaseSettings


class Settings(BaseSettings):
    # API
    API_DEFAULT_URL: str = "https://aeki-api-service.azurewebsites.net"
    API_ROUTE: str = "/api/latest"
    PREDICT_ONE_ENDPOINT: str = "/object-detection/predict"
    PREDICT_BATCH_ENDPOINT: str = "/object-detection/predict/batch"

    # Azure project
    AZURE_APP_CLIENT_ID: str = "84daa76c-57d6-4a7b-863e-6a906211a3ac"
    AZURE_AAD_AUTHORITY: str = (
        "https://login.microsoftonline.com/6784bddd-735e-476f-b767-f2ddcaa828f7"
    )
    AZURE_TOKEN_SCOPES: List[str] = [
        "84daa76c-57d6-4a7b-863e-6a906211a3ac/user_impersonation"
    ]


settings = Settings()
