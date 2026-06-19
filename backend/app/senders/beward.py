import base64
import time
from datetime import datetime, timedelta
from pathlib import Path
from random import choice, randint

from backend.app.senders.base import DeviceSender, ProgressCallback
from backend.app.senders.types import DeviceRuntimeSettings


class BewardSender(DeviceSender):
    delay_seconds = 3.1

    def make_selected_photos_request(
        self,
        faces: list[str],
        terminal: DeviceRuntimeSettings,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, int]:
        result: dict[str, int] = {}
        total = len(faces)
        for index, face in enumerate(faces):
            try:
                body = self.get_beward_body(
                    self.context.images_path / face,
                    enable_temp=terminal.temperature_enabled,
                    above_normal_temp=terminal.above_normal_temp,
                    abnormal_temp=terminal.abnormal_temp,
                    old_event=terminal.old_event,
                )
                status = self._post_json(body)
                result[face] = status
                if progress_callback:
                    progress_callback(face, status, ((index + 1) / total) * 100)
                time.sleep(self.delay_seconds)
            except Exception as exc:
                self.logger.exception("Error processing %s", face)
                result[face] = 500
                if progress_callback:
                    progress_callback(face, 500, ((index + 1) / total) * 100, str(exc))
        return result

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
        return base64.encodebytes(face_path.read_bytes()).decode()

    @staticmethod
    def get_old_datetime_string() -> str:
        delta = timedelta(days=randint(0, 1000), hours=randint(0, 23), minutes=randint(1, 59))
        return (datetime.now() - delta).strftime("%Y-%m-%dT%H:%M:%S")
