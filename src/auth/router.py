from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from src.auth.schemas import (
    ActivateAccountWithToken,
    ForgotPasswordPublicRequest,
    LoginResponse,
    ResetPassword,
)
from src.auth.service import AuthService
from src.core.dependencies import async_session_dependency, current_user_dependency
from src.core.limiter import ip_limiter
from src.utils.base_constant import HTTP401
from src.utils.response_schema import MessageResponse

router = APIRouter(
    prefix="/auth",
    tags=["Auth - Public"],
)


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
@ip_limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    session: async_session_dependency,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    return await AuthService.login(session, response, form_data)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session: async_session_dependency,
    current_user: current_user_dependency,
):
    await AuthService.logout(response, session, current_user.id)


@router.post("/activate_with_token", status_code=status.HTTP_204_NO_CONTENT)
@ip_limiter.limit("3/minute")
async def activate_with_token(
    request: Request,
    session: async_session_dependency,
    activation_request: ActivateAccountWithToken,
):
    await AuthService.activate_account_with_token(session, activation_request)


@router.post(
    "/refresh_token", response_model=LoginResponse, status_code=status.HTTP_200_OK
)
@ip_limiter.limit("30/minute")
async def refresh_token(
    request: Request,
    response: Response,
    session: async_session_dependency,
    refresh_token: str | None = Cookie(default=None),
    refresh_token_family: str | None = Cookie(default=None),
):
    if refresh_token is None or refresh_token_family is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=HTTP401.INVALID_REFRESH_TOKEN,
        )

    return await AuthService.refresh_token(
        session, response, refresh_token, refresh_token_family
    )


@router.post("/reset_password", status_code=status.HTTP_204_NO_CONTENT)
@ip_limiter.limit("5/minute")
async def reset_password(
    request: Request,
    session: async_session_dependency,
    update_request: ResetPassword,
):
    return await AuthService.reset_password(session, update_request)


@router.post(
    "/forgot_password", response_model=MessageResponse, status_code=status.HTTP_200_OK
)
@ip_limiter.limit("5/minute")
async def create_forgot_password_request(
    request: Request,
    session: async_session_dependency,
    forgot_password_request: ForgotPasswordPublicRequest,
):
    return await AuthService.create_forgot_password_request(session, forgot_password_request)
