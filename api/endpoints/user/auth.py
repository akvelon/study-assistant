import sqlite3
from fastapi import APIRouter, Response, HTTPException
from pydantic import BaseModel
import os

from api.endpoints.user import user_router, User, get_token
from api.db.users import users_db, get_pass_hash


class UserRequest(BaseModel):
    email: str
    password: str
    schoolId: int = 0   

class UserResponse(User):
    pass

class AuthRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    token: str
    user: UserResponse


def check_email(email: str):
    # TODO: implement email checking
    # Should raise HTTPException with proper status code
    pass

@user_router.post("/auth")
async def authenticate_user(credentials: AuthRequest) -> AuthResponse:
    try:
        check_email(credentials.email)
        user = users_db.get_user(credentials.email)

        # TODO: check if user is None

        if get_pass_hash(credentials.password, user.salt) == user.password_hash:
            return AuthResponse(token=user.token, user=UserResponse(email=user.email, schoolId=user.school_id))
        else:
            # TODO: use status from fastapi e.g. status.500_...
            raise HTTPException(status_code=401, detail="Invalid Credentials")

    except sqlite3.Error as error:
        print("Failed to connect to sqlite3 database, error: ", error)
        # TODO: use status from fastapi e.g. status.500_...
        raise HTTPException(status_code=500, detail="Could not connect to Users Database")


@user_router.post('/register', status_code=201)
async def register_user(user: UserRequest) -> AuthResponse:
    try:
        db_user = users_db.get_user(user.email)
        if db_user is None:
            check_email(user.email)

            user_id = users_db.add_user(user)

            token = get_token(user_id, user.email)
            users_db.add_token(user_id, token)

            db_user = users_db.get_user(user.email)
    
            return AuthResponse(token=token, user=UserResponse(email=db_user.email, schoolId=db_user.school_id))
        else:
            # TODO: use status from fastapi e.g. status.500_...
            raise HTTPException(status_code=409, detail="User already exists")

    except sqlite3.Error as error:
        print("Failed to connect to sqlite3 database, error: ", error)
        # TODO: use status from fastapi e.g. status.500_...
        raise HTTPException(status_code=500, detail="Could not connect to Users Database")