def test_list_tenants(client, test_tenant, auth_header_global_admin):
    response = client.get("/api/v1/tenants", headers=auth_header_global_admin)
    assert response.status_code == 200
    assert response.json()[0]["id"] == str(test_tenant.id)


def test_create_tenant(client, auth_header_global_admin) -> None:
    response = client.post("/api/v1/tenants", headers=auth_header_global_admin,
                           json={"name": "New Tenant", "code": "NT"})
    assert response.status_code == 200
    assert response.json()["id"]


def test_cannot_create_duplicate_tenant(client, auth_header_global_admin, test_tenant) -> None:
    response = client.post("/api/v1/tenants", headers=auth_header_global_admin,
                           json={"name": test_tenant.name, "code": "test"})
    assert response.status_code == 400