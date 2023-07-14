import jwt
from fastapi import APIRouter, Depends, Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing_extensions import Annotated
from api.db.users import UsersDB
from api.endpoints.user.auth import check_email

secret_key = "temporary_secret_key_73857982"

user_router = APIRouter(prefix='/user', tags=[""])

class User(BaseModel):
    id: int
    email: str = ""
    schoolId: int = 0

def get_token(id, email):
    payload = {
        "sub": { "id": id, "email": email },
        "exp": None
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

class TokenData(BaseModel):
    id: int
    email: str


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
        token_data = TokenData(user_data)

    # TODO: refactor exceptions handling
    except Exception as error:
        print(error)
        raise credentials_exception

    check_email(token_data.email)
    db_user = UsersDB.get_user(token_data.email)
    if db_user is None:
        raise credentials_exception

    return User(id=db_user.id, email=db_user.email, schoolId=db_user.school_id)

import api.endpoints.user.auth
import api.endpoints.user.school
