import re
import uuid

from core import User


def test_list_tenants(client, test_tenant, auth_header_global_admin):
    response = client.get("/api/v1/tenants", headers=auth_header_global_admin)
    assert response.status_code == 200
    assert response.json()[0]["id"] == str(test_tenant.id)


def test_create_tenant(client, auth_header_global_admin, test_db) -> None:
    response = client.post("/api/v1/tenants", headers=auth_header_global_admin,
                           json={"name": "New Tenant", "email": "test@example.com", "admin_name": "Admin User",
                                 "phone_number": "0886265490"})
    assert response.status_code == 200
    assert response.json()["id"]
    assert re.match(r"^NT\d{4}$", response.json()["code"])
    user = test_db.query(User).filter(
        User.email == "test@example.com",
        User.tenant_id == uuid.UUID(response.json()["id"])
    ).first()
    print(user.__dict__)
    assert user is not None



def test_cannot_create_duplicate_tenant(client, auth_header_global_admin, test_tenant) -> None:
    response = client.post("/api/v1/tenants", headers=auth_header_global_admin,
                           json={"name": test_tenant.name, "code": "test", "email": "test@example.com",
                                 "admin_name": "man",
                                 "phone_number": "265886265490"})
    assert response.status_code == 400
