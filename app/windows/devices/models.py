from pydantic import BaseModel


class TerminalDataBase(BaseModel):
    device_id: str


class LunaFast2Data(TerminalDataBase):
    pass


class R20Data(TerminalDataBase):
    pass


class TerminalDataWithTemperature(TerminalDataBase):
    temperature_enabled: bool = False
    old_event: bool = False
    above_normal_temp: bool = False
    abnormal_temp: bool = False


class BewardData(TerminalDataWithTemperature):
    pass


class LunaFastData(TerminalDataWithTemperature):
    card_event: bool = False
    card_number: str = ""
