from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.department import Department
from app.models.employee import Employee
from app.repositories.base import BaseRepository


class DepartmentRepository(BaseRepository[Department]):
    def __init__(self, session: AsyncSession):
        super().__init__(Department, session)

    async def get_by_id_with_employees(self, dept_id: int) -> Optional[Department]:
        result = await self.session.execute(
            select(Department)
            .where(Department.id == dept_id)
            .options(selectinload(Department.employees))
        )
        return result.scalars().first()

    async def get_by_id_with_children(self, dept_id: int) -> Optional[Department]:
        result = await self.session.execute(
            select(Department)
            .where(Department.id == dept_id)
            .options(selectinload(Department.children))
        )
        return result.scalars().first()

    async def get_by_id_full(self, dept_id: int) -> Optional[Department]:
        result = await self.session.execute(
            select(Department)
            .where(Department.id == dept_id)
            .options(
                selectinload(Department.employees),
                selectinload(Department.children),
            )
        )
        return result.scalars().first()

    async def get_direct_children(self, dept_id: int) -> List[Department]:
        result = await self.session.execute(
            select(Department).where(Department.parent_id == dept_id)
        )
        return list(result.scalars().all())

    async def get_siblings_with_name(
        self, name: str, parent_id: Optional[int], exclude_id: Optional[int] = None
    ) -> List[Department]:
        query = select(Department).where(
            Department.name == name,
            Department.parent_id == parent_id,
        )
        if exclude_id is not None:
            query = query.where(Department.id != exclude_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_employees_sorted(self, dept_id: int, sort_by: str = "created_at") -> List[Employee]:
        order_col = Employee.full_name.asc() if sort_by == "full_name" else Employee.created_at.asc()
        result = await self.session.execute(
            select(Employee).where(Employee.department_id == dept_id).order_by(order_col)
        )
        return list(result.scalars().all())

    async def get_employees_by_department(self, dept_id: int) -> List[Employee]:
        result = await self.session.execute(
            select(Employee).where(Employee.department_id == dept_id)
        )
        return list(result.scalars().all())

    async def reassign_employees_orm(self, from_dept_id: int, to_dept_id: int) -> None:
        employees = await self.get_employees_by_department(from_dept_id)
        for emp in employees:
            emp.department_id = to_dept_id
        await self.session.flush()

    async def get_all_children_recursive(self, dept_id: int) -> List[int]:
        ids: List[int] = []
        queue = [dept_id]
        while queue:
            current_id = queue.pop(0)
            children = await self.get_direct_children(current_id)
            for child in children:
                ids.append(child.id)
                queue.append(child.id)
        return ids

    async def cascade_delete(self, dept_id: int) -> None:
        all_child_ids = await self.get_all_children_recursive(dept_id)
        for child_id in reversed(all_child_ids):
            child = await self.get_by_id_with_employees(child_id)
            if child:
                await self.session.delete(child)
        dept = await self.get_by_id_with_employees(dept_id)
        if dept:
            await self.session.delete(dept)
        await self.session.flush()
