from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import get_settings
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.models.models import Device

DEFAULT_DEVICES = [
    ("lunafast2nextgen", "Luna Fast 2 Next Gen", False, False),
    ("lunafast4a", "Luna Fast 4A", True, True),
    ("r20", "R20", False, False),
    ("beward", "Beward", True, False),
    ("hikvision_terminal_thermo", "Hikvision Terminal Thermo", True, False),
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


async def seed_defaults(session: AsyncSession) -> None:
    existing_devices = set((await session.scalars(select(Device.name))).all())
    for name, title, supports_temperature, supports_card in DEFAULT_DEVICES:
        if name in existing_devices:
            device = await session.get(Device, name)
            if device is not None:
                device.title = title
                device.supports_temperature = supports_temperature
                device.supports_card = supports_card
            continue
        session.add(
            Device(
                name=name,
                title=title,
                supports_temperature=supports_temperature,
                supports_card=supports_card,
            )
        )

    await session.commit()
