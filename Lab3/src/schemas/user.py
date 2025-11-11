from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List


class UserBase(BaseModel):
    """Базовая схема пользователя"""
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    full_name: Optional[str] = Field(None, max_length=100, description="Полное имя")
    is_active: bool = Field(default=True, description="Активен ли пользователь")


class UserCreate(UserBase):
    """Схема для создания пользователя"""
    pass


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Имя пользователя")
    email: Optional[EmailStr] = Field(None, description="Email пользователя")
    full_name: Optional[str] = Field(None, max_length=100, description="Полное имя")
    is_active: Optional[bool] = Field(None, description="Активен ли пользователь")

    model_config = ConfigDict(extra="forbid")


class UserResponse(UserBase):
    """Схема для ответа с данными пользователя"""
    id: int = Field(..., description="ID пользователя")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата последнего обновления")

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    total: int
    items: List[UserResponse]
