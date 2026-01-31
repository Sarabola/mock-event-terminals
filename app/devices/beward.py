

import base64
import time
from datetime import datetime, timedelta
from random import choice, randint

import requests
from pathlib import Path
from app.devices.abc import DeviceSender


class BewardSender(DeviceSender):
    _DEVICE_NAME = "beward"

    def make_selected_photos_request(
            self,
            faces: list[str],
            progress_callback=None,
            temperature_enabled: bool = False,
            old_event: bool = False,
            above_normal_temp: bool = False,
            abnormal_temp: bool = False
    ) -> dict[str, int]:
        result = {}
        for i, face in enumerate(faces):
            face_path = self._IMAGES_PATH.joinpath(face)
            try:
                body = self.get_beward_body(face_path, temperature_enabled, above_normal_temp ,abnormal_temp, old_event)
                status = self.make_request(body)
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
        response = requests.post(url=self._URL, json=body)
        if response.status_code != 200:
            self.logger.warning(f"Failed request! Error: {response.text}.")
        return response.status_code

    def get_beward_body(
            self,
            face_path: Path,
            enable_temp: bool = False,
            above_normal_temp: bool = False,
            abnormal_temp: bool = False,
            old_event: bool = False,
    ) -> dict:
        temperature = None
        if enable_temp:
            if above_normal_temp:
                temperature = str(randint(370, 413) / 10)
            elif abnormal_temp:
                temperature = str(choice([randint(330, 360) / 10, randint(414, 435) / 10]))
            else:
                temperature = str(randint(361, 369) / 10)

        return {
            "operator": "SnapPush",
            "info": {
                "CreateTime": self.get_old_datetime_string() if old_event else self.get_current_datetime_string(),
                "Temperature": temperature,
                "TemperatureAlarm": 0,
                "TemperatureMode": 0,
                "Mask": 0,
                "PictureType": 0,
                "Sendintime": 1,
            },
            "SnapPic": f"data:image/jpeg;base64,{self.get_image_b64_string(face_path)}",
        }

    @staticmethod
    def get_current_datetime_string() -> str:
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    @staticmethod
    def get_image_b64_string(face_path: Path) -> str:
        face = face_path.read_bytes()
        _img_b64 = base64.encodebytes(face)
        return _img_b64.decode()

    @staticmethod
    def get_old_datetime_string() -> str:
        delta = timedelta(
            days=randint(0, 1000),
            hours=randint(0, 23),
            minutes=randint(1, 59),
        )
        return (datetime.now() - delta).strftime("%Y-%m-%dT%H:%M:%S")


