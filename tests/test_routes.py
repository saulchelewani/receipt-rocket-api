import uuid

import pytest
from fastapi import status
from sqlalchemy.orm import Session

from core.models import Route


@pytest.fixture
def test_route(test_db: Session):
    return create_route(test_db, "/test_path", "GET")


def create_route(test_db: Session, path: str, method: str, action: str = "allow"):
    route = Route(path=path, method=method, action=action, name=f"{method}:{path}")
    test_db.add(route)
    test_db.commit()
    test_db.refresh(route)
    return route


def test_create_route(auth_header_global_admin, client):
    route_data = {"path": "/test_path", "method": "GET", "action": "Test action"}
    response = client.post("/api/v1/routes/", json=route_data, headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["path"] == "/test_path"
    assert response.json()["method"] == "GET"


def test_create_existing_route(auth_header_global_admin, client):
    route_data = {"path": "/test_path", "method": "GET", "action": "Test action"}
    client.post("/api/v1/routes/", json=route_data, headers=auth_header_global_admin)
    response = client.post("/api/v1/routes/", json=route_data, headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Route already registered" in response.json()["detail"]


def test_create_route_not_global_admin(auth_header, client):
    route_data = {"path": "/test_path", "method": "GET"}
    response = client.post("/api/v1/routes/", json=route_data, headers=auth_header)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_route_admin_not_global(auth_header_admin, client):
    route_data = {"path": "/test_path", "method": "GET"}
    response = client.post("/api/v1/routes/", json=route_data, headers=auth_header_admin)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_routes(client, auth_header_global_admin, test_route):
    response = client.get(f"/api/v1/routes/", headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["path"] == "/test_path"
    assert response.json()[0]["method"] == "GET"


def test_get_route(client, auth_header_global_admin, test_route):
    response = client.get(f"/api/v1/routes/{test_route.id}", headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["path"] == "/test_path"
    assert response.json()["method"] == "GET"


def test_get_route_not_found(client, auth_header_global_admin):
    response = client.get(f"/api/v1/routes/{uuid.uuid4()}", headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_route(client, auth_header_global_admin, test_route):
    response = client.patch(f"/api/v1/routes/{test_route.id}",
                            json={"path": "/updated_path", "method": "PUT", "action": "Test action"},
                            headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["path"] == "/updated_path"
    assert response.json()["method"] == "PUT"


def test_update_route_not_found(client, auth_header_global_admin):
    response = client.patch(f"/api/v1/routes/{uuid.uuid4()}",
                            json={"path": "/updated_path", "method": "PUT", "action": "Test action"},
                            headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_route(client, auth_header_global_admin, test_route):
    response = client.delete(f"/api/v1/routes/{test_route.id}", headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_route_not_found(client, auth_header_global_admin):
    response = client.delete(f"/api/v1/routes/{uuid.uuid4()}", headers=auth_header_global_admin)
    assert response.status_code == status.HTTP_404_NOT_FOUND
