import pytest
from httpx import AsyncClient


async def create_dept(client: AsyncClient, name: str, parent_id: int | None = None) -> dict:
    payload = {"name": name}
    if parent_id is not None:
        payload["parent_id"] = parent_id
    r = await client.post("/departments/", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


async def create_emp(client: AsyncClient, dept_id: int, full_name: str, position: str) -> dict:
    r = await client.post(
        f"/departments/{dept_id}/employees/",
        json={"full_name": full_name, "position": position},
    )
    assert r.status_code == 201, r.text
    return r.json()


class TestCreateDepartment:

    async def test_create_root(self, client):
        r = await client.post("/departments/", json={"name": "IT"})
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "IT"
        assert data["parent_id"] is None
        assert "id" in data and "created_at" in data

    async def test_create_child(self, client):
        parent = await create_dept(client, "IT")
        r = await client.post("/departments/", json={"name": "Backend", "parent_id": parent["id"]})
        assert r.status_code == 201
        assert r.json()["parent_id"] == parent["id"]

    async def test_name_trimmed(self, client):
        r = await client.post("/departments/", json={"name": "  IT  "})
        assert r.status_code == 201
        assert r.json()["name"] == "IT"

    async def test_duplicate_name_same_parent_rejected(self, client):
        await create_dept(client, "IT")
        r = await client.post("/departments/", json={"name": "IT"})
        assert r.status_code == 409

    async def test_same_name_different_parents_allowed(self, client):
        p1 = await create_dept(client, "Parent1")
        p2 = await create_dept(client, "Parent2")
        r1 = await client.post("/departments/", json={"name": "Team", "parent_id": p1["id"]})
        r2 = await client.post("/departments/", json={"name": "Team", "parent_id": p2["id"]})
        assert r1.status_code == 201
        assert r2.status_code == 201

    async def test_nonexistent_parent_rejected(self, client):
        r = await client.post("/departments/", json={"name": "IT", "parent_id": 9999})
        assert r.status_code == 404

    async def test_empty_name_rejected(self, client):
        r = await client.post("/departments/", json={"name": ""})
        assert r.status_code == 422


class TestCreateEmployee:

    async def test_create_employee(self, client):
        dept = await create_dept(client, "IT")
        r = await client.post(
            f"/departments/{dept['id']}/employees/",
            json={"full_name": "Ivan Petrov", "position": "Developer"},
        )
        assert r.status_code == 201
        data = r.json()
        assert data["full_name"] == "Ivan Petrov"
        assert data["position"] == "Developer"
        assert data["department_id"] == dept["id"]
        assert data["hired_at"] is None

    async def test_create_employee_with_hired_at(self, client):
        dept = await create_dept(client, "IT")
        r = await client.post(
            f"/departments/{dept['id']}/employees/",
            json={"full_name": "Maria Ivanova", "position": "QA", "hired_at": "2023-06-15"},
        )
        assert r.status_code == 201
        assert r.json()["hired_at"] == "2023-06-15"

    async def test_nonexistent_department_rejected(self, client):
        r = await client.post(
            "/departments/9999/employees/",
            json={"full_name": "Ivan", "position": "Dev"},
        )
        assert r.status_code == 404

    async def test_empty_full_name_rejected(self, client):
        dept = await create_dept(client, "IT")
        r = await client.post(
            f"/departments/{dept['id']}/employees/",
            json={"full_name": "", "position": "Dev"},
        )
        assert r.status_code == 422

    async def test_empty_position_rejected(self, client):
        dept = await create_dept(client, "IT")
        r = await client.post(
            f"/departments/{dept['id']}/employees/",
            json={"full_name": "Ivan", "position": ""},
        )
        assert r.status_code == 422


class TestGetDepartment:

    async def test_get_department(self, client):
        dept = await create_dept(client, "IT")
        r = await client.get(f"/departments/{dept['id']}")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "IT"
        assert "employees" in data and "children" in data

    async def test_get_nonexistent(self, client):
        r = await client.get("/departments/9999")
        assert r.status_code == 404

    async def test_include_employees_true(self, client):
        dept = await create_dept(client, "IT")
        await create_emp(client, dept["id"], "Ivan", "Dev")
        r = await client.get(f"/departments/{dept['id']}?include_employees=true")
        assert len(r.json()["employees"]) == 1

    async def test_include_employees_false(self, client):
        dept = await create_dept(client, "IT")
        await create_emp(client, dept["id"], "Ivan", "Dev")
        r = await client.get(f"/departments/{dept['id']}?include_employees=false")
        assert r.json()["employees"] == []

    async def test_depth_1_includes_direct_children_only(self, client):
        parent = await create_dept(client, "IT")
        child = await create_dept(client, "Backend", parent["id"])
        await create_dept(client, "Python Team", child["id"])

        r = await client.get(f"/departments/{parent['id']}?depth=1")
        data = r.json()
        assert len(data["children"]) == 1
        assert data["children"][0]["children"] == []

    async def test_depth_2_includes_grandchildren(self, client):
        parent = await create_dept(client, "IT")
        child = await create_dept(client, "Backend", parent["id"])
        await create_dept(client, "Python Team", child["id"])

        r = await client.get(f"/departments/{parent['id']}?depth=2")
        assert len(r.json()["children"][0]["children"]) == 1

    async def test_depth_0_no_children(self, client):
        parent = await create_dept(client, "IT")
        await create_dept(client, "Backend", parent["id"])

        r = await client.get(f"/departments/{parent['id']}?depth=0")
        assert r.json()["children"] == []

    async def test_depth_exceeds_max_rejected(self, client):
        dept = await create_dept(client, "IT")
        r = await client.get(f"/departments/{dept['id']}?depth=6")
        assert r.status_code == 422


class TestUpdateDepartment:

    async def test_rename(self, client):
        dept = await create_dept(client, "IT")
        r = await client.patch(f"/departments/{dept['id']}", json={"name": "Engineering"})
        assert r.status_code == 200
        assert r.json()["name"] == "Engineering"

    async def test_move_to_parent(self, client):
        parent = await create_dept(client, "IT")
        child = await create_dept(client, "Backend")
        r = await client.patch(f"/departments/{child['id']}", json={"parent_id": parent["id"]})
        assert r.status_code == 200
        assert r.json()["parent_id"] == parent["id"]

    async def test_make_root_by_setting_null(self, client):
        parent = await create_dept(client, "IT")
        child = await create_dept(client, "Backend", parent["id"])
        r = await client.patch(f"/departments/{child['id']}", json={"parent_id": None})
        assert r.status_code == 200
        assert r.json()["parent_id"] is None

    async def test_self_reference_rejected(self, client):
        dept = await create_dept(client, "IT")
        r = await client.patch(f"/departments/{dept['id']}", json={"parent_id": dept["id"]})
        assert r.status_code == 409

    async def test_cyclic_dependency_rejected(self, client):
        parent = await create_dept(client, "IT")
        child = await create_dept(client, "Backend", parent["id"])
        r = await client.patch(f"/departments/{parent['id']}", json={"parent_id": child["id"]})
        assert r.status_code == 409

    async def test_duplicate_name_on_rename_rejected(self, client):
        await create_dept(client, "IT")
        dept2 = await create_dept(client, "HR")
        r = await client.patch(f"/departments/{dept2['id']}", json={"name": "IT"})
        assert r.status_code == 409

    async def test_update_nonexistent(self, client):
        r = await client.patch("/departments/9999", json={"name": "New"})
        assert r.status_code == 404


class TestDeleteDepartment:

    async def test_cascade_deletes_children(self, client):
        parent = await create_dept(client, "IT")
        child = await create_dept(client, "Backend", parent["id"])

        r = await client.delete(f"/departments/{parent['id']}?mode=cascade")
        assert r.status_code == 204
        assert (await client.get(f"/departments/{parent['id']}")).status_code == 404
        assert (await client.get(f"/departments/{child['id']}")).status_code == 404

    async def test_cascade_deletes_employees(self, client):
        dept = await create_dept(client, "IT")
        await create_emp(client, dept["id"], "Ivan", "Dev")

        r = await client.delete(f"/departments/{dept['id']}?mode=cascade")
        assert r.status_code == 204

    async def test_reassign_moves_employees(self, client):
        source = await create_dept(client, "IT")
        target = await create_dept(client, "HR")
        emp = await create_emp(client, source["id"], "Ivan", "Dev")

        r = await client.delete(
            f"/departments/{source['id']}?mode=reassign&reassign_to_department_id={target['id']}"
        )
        assert r.status_code == 204
        assert (await client.get(f"/departments/{source['id']}")).status_code == 404

        target_data = (await client.get(f"/departments/{target['id']}?include_employees=true")).json()
        assert any(e["id"] == emp["id"] for e in target_data["employees"])

    async def test_reassign_without_target_rejected(self, client):
        dept = await create_dept(client, "IT")
        r = await client.delete(f"/departments/{dept['id']}?mode=reassign")
        assert r.status_code == 400

    async def test_reassign_to_same_department_rejected(self, client):
        dept = await create_dept(client, "IT")
        r = await client.delete(
            f"/departments/{dept['id']}?mode=reassign&reassign_to_department_id={dept['id']}"
        )
        assert r.status_code == 400

    async def test_reassign_nonexistent_target_rejected(self, client):
        dept = await create_dept(client, "IT")
        r = await client.delete(
            f"/departments/{dept['id']}?mode=reassign&reassign_to_department_id=9999"
        )
        assert r.status_code == 404

    async def test_delete_nonexistent(self, client):
        r = await client.delete("/departments/9999?mode=cascade")
        assert r.status_code == 404

    async def test_delete_without_mode_rejected(self, client):
        dept = await create_dept(client, "IT")
        r = await client.delete(f"/departments/{dept['id']}")
        assert r.status_code == 422


class TestHealth:

    async def test_health(self, client):
        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
