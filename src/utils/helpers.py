from typing import Any

from pydantic import BaseModel

from utils.base_constant import HTTP400
from utils.base_exception import AppException, NoChangesDetectedError


def ensure_exists(obj: Any, exception: AppException) -> None:
    if obj is None:
        raise exception


def update_object(instance: Any, request: BaseModel) -> None:
    changed = False

    for field, value in request.model_dump(
        exclude_unset=True, exclude={"type"}
    ).items():
        if getattr(instance, field) != value:
            setattr(instance, field, value)
            changed = True

    if not changed:
        raise NoChangesDetectedError(HTTP400.NO_CHANGES_DETECTED)
