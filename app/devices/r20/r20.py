import base64
import time
from datetime import datetime
from pathlib import Path

import requests
from pydantic import BaseModel, Extra
from app.devices.abc import DeviceSender
from app.devices.r20.data import R20FACE_JSON


class R20Event(BaseModel, extra="allow"):
    base64: str
    ip: str
    tempUnit: str = None
    temperature: str = None
    time: str


class R20Sender(DeviceSender):
    _DEVICE_NAME = "r20"
    _R20_BODY_TEMPLATE = R20FACE_JSON

    def make_selected_photos_request(self, faces: list[str], progress_callback=None) -> dict[str, int]:
        result = {}
        for i, face in enumerate(faces):
            face_path = self._IMAGES_PATH.joinpath(face)
            try:
                payload = self.get_json_body(face_path)
                status = self.make_request(payload.model_dump())
                result[face] = status

                if progress_callback:
                    progress = ((i + 1) / len(faces)) * 100
                    progress_callback(face, status, progress)

                time.sleep(4)

            except Exception as e:
                self.logger.error(f"Error processing {face}: {str(e)}")
                result[face] = 500

                if progress_callback:
                    progress = ((i + 1) / len(faces)) * 100
                    progress_callback(face, 500, progress)

        self.logger.info("Sending successfully end.")
        return result

    def make_request(self, body: dict | bytes) -> int:
        response = requests.request(method='POST', url=self._url, json=body)
        if response.status_code != 200:
            self.logger.warning(f"Bad status {response.status_code}: Error {response.text}")
        return response.status_code

    def get_json_body(self, photo: Path):
        image_content = base64.b64encode(photo.read_bytes()).decode("utf-8")
        return R20Event(base64=image_content, ip=self.host, tempUnit="1", temperature="36.6", time=self.get_timestamp())

    @staticmethod
    def get_timestamp():
        return str(datetime.today().timestamp() * 1000).split('.')[0]
