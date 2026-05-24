from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.employee import EmployeeCreate, EmployeeResponse
from app.services.employee_service import EmployeeService

router = APIRouter(tags=["Employees"])


@router.post("/departments/{id}/employees/", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    id: int,
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
):
    return await EmployeeService(db).create_employee(id, data)
