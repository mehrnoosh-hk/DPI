from passlib.hash import sha256_crypt
from jose import jwt
from config import encryption_config

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def encrypt_password(password: str) -> str:
    return sha256_crypt.hash(password)


def check_password(password: str, hashed_password: str) -> bool:
    return sha256_crypt.verify(password, hashed_password)


def create_token(id: int) -> str:
    token = jwt.encode(
        {"id": id},
        encryption_config["SECRET_KEY"],
        encryption_config["ALGORITHM"]
    )
    return token


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        encryption_config["SECRET_KEY"],
        algorithms=[encryption_config["ALGORITHM"]]
    )


def get_user_id_from_token(token: str) -> int:
    return decode_token(token)["id"]