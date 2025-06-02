import uuid

import pytest
from sqlalchemy.orm import Session

from core.models import Role, Tenant, User
from core.settings import settings
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
                           json={'email': 'test@example.com', "name": "John Doe", 'password': settings.TEST_SECRET,
                                 'role_id': str(test_role.id)},
                           headers=auth_header)
    assert response.status_code == 201
    assert response.json()['email'] == 'test@example.com'


def test_create_admin(client, auth_header_global_admin, test_role: Role, test_tenant: Tenant):
    response = client.post(f"/api/v1/tenants/{test_tenant.id}/users",
                           json={'email': 'test@example.com', "name": "John Doe", 'password': settings.TEST_SECRET,
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
                           json={'email': test_user.email, 'name': 'John Doe', 'password': settings.TEST_SECRET,
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
                           json={'email': 'test@example.com', 'name': 'John Doe', 'password': settings.TEST_SECRET,
                                 'role_id': str(test_global_admin.id)},
                           headers=auth_header_admin)
    assert response.status_code == 403


def test_create_tenant_user_with_global_admin_privilege(client, auth_header_global_admin, test_global_admin,
                                                        test_tenant):
    response = client.post("/api/v1/users",
                           json={'email': 'test@example.com', 'name': 'John Doe', 'password': settings.TEST_SECRET,
                                 'role_id': str(test_global_admin.id), 'tenant_id': str(test_tenant.id)},
                           headers=auth_header_global_admin)
    assert response.status_code == 403


def test_delete_user(client, auth_header_admin, test_tenant, test_db, test_role):
    user = User(tenant_id=test_tenant.id, role_id=test_role.id, name='John Doe', email='e@i.com')
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    response = client.delete(f"/api/v1/users/{user.id}", headers=auth_header_admin)
    assert response.status_code == 204


def test_delete_user_not_found(client, auth_header_admin):
    response = client.delete(f"/api/v1/users/{uuid.uuid4()}", headers=auth_header_admin)
    assert response.status_code == 404
