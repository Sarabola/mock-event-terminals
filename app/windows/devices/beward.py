from pydantic import BaseModel

from app.db import db_helper
from app.devices.beward import BewardSender
from app.windows.abc import DeviceWindow, Window
from app.windows.devices.settings_with_temperature import DeviceWithTemperatureSettingsWindow
from app.windows.select_photo import SelectPhotosWindow
from app.windows.send_status_window import SendStatusWindow


class TerminalFlags(BaseModel):
    temperature_enabled: bool = False
    old_event: bool = False
    above_normal_temp: bool = False
    abnormal_temp: bool = False


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

        device_data = db_helper.get_device_by_name(self.TERMINAL_NAME)
        flags = self.get_flags(device_data)

        def send_photos_callback(selected_photos, progress_callback):
            return self.sender.make_selected_photos_request(
                faces=selected_photos,
                progress_callback=progress_callback,
                temperature_enabled=flags.temperature_enabled,
                abnormal_temp=flags.abnormal_temp,
                above_normal_temp=flags.above_normal_temp,
                old_event=flags.old_event
            )

        status_window.show_status(send_photos_callback)

    @staticmethod
    def get_flags(device_data) -> TerminalFlags:
        temperature_enabled = device_data.get("enable_temp")
        return TerminalFlags(
            temperature_enabled=temperature_enabled,
            old_event=device_data.get("old_event"),
            above_normal_temp=device_data.get("above_normal_temp") and temperature_enabled,
            abnormal_temp=device_data.get("abnormal_temp") and temperature_enabled,
        )

    def go_back(self):
        self._clear_window()
        self.devices_window.show_devices()
