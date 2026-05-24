from fastapi import HTTPException, status


class DepartmentNotFoundError(HTTPException):
    def __init__(self, dept_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with id={dept_id} not found",
        )


class DuplicateDepartmentNameError(HTTPException):
    def __init__(self, name: str, parent_id: int | None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Department with name='{name}' already exists under parent_id={parent_id}",
        )


class SelfReferenceError(HTTPException):
    def __init__(self, dept_id: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Department cannot be a parent of itself (id={dept_id})",
        )


class CyclicDependencyError(HTTPException):
    def __init__(self, dept_id: int, target_parent_id: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Moving department id={dept_id} under id={target_parent_id} would create a cycle",
        )


class ReassignDepartmentRequiredError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="reassign_to_department_id is required when mode=reassign",
        )


class ReassignTargetNotFoundError(HTTPException):
    def __init__(self, dept_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reassign target department with id={dept_id} not found",
        )


class ReassignToSameDepartmentError(HTTPException):
    def __init__(self, dept_id: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reassign employees to the department being deleted (id={dept_id})",
        )
