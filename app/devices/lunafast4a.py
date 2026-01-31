import json
import time
from datetime import datetime, timedelta
from random import choice, randint

import requests

from app.devices.abc import DeviceSender


class LunaFast4ASender(DeviceSender):
    _DEVICE_NAME = "lunafast4a"
    HIK_FACE_BODY_TEMPLATE = 'Picture--MIME_boundary\r\n\r\n{body}\r\n\r\n--MIME_boundary\r\n\r\n'
    HIK_CARD_BODY_TEMPLATE = '--MIME_boundary\r\n\r\n{body}--MIME_boundary\r\n\r\n'

    @staticmethod
    def get_current_datetime_string():
        return datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

    @staticmethod
    def get_old_datetime_string():
        delta = timedelta(days=randint(0, 1000), hours=randint(0, 23), minutes=randint(1, 59))
        return (datetime.now() - delta).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

    def _get_base_body(self, major_code: str, minor_code: str, old_event: bool):
        return {
            "dateTime": self.get_old_datetime_string() if old_event else self.get_current_datetime_string(),
            "AccessControllerEvent": {
                "majorEventType": major_code,
                "subEventType": minor_code,
            }
        }

    def get_face_body(self, major_code: str = "5", minor_code: str = "75", old_event: bool = False):
        return self._get_base_body(major_code=major_code, minor_code=minor_code, old_event=old_event)

    def get_card_body(self, major_code: str = "5", minor_code: str = "0", card: str = "07925127",
                      old_event: bool = False):
        card_body = self._get_base_body(major_code=major_code, minor_code=minor_code, old_event=old_event)
        card_body['AccessControllerEvent']["cardNo"] = card
        return card_body

    def get_face_body_with_temperature(
            self,
            old_event: bool = False,
            above_normal_temp: bool = False,
            abnormal_temp: bool = False
    ):
        if above_normal_temp:
            temperature = str(randint(370, 413) / 10)
        elif abnormal_temp:
            temperature = str(choice([randint(330, 360) / 10, randint(414, 435) / 10]))
        else:
            temperature = str(randint(361, 369) / 10)
        func_body = self.get_face_body(old_event=old_event)
        func_body['AccessControllerEvent']['currTemperature'] = temperature
        return func_body

    def make_selected_photos_request(
            self,
            faces: list[str],
            progress_callback=None,
            temperature_enabled=False,
            card_event=False
    ) -> dict[str, int]:
        result = {}

        for i, face in enumerate(faces):
            try:
                if card_event:
                    status = self.make_card_request()
                else:
                    face_path = self._IMAGES_PATH.joinpath(face)
                    face_bytes = face_path.read_bytes()
                    if temperature_enabled:
                        status = self.make_face_request_with_temperature(face_bytes)
                    else:
                        status = self.make_face_request(face_bytes)

                result[face] = status

                if progress_callback:
                    progress = ((i + 1) / len(faces)) * 100
                    progress_callback(face, status, progress)

                time.sleep(1.0 if card_event else 3.1)

            except Exception as e:
                self.logger.error(f"Error processing {face}: {str(e)}")
                result[face] = 500

                if progress_callback:
                    progress = ((i + 1) / len(faces)) * 100
                    progress_callback(face, 500, progress)

        self.logger.info("Sending successfully end.")
        return result

    def make_face_request_with_temperature(self, face: bytes) -> int:
        """Send face request with temperature data."""
        face_body = self.get_face_body_with_temperature()
        face_body = json.dumps(face_body)
        template_data = self.HIK_FACE_BODY_TEMPLATE.format(body=face_body)
        face_data = template_data.encode() + face
        return self.make_request(body=face_data)

    def make_face_request(self, face: bytes):
        """Send face request without temperature."""
        time.sleep(1)
        face_body = self.get_face_body()
        face_body = json.dumps(face_body)
        template_data = self.HIK_FACE_BODY_TEMPLATE.format(body=face_body)
        face_data = template_data.encode() + face
        return self.make_request(body=face_data)

    def make_card_request(self, card: str = "456784"):
        """Send card request."""
        body = self.get_card_body(card=card)
        body = json.dumps(body)
        data = self.HIK_CARD_BODY_TEMPLATE.format(body=body).encode()
        return self.make_request(body=data)

    def make_request(self, body: dict | bytes) -> int:
        response = requests.request(method='POST', url=self._URL, data=body)
        if response.status_code != 200:
            self.logger.warning(f"Failed request! Error: {response.text}.")
        return response.status_code