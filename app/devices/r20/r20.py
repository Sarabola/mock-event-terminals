import base64
import json
import time
from datetime import datetime
from pathlib import Path

import requests

from app.devices.abc import DeviceSender
from app.devices.r20.data import R20FACE_JSON


class R20Sender(DeviceSender):
    _DEVICE_NAME = "r20"
    _R20_BODY_TEMPLATE = R20FACE_JSON

    def make_selected_photos_request(self, faces: list[str], progress_callback=None) -> dict[str, int]:
        result = {}
        for i, face in enumerate(faces):
            face_path = self._IMAGES_PATH.joinpath(face)
            try:
                payload = self.get_request_body(face_path)
                status = self.make_request(payload)
                result[face] = status

                if progress_callback:
                    progress = ((i + 1) / len(faces)) * 100
                    progress_callback(face, status, progress)

                time.sleep(3.1)

            except Exception as e:
                self.logger.error(f"Error processing {face}: {str(e)}")
                result[face] = 500

                if progress_callback:
                    progress = ((i + 1) / len(faces)) * 100
                    progress_callback(face, 500, progress)

        self.logger.info("Sending successfully end.")
        return result

    def make_request(self, body: dict | bytes) -> int:
        response = requests.request(method='POST', url=self._URL, data=body)
        if response.status_code != 200:
            self.logger.warning(f"Bad status {response.status_code}: Error {response.text}")
        return response.status_code

    def get_request_body(self, photo_content: Path):
        image_content = base64.b64encode(photo_content.read_bytes()).decode("utf8")
        body = self._R20_BODY_TEMPLATE
        body["base64"] = image_content
        body["time"] = self.get_timestamp()
        body_json = json.dumps(body)
        payload = b'' + body_json.encode() + b'\n'
        return payload

    @staticmethod
    def get_timestamp():
        return str(datetime.today().timestamp() * 1000).split('.')[0]
