from pydantic import BaseModel

from app.db import db_helper
from app.devices.beward import BewardSender
from app.windows.abc import DeviceWindow, Window
from app.windows.devices.models import BewardData
from app.windows.devices.settings_with_temperature import \
    DeviceWithTemperatureSettingsWindow
from app.windows.select_photo import SelectPhotosWindow
from app.windows.send_status_window import SendStatusWindow




class BewardWindow(DeviceWindow, Window):
    TERMINAL_NAME = "beward"

    def __init__(self, master, devices_window):
        DeviceWindow.__init__(self, master, devices_window)
        Window.__init__(self, master, None)
        self.sender = BewardSender()

    def open_settings(self):
        self._clear_window()
        devices_window = DeviceWithTemperatureSettingsWindow(self.master, self, self.TERMINAL_NAME, self.sender)
        devices_window.show_settings()

    def select_photos(self):
        images_window = SelectPhotosWindow(self.master, self)
        images_window.show_images()

    def send_event(self):
        status_window = SendStatusWindow(self.master, self.TERMINAL_NAME)

        terminal = self.get_terminal()
        def send_photos_callback(selected_photos, progress_callback):
            return self.sender.make_selected_photos_request(
                faces=selected_photos,
                progress_callback=progress_callback,
                terminal=terminal
            )

        status_window.show_status(send_photos_callback)

    def get_terminal(self) -> BewardData:
        device_data = db_helper.get_device_by_name(self.TERMINAL_NAME)
        return BewardData(**device_data)

    def go_back(self):
        self._clear_window()
        self.devices_window.show_devices()
