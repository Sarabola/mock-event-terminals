import base64
import time
from pathlib import Path

from pydantic import BaseModel

from backend.app.senders.base import DeviceSender, ProgressCallback


class LunaFast2Body(BaseModel):
    bestshot_b64: str
    isSigned: bool = False
    device_id: str


class LunaFast2NextGenSender(DeviceSender):
    delay_seconds = 3.1

    def make_selected_photos_request(
        self,
        faces: list[str],
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, int]:
        result: dict[str, int] = {}
        total = len(faces)
        for index, face in enumerate(faces):
            try:
                body = self.get_request_body(self.context.images_path / face)
                status = self._post_json(body.model_dump())
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

    def get_request_body(self, face: Path) -> LunaFast2Body:
        base_64 = base64.b64encode(face.read_bytes()).decode("utf-8")
        return LunaFast2Body(bestshot_b64=base_64, isSigned=False, device_id=self.context.device_id)
