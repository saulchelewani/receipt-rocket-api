from starlette import status


def test_create_profile(client, auth_header_tenant_admin):
    response = client.post("/api/v1/profiles/", headers=auth_header_tenant_admin, json={
        "business_name": "Test Business",
        "address": "123 Main St",
        "phone": "123-456-7890",
        "email": "0Bm0e@example.com",
        "tin": "123456789"
    })
    assert response.status_code == status.HTTP_201_CREATED