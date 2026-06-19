from pydantic import BaseModel


class DeviceRuntimeSettings(BaseModel):
    device_id: str = ""
    temperature_enabled: bool = False
    above_normal_temp: bool = False
    abnormal_temp: bool = False
    old_event: bool = False
    card_event: bool = False
    card_number: str = "12345"
