import re
import uuid
from unittest.mock import patch

import httpx
import pytest

from apps.main import app
from core import User


def test_list_tenants(client, test_tenant, auth_header_global_admin):
    response = client.get("/api/v1/tenants", headers=auth_header_global_admin)
    assert response.status_code == 200
    assert response.json()[0]["id"] == str(test_tenant.id)


@pytest.mark.asyncio
async def test_create_tenant(auth_header_global_admin, test_db) -> None:
    with patch("apps.tenants.routes.send_email") as mock_send_email:
        mock_send_email.return_value = None

        async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/tenants/",
                headers=auth_header_global_admin,
                json={
                    "name": "New Tenant",
                    "email": "test@example.com",
                    "admin_name": "Admin User",
                    "phone_number": "0886265490"
                })
        assert response.status_code == 200
        assert response.json()["id"]
        assert re.match(r"^NT\d{4}$", response.json()["code"])
        user = test_db.query(User).filter(
            User.email == "test@example.com",
            User.tenant_id == uuid.UUID(response.json()["id"])
        ).first()
        assert user is not None
        mock_send_email.assert_called_once()


def test_cannot_create_duplicate_tenant(client, auth_header_global_admin, test_tenant) -> None:
    response = client.post(
        "/api/v1/tenants/",
        headers=auth_header_global_admin,
        json={
            "name": test_tenant.name,
            "code": "test",
            "email": "test@example.com",
            "admin_name": "man",
            "phone_number": "265886265490"
        })
    assert response.status_code == 400
