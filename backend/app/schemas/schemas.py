from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NetworkSettingsRead(BaseModel):
    host: str
    port: int

    model_config = ConfigDict(from_attributes=True)


class NetworkSettingsUpdate(BaseModel):
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)


class UserRead(BaseModel):
    id: int
    email: str

    model_config = ConfigDict(from_attributes=True)


class AuthRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class DeviceSettingsRead(BaseModel):
    device_id: str
    temperature_enabled: bool
    above_normal_temp: bool
    abnormal_temp: bool
    old_event: bool
    card_event: bool
    card_number: str

    model_config = ConfigDict(from_attributes=True)


class DeviceSettingsUpdate(BaseModel):
    device_id: str = ""
    temperature_enabled: bool = False
    above_normal_temp: bool = False
    abnormal_temp: bool = False
    old_event: bool = False
    card_event: bool = False
    card_number: str = "12345"


class DeviceRead(BaseModel):
    name: str
    title: str
    supports_temperature: bool
    supports_card: bool
    settings: DeviceSettingsRead

    model_config = ConfigDict(from_attributes=True)


class ImageFileRead(BaseModel):
    name: str
    selected: bool

    model_config = ConfigDict(from_attributes=True)


class ImageSelectionUpdate(BaseModel):
    selected: bool


class BulkImageSelectionUpdate(BaseModel):
    images: dict[str, bool]


class ImageRenameRequest(BaseModel):
    new_name: str = Field(min_length=1, max_length=255)


class SendJobRead(BaseModel):
    id: int
    device_name: str
    status: str
    total: int
    sent: int
    progress: float


class SendResultRead(BaseModel):
    image_name: str
    status_code: int
    error: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SendJobDetail(SendJobRead):
    results: list[SendResultRead]
    created_at: datetime | None = None
    finished_at: datetime | None = None


class CardEventRequest(BaseModel):
    card_number: str


class CardEventResponse(BaseModel):
    status_code: int
