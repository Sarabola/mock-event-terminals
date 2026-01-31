from abc import ABC, abstractmethod

from app.config import project_settings, get_logger
from app.db import db_helper


class DeviceSender(ABC):
    _ENDPOINT_TEMPLATE = "vl-access/webhook/device/{component_id}/event/handle_event"
    _URL_TEMPLATE = "http://{host}:{port}/"
    _IMAGES_PATH = project_settings.images_path

    def __init__(self):
        self.host = db_helper.get_host()
        self.port = db_helper.get_port()
        self.device_id = db_helper.get_device_id_by_name(self._DEVICE_NAME)
        self.logger = get_logger(self.__class__.__name__)

        self._URL = (self._URL_TEMPLATE.format(host=self.host, port=self.port) +
                     self._ENDPOINT_TEMPLATE.format(component_id=self.device_id))

    @abstractmethod
    def make_request(self, body) -> int:
        pass