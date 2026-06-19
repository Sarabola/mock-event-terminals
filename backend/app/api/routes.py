from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.config import get_settings
from backend.app.db.session import get_session
from backend.app.models.models import Device, DeviceSettings, ImageSelection, NetworkSettings, User
from backend.app.schemas.schemas import (
    AuthRequest,
    AuthResponse,
    BulkImageSelectionUpdate,
    CardEventRequest,
    CardEventResponse,
    DeviceRead,
    DeviceSettingsRead,
    DeviceSettingsUpdate,
    ImageFileRead,
    ImageSelectionUpdate,
    NetworkSettingsRead,
    NetworkSettingsUpdate,
    SendJobDetail,
    SendJobRead,
    UserRead,
)
from backend.app.services.auth import create_access_token, hash_password, verify_password
from backend.app.services.images import refresh_images
from backend.app.services.sending import create_send_job, get_job_payload, run_send_job, send_card_event

router = APIRouter(prefix="/api")


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/auth/register", response_model=AuthResponse)
async def register(payload: AuthRequest, session: AsyncSession = Depends(get_session)) -> AuthResponse:
    email = payload.email.strip().lower()
    existing = await session.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="User with this email already exists")

    user_count = len((await session.scalars(select(User.id))).all())
    if user_count >= 50:
        raise HTTPException(status_code=403, detail="User limit reached")

    user = User(email=email, password_hash=hash_password(payload.password))
    session.add(user)
    await session.flush()
    session.add(NetworkSettings(user_id=user.id, host="localhost", port=9091))
    await ensure_user_device_settings(session, user.id)
    await session.commit()
    await session.refresh(user)
    return AuthResponse(access_token=create_access_token(user.id), user=UserRead.model_validate(user))


@router.post("/auth/login", response_model=AuthResponse)
async def login(payload: AuthRequest, session: AsyncSession = Depends(get_session)) -> AuthResponse:
    email = payload.email.strip().lower()
    user = await session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await ensure_user_defaults(session, user.id)
    await session.commit()
    return AuthResponse(access_token=create_access_token(user.id), user=UserRead.model_validate(user))


@router.get("/auth/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/settings/network", response_model=NetworkSettingsRead)
async def get_network_settings(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> NetworkSettings:
    return await get_or_create_network_settings(session, current_user.id)


@router.put("/settings/network", response_model=NetworkSettingsRead)
async def update_network_settings(
    payload: NetworkSettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> NetworkSettings:
    settings = await get_or_create_network_settings(session, current_user.id)
    settings.host = payload.host
    settings.port = payload.port
    await session.commit()
    await session.refresh(settings)
    return settings


@router.get("/devices", response_model=list[DeviceRead])
async def get_devices(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[DeviceRead]:
    await ensure_user_device_settings(session, current_user.id)
    devices = list((await session.scalars(select(Device).order_by(Device.title))).all())
    settings = await get_user_device_settings(session, current_user.id)
    return [device_to_schema(device, settings[device.name]) for device in devices]


@router.get("/devices/{device_name}", response_model=DeviceRead)
async def get_device(
    device_name: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DeviceRead:
    device = await session.get(Device, device_name)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    settings = await get_or_create_device_settings(session, current_user.id, device_name)
    await session.commit()
    return device_to_schema(device, settings)


@router.put("/devices/{device_name}/settings", response_model=DeviceRead)
async def update_device_settings(
    device_name: str,
    payload: DeviceSettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DeviceRead:
    device = await session.get(Device, device_name)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    settings = await get_or_create_device_settings(session, current_user.id, device_name)
    settings.device_id = payload.device_id
    settings.temperature_enabled = payload.temperature_enabled and device.supports_temperature
    settings.above_normal_temp = payload.above_normal_temp and settings.temperature_enabled
    settings.abnormal_temp = payload.abnormal_temp and settings.temperature_enabled
    settings.old_event = payload.old_event
    settings.card_event = payload.card_event and device.supports_card
    settings.card_number = payload.card_number
    await session.commit()
    await session.refresh(settings)
    return device_to_schema(device, settings)


@router.get("/images", response_model=list[ImageFileRead])
async def get_images(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ImageSelection]:
    return list(
        (
            await session.scalars(
                select(ImageSelection)
                .where(ImageSelection.user_id == current_user.id)
                .order_by(ImageSelection.name)
            )
        ).all()
    )


@router.post("/images/refresh", response_model=list[ImageFileRead])
async def refresh_image_list(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ImageSelection]:
    return await refresh_images(session, get_settings().images_path, current_user.id)


@router.put("/images/{image_name}", response_model=ImageFileRead)
async def update_image_selection(
    image_name: str,
    payload: ImageSelectionUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ImageSelection:
    image = await session.scalar(
        select(ImageSelection).where(
            ImageSelection.user_id == current_user.id,
            ImageSelection.name == image_name,
        )
    )
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    image.selected = payload.selected
    await session.commit()
    await session.refresh(image)
    return image


@router.put("/images", response_model=list[ImageFileRead])
async def update_bulk_image_selection(
    payload: BulkImageSelectionUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ImageSelection]:
    images = list(
        (
            await session.scalars(
                select(ImageSelection).where(ImageSelection.user_id == current_user.id)
            )
        ).all()
    )
    selection_by_name = payload.images
    for image in images:
        if image.name in selection_by_name:
            image.selected = selection_by_name[image.name]
    await session.commit()
    return list(
        (
            await session.scalars(
                select(ImageSelection)
                .where(ImageSelection.user_id == current_user.id)
                .order_by(ImageSelection.name)
            )
        ).all()
    )


@router.post("/devices/{device_name}/send", response_model=SendJobRead)
async def start_sending(
    device_name: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
) -> dict:
    try:
        job_id = await create_send_job(device_name, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    background_tasks.add_task(run_send_job, job_id)
    payload = await get_job_payload(job_id, current_user.id)
    if payload is None:
        raise HTTPException(status_code=500, detail="Send job was not created")
    return payload


@router.get("/send-jobs/{job_id}", response_model=SendJobDetail)
async def get_send_job(job_id: int, current_user: User = Depends(get_current_user)) -> dict:
    payload = await get_job_payload(job_id, current_user.id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Send job not found")
    return payload


@router.post("/devices/{device_name}/card-event", response_model=CardEventResponse)
async def send_card(
    device_name: str,
    payload: CardEventRequest,
    current_user: User = Depends(get_current_user),
) -> CardEventResponse:
    try:
        status_code = await send_card_event(device_name, payload.card_number, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CardEventResponse(status_code=status_code)


async def ensure_user_defaults(session: AsyncSession, user_id: int) -> None:
    await get_or_create_network_settings(session, user_id)
    await ensure_user_device_settings(session, user_id)


async def get_or_create_network_settings(session: AsyncSession, user_id: int) -> NetworkSettings:
    settings = await session.scalar(select(NetworkSettings).where(NetworkSettings.user_id == user_id))
    if settings is None:
        settings = NetworkSettings(user_id=user_id, host="localhost", port=9091)
        session.add(settings)
        await session.flush()
    return settings


async def ensure_user_device_settings(session: AsyncSession, user_id: int) -> None:
    devices = list((await session.scalars(select(Device))).all())
    existing = {
        settings.device_name
        for settings in (
            await session.scalars(select(DeviceSettings).where(DeviceSettings.user_id == user_id))
        ).all()
    }
    for device in devices:
        if device.name not in existing:
            session.add(DeviceSettings(user_id=user_id, device_name=device.name))
    await session.flush()


async def get_or_create_device_settings(
    session: AsyncSession,
    user_id: int,
    device_name: str,
) -> DeviceSettings:
    settings = await session.scalar(
        select(DeviceSettings).where(
            DeviceSettings.user_id == user_id,
            DeviceSettings.device_name == device_name,
        )
    )
    if settings is None:
        settings = DeviceSettings(user_id=user_id, device_name=device_name)
        session.add(settings)
        await session.flush()
    return settings


async def get_user_device_settings(session: AsyncSession, user_id: int) -> dict[str, DeviceSettings]:
    return {
        settings.device_name: settings
        for settings in (
            await session.scalars(select(DeviceSettings).where(DeviceSettings.user_id == user_id))
        ).all()
    }


def device_to_schema(device: Device, settings: DeviceSettings) -> DeviceRead:
    return DeviceRead(
        name=device.name,
        title=device.title,
        supports_temperature=device.supports_temperature,
        supports_card=device.supports_card,
        settings=DeviceSettingsRead.model_validate(settings),
    )
