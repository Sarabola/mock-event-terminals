from app.windows.abc import DeviceWindow, Window
from app.windows.devices.settings_window import DeviceSettingsWindow
from app.windows.select_photo import SelectPhotosWindow
from app.devices.lunafast2nextgen import LunaFast2NextGenSender
from app.db import db_helper


class LunaFast2NextGenWindow(DeviceWindow, Window):
    TERMINAL_NAME = "lunafast2nextgen"

    def __init__(self, master, devices_window):
        DeviceWindow.__init__(self, master, devices_window)
        Window.__init__(self, master, None)
        self.sender = LunaFast2NextGenSender()

    def open_settings(self):
        self._clear_window()
        devices_window = DeviceSettingsWindow(self.master, self, self.TERMINAL_NAME)
        devices_window.show_settings()

    def select_photos(self):
        self._clear_window()
        images_window = SelectPhotosWindow(self.master, self)
        images_window.show_images()

    def send_event(self):
        faces = db_helper.get_actual_images()
        self.sender.make_selected_photos_request(faces)

    def go_back(self):
        self._clear_window()
        self.devices_window.show_devices()
