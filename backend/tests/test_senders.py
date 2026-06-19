from pathlib import Path

from backend.app.senders.base import DeviceContext
from backend.app.senders.beward import BewardSender
from backend.app.senders.hikvision_terminal_thermo import HikvisionTerminalThermoSender
from backend.app.senders.lunafast2nextgen import LunaFast2NextGenSender
from backend.app.senders.lunafast4a import LunaFast4ASender
from backend.app.senders.types import DeviceRuntimeSettings
from backend.app.services.auth import create_access_token, hash_password, parse_access_token, verify_password


def make_context(tmp_path: Path) -> DeviceContext:
    return DeviceContext(host="localhost", port=9091, device_id="device-1", images_path=tmp_path)


def test_lunafast2_body_contains_device_id_and_base64(tmp_path: Path) -> None:
    image = tmp_path / "face.jpg"
    image.write_bytes(b"face-bytes")

    sender = LunaFast2NextGenSender(make_context(tmp_path))
    body = sender.get_request_body(image)

    assert body.device_id == "device-1"
    assert body.bestshot_b64 == "ZmFjZS1ieXRlcw=="
    assert body.isSigned is False


def test_beward_temperature_body(tmp_path: Path) -> None:
    image = tmp_path / "face.jpg"
    image.write_bytes(b"face-bytes")

    sender = BewardSender(make_context(tmp_path))
    body = sender.get_beward_body(image, enable_temp=True, above_normal_temp=True)

    assert body["operator"] == "SnapPush"
    assert body["info"]["Temperature"] is not None
    assert body["SnapPic"].startswith("data:image/jpeg;base64,")


def test_lunafast4a_card_body_contains_card_number(tmp_path: Path) -> None:
    sender = LunaFast4ASender(make_context(tmp_path))
    body = sender.get_card_body(card="12345")

    assert body["AccessControllerEvent"]["cardNo"] == "12345"
    assert body["AccessControllerEvent"]["majorEventType"] == "5"


def test_lunafast4a_liveness_changes_minor_code(tmp_path: Path) -> None:
    sender = LunaFast4ASender(make_context(tmp_path))

    assert sender.get_face_body(liveness=True)["AccessControllerEvent"]["subEventType"] == "75"
    assert sender.get_face_body(liveness=False)["AccessControllerEvent"]["subEventType"] == "140"


def test_hikvision_terminal_thermo_body_contains_temperature(tmp_path: Path) -> None:
    sender = HikvisionTerminalThermoSender(make_context(tmp_path))
    body = sender.get_face_body_with_temperature(old_event=False, above_normal_temp=True)

    assert body["AccessControllerEvent"]["majorEventType"] == "5"
    assert body["AccessControllerEvent"]["subEventType"] == "75"
    assert body["AccessControllerEvent"]["currTemperature"] is not None


def test_hikvision_terminal_thermo_liveness_changes_minor_code(tmp_path: Path) -> None:
    sender = HikvisionTerminalThermoSender(make_context(tmp_path))

    assert sender.get_face_body(liveness=True)["AccessControllerEvent"]["subEventType"] == "75"
    assert sender.get_face_body(liveness=False)["AccessControllerEvent"]["subEventType"] == "140"


def test_hikvision_terminal_thermo_event_payload_contains_image_bytes(tmp_path: Path, monkeypatch) -> None:
    sender = HikvisionTerminalThermoSender(make_context(tmp_path))
    captured = {}

    def fake_post_data(body: bytes) -> int:
        captured["body"] = body
        return 200

    monkeypatch.setattr(sender, "_post_data", fake_post_data)
    status = sender.make_face_request(b"image-bytes", DeviceRuntimeSettings(temperature_enabled=True))

    assert status == 200
    assert captured["body"].startswith(b"Picture--MIME_boundary")
    assert captured["body"].endswith(b"image-bytes")


def test_password_hash_and_token_roundtrip() -> None:
    password_hash = hash_password("secret")

    assert password_hash != "secret"
    assert verify_password("secret", password_hash) is True
    assert verify_password("wrong", password_hash) is False
    assert parse_access_token(create_access_token(42)) == 42
