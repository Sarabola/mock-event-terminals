from pydantic import BaseModel


class DeviceRuntimeSettings(BaseModel):
    device_id: str = ""
    delay_seconds: float = 3.1
    temperature_enabled: bool = False
    above_normal_temp: bool = False
    abnormal_temp: bool = False
    old_event: bool = False
    liveness_enabled: bool = True
    card_event: bool = False
    card_number: str = "12345"
