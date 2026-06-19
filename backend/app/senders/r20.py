import base64
import time
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from backend.app.senders.base import DeviceSender, ProgressCallback


class R20Event(BaseModel):
    model_config = ConfigDict(extra="allow")

    base64: str
    ip: str
    tempUnit: str | None = None
    temperature: str | None = None
    time: str


class R20Sender(DeviceSender):
    delay_seconds = 4

    def make_selected_photos_request(
        self,
        faces: list[str],
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, int]:
        result: dict[str, int] = {}
        total = len(faces)
        for index, face in enumerate(faces):
            try:
                payload = self.get_json_body(self.context.images_path / face)
                status = self._post_json(payload.model_dump())
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

    def get_json_body(self, photo: Path) -> R20Event:
        image_content = base64.b64encode(photo.read_bytes()).decode("utf-8")
        return R20Event(
            base64=image_content,
            ip=self.context.host,
            tempUnit="1",
            temperature="36.6",
            time=self.get_timestamp(),
        )

    @staticmethod
    def get_timestamp() -> str:
        return str(datetime.today().timestamp() * 1000).split(".")[0]
