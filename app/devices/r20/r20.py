import base64
import json
import time
from datetime import datetime
from pathlib import Path

from requests import request

from app.config import project_settings, get_logger
from app.db import db_helper
from app.devices.r20.data import R20FACE_JSON


class R20Sender:
    _DEVICE_NAME = "r20"
    _ENDPOINT_TEMPLATE = "vl-access/webhook/device/{component_id}/event/handle_event"
    _URL_TEMPLATE = "http://{host}:{port}/"
    _IMAGES_PATH = project_settings.images_path

    _R20_BODY_TEMPLATE = R20FACE_JSON

    def __init__(self):
        self.host = db_helper.get_host()
        self.port = db_helper.get_port()
        self.device_id = db_helper.get_device_id_by_name(self._DEVICE_NAME)
        self.logger = get_logger(self.__class__.__name__)

        self._URL = (self._URL_TEMPLATE.format(host=self.host, port=self.port) +
                     self._ENDPOINT_TEMPLATE.format(component_id=self.device_id))

    def make_request(self, photo_content: Path) -> int:
        body_json = self.get_request_body(photo_content)
        payload = b'' + body_json.encode() + b'\n'
        response = request("POST", self._URL, data=payload)
        return response.status_code

    def get_request_body(self, photo_content: Path):
        image_content = base64.b64encode(photo_content.read_bytes()).decode("utf8")
        body = self._R20_BODY_TEMPLATE
        body["base64"] = image_content
        body["time"] = self.get_timestamp()
        body_json = json.dumps(body)
        return body_json

    @staticmethod
    def get_timestamp():
        return str(datetime.today().timestamp() * 1000).split('.')[0]

    def make_selected_photos_request(self, faces: list[str], progress_callback=None) -> dict[str, int]:
        result = {}
        for i, face in enumerate(faces):
            face_path = self._IMAGES_PATH.joinpath(face)
            try:
                status = self.make_request(face_path)
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
