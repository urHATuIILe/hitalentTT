from typing import Optional

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentBriefResponse,
)
from app.services.department_service import DepartmentService

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("/", response_model=DepartmentBriefResponse, status_code=201)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
):
    return await DepartmentService(db).create_department(data)


@router.get("/{id}", response_model=DepartmentResponse)
async def get_department(
    id: int,
    depth: int = Query(1, ge=0, le=5, description="Глубина вложенных подразделений"),
    include_employees: bool = Query(True, description="Включать ли сотрудников"),
    sort_employees_by: str = Query(
        "created_at",
        pattern="^(created_at|full_name)$",
        description="Сортировка сотрудников: created_at или full_name",
    ),
    db: AsyncSession = Depends(get_db),
):
    return await DepartmentService(db).get_department(id, depth, include_employees, sort_employees_by)


@router.patch("/{id}", response_model=DepartmentBriefResponse)
async def update_department(
    id: int,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
):
    return await DepartmentService(db).update_department(id, data)


@router.delete("/{id}", status_code=204)
async def delete_department(
    id: int,
    mode: str = Query(..., pattern="^(cascade|reassign)$", description="Режим удаления"),
    reassign_to_department_id: Optional[int] = Query(
        None,
        description="ID подразделения для перемещения сотрудников (при mode=reassign)",
    ),
    db: AsyncSession = Depends(get_db),
):
    await DepartmentService(db).delete_department(id, mode, reassign_to_department_id)
    return Response(status_code=204)
