import os
import jwt
import bcrypt
import hashlib
import base64
from typing import Literal
from pathlib import Path
from datetime import datetime, timezone, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.db import get_session
from app.models import User

PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH", "./data/private_key.pem")
PUBLIC_KEY_PATH = os.getenv("PUBLIC_KEY_PATH", "./data/public_key.pem")


def get_kid(public_key) -> str:
    """
    提取公钥的 DER 字节流，计算 SHA-256 哈希，
    然后转成 URL 安全的 Base64 字符串作为唯一的 kid。
    """

    der_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    # 计算 SHA-256 指纹
    digest = hashlib.sha256(der_bytes).digest()
    # 截取前 16 个字节转 Base64，去掉等号填充，足够保证唯一性
    kid = base64.urlsafe_b64encode(digest[:16]).rstrip(b"=").decode("ascii")

    return f"key-{kid}"


def load_keys():
    priv_path = Path(PRIVATE_KEY_PATH)
    pub_path = Path(PUBLIC_KEY_PATH)

    priv_path.parent.mkdir(parents=True, exist_ok=True)
    pub_path.parent.mkdir(parents=True, exist_ok=True)

    if priv_path.exists() and pub_path.exists():
        with open(priv_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
            )
        with open(pub_path, "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read(),
            )
        return private_key, public_key

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    with open(priv_path, "wb") as key_file:
        key_file.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    with open(pub_path, "wb") as key_file:
        key_file.write(
            public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )

    return private_key, public_key


PRIVATE_KEY, PUBLIC_KEY = load_keys()

PRIVATE_PEM = PRIVATE_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

CURRENT_KID = get_kid(PUBLIC_KEY)

jwk_dict = RSAAlgorithm.to_jwk(PUBLIC_KEY, as_dict=True)
jwk_dict.update({"kid": CURRENT_KID, "alg": "RS256", "use": "sig"})
JWKS = {"keys": [jwk_dict]}


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


DEFAULT_ACCESS_EXPIRATION_TIME = timedelta(minutes=15)
DEFAULT_REFRESH_EXPIRATION_TIME = timedelta(days=7)


def create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode["iat"] = now
    to_encode["exp"] = now + expires_delta

    token = jwt.encode(
        to_encode,
        PRIVATE_PEM,
        algorithm="RS256",
        headers={"kid": CURRENT_KID},
    )
    return token


def create_access_token(
    user: User, expires_delta: timedelta = DEFAULT_ACCESS_EXPIRATION_TIME
) -> str:
    return create_token({"sub": user.username, "type": "access"}, expires_delta)


def create_refresh_token(
    user: User, expires_delta: timedelta = DEFAULT_REFRESH_EXPIRATION_TIME
) -> str:
    return create_token(
        {"sub": user.username, "version": user.token_version, "type": "refresh"},
        expires_delta,
    )


security = HTTPBearer()


def _unauthorized(detail: str = "Unauthorized"):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


class TokenValidator:
    def __init__(self, token_type: Literal["access", "refresh"] = "access") -> None:
        self.token_type = token_type

    async def __call__(
        self,
        credentils: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_session),
    ) -> User:
        token = credentils.credentials

        try:
            payload = jwt.decode(token, PUBLIC_KEY, algorithms=["RS256"])
        except jwt.ExpiredSignatureError:
            raise _unauthorized("Token has expired")
        except jwt.InvalidTokenError:
            raise _unauthorized("Invalid token")

        if payload.get("type") != self.token_type:
            raise _unauthorized("Invalid token type")

        username = payload.get("sub")
        if not isinstance(username, str) or not username:
            raise _unauthorized("Invalid token payload")

        result = await db.exec(select(User).where(User.username == username))
        user = result.first()

        if user is None:
            raise _unauthorized("Unknown user")

        if self.token_type == "refresh":
            token_version_payload = payload.get("version", 0)
            try:
                token_version_payload = int(token_version_payload)
            except (ValueError, TypeError):
                token_version_payload = 0

            if user.token_version < token_version_payload:
                raise _unauthorized("Token version is from the future, are you alien?")
            elif user.token_version > token_version_payload:
                raise _unauthorized("Token has been revoked")

        return user
