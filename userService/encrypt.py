from passlib.hash import sha256_crypt
import jwt
from config import encryption_config

from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


def encrypt_password(password: str) -> str:
    return sha256_crypt.hash(password)


def check_password(password: str, hashed_password: str) -> bool:
    return sha256_crypt.verify(password, hashed_password)


def create_token(id: int, role: str) -> str:
    user_dict = {"id": id, "role": role}
    token = jwt.encode(
        user_dict,
        encryption_config["SECRET_KEY"],
        encryption_config["ALGORITHM"]
    )
    return token


def decode_token(token: str) -> dict:
    user_dict = jwt.decode(
        token,
        encryption_config["SECRET_KEY"],
        algorithms=[encryption_config["ALGORITHM"]]
    )
    return user_dict


def get_user_from_token(token: str) -> list[int, str]:
    decoded = decode_token(token)
    return decoded["id"], decoded["role"]