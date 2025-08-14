import re
from unittest.mock import patch
from uuid import UUID

import httpx
import pytest
import rstr
from starlette import status

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
                    "name": "FMC Inc",
                    "email": "test@example.com",
                    "admin_name": "Chimwewemwe Kampingo",
                    "phone_number": rstr.xeger(r"^(\+?265|0)[89]{2}[0-9]{7}$"),
                    "tin": rstr.xeger(r"^[0-9]{8}$"),
                })
            data = response.json()

        assert response.status_code == status.HTTP_200_OK
        assert all(key in data for key in ["id", "code", "name"])
        assert re.match(r"^FI[0-9]{4}$", data.get("code"))
        user = test_db.query(User).filter(
            User.email == "test@example.com",
            User.name == "Chimwewemwe Kampingo",
            User.tenant_id == UUID(data.get("id")),
            User.status == 1001
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
            "phone_number": "265886265490",
            "tin": "31699145"
        })
    assert response.status_code == 400
