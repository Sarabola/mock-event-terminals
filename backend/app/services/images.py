from pathlib import Path
from shutil import copyfileobj
from typing import Literal

from fastapi import HTTPException, UploadFile
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.models import ImageAsset, ImageSelection

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ImageScope = Literal["all", "mine"]


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


def normalize_scope(scope: str) -> ImageScope:
    if scope in {"all", "mine"}:
        return scope
    raise HTTPException(status_code=400, detail="Image scope must be 'all' or 'mine'")


def image_path(images_path: Path, name: str) -> Path:
    image_name = safe_image_name(name)
    path = images_path / image_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return path


async def refresh_images(
    session: AsyncSession,
    images_path: Path,
    user_id: int,
    scope: str = "all",
) -> list[dict]:
    image_scope = normalize_scope(scope)
    filesystem_names = list_image_names(images_path)
    assets = {asset.name: asset for asset in (await session.scalars(select(ImageAsset))).all()}

    for name in filesystem_names - set(assets):
        session.add(ImageAsset(name=name, uploaded_by_user_id=None))

    missing_names = set(assets) - filesystem_names
    if missing_names:
        await session.execute(delete(ImageAsset).where(ImageAsset.name.in_(missing_names)))
        await session.execute(delete(ImageSelection).where(ImageSelection.name.in_(missing_names)))

    await session.execute(
        delete(ImageSelection).where(
            ImageSelection.user_id == user_id,
            ImageSelection.selected.is_(False),
        )
    )
    await session.commit()
    return await list_images(session, user_id, image_scope)


async def list_images(session: AsyncSession, user_id: int, scope: str = "all") -> list[dict]:
    image_scope = normalize_scope(scope)
    query = select(ImageAsset).order_by(ImageAsset.name)
    if image_scope == "mine":
        query = query.where(ImageAsset.uploaded_by_user_id == user_id)

    assets = list((await session.scalars(query)).all())
    selected_names = set(
        (
            await session.scalars(
                select(ImageSelection.name).where(
                    ImageSelection.user_id == user_id,
                    ImageSelection.selected.is_(True),
                )
            )
        ).all()
    )
    return [
        {
            "name": asset.name,
            "selected": asset.name in selected_names,
            "uploaded_by_user_id": asset.uploaded_by_user_id,
            "uploaded_by_me": asset.uploaded_by_user_id == user_id,
        }
        for asset in assets
    ]


async def upload_image(
    session: AsyncSession,
    images_path: Path,
    user_id: int,
    upload: UploadFile,
    scope: str = "all",
) -> list[dict]:
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

    session.add(ImageAsset(name=target.name, uploaded_by_user_id=user_id))
    await session.commit()
    return await refresh_images(session, images_path, user_id, scope)


async def delete_image(
    session: AsyncSession,
    images_path: Path,
    user_id: int,
    name: str,
    scope: str = "all",
) -> list[dict]:
    path = image_path(images_path, name)
    path.unlink()
    await session.execute(delete(ImageAsset).where(ImageAsset.name == path.name))
    await session.execute(delete(ImageSelection).where(ImageSelection.name == path.name))
    await session.commit()
    return await refresh_images(session, images_path, user_id, scope)


async def rename_image(
    session: AsyncSession,
    images_path: Path,
    user_id: int,
    old_name: str,
    new_name: str,
    scope: str = "all",
) -> list[dict]:
    old_path = image_path(images_path, old_name)
    target_name = safe_image_name(new_name)
    new_path = images_path / target_name
    if new_path.exists():
        raise HTTPException(status_code=409, detail="Image with this name already exists")

    old_path.rename(new_path)
    await session.execute(
        update(ImageAsset)
        .where(ImageAsset.name == old_path.name)
        .values(name=target_name)
    )
    await session.execute(
        update(ImageSelection)
        .where(ImageSelection.name == old_path.name)
        .values(name=target_name)
    )
    await session.commit()
    return await refresh_images(session, images_path, user_id, scope)


async def set_image_selection(
    session: AsyncSession,
    user_id: int,
    image_name: str,
    selected: bool,
) -> None:
    if await session.get(ImageAsset, image_name) is None:
        raise HTTPException(status_code=404, detail="Image not found")

    existing = await session.scalar(
        select(ImageSelection).where(
            ImageSelection.user_id == user_id,
            ImageSelection.name == image_name,
        )
    )
    if selected:
        if existing is None:
            session.add(ImageSelection(user_id=user_id, name=image_name, selected=True))
        else:
            existing.selected = True
    elif existing is not None:
        await session.delete(existing)


async def update_image_selections(
    session: AsyncSession,
    user_id: int,
    selections: dict[str, bool],
    scope: str = "all",
) -> list[dict]:
    for image_name, selected in selections.items():
        await set_image_selection(session, user_id, image_name, selected)
    await session.commit()
    return await list_images(session, user_id, scope)


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
