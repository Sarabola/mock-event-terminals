import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user
from backend.app.core.config import get_settings
from backend.app.db.session import AsyncSessionLocal, get_session
from backend.app.models.models import Device, DeviceSettings, NetworkSettings, User
from backend.app.schemas.schemas import (
    AuthRequest,
    AuthResponse,
    BatchSendRequest,
    BatchSendStartResponse,
    BulkImageSelectionUpdate,
    CardEventRequest,
    CardEventResponse,
    DeviceRead,
    DeviceSettingsRead,
    DeviceSettingsUpdate,
    ImageFileRead,
    ImageRenameRequest,
    ImageSelectionUpdate,
    NetworkSettingsRead,
    NetworkSettingsUpdate,
    PasswordChangeRequest,
    SendJobDetail,
    SendJobRead,
    SendStartRequest,
    UserRead,
)
from backend.app.services.auth import create_access_token, hash_password, parse_access_token, verify_password
from backend.app.services.images import (
    delete_image,
    image_path,
    list_images,
    refresh_images,
    rename_image,
    set_image_selection,
    update_image_selections,
    upload_image,
)
from backend.app.services.sending import create_send_job, get_job_payload, run_send_job, send_card_event, stop_send_job
from backend.app.senders.types import DeviceRuntimeSettings

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


@router.put("/auth/password", response_model=UserRead)
async def change_password(
    payload: PasswordChangeRequest,
    session: AsyncSession = Depends(get_session),
) -> User:
    email = payload.email.strip().lower()
    user = await session.scalar(select(User).where(User.email == email))
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(payload.password)
    await session.commit()
    await session.refresh(user)
    return user


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
    settings.liveness_enabled = payload.liveness_enabled if device.supports_liveness else True
    settings.card_event = payload.card_event and device.supports_card
    settings.card_number = payload.card_number
    await session.commit()
    await session.refresh(settings)
    return device_to_schema(device, settings)


@router.get("/images", response_model=list[ImageFileRead])
async def get_images(
    scope: str = Query(default="all"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await list_images(session, current_user.id, scope)


@router.post("/images/refresh", response_model=list[ImageFileRead])
async def refresh_image_list(
    scope: str = Query(default="all"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await refresh_images(session, get_settings().images_path, current_user.id, scope)


@router.get("/images/{image_name}/content")
async def get_image_content(
    image_name: str,
    token: str,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    user_id = parse_access_token(token)
    if user_id is None or await session.get(User, user_id) is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    path = image_path(get_settings().images_path, image_name)
    return FileResponse(path)


@router.post("/images/upload", response_model=list[ImageFileRead])
async def upload_new_image(
    scope: str = Query(default="all"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    file: UploadFile = File(...),
) -> list[dict]:
    return await upload_image(session, get_settings().images_path, current_user.id, file, scope)


@router.delete("/images/{image_name}", response_model=list[ImageFileRead])
async def delete_existing_image(
    image_name: str,
    scope: str = Query(default="all"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await delete_image(session, get_settings().images_path, current_user.id, image_name, scope)


@router.put("/images/{image_name}/rename", response_model=list[ImageFileRead])
async def rename_existing_image(
    image_name: str,
    payload: ImageRenameRequest,
    scope: str = Query(default="all"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await rename_image(session, get_settings().images_path, current_user.id, image_name, payload.new_name, scope)


@router.put("/images/{image_name}", response_model=ImageFileRead)
async def update_image_selection(
    image_name: str,
    payload: ImageSelectionUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    await set_image_selection(session, current_user.id, image_name, payload.selected)
    await session.commit()
    images = await list_images(session, current_user.id)
    for image in images:
        if image["name"] == image_name:
            return image
    raise HTTPException(status_code=404, detail="Image not found")


@router.put("/images", response_model=list[ImageFileRead])
async def update_bulk_image_selection(
    payload: BulkImageSelectionUpdate,
    scope: str = Query(default="all"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await update_image_selections(session, current_user.id, payload.images, scope)


@router.post("/devices/{device_name}/send", response_model=SendJobRead)
async def start_sending(
    device_name: str,
    background_tasks: BackgroundTasks,
    payload: SendStartRequest | None = None,
    current_user: User = Depends(get_current_user),
) -> dict:
    send_options = payload or SendStartRequest()
    try:
        job_id = await create_send_job(
            device_name=device_name,
            user_id=current_user.id,
            repeat_enabled=send_options.repeat_enabled,
            repeat_minutes=send_options.repeat_minutes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    background_tasks.add_task(run_send_job, job_id)
    payload = await get_job_payload(job_id, current_user.id)
    if payload is None:
        raise HTTPException(status_code=500, detail="Send job was not created")
    return payload


@router.post("/devices/send", response_model=BatchSendStartResponse)
async def start_batch_sending(
    payload: BatchSendRequest,
    current_user: User = Depends(get_current_user),
) -> BatchSendStartResponse:
    """Start a separate job for every terminal instance at the same time."""
    job_ids: list[int] = []
    async with AsyncSessionLocal() as session:
        for target in payload.targets:
            device = await session.get(Device, target.device_name)
            if device is None:
                raise HTTPException(status_code=404, detail=f"Unsupported device: {target.device_name}")

            source = target.settings
            runtime_settings = DeviceRuntimeSettings(
                device_id=source.device_id,
                delay_seconds=source.delay_seconds,
                temperature_enabled=source.temperature_enabled and device.supports_temperature,
                above_normal_temp=source.above_normal_temp and source.temperature_enabled and device.supports_temperature,
                abnormal_temp=source.abnormal_temp and source.temperature_enabled and device.supports_temperature,
                old_event=source.old_event,
                liveness_enabled=source.liveness_enabled if device.supports_liveness else True,
                card_event=source.card_event and device.supports_card,
                card_number=source.card_number,
            )
            job_ids.append(
                await create_send_job(
                    device_name=target.device_name,
                    user_id=current_user.id,
                    repeat_enabled=payload.repeat_enabled,
                    repeat_minutes=payload.repeat_minutes,
                    settings_override=runtime_settings,
                    target_name=target.name,
                )
            )

    # Starlette's BackgroundTasks await tasks one by one. These tasks run independently.
    for job_id in job_ids:
        asyncio.create_task(run_send_job(job_id))
    jobs = [await get_job_payload(job_id, current_user.id) for job_id in job_ids]
    return BatchSendStartResponse(jobs=[job for job in jobs if job is not None])


@router.get("/send-jobs/{job_id}", response_model=SendJobDetail)
async def get_send_job(job_id: int, current_user: User = Depends(get_current_user)) -> dict:
    payload = await get_job_payload(job_id, current_user.id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Send job not found")
    return payload


@router.post("/send-jobs/{job_id}/stop", response_model=SendJobDetail)
async def stop_sending(job_id: int, current_user: User = Depends(get_current_user)) -> dict:
    payload = await stop_send_job(job_id, current_user.id)
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
        supports_liveness=device.supports_liveness,
        settings=DeviceSettingsRead.model_validate(settings),
    )
