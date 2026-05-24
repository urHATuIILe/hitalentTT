from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.employee import Employee
from app.repositories.department_repo import DepartmentRepository
from app.repositories.employee_repo import EmployeeRepository
from app.schemas.employee import EmployeeCreate, EmployeeResponse
from app.utils.exceptions import DepartmentNotFoundError


class EmployeeService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dept_repo = DepartmentRepository(session)
        self.emp_repo = EmployeeRepository(session)

    async def create_employee(self, department_id: int, data: EmployeeCreate) -> EmployeeResponse:
        logger.info(f"Creating employee in department_id={department_id}: full_name={data.full_name}")

        department = await self.dept_repo.get_by_id(department_id)
        if department is None:
            raise DepartmentNotFoundError(department_id)

        employee = Employee(
            department_id=department_id,
            full_name=data.full_name,
            position=data.position,
            hired_at=data.hired_at,
        )
        employee = await self.emp_repo.create(employee)

        logger.info(f"Employee created: id={employee.id}")
        return EmployeeResponse.model_validate(employee)
