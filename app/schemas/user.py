import datetime as dt

from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserCreate(BaseModel):
    email: str = Field(pattern=EMAIL_PATTERN, max_length=255)
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    birth_date: dt.date

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()

    @field_validator("birth_date")
    @classmethod
    def must_be_adult(cls, value: dt.date) -> dt.date:
        today = dt.date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise ValueError("Debes ser mayor de 18 años para usar la aplicación")
        return value


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    birth_date: dt.date
    created_at: dt.datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
