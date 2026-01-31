from app.windows.abc import DeviceWindow, Window
from app.windows.devices.settings_window import DeviceSettingsWindow
from app.windows.select_photo import SelectPhotosWindow
from app.windows.send_status_window import SendStatusWindow
from app.devices.lunafast2nextgen import LunaFast2NextGenSender


class LunaFast2NextGenWindow(DeviceWindow, Window):
    TERMINAL_NAME = "lunafast2nextgen"

    def __init__(self, master, devices_window):
        DeviceWindow.__init__(self, master, devices_window)
        Window.__init__(self, master, None)
        self.sender = LunaFast2NextGenSender()

    def open_settings(self):
        self._clear_window()
        devices_window = DeviceSettingsWindow(self.master, self, self.TERMINAL_NAME, self.sender)
        devices_window.show_settings()

    def select_photos(self):
        images_window = SelectPhotosWindow(self.master, self)
        images_window.show_images()

    def send_event(self):
        status_window = SendStatusWindow(self.master, self.TERMINAL_NAME)

        def send_photos_callback(selected_photos, progress_callback):
            return self.sender.make_selected_photos_request(selected_photos, progress_callback)

        status_window.show_status(send_photos_callback)

    def show(self):
        super().show()
        self._update_photos_preview()

    def go_back(self):
        self._clear_window()
        self.devices_window.show_devices()
