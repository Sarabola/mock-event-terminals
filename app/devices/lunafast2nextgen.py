import base64
import time
from pathlib import Path

import requests

from app.config import get_logger, project_settings
from app.db import db_helper


class LunaFast2NextGenSender:
    _DEVICE_NAME = "lunafast2nextgen"
    _ENDPOINT_TEMPLATE = "vl-access/webhook/device/{component_id}/event/handle_event"
    _URL_TEMPLATE = "http://{host}:{port}/"
    _IMAGES_PATH = project_settings.images_path

    def __init__(self):
        self.host = db_helper.get_host()
        self.port = db_helper.get_port()
        self.device_id = db_helper.get_device_by_name(self._DEVICE_NAME).get("device_id")
        self.logger = get_logger(self.__class__.__name__)

        self._URL = (self._URL_TEMPLATE.format(host=self.host, port=self.port) +
                     self._ENDPOINT_TEMPLATE.format(component_id=self.device_id))

    def get_request_body(self, _face: Path):
        face_bytes = _face.read_bytes()
        base_64 = base64.b64encode(face_bytes)
        return {"bestshot_b64": base_64.decode("utf-8"), "isSigned": False, "device_id": self.device_id}

    def make_request(self, face_path) -> int:
        face_name = face_path.name
        face_body = self.get_request_body(face_path)
        response = requests.request(method='POST', url=self._URL, json=face_body)
        log_message = f"Image: {face_name}, status_code: {response.status_code}"
        if response.status_code != 200:
            self.logger.warning(log_message + f" desc: {response.text}")
        else:
            self.logger.info(log_message)
        return response.status_code

    def make_selected_photos_request(self, faces: list[str], progress_callback=None) -> dict[str, int]:
        result = {}
        for i, face in enumerate(faces):
            face_path = self._IMAGES_PATH.joinpath(face)
            status = self.make_request(face_path)
            result[face] = status
            if progress_callback:
                progress = ((i + 1) / len(faces)) * 100
                progress_callback(face, status, progress)
            
            time.sleep(3.1)

        self.logger.info("Sending successfully end.")
        return result
