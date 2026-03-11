from fastapi import HTTPException


MESSAGE_403 = "Access denied"


def require_admin(user) -> None:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail=MESSAGE_403)
    

def require_user(user, user_id) -> None:
    if user["id"] != user_id:
        raise HTTPException(status_code=403, detail=MESSAGE_403)
    

def require_director(user) -> None:
    if user["role"] not in ("director", "vice_director"):
        raise HTTPException(status_code=403, detail=MESSAGE_403)
    

def require_teacher(user) -> None:
    if user["role"] != "teacher":
        raise HTTPException(status_code=403, detail=MESSAGE_403)
    

def require_existence(object, message) -> None:
    if object is None:
        raise HTTPException(status_code=404, detail=message)
     

def update_object(instance, request) -> None:
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(instance, field, value)


def hash_password(password, bcrypt_context):
    return bcrypt_context.hash(password)


def verify_password(user, user_password_request, bcrypt_context) -> None:
    if not bcrypt_context.verify(user_password_request.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid old password")