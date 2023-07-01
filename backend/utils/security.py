import datetime as dt
from typing import Any, Annotated
from pydantic import BaseModel

from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
import jose
import jose.jwt

from utils.util import settings
from data.db.client import mongo_client
from data.models.user import User, UserTypeEnum

## Password hasing related
class HashUtil:
    pwd_context = CryptContext(schemes=settings["HASH.CYRPTCONTEXT.SCHEMES"].split(","), deprecated='auto')

    @staticmethod
    def get_password_hash(password: str) -> str:
        return HashUtil.pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return HashUtil.pwd_context.verify(plain_password, hashed_password)

## Json Web Token related
class JWTUtil:

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/login")
    SECRET_KEY = settings["JWT.JWT_SECRET_KEY"]
    ALGORITHM = settings["JWT.ALGORITHM"]
    ACCESS_TOKEN_EXPIRE_MINUTES = int(settings["JWT.ACCESS_TOKEN_EXPIRE_MINUTES"])

    class TokenModel(BaseModel):
        access_token: str
        token_type: str

    @staticmethod
    def generate_access_token(data: dict, expires_delta: dt.timedelta | None = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = dt.datetime.utcnow() + expires_delta
        else:
            expire = dt.datetime.utcnow() + dt.timedelta(minutes=JWTUtil.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({ "exp": expire })
        encoded_jwt = jose.jwt.encode(to_encode, JWTUtil.SECRET_KEY, algorithm=JWTUtil.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def parse_access_token(token: str) -> dict[str, Any]:
        try:
            payload = jose.jwt.decode(token, JWTUtil.SECRET_KEY, algorithms=[JWTUtil.ALGORITHM])
            return payload
        except jose.JWTError:
            return dict({})
        
    @staticmethod
    async def get_current_user(token: str = Depends(oauth2_scheme)):
        payload = JWTUtil.parse_access_token(token)
        username: str = payload.get("sub") or "" if payload else ""
        user_in_db = await mongo_client.user.find_one({"username": username}, {"password": 0}) if username else None
        if (user_in_db and not user_in_db["disabled"]):
            return user_in_db
        else:
            return None
        
# User Auth related
class UserUtil:
        
    @staticmethod
    async def is_owner(user: User = Depends(JWTUtil.get_current_user)):
        if not user or not user["type"] == UserTypeEnum.owner:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    @staticmethod
    async def is_atleast_admin(user: User = Depends(JWTUtil.get_current_user)):
        if not user or not user["type"] in (UserTypeEnum.admin, UserTypeEnum.owner):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    @staticmethod
    async def is_authenticated(user: User = Depends(JWTUtil.get_current_user)):
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)