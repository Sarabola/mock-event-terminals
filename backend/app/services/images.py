from pathlib import Path
from shutil import copyfileobj

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select, update
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


def safe_image_name(name: str) -> str:
    raw_name = name.strip()
    image_name = Path(raw_name).name
    if not image_name:
        raise HTTPException(status_code=400, detail="Image name is required")
    if image_name != raw_name:
        raise HTTPException(status_code=400, detail="Image name must not contain path separators")
    if Path(image_name).suffix.lower() not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Supported image extensions: .jpg, .jpeg, .png")
    return image_name


def image_path(images_path: Path, name: str) -> Path:
    image_name = safe_image_name(name)
    path = images_path / image_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return path


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


async def upload_image(
    session: AsyncSession,
    images_path: Path,
    user_id: int,
    upload: UploadFile,
) -> list[ImageSelection]:
    image_name = safe_image_name(upload.filename or "")
    images_path.mkdir(parents=True, exist_ok=True)
    target = images_path / image_name
    if target.exists():
        stem = target.stem
        suffix = target.suffix
        index = 1
        while target.exists():
            target = images_path / f"{stem}-{index}{suffix}"
            index += 1

    with target.open("wb") as destination:
        copyfileobj(upload.file, destination)

    return await refresh_images(session, images_path, user_id)


async def delete_image(
    session: AsyncSession,
    images_path: Path,
    user_id: int,
    name: str,
) -> list[ImageSelection]:
    path = image_path(images_path, name)
    path.unlink()
    await session.execute(delete(ImageSelection).where(ImageSelection.name == path.name))
    await session.commit()
    return await refresh_images(session, images_path, user_id)


async def rename_image(
    session: AsyncSession,
    images_path: Path,
    user_id: int,
    old_name: str,
    new_name: str,
) -> list[ImageSelection]:
    old_path = image_path(images_path, old_name)
    target_name = safe_image_name(new_name)
    new_path = images_path / target_name
    if new_path.exists():
        raise HTTPException(status_code=409, detail="Image with this name already exists")

    old_path.rename(new_path)
    await session.execute(
        update(ImageSelection)
        .where(ImageSelection.name == old_path.name)
        .values(name=target_name)
    )
    await session.commit()
    return await refresh_images(session, images_path, user_id)


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
