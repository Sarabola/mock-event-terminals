import asyncio
import time
from datetime import datetime

from sqlalchemy import select

from backend.app.core.config import get_settings
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.models import Device, DeviceSettings, NetworkSettings, SendJob, SendResult
from backend.app.senders.base import DeviceContext
from backend.app.senders.factory import build_sender
from backend.app.senders.types import DeviceRuntimeSettings
from backend.app.services.images import get_selected_image_names

JOB_PROGRESS: dict[int, dict] = {}


def _settings_to_runtime(settings: DeviceSettings) -> DeviceRuntimeSettings:
    return DeviceRuntimeSettings(
        device_id=settings.device_id,
        delay_seconds=settings.delay_seconds,
        temperature_enabled=settings.temperature_enabled,
        above_normal_temp=settings.above_normal_temp,
        abnormal_temp=settings.abnormal_temp,
        old_event=settings.old_event,
        liveness_enabled=settings.liveness_enabled,
        card_event=settings.card_event,
        card_number=settings.card_number,
    )


async def create_send_job(
    device_name: str,
    user_id: int,
    repeat_enabled: bool = False,
    repeat_minutes: float | None = None,
    settings_override: DeviceRuntimeSettings | None = None,
    target_name: str | None = None,
) -> int:
    async with AsyncSessionLocal() as session:
        image_names = await get_selected_image_names(session, user_id)
        device = await session.get(Device, device_name)
        if device is None:
            raise ValueError(f"Unsupported device: {device_name}")
        job = SendJob(user_id=user_id, device_name=device_name, status="pending", total=len(image_names), sent=0)
        session.add(job)
        await session.commit()
        await session.refresh(job)
        repeat_duration_seconds = (repeat_minutes or 0) * 60
        JOB_PROGRESS[job.id] = {
            "id": job.id,
            "device_name": device_name,
            "status": "pending",
            "total": len(image_names),
            "sent": 0,
            "results": [],
            "progress": 0.0,
            "repeat_enabled": repeat_enabled and repeat_duration_seconds > 0,
            "repeat_duration_seconds": repeat_duration_seconds,
            "repeat_deadline": time.monotonic() + repeat_duration_seconds if repeat_enabled and repeat_duration_seconds > 0 else None,
            "settings_override": settings_override.model_dump() if settings_override else None,
            "target_name": target_name,
            "device_id": settings_override.device_id if settings_override else None,
        }
        return job.id


async def run_send_job(job_id: int) -> None:
    settings = get_settings()
    async with AsyncSessionLocal() as session:
        job = await session.get(SendJob, job_id)
        if job is None:
            return

        network = await session.scalar(select(NetworkSettings).where(NetworkSettings.user_id == job.user_id))
        device_settings = await session.scalar(
            select(DeviceSettings).where(
                DeviceSettings.user_id == job.user_id,
                DeviceSettings.device_name == job.device_name,
            )
        )
        image_names = await get_selected_image_names(session, job.user_id)

        if network is None or device_settings is None:
            job.status = "failed"
            job.finished_at = datetime.utcnow()
            await session.commit()
            return

        job.status = "running"
        job.total = len(image_names)
        job.sent = 0
        await session.commit()

    if not image_names:
        await _finish_empty_job(job_id)
        return

    progress = JOB_PROGRESS.setdefault(job_id, {})
    repeat_enabled = bool(progress.get("repeat_enabled"))
    repeat_deadline = progress.get("repeat_deadline")
    repeat_duration_seconds = float(progress.get("repeat_duration_seconds") or 0)
    progress.update(
        {
            "status": "running",
            "total": len(image_names),
            "sent": 0,
            "progress": 0.0,
            "results": [],
            "started_at": time.monotonic(),
        }
    )

    override = progress.get("settings_override")
    runtime_settings = DeviceRuntimeSettings(**override) if override else _settings_to_runtime(device_settings)
    context = DeviceContext(
        host=network.host,
        port=network.port,
        device_id=runtime_settings.device_id,
        images_path=settings.images_path,
    )
    sender = build_sender(job.device_name, context)
    sender.delay_seconds = runtime_settings.delay_seconds

    def progress_callback(image_name: str, status_code: int, percent: float, error: str | None = None) -> None:
        current = JOB_PROGRESS.setdefault(job_id, {})
        results = current.setdefault("results", [])
        results.append({"image_name": image_name, "status_code": status_code, "error": error})
        if repeat_enabled and repeat_duration_seconds > 0:
            elapsed = time.monotonic() - current.get("started_at", time.monotonic())
            job_progress = min((elapsed / repeat_duration_seconds) * 100, 100)
        else:
            job_progress = ((len(results) / len(image_names)) * 100) if image_names else percent
        current.update(
            {
                "status": "running",
                "sent": len(results),
                "total": len(image_names),
                "progress": job_progress,
                "repeat_enabled": repeat_enabled,
            }
        )

    def send() -> None:
        while True:
            for image_name in image_names:
                if progress.get("cancel_requested"):
                    progress["repeat_enabled"] = False
                    return
                if repeat_enabled and repeat_deadline is not None and time.monotonic() >= repeat_deadline:
                    progress["repeat_enabled"] = False
                    return

                if job.device_name in {"lunafast4a", "beward", "hikvision_terminal_thermo"}:
                    sender.make_selected_photos_request([image_name], runtime_settings, progress_callback)
                else:
                    sender.make_selected_photos_request([image_name], progress_callback)

            if not repeat_enabled:
                return
            if repeat_deadline is not None and time.monotonic() >= repeat_deadline:
                progress["repeat_enabled"] = False
                return

    try:
        await asyncio.to_thread(send)
        await _persist_job_results(job_id, "cancelled" if progress.get("cancel_requested") else "completed")
    except Exception as exc:
        progress["status"] = "failed"
        progress["error"] = str(exc)
        await _persist_job_results(job_id, "failed")


async def _finish_empty_job(job_id: int) -> None:
    async with AsyncSessionLocal() as session:
        job = await session.get(SendJob, job_id)
        if job is None:
            return
        job.status = "completed"
        job.sent = 0
        job.total = 0
        job.finished_at = datetime.utcnow()
        await session.commit()
    JOB_PROGRESS.setdefault(job_id, {}).update(
        {"status": "completed", "sent": 0, "total": 0, "progress": 100.0, "results": []}
    )


async def _persist_job_results(job_id: int, status: str) -> None:
    progress = JOB_PROGRESS.setdefault(job_id, {})
    results = progress.get("results", [])
    async with AsyncSessionLocal() as session:
        job = await session.get(SendJob, job_id)
        if job is None:
            return
        job.status = status
        job.sent = len(results)
        job.total = progress.get("total", job.total)
        job.finished_at = datetime.utcnow()
        session.add_all(
            SendResult(
                job_id=job_id,
                image_name=result["image_name"],
                status_code=result["status_code"],
                error=result.get("error"),
            )
            for result in results
        )
        await session.commit()

    progress["status"] = status
    if status == "completed":
        progress["progress"] = 100.0
    progress["repeat_enabled"] = False


async def stop_send_job(job_id: int, user_id: int) -> dict | None:
    """Request a graceful stop; the sender finishes no further photos after its current call."""
    async with AsyncSessionLocal() as session:
        job = await session.get(SendJob, job_id)
        if job is None or job.user_id != user_id:
            return None
        if job.status in {"completed", "failed", "cancelled"}:
            return await get_job_payload(job_id, user_id)

        job.status = "cancelling"
        await session.commit()

    progress = JOB_PROGRESS.setdefault(job_id, {})
    progress.update({"cancel_requested": True, "status": "cancelling", "repeat_enabled": False})
    return await get_job_payload(job_id, user_id)


async def get_job_payload(job_id: int, user_id: int) -> dict | None:
    async with AsyncSessionLocal() as session:
        job = await session.get(SendJob, job_id)
        if job is None or job.user_id != user_id:
            return None
        db_results = list((await session.scalars(select(SendResult).where(SendResult.job_id == job_id))).all())

    live = JOB_PROGRESS.get(job_id, {})
    results = live.get("results") or [
        {"image_name": result.image_name, "status_code": result.status_code, "error": result.error}
        for result in db_results
    ]
    total = live.get("total", job.total)
    sent = live.get("sent", job.sent)
    progress = live.get("progress", 100.0 if job.status == "completed" else ((sent / total) * 100 if total else 0.0))
    repeat_deadline = live.get("repeat_deadline")
    repeat_remaining_seconds = None
    if repeat_deadline is not None and live.get("repeat_enabled"):
        repeat_remaining_seconds = max(repeat_deadline - time.monotonic(), 0)
    return {
        "id": job.id,
        "device_name": job.device_name,
        "status": live.get("status", job.status),
        "total": total,
        "sent": sent,
        "progress": progress,
        "repeat_enabled": bool(live.get("repeat_enabled", False)),
        "repeat_remaining_seconds": repeat_remaining_seconds,
        "target_name": live.get("target_name"),
        "device_id": live.get("device_id"),
        "results": results,
        "created_at": job.created_at,
        "finished_at": job.finished_at,
    }


async def send_card_event(device_name: str, card_number: str, user_id: int) -> int:
    if device_name != "lunafast4a":
        raise ValueError("Card events are supported only for Luna Fast 4A")

    async with AsyncSessionLocal() as session:
        network = await session.scalar(select(NetworkSettings).where(NetworkSettings.user_id == user_id))
        device_settings = await session.scalar(
            select(DeviceSettings).where(
                DeviceSettings.user_id == user_id,
                DeviceSettings.device_name == device_name,
            )
        )
        if network is None or device_settings is None:
            raise ValueError("Device or network settings were not initialized")

    settings = get_settings()
    context = DeviceContext(network.host, network.port, device_settings.device_id, settings.images_path)
    sender = build_sender(device_name, context)
    return await asyncio.to_thread(sender.make_card_request, card_number, device_settings.old_event)
