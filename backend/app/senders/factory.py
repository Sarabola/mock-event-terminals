from backend.app.senders.base import DeviceContext, DeviceSender
from backend.app.senders.beward import BewardSender
from backend.app.senders.hikvision_terminal_thermo import HikvisionTerminalThermoSender
from backend.app.senders.lunafast2nextgen import LunaFast2NextGenSender
from backend.app.senders.lunafast4a import LunaFast4ASender
from backend.app.senders.r20 import R20Sender

SENDER_BY_DEVICE: dict[str, type[DeviceSender]] = {
    "lunafast2nextgen": LunaFast2NextGenSender,
    "lunafast4a": LunaFast4ASender,
    "r20": R20Sender,
    "beward": BewardSender,
    "hikvision_terminal_thermo": HikvisionTerminalThermoSender,
}


def build_sender(device_name: str, context: DeviceContext) -> DeviceSender:
    try:
        sender_class = SENDER_BY_DEVICE[device_name]
    except KeyError as exc:
        raise ValueError(f"Unsupported device: {device_name}") from exc
    return sender_class(context)
