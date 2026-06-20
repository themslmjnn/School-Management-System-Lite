from fastapi import HTTPException

from models.users import UserRole


MESSAGE_403 = "Access denied"


def require_admin(user) -> None:
    if user["role"] != UserRole.admin:
        raise HTTPException(status_code=403, detail=MESSAGE_403)


def require_user(user, user_id) -> None:
    if user["id"] != user_id:
        raise HTTPException(status_code=403, detail=MESSAGE_403)


def require_director(user) -> None:
    if user["role"] not in (UserRole.director, UserRole.vice_director):
        raise HTTPException(status_code=403, detail=MESSAGE_403)


def require_teacher(user) -> None:
    if user["role"] != UserRole.teacher:
        raise HTTPException(status_code=403, detail=MESSAGE_403)


def ensure_exists(object, message) -> None:
    if object is None:
        raise HTTPException(status_code=404, detail=message)


def update_object(instance, request) -> None:
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)


def hash_password(password, bcrypt_context) -> str:
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password, bcrypt_context) -> None:
    if not bcrypt_context.verify(plain_password, hashed_password):
        raise HTTPException(status_code=400, detail="Invalid old password")
