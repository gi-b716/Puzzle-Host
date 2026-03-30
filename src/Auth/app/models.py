from typing import Optional
from sqlalchemy import text
from sqlmodel import SQLModel, Field


class Token(SQLModel):
    access_token: str
    token_type: str


class UserInfo(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)


class User(UserInfo, table=True):
    __tablename__ = "users"

    password_hash: str
    token_version: int = Field(
        default=1, sa_column_kwargs={"server_default": text("1")}
    )


class UserAuth(SQLModel):
    username: str
    password: str


class ResetPassword(SQLModel):
    password: str
    new_password: str
