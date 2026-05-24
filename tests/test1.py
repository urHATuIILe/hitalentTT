import sys
import pytest
from datetime import date, datetime
from loguru import logger
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    EmployeeShort,
)
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
)


class TestDepartmentSchemas:

    def test_create_department_with_trim(self):
        data = DepartmentCreate(name="  IT Department  ", parent_id=None)
        assert data.name == "IT Department"
        assert data.parent_id is None
        logger.info("test_create_department_with_trim passed")

    def test_create_department_with_parent(self):
        data = DepartmentCreate(name="Backend Team", parent_id=1)
        assert data.name == "Backend Team"
        assert data.parent_id == 1
        logger.info("test_create_department_with_parent passed")

    def test_create_department_empty_name_raises_error(self):
        with pytest.raises(Exception):
            DepartmentCreate(name="", parent_id=None)
        logger.info("test_create_department_empty_name_raises_error passed")

    def test_update_department_name_only(self):
        data = DepartmentUpdate(name="  New Name  ")
        assert data.name == "New Name"
        assert data.parent_id is None
        logger.info("test_update_department_name_only passed")

    def test_update_department_parent_only(self):
        data = DepartmentUpdate(parent_id=5)
        assert data.name is None
        assert data.parent_id == 5
        logger.info("test_update_department_parent_only passed")

    def test_response_schema_has_all_fields(self):
        fields = list(DepartmentResponse.model_fields.keys())
        expected_fields = ['id', 'name', 'parent_id', 'created_at', 'employees', 'children']
        for field in expected_fields:
            assert field in fields, f"Missing field: {field}"
        logger.info(f"test_response_schema_has_all_fields passed (fields: {fields})")


class TestEmployeeSchemas:

    def test_create_employee_full(self):
        data = EmployeeCreate(
            full_name="Ivan Petrov",
            position="Senior Developer",
            hired_at=date(2023, 1, 15),
        )
        assert data.full_name == "Ivan Petrov"
        assert data.position == "Senior Developer"
        assert data.hired_at == date(2023, 1, 15)
        logger.info("test_create_employee_full passed")

    def test_create_employee_minimal(self):
        data = EmployeeCreate(
            full_name="Maria Ivanova",
            position="Junior QA",
        )
        assert data.full_name == "Maria Ivanova"
        assert data.position == "Junior QA"
        assert data.hired_at is None
        logger.info("test_create_employee_minimal passed")

    def test_create_employee_empty_name_raises_error(self):
        with pytest.raises(Exception):
            EmployeeCreate(full_name="", position="Dev")
        logger.info("test_create_employee_empty_name_raises_error passed")

    def test_create_employee_empty_position_raises_error(self):
        with pytest.raises(Exception):
            EmployeeCreate(full_name="Ivan", position="")
        logger.info("test_create_employee_empty_position_raises_error passed")


class TestRecursiveSchema:

    def test_nested_structure(self):
        emp_data = {"id": 1, "full_name": "Ivan", "position": "Dev", "created_at": datetime.utcnow()}
        employee = EmployeeShort(**emp_data)

        dept_data = {
            "id": 1,
            "name": "IT Dept",
            "parent_id": None,
            "created_at": datetime.utcnow(),
            "employees": [employee],
            "children": [],
        }
        department = DepartmentResponse(**dept_data)

        assert department.id == 1
        assert len(department.employees) == 1
        assert department.employees[0].full_name == "Ivan"
        assert len(department.children) == 0
        logger.info("test_nested_structure passed")


if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stdout, format="{message}")

    logger.info("=" * 60)
    logger.info(" RUNNING SCHEMAS TESTS ")
    logger.info("=" * 60)

    test_dept = TestDepartmentSchemas()
    test_emp = TestEmployeeSchemas()
    test_rec = TestRecursiveSchema()

    logger.info("--- Department Schemas ---")
    test_dept.test_create_department_with_trim()
    test_dept.test_create_department_with_parent()
    test_dept.test_create_department_empty_name_raises_error()
    test_dept.test_update_department_name_only()
    test_dept.test_update_department_parent_only()
    test_dept.test_response_schema_has_all_fields()

    logger.info("--- Employee Schemas ---")
    test_emp.test_create_employee_full()
    test_emp.test_create_employee_minimal()
    test_emp.test_create_employee_empty_name_raises_error()
    test_emp.test_create_employee_empty_position_raises_error()

    logger.info("--- Recursive Schema ---")
    test_rec.test_nested_structure()

    logger.info("=" * 60)
    logger.info(" ALL TESTS PASSED ")
    logger.info("=" * 60)