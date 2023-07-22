"""
    Authentication and Registration endpoints
"""

import sqlite3
from fastapi import HTTPException, status
from pydantic import BaseModel

from api.endpoints.user import user_router, User, get_token, check_email
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


@user_router.post("/auth")
async def authenticate_user(credentials: AuthRequest) -> AuthResponse:
    """Authenticate user using given email and password"""
    try:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        existence_exception = HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist",
        )

        check_email(credentials.email)
        user = users_db.get_user(credentials.email)

        if user is None:
            raise existence_exception
        if get_pass_hash(credentials.password, user.salt) == user.password_hash:
            return AuthResponse(
                token=user.token,
                user=UserResponse(id=user.id, email=user.email, schoolId=user.school_id),
            )
        raise credentials_exception

    except sqlite3.Error as error:
        connection_exception = HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not connect to Users Database",
        )
        print("Failed to connect to sqlite3 database, error: ", error)
        raise connection_exception


@user_router.post("/register", status_code=201)
async def register_user(user: UserRequest) -> AuthResponse:
    """Register a new user with given data"""
    try:
        duplicate_exception = HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

        db_user = users_db.get_user(user.email)
        if db_user is None:
            check_email(user.email)

            user_id = users_db.add_user(user)

            token = get_token(user_id, user.email)
            users_db.add_token(user_id, token)

            db_user = users_db.get_user(user.email)

            return AuthResponse(
                token=token,
                user=UserResponse(
                    id=db_user.id, email=db_user.email, schoolId=db_user.school_id
                ),
            )
        raise duplicate_exception

    except sqlite3.Error as error:
        connection_exception = HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not connect to Users Database",
        )
        print("Failed to connect to sqlite3 database, error: ", error)
        raise connection_exception
