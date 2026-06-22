from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.models.models import Device

DEFAULT_DEVICES = [
    ("lunafast2nextgen", "Luna Fast 2 Next Gen", False, False, False),
    ("lunafast4a", "Luna Fast 4A", True, True, True),
    ("r20", "R20", False, False, False),
    ("beward", "Beward", True, False, False),
    ("hikvision_terminal_thermo", "Hikvision Terminal Thermo", True, False, True),
]


async def create_db_schema() -> None:
    settings = get_settings()
    settings.images_path.mkdir(parents=True, exist_ok=True)
    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.replace("sqlite+aiosqlite:///", "", 1)
        if db_path and db_path != ":memory:":
            from pathlib import Path

            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await ensure_sqlite_columns(conn)


async def seed_defaults(session: AsyncSession) -> None:
    existing_devices = set((await session.scalars(select(Device.name))).all())
    for name, title, supports_temperature, supports_card, supports_liveness in DEFAULT_DEVICES:
        if name in existing_devices:
            device = await session.get(Device, name)
            if device is not None:
                device.title = title
                device.supports_temperature = supports_temperature
                device.supports_card = supports_card
                device.supports_liveness = supports_liveness
            continue
        session.add(
            Device(
                name=name,
                title=title,
                supports_temperature=supports_temperature,
                supports_card=supports_card,
                supports_liveness=supports_liveness,
            )
        )

    await session.commit()


async def ensure_sqlite_columns(conn) -> None:
    if engine.url.get_backend_name() != "sqlite":
        return

    device_columns = {
        row[1] for row in (await conn.exec_driver_sql("PRAGMA table_info(devices)")).all()
    }
    if "supports_liveness" not in device_columns:
        await conn.exec_driver_sql("ALTER TABLE devices ADD COLUMN supports_liveness BOOLEAN NOT NULL DEFAULT 0")

    settings_columns = {
        row[1] for row in (await conn.exec_driver_sql("PRAGMA table_info(device_settings)")).all()
    }
    if "delay_seconds" not in settings_columns:
        await conn.exec_driver_sql("ALTER TABLE device_settings ADD COLUMN delay_seconds FLOAT NOT NULL DEFAULT 3.1")
    if "liveness_enabled" not in settings_columns:
        await conn.exec_driver_sql("ALTER TABLE device_settings ADD COLUMN liveness_enabled BOOLEAN NOT NULL DEFAULT 1")
