import base64
import time
from pathlib import Path

import requests

from app.devices.abc import DeviceSender


class LunaFast2NextGenSender(DeviceSender):
    _DEVICE_NAME = "lunafast2nextgen"

    def get_request_body(self, _face: Path):
        face_bytes = _face.read_bytes()
        base_64 = base64.b64encode(face_bytes)
        return {"bestshot_b64": base_64.decode("utf-8"), "isSigned": False, "device_id": self.device_id}

    def make_request(self, face_body) -> int:
        response = requests.request(method='POST', url=self._URL, json=face_body)
        if response.status_code != 200:
            self.logger.warning(f"Bad status {response.status_code}: Error {response.text}")
        return response.status_code

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
