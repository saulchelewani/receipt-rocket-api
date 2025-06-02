import uuid

from fastapi import status
from sqlalchemy.orm import Session

from core.models import Role, Route
from tests.conftest import create_role
from tests.test_routes import create_route


def test_create_role(auth_header_global_admin, client):
    role_data = {"name": "test_role", "description": "A test role"}
    response = client.post("/api/v1/roles/", json=role_data, headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "test_role"
    assert response.json()["description"] == "A test role"


def test_list_roles(auth_header_global_admin, client):
    response = client.get("/api/v1/roles/", headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "global_admin"


# def create_multiple_

def test_assign_routes_to_role(auth_header_global_admin, test_db: Session, client):
    route1 = create_route(test_db, "/test_route1", "GET")
    route2 = create_route(test_db, path="/test_route2", method="POST")

    role = test_db.query(Role).filter(Role.name == "test_role").first()
    if not role: role = create_role(test_db, "test_role")

    route_ids = [str(route1.id), str(route2.id)]
    response = client.put(f"/api/v1/roles/{role.id}/routes", json=route_ids, headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_200_OK

    # Verify routes are assigned in the database
    db_role = test_db.query(Role).filter(Role.id == role.id).first()
    assert len(db_role.routes) == 2
    assert route1 in db_role.routes
    assert route2 in db_role.routes


def test_assign_routes_to_role_not_found(auth_header_global_admin, client):
    response = client.put(f"/api/v1/roles/{uuid.uuid4()}/routes", json=[str(uuid.uuid4()), str(uuid.uuid4())],
                          headers=auth_header_global_admin)  # Non-existent role ID
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Role not found"


def test_remove_routes_from_role(auth_header_global_admin, test_db: Session, client):
    route1 = create_route(test_db, "/test_route1", "GET")
    route2 = create_route(test_db, path="/test_route2", method="POST")
    role = test_db.query(Role).filter(Role.name == "test_role").first()
    if not role: role = create_role(test_db, "test_role")
    role.routes = [route1, route2]
    test_db.commit()
    test_db.refresh(role)
    response = client.delete(f"/api/v1/roles/{role.id}/routes/{route1.id}", headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_assign_non_existent_routes_to_role(auth_header_global_admin, test_db: Session, client):
    role = test_db.query(Role).filter(Role.name == "test_role").first()
    if not role: role = create_role(test_db, "test_role")

    response = client.put(f"/api/v1/roles/{role.id}/routes", json=[str(uuid.uuid4()), str(uuid.uuid4())],
                          headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_role_with_routes(auth_header_global_admin, test_db: Session, client):
    route1 = create_route(test_db, path="/test_route1", method="GET")
    route2 = create_route(test_db, path="/test_route2", method="POST")

    role = test_db.query(Role).filter(Role.name == "test_role").first()
    if not role: role = create_role(test_db, "test_role")

    role.routes = [route1, route2]
    test_db.commit()
    test_db.refresh(role)

    response = client.get(f"/api/v1/roles/{role.id}", headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(role.id)
    assert response.json()["name"] == role.name
    assert len(response.json()["routes"]) == 2


def test_get_role_with_routes_not_found(auth_header_global_admin, client):
    response = client.get(f"/api/v1/roles/{uuid.uuid4()}", headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Role not found"


def test_delete_route_role_not_found(auth_header_global_admin, test_db: Session, client):
    response = client.delete(f"/api/v1/roles/{uuid.uuid4()}/routes/{uuid.uuid4()}", headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Role not found"


def test_delete_route_not_found(auth_header_global_admin, test_db: Session, client, test_role: Role):
    response = client.delete(f"/api/v1/roles/{test_role.id}/routes/{uuid.uuid4()}", headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Route not found"


def test_delete_route_role_not_assigned(auth_header_global_admin, test_db: Session, client, test_role: Role,
                                        test_route: Route):
    response = client.delete(f"/api/v1/roles/{test_role.id}/routes/{test_route.id}", headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Route is not assigned to role"


def test_create_duplicate_role(auth_header_global_admin, test_db: Session, client, test_role: Role):
    response = client.post("/api/v1/roles/", json={"name": test_role.name, "description": test_role.description},
                           headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Role already exists"


def test_delete_role(auth_header_global_admin, test_db: Session, client, test_role: Role):
    response = client.delete(f"/api/v1/roles/{test_role.id}", headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_update_role(auth_header_global_admin, test_db: Session, client, test_role: Role):
    response = client.patch(f"/api/v1/roles/{test_role.id}",
                            json={"name": "new_name", "description": "new_description"},
                            headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "new_name"
    assert response.json()["description"] == "new_description"


def test_delete_protected_role(client, auth_header_global_admin, test_admin_user):
    response = client.delete(f"/api/v1/roles/{test_admin_user.role_id}", headers=auth_header_global_admin)
    assert response.status_code == 400


def test_delete_role_not_found(client, auth_header_global_admin):
    response = client.delete(f"/api/v1/roles/{uuid.uuid4()}", headers=auth_header_global_admin)
    assert response.status_code == 404


def test_update_role_not_found(client, auth_header_global_admin):
    response = client.patch(f"/api/v1/roles/{uuid.uuid4()}",
                            json={'name': 'head'},
                            headers=auth_header_global_admin)
    assert response.status_code == 404
