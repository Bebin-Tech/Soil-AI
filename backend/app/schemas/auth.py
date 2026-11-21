from typing import Literal
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)


class Register(StrictModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=12, max_length=128)
    language: Literal['en', 'ta'] = 'en'


class Login(StrictModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class Refresh(StrictModel):
    refresh_token: str = Field(min_length=30, max_length=500)


class Profile(StrictModel):
    name: str = Field(min_length=2, max_length=100)
    language: Literal['en', 'ta'] = 'en'


class Forgot(StrictModel):
    email: EmailStr


class Reset(StrictModel):
    token: str = Field(min_length=30, max_length=500)
    password: str = Field(min_length=12, max_length=128)
