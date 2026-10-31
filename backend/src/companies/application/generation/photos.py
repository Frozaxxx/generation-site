import io
from pathlib import Path
from uuid import UUID

from PIL import Image, ImageFilter, ImageOps

from src.core.settings import storage_config

PHOTO_SIZE = (640, 800)  # 4:5, как на страницах команды
JPEG_QUALITY = 84


def company_media_dir(company_id: UUID) -> Path:
    return storage_config.media_dir / "companies" / str(company_id)


def team_photo_relpath(person_id: str) -> str:
    return f"team/{person_id}.jpg"


def prepare_photo(content: bytes) -> bytes:
    """
    Приводит портрет к виду фото с сайта: кадр 4:5, умеренный размер, JPEG без
    метаданных. Лёгкое смягчение убирает «пересушенную» резкость генерации.
    """

    with Image.open(io.BytesIO(content)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")

    image = ImageOps.fit(image, PHOTO_SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.4))
    image = image.filter(ImageFilter.GaussianBlur(radius=0.3))

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return buffer.getvalue()


def save_team_photo(company_id: UUID, person_id: str, content: bytes) -> str:
    relpath = team_photo_relpath(person_id)
    path = company_media_dir(company_id) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(prepare_photo(content))
    return relpath
