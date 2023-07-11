import jwt
from fastapi import APIRouter, Depends, Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing_extensions import Annotated

secret_key = "temporary_secret_key_73857982"

user_router = APIRouter(prefix='/user', tags=[""])

class User(BaseModel):
    email: str = ""
    schoolId: int = 0

def get_token(id, email):
    payload = {
        "sub": { "id": id, "email": email },
        "exp": None
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

# FIXME: the method doesn't work, needs debugging and fixing
async def get_current_user(token: str = Security(APIKeyHeader(name="Authorization"))):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_data = None
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        user_data = payload.get("sub")
        if user_data is None:
            raise credentials_exception
        token_data = TokenData()
    # TODO: refactor exceptions handling
    except Exception as error:
        print(error)
        raise credentials_exception
    # TODO: fetch user from DB
    # TODO: handle user related errors e.g.
    # if user is None:
    #    raise credentials_exception
    return user_data

import api.endpoints.user.auth
import api.endpoints.user.school
