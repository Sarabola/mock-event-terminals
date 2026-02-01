import json

from app.config import project_settings

DATA_TEMPLATE = {
    "network": {
        "host": "localhost",
        "port": 9091
    },
    "terminals": {
        "lunafast2nextgen": {
            "device_id": ""
        },
        "lunafast4a": {
            "device_id": "",
            "card_event": False,
            "card_number": "12345",
            "temperature_enabled": False,
            "above_normal_temp": False,
            "abnormal_temp": False,
            "old_event": False
        },
        "r20": {
            "device_id": ""
        },
        "beward": {
            "device_id": "",
            "enable_temp": False,
            "above_normal_temp": False,
            "abnormal_temp": False,
            "old_event": False
        }
    },
    "images": {}
}


class DatabaseManager:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def get_host(self) -> str:
        with open(self.db_path, "r") as f:
            json_data = json.load(f)
            return json_data["network"]["host"]

    def get_port(self) -> int:
        with open(self.db_path, "r") as f:
            json_data = json.load(f)
            return int(json_data["network"]["port"])

    def get_device_by_name(self, device_name: str) -> dict:
        with open(self.db_path, "r") as f:
            json_data = json.load(f)
            return json_data["terminals"].get(device_name)

    def get_device_id_by_name(self, device_name: str) -> str | None:
        with open(self.db_path, "r") as f:
            json_data = json.load(f)
            terminal = json_data["terminals"][device_name]
            return terminal.get("device_id")

    def get_images_data(self) -> dict[str, bool]:
        with open(self.db_path, "r") as f:
            json_data = json.load(f)
            return json_data["images"]

    def get_device_data(self) -> dict[str, dict]:
        with open(self.db_path, "r") as f:
            json_data = json.load(f)
            return json_data["terminals"]

    def update_data(self, new_data: dict) -> None:
        with open(self.db_path, "w") as f:
            json.dump(new_data, f, indent=2)

    def get_actual_images(self) -> list[str]:
        faces = []
        with open(self.db_path, "r") as f:
            data = json.load(f)
            for face, status in data.get("images").items():
                if status is True:
                    faces.append(face)
        return faces

    def get_data(self) -> dict:
        with open(self.db_path, "r") as f:
            data = json.load(f)
            return data

    @staticmethod
    def initialize_db():
        if not project_settings.db_file.exists():
            with open("settings.json", "w") as file:
                json.dump(DATA_TEMPLATE, file, indent=2)


db_helper = DatabaseManager(project_settings.db_file)
