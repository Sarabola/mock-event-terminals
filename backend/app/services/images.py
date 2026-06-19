from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import ImageSelection

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def list_image_names(images_path: Path) -> set[str]:
    images_path.mkdir(parents=True, exist_ok=True)
    return {
        path.name
        for path in images_path.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    }


async def refresh_images(session: AsyncSession, images_path: Path, user_id: int) -> list[ImageSelection]:
    filesystem_names = list_image_names(images_path)
    db_images = {
        image.name: image
        for image in (
            await session.scalars(select(ImageSelection).where(ImageSelection.user_id == user_id))
        ).all()
    }

    for name in filesystem_names - set(db_images):
        session.add(ImageSelection(user_id=user_id, name=name, selected=False))

    missing_names = set(db_images) - filesystem_names
    if missing_names:
        await session.execute(
            delete(ImageSelection).where(
                ImageSelection.user_id == user_id,
                ImageSelection.name.in_(missing_names),
            )
        )

    await session.commit()
    return (
        await session.scalars(
            select(ImageSelection).where(ImageSelection.user_id == user_id).order_by(ImageSelection.name)
        )
    ).all()


async def get_selected_image_names(session: AsyncSession, user_id: int) -> list[str]:
    return list(
        (
            await session.scalars(
                select(ImageSelection.name)
                .where(ImageSelection.user_id == user_id, ImageSelection.selected.is_(True))
                .order_by(ImageSelection.name)
            )
        ).all()
    )
