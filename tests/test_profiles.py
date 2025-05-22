from starlette import status
import rstr

from core.utils import get_random_number


def test_create_profile(client, auth_header_tenant_admin):
    response = client.post("/api/v1/profiles/", headers=auth_header_tenant_admin, json={
        "business_name": "Test Business",
        "address": "123 Main St",
        "phone": rstr.xeger(r'^0[89]{2}\d{7}$'),
        "email": "0Bm0e@example.com",
        "tin": get_random_number(8)
    })
    assert response.status_code == status.HTTP_201_CREATED