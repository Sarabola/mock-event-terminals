import json
import time
from datetime import datetime, timedelta
from random import choice, randint

from backend.app.senders.base import DeviceSender, ProgressCallback
from backend.app.senders.types import DeviceRuntimeSettings


class LunaFast4ASender(DeviceSender):
    delay_seconds = 3.1
    HIK_FACE_BODY_TEMPLATE = "Picture--MIME_boundary\r\n\r\n{body}\r\n\r\n--MIME_boundary\r\n\r\n"
    HIK_CARD_BODY_TEMPLATE = "--MIME_boundary\r\n\r\n{body}--MIME_boundary\r\n\r\n"

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
                if terminal_data.temperature_enabled:
                    status = self.make_face_request_with_temperature(face_bytes, terminal_data)
                else:
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

    @staticmethod
    def get_current_datetime_string() -> str:
        return datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

    @staticmethod
    def get_old_datetime_string() -> str:
        delta = timedelta(days=randint(0, 1000), hours=randint(0, 23), minutes=randint(1, 59))
        return (datetime.now() - delta).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

    def _get_base_body(self, major_code: str, minor_code: str, old_event: bool) -> dict:
        return {
            "dateTime": self.get_old_datetime_string() if old_event else self.get_current_datetime_string(),
            "AccessControllerEvent": {
                "majorEventType": major_code,
                "subEventType": minor_code,
            },
        }

    def get_face_body(self, major_code: str = "5", minor_code: str = "75", old_event: bool = False) -> dict:
        return self._get_base_body(major_code=major_code, minor_code=minor_code, old_event=old_event)

    def get_card_body(
        self,
        major_code: str = "5",
        minor_code: str = "0",
        card: str = "07925127",
        old_event: bool = False,
    ) -> dict:
        body = self._get_base_body(major_code=major_code, minor_code=minor_code, old_event=old_event)
        body["AccessControllerEvent"]["cardNo"] = card
        return body

    def get_face_body_with_temperature(
        self,
        old_event: bool = False,
        above_normal_temp: bool = False,
        abnormal_temp: bool = False,
    ) -> dict:
        if above_normal_temp:
            temperature = str(randint(370, 413) / 10)
        elif abnormal_temp:
            temperature = str(choice([randint(330, 360) / 10, randint(414, 435) / 10]))
        else:
            temperature = str(randint(361, 369) / 10)
        body = self.get_face_body(old_event=old_event)
        body["AccessControllerEvent"]["currTemperature"] = temperature
        return body

    def make_face_request_with_temperature(self, face: bytes, terminal: DeviceRuntimeSettings) -> int:
        face_body = self.get_face_body_with_temperature(
            old_event=terminal.old_event,
            abnormal_temp=terminal.abnormal_temp,
            above_normal_temp=terminal.above_normal_temp,
        )
        template_data = self.HIK_FACE_BODY_TEMPLATE.format(body=json.dumps(face_body))
        return self._post_data(template_data.encode() + face)

    def make_face_request(self, face: bytes, terminal: DeviceRuntimeSettings) -> int:
        face_body = self.get_face_body(old_event=terminal.old_event)
        template_data = self.HIK_FACE_BODY_TEMPLATE.format(body=json.dumps(face_body))
        return self._post_data(template_data.encode() + face)

    def make_card_request(self, card: str = "456784", old_event: bool = False) -> int:
        body = self.get_card_body(card=card, old_event=old_event)
        data = self.HIK_CARD_BODY_TEMPLATE.format(body=json.dumps(body)).encode()
        return self._post_data(data)
