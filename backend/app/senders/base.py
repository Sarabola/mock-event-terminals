import logging
from pathlib import Path
from typing import Protocol

import requests


class ProgressCallback(Protocol):
    def __call__(self, image_name: str, status_code: int, progress: float, error: str | None = None) -> None:
        pass


class DeviceContext:
    def __init__(self, host: str, port: int, device_id: str, images_path: Path) -> None:
        self.host = host
        self.port = port
        self.device_id = device_id
        self.images_path = images_path

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/vl-access/webhook/device/{self.device_id}/event/handle_event/"


class DeviceSender:
    def __init__(self, context: DeviceContext) -> None:
        self.context = context
        self.logger = logging.getLogger(self.__class__.__name__)

    def _post_json(self, body: dict) -> int:
        response = requests.post(url=self.context.url, json=body, timeout=15)
        if response.status_code != 200:
            self.logger.warning("Bad status %s: %s", response.status_code, response.text)
        return response.status_code

    def _post_data(self, body: bytes | str) -> int:
        response = requests.post(url=self.context.url, data=body, timeout=15)
        if response.status_code != 200:
            self.logger.warning("Bad status %s: %s", response.status_code, response.text)
        return response.status_code
