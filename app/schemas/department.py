from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v


class DepartmentCreate(DepartmentBase):
    parent_id: Optional[int] = Field(None)


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    parent_id: Optional[int] = Field(None)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip()
        return v


class EmployeeShort(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    position: str
    hired_at: Optional[date] = None
    created_at: datetime


class DepartmentResponse(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: Optional[int] = None
    created_at: datetime
    employees: List[EmployeeShort] = []
    children: List["DepartmentResponse"] = []


class DepartmentBriefResponse(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: Optional[int] = None
    created_at: datetime


DepartmentResponse.model_rebuild()
