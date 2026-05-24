from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class EmployeeBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200, description="ФИО сотрудника")
    position: str = Field(..., min_length=1, max_length=200, description="Должность")

    @field_validator("full_name", mode="before")
    @classmethod
    def trim_full_name(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("position", mode="before")
    @classmethod
    def trim_position(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v


class EmployeeCreate(EmployeeBase):
    hired_at: Optional[date] = Field(None, description="Дата найма")


class EmployeeResponse(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department_id: int
    hired_at: Optional[date] = None
    created_at: datetime
