import re
import jwt
from fastapi import APIRouter, Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from api.db.users import users_db

SECRET_KEY = "temporary_secret_key_73857982"

user_router = APIRouter(prefix='/user', tags=[""])

class User(BaseModel):
    id: int
    email: str = ""
    schoolId: int = 0

def get_token(id, email):
    """Create token for given user data"""
    payload = {
        "sub": { "id": id, "email": email },
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

class TokenData(BaseModel):
    """Data available in token"""
    id: int
    email: str

def check_email(email: str):
    """
        Email structure: local_part@domain_part
        Structure of local_part: Any alphanumeric characters, including:
          . ! # $ % & \ ' * + / = ? ^ _ ` { | } ~ -
        Structure of domain_part: Any alphanumeric characters, sections
        separated by a .
    """
    pattern = r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$'
    if re.match(pattern, email):
        return
    email_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Malformed Email",
    )
    raise email_exception


async def get_current_user(token: str = Security(APIKeyHeader(name="Authorization"))):
    """Check the Authorization header is valid and return back user from db"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_data = None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms="HS256")
        user_data = payload.get("sub")
        if user_data is None:
            raise credentials_exception
        token_data = TokenData(id=user_data.get("id"), email=user_data.get("email"))

    except Exception as error:
        print(error)
        raise credentials_exception

    check_email(token_data.email)
    db_user = users_db.get_user(token_data.email)
    if db_user is None:
        raise credentials_exception

    return User(id=db_user.id, email=db_user.email, schoolId=db_user.school_id)

import api.endpoints.user.auth
import api.endpoints.user.school
