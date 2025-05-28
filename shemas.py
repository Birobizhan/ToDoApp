
from pydantic import BaseModel, EmailStr, field_validator
from models import task_status
from datetime import datetime, date


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr


class ToDoCreate(BaseModel):
    title: str
    plan_date: str
    status: task_status
    description: str | None

    @field_validator('plan_date')
    def validate_plan_date(cls, value):
        if datetime.strptime(value, '%d.%m.%Y').date() < date.today():
            raise ValueError('Дата должна быть в будущем')
        return datetime.strptime(value, '%d.%m.%Y').date()


class ToDoResponse(BaseModel):
    title: str
    created: datetime
    status: task_status
    description: str | None


class ToDoUpdate(BaseModel):
    title: str | None
    plan_date: str | None
    status: task_status | None
    description: str | None

    @field_validator('plan_date')
    def validate_plan_date(cls, value):
        if datetime.strptime(value, '%d.%m.%Y').date() < date.today():
            raise ValueError('Дата должна быть в будущем')
        return datetime.strptime(value, '%d.%m.%Y').date()