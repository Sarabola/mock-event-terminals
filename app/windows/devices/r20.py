from app.devices.r20.r20 import R20Sender
from app.windows.abc import DeviceWindow, Window
from app.windows.devices.settings_window import DeviceSettingsWindow
from app.windows.select_photo import SelectPhotosWindow
from app.windows.send_status_window import SendStatusWindow


class R20Window(DeviceWindow, Window):
    TERMINAL_NAME = "r20"

    def __init__(self, master, devices_window):
        DeviceWindow.__init__(self, master, devices_window)
        Window.__init__(self, master, None)
        self.sender = R20Sender()

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

    def go_back(self):
        self._clear_window()
        self.devices_window.show_devices()
