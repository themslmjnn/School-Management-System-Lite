from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.schemas import ActivateAccountWithToken, LoginResponse
from src.auth.service import AuthService
from src.core.dependencies import async_db_dependency, current_user_dependency
from src.core.limiter import ip_limiter

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
@ip_limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    db: async_db_dependency,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    return await AuthService.login(db, response, form_data)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    db: async_db_dependency,
    current_user: current_user_dependency,
):
    await AuthService.logout(response, db, current_user.id)

@router.post("/activate_with_token", status_code=status.HTTP_204_NO_CONTENT)
@ip_limiter.limit("3/minute")
async def activate_with_token(
    request: Request,
    db: async_db_dependency,
    activation_request: ActivateAccountWithToken,
):
    await AuthService.activate_account_with_token(db, activation_request)