from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.department import Department
from app.repositories.department_repo import DepartmentRepository
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentBriefResponse,
    EmployeeShort,
)
from app.utils.exceptions import (
    DepartmentNotFoundError,
    DuplicateDepartmentNameError,
    SelfReferenceError,
    CyclicDependencyError,
    ReassignDepartmentRequiredError,
    ReassignTargetNotFoundError,
    ReassignToSameDepartmentError,
)
from app.utils.tree import collect_subtree_ids


class DepartmentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DepartmentRepository(session)

    async def create_department(self, data: DepartmentCreate) -> DepartmentBriefResponse:
        logger.info(f"Creating department: name={data.name}, parent_id={data.parent_id}")

        if data.parent_id is not None:
            parent = await self.repo.get_by_id(data.parent_id)
            if parent is None:
                raise DepartmentNotFoundError(data.parent_id)

        siblings = await self.repo.get_siblings_with_name(data.name, data.parent_id)
        if siblings:
            raise DuplicateDepartmentNameError(data.name, data.parent_id)

        department = Department(name=data.name, parent_id=data.parent_id)
        department = await self.repo.create(department)

        logger.info(f"Department created: id={department.id}, name={department.name}")
        return DepartmentBriefResponse.model_validate(department)

    async def get_department(
        self,
        dept_id: int,
        depth: int = 1,
        include_employees: bool = True,
        sort_employees_by: str = "created_at",
    ) -> DepartmentResponse:
        logger.info(f"Getting department: id={dept_id}, depth={depth}, include_employees={include_employees}")

        department = await self.repo.get_by_id(dept_id)
        if department is None:
            raise DepartmentNotFoundError(dept_id)

        return await self._build_department_response(department, depth, include_employees, sort_employees_by)

    async def update_department(self, dept_id: int, data: DepartmentUpdate) -> DepartmentBriefResponse:
        logger.info(f"Updating department: id={dept_id}, data={data}")

        department = await self.repo.get_by_id(dept_id)
        if department is None:
            raise DepartmentNotFoundError(dept_id)

        new_name = data.name if data.name is not None else department.name

        parent_id_changed = "parent_id" in data.model_fields_set
        new_parent_id = data.parent_id if parent_id_changed else department.parent_id
        name_changed = data.name is not None

        if new_parent_id is not None and new_parent_id == dept_id:
            raise SelfReferenceError(dept_id)

        if parent_id_changed and new_parent_id is not None:
            new_parent = await self.repo.get_by_id(new_parent_id)
            if new_parent is None:
                raise DepartmentNotFoundError(new_parent_id)

        if parent_id_changed and new_parent_id is not None:
            subtree_ids = await collect_subtree_ids(self.repo, dept_id)
            if new_parent_id in subtree_ids:
                raise CyclicDependencyError(dept_id, new_parent_id)

        if name_changed or parent_id_changed:
            siblings = await self.repo.get_siblings_with_name(new_name, new_parent_id, exclude_id=dept_id)
            if siblings:
                raise DuplicateDepartmentNameError(new_name, new_parent_id)

        department.name = new_name
        department.parent_id = new_parent_id

        await self.session.flush()
        await self.session.refresh(department)

        logger.info(f"Department updated: id={department.id}")
        return DepartmentBriefResponse.model_validate(department)

    async def delete_department(
        self,
        dept_id: int,
        mode: str = "cascade",
        reassign_to_department_id: Optional[int] = None,
    ) -> None:
        logger.info(f"Deleting department: id={dept_id}, mode={mode}, reassign_to={reassign_to_department_id}")

        department = await self.repo.get_by_id(dept_id)
        if department is None:
            raise DepartmentNotFoundError(dept_id)

        if mode == "cascade":
            await self.repo.cascade_delete(dept_id)
            logger.info(f"Department {dept_id} cascade deleted")

        elif mode == "reassign":
            if reassign_to_department_id is None:
                raise ReassignDepartmentRequiredError()

            if reassign_to_department_id == dept_id:
                raise ReassignToSameDepartmentError(dept_id)

            target_dept = await self.repo.get_by_id(reassign_to_department_id)
            if target_dept is None:
                raise ReassignTargetNotFoundError(reassign_to_department_id)

            all_child_ids = await self.repo.get_all_children_recursive(dept_id)
            all_dept_ids = [dept_id] + all_child_ids

            for did in all_dept_ids:
                await self.repo.reassign_employees_orm(did, reassign_to_department_id)

            self.session.expire_all()
            department = await self.repo.get_by_id(dept_id)

            for child_id in reversed(all_child_ids):
                child = await self.repo.get_by_id(child_id)
                if child:
                    await self.session.delete(child)

            if department:
                await self.session.delete(department)

            await self.session.flush()
            logger.info(f"Department {dept_id} deleted, employees reassigned to {reassign_to_department_id}")

    async def _build_department_response(
        self,
        department: Department,
        depth: int,
        include_employees: bool,
        sort_employees_by: str,
    ) -> DepartmentResponse:
        employees_data = []
        if include_employees:
            employees = await self.repo.get_employees_sorted(department.id, sort_employees_by)
            employees_data = [EmployeeShort.model_validate(e) for e in employees]

        children_data = []
        if depth > 0:
            children = await self.repo.get_direct_children(department.id)
            for child in children:
                child_response = await self._build_department_response(
                    child, depth - 1, include_employees, sort_employees_by
                )
                children_data.append(child_response)

        return DepartmentResponse(
            id=department.id,
            name=department.name,
            parent_id=department.parent_id,
            created_at=department.created_at,
            employees=employees_data,
            children=children_data,
        )
