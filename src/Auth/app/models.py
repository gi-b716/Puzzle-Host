from typing import Optional
from sqlalchemy import text
from sqlmodel import SQLModel, Field


class UserBase(SQLModel):
    username: str = Field(unique=True, index=True)


class User(UserBase, table=True):
    __tablename__ = "users"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str
    token_version: int = Field(default=1, sa_column_kwargs={"server_default": text("1")})


class UserCreate(UserBase):
    password: str


class UserResetPassword(UserCreate):
    new_password: str


class Token(SQLModel):
    access_token: str
    token_type: str
