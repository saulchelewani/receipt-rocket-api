import uuid

import pytest
from sqlalchemy.orm import Session

from core.models import Role, Tenant
from tests.conftest import client


@pytest.fixture
def test_role(test_db: Session, ):
    db_role = Role(name='test_role')
    test_db.add(db_role)
    test_db.commit()
    test_db.refresh(db_role)
    return db_role


@pytest.fixture
def test_tenant(test_db: Session):
    db_tenant = Tenant(name='Test Tenant', code=str(uuid.uuid4()))
    test_db.add(db_tenant)
    test_db.commit()
    test_db.refresh(db_tenant)
    return db_tenant


def test_create_user(client, auth_header, test_role: Role):
    response = client.post('/api/v1/users',
                           json={'email': 'test@example.com', "name": "John Doe", "phone_number": "0886265490",
                                 "password": "password",
                                 'role_id': str(test_role.id)},
                           headers=auth_header)
    assert response.status_code == 201
    assert response.json()['email'] == 'test@example.com'


def test_create_admin(client, auth_header_global_admin, test_role: Role, test_tenant: Tenant):
    response = client.post(f"/api/v1/tenants/{test_tenant.id}/users",
                           json={'email': 'test@example.com', "name": "John Doe", "phone_number": "0886265490",
                                 "password": "password",
                                 'role_id': str(test_role.id)},
                           headers=auth_header_global_admin)
    assert response.status_code == 201
    assert response.json()['email'] == 'test@example.com'


def test_list_all_users(client, auth_header_global_admin):
    response = client.get("/api/v1/users/", headers=auth_header_global_admin)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_create_user_already_exists(client, auth_header, test_role: Role, test_user):
    response = client.post('/api/v1/users',
                           json={'email': test_user.email, 'name': 'John Doe', "phone_number": "0886265490",
                                 "password": "password",
                                 'role_id': str(test_role.id)},
                           headers=auth_header)
    assert response.status_code == 400
    assert response.json()['detail'] == 'Email already registered'


def test_list_users_no_tenant(client, auth_header_global_admin):
    response = client.get("/api/v1/users/", headers=auth_header_global_admin)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_users_for_tenant(client, auth_header_admin):
    response = client.get("/api/v1/users", headers=auth_header_admin)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_local_admin_cannot_create_global_admin(client, auth_header_admin, test_global_admin):
    response = client.post("/api/v1/users",
                           json={'email': 'test@example.com', 'name': 'John Doe', "phone_number": "0886265490",
                                 "password": "password",
                                 'role_id': str(test_global_admin.id)},
                           headers=auth_header_admin)
    assert response.status_code == 403


def test_create_tenant_user_with_global_admin_privilege(client, auth_header_global_admin, test_global_admin,
                                                        test_tenant):
    response = client.post("/api/v1/users",
                           json={'email': 'test@example.com', 'name': 'John Doe', "phone_number": "0886265490",
                                 "password": "password",
                                 'role_id': str(test_global_admin.id), 'tenant_id': str(test_tenant.id)},
                           headers=auth_header_global_admin)
    assert response.status_code == 403


def test_delete_user(client, auth_header_admin, test_tenant, test_db, test_role):
    user = User(tenant_id=test_tenant.id, role_id=test_role.id, name='John Doe', email='e@i.com',
                phone_number='0886265490')
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    response = client.delete(f"/api/v1/users/{user.id}", headers=auth_header_admin)
    assert response.status_code == 204


def test_delete_user_not_found(client, auth_header_admin):
    response = client.delete(f"/api/v1/users/{uuid.uuid4()}", headers=auth_header_admin)
    assert response.status_code == 404


# tests/users/test_routes.py

from uuid import uuid4

from fastapi.testclient import TestClient
from starlette import status

from core.models import User


def test_read_user_by_id_as_tenant_user(
        client: TestClient, test_user: User, test_tenant: Tenant, auth_header_tenant_admin: dict[str, str]
):
    """
    Tests that a tenant user can fetch another user from the same tenant.
    """
    response = client.get(f"/api/v1/users/{test_user.id}", headers=auth_header_tenant_admin)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == str(test_user.id)
    assert data["email"] == test_user.email


def test_read_user_by_id_not_found(
        client: TestClient, auth_header_tenant_admin: dict
):
    """
    Tests that a 404 is returned for a non-existent user ID.
    """
    non_existent_id = uuid4()
    response = client.get(f"/api/vi/users/{non_existent_id}", headers=auth_header_tenant_admin)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Not Found"
