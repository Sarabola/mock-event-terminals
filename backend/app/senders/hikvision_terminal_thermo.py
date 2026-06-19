import json
import time
from datetime import datetime, timedelta
from random import choice, randint

from backend.app.senders.base import DeviceSender, ProgressCallback
from backend.app.senders.types import DeviceRuntimeSettings


class HikvisionTerminalThermoSender(DeviceSender):
    delay_seconds = 3.1
    HIK_FACE_BODY_TEMPLATE = "Picture--MIME_boundary\r\n\r\n{body}\r\n\r\n--MIME_boundary\r\n\r\n"

    def make_selected_photos_request(
        self,
        faces: list[str],
        terminal_data: DeviceRuntimeSettings,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, int]:
        result: dict[str, int] = {}
        total = len(faces)
        for index, face in enumerate(faces):
            try:
                face_bytes = (self.context.images_path / face).read_bytes()
                status = self.make_face_request(face_bytes, terminal_data)
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

    def make_face_request(self, face: bytes, terminal: DeviceRuntimeSettings) -> int:
        face_body = self.get_face_body_with_temperature(
            old_event=terminal.old_event,
            above_normal_temp=terminal.temperature_enabled and terminal.above_normal_temp,
            abnormal_temp=terminal.temperature_enabled and terminal.abnormal_temp,
            liveness=terminal.liveness_enabled,
        )
        event_data = self.HIK_FACE_BODY_TEMPLATE.format(body=json.dumps(face_body)).encode()
        return self._post_data(event_data + face)

    def get_face_body_with_temperature(
        self,
        old_event: bool = False,
        above_normal_temp: bool = False,
        abnormal_temp: bool = False,
        liveness: bool = True,
    ) -> dict:
        body = self.get_face_body(old_event=old_event, liveness=liveness)
        body["AccessControllerEvent"]["currTemperature"] = self.get_temperature_value(
            above_normal_temp=above_normal_temp,
            abnormal_temp=abnormal_temp,
        )
        return body

    def get_face_body(
        self,
        major_code: str = "5",
        minor_code: str = "75",
        old_event: bool = False,
        liveness: bool = True,
    ) -> dict:
        minor_code = "75" if liveness else "140"
        return {
            "dateTime": self.get_old_datetime_string() if old_event else self.get_current_datetime_string(),
            "AccessControllerEvent": {
                "majorEventType": major_code,
                "subEventType": minor_code,
            },
        }

    @staticmethod
    def get_temperature_value(above_normal_temp: bool = False, abnormal_temp: bool = False) -> str:
        if above_normal_temp:
            return str(randint(370, 413) / 10)
        if abnormal_temp:
            return str(choice([randint(330, 360) / 10, randint(414, 435) / 10]))
        return str(randint(361, 369) / 10)

    @staticmethod
    def get_current_datetime_string() -> str:
        return datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

    @staticmethod
    def get_old_datetime_string() -> str:
        delta = timedelta(days=randint(0, 1000), hours=randint(0, 23), minutes=randint(1, 59))
        return (datetime.now() - delta).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
