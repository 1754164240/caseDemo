from pathlib import Path, PureWindowsPath
from typing import Tuple

from app.core.config import settings


BACKEND_DIR = Path(__file__).resolve().parents[2]


def normalize_file_path(file_path: str) -> str:
    """Normalize stored file paths across Windows and POSIX environments."""
    if not file_path:
        raise ValueError("file_path is empty")

    normalized = PureWindowsPath(file_path).as_posix()
    path_obj = Path(normalized).expanduser()
    if path_obj.is_absolute():
        return str(path_obj)
    return path_obj.as_posix()


def resolve_file_path(file_path: str) -> Path:
    """Resolve database-stored file paths to an absolute local path."""
    normalized = normalize_file_path(file_path)
    path_obj = Path(normalized).expanduser()
    if path_obj.is_absolute():
        return path_obj
    return (BACKEND_DIR / path_obj).resolve(strict=False)


def get_upload_dir_path() -> Path:
    """Return the absolute upload directory path."""
    return resolve_file_path(settings.UPLOAD_DIR)


def build_upload_file_path(filename: str) -> Tuple[str, Path]:
    """Build the stored path and absolute path for a new upload."""
    upload_dir = get_upload_dir_path()
    absolute_path = upload_dir / filename

    normalized_upload_dir = Path(normalize_file_path(settings.UPLOAD_DIR))
    if normalized_upload_dir.is_absolute():
        stored_path = str(absolute_path)
    else:
        stored_path = (normalized_upload_dir / filename).as_posix()

    return stored_path, absolute_path
