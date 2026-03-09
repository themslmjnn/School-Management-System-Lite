from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from jose import jwt, JWTError

from passlib.context import CryptContext

from typing import Annotated

from core.config import settings


oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        username: str = payload.get('sub')
        user_id: str = payload.get('id')
        user_role: str = payload.get('role')

        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail=MESSAGE_401)
        
        return {"username": username, "id": user_id, "role": user_role}
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate user")
    

user_dependency = Annotated[dict, Depends(get_current_user)]
        

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated="auto")