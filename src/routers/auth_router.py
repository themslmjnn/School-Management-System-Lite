from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from starlette import status
from typing import Annotated
from datetime import timedelta

from core.security import bcrypt_context
from database import db_dependency
from src.schemas.token_schemas import Token
from src.services.auth_services import AuthService
from src.services.token_services import create_access_token


router = APIRouter(
    tags=["Auth"]
)

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")


@router.post("/auth/token", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = AuthService.authenticate_user(db, form_data.username, form_data.password, bcrypt_context)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")
    
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))

    return {"access_token": token, "token_type": "bearer"}