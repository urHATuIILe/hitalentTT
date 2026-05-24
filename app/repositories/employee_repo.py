from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.employee import Employee
from app.repositories.base import BaseRepository


class EmployeeRepository(BaseRepository[Employee]):
    def __init__(self, session: AsyncSession):
        super().__init__(Employee, session)

    async def get_by_id_with_department(self, emp_id: int) -> Optional[Employee]:
        result = await self.session.execute(
            select(Employee)
            .where(Employee.id == emp_id)
            .options(selectinload(Employee.department))
        )
        return result.scalars().first()
