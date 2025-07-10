import json
import uuid
from pathlib import Path

import pytest
import respx
from httpx import Response

from core import ApiLog
from core.models import Terminal, Tenant
from core.settings import settings
from core.utils.helpers import create_fake_mac_address
from tests.conftest import test_db


@pytest.mark.asyncio
@respx.mock
def test_activate_terminal_mocked(client, auth_header, test_db):
    mock_path = Path(__file__).parent / "data" / "activation_response.json"
    mock_data = json.loads(mock_path.read_text())

    respx.post(f"{settings.MRA_EIS_URL}/onboarding/activate-terminal").mock(
        return_value=Response(200, json=mock_data))

    response = client.post(
        "/api/v1/activation/activate",
        headers={
            "Authorization": auth_header["Authorization"],
            "x-mac-address": create_fake_mac_address(),
        }, json={"terminal_activation_code": "MOCK-CODE-1234-36ES"})

    assert response.status_code == 200
    assert test_db.query(Terminal).count() == 1
    assert test_db.query(Terminal).first().site_id == "BL44c73cd2-bff0-4d54-9437-ff4e3fdd294a"

    assert test_db.query(Tenant).count() == 1
    db_tenants = test_db.query(Tenant).first()
    assert db_tenants.tin == "31699145"
    assert db_tenants.vat_registered == False
    assert db_tenants.config_version == 1
    assert db_tenants.taxpayer_id == 266
    assert test_db.query(ApiLog).count() == 1

    terminal = test_db.query(Terminal).filter(
        Terminal.activation_code == "MOCK-CODE-1234-36ES",
        Terminal.id == uuid.UUID(response.json()["id"]),
        Terminal.site_id == "BL44c73cd2-bff0-4d54-9437-ff4e3fdd294a",
        Terminal.position == 1
    ).first()
    assert terminal is not None


@pytest.mark.asyncio
@respx.mock
def test_activate_terminal_mock_failure(client, auth_header):
    respx.post(f"{settings.MRA_EIS_URL}/onboarding/activate-terminal").mock(
        return_value=Response(400, json={
            "statusCode": -200011,
            "remark": "Value is outside range eg too long or too short or does not match expected pattern",
            "data": "string",
            "errors": [
                {
                    "errorCode": --200011,
                    "fieldName": "string",
                    "errorMessage": "string"
                }
            ]
        }))

    response = client.post(
        "/api/v1/activation/activate",
        headers={
            "Authorization": auth_header["Authorization"],
            "x-mac-address": create_fake_mac_address(),
        },
        json={"terminal_activation_code": "MOCK-CODE-1234-2345"})

    assert response.status_code == 400


@pytest.mark.asyncio
@respx.mock
def test_confirm_activation(client, auth_header, test_terminal, test_db):
    respx.post(f"{settings.MRA_EIS_URL}/onboarding/terminal-activated-confirmation").mock(
        return_value=Response(200, json={
            "statusCode": 1,
            "remark": "Terminal is now fully activated and ready for use!",
            "data": True,
            "errors": []
        }))
    response = client.post(
        "/api/v1/activation/confirm",
        headers={
            "Authorization": auth_header["Authorization"],
            "x-mac-address": create_fake_mac_address(),
        },
        json={"terminal_id": str(test_terminal.id)}
    )
    assert response.status_code == 200
    assert test_terminal.confirmed_at is not None
    assert test_db.query(ApiLog).count() == 1


@pytest.mark.asyncio
@respx.mock
def test_confirm_activation_failure(client, auth_header, test_terminal):
    respx.post(f"{settings.MRA_EIS_URL}/onboarding/terminal-activated-confirmation").mock(
        return_value=Response(400, json={
            "statusCode": -199999,
            "remark": "Terminal is de-activated.",
            "data": True,
            "errors": []
        }))
    response = client.post(
        "/api/v1/activation/confirm",
        headers={
            "Authorization": auth_header["Authorization"],
            "x-mac-address": create_fake_mac_address(),
        },
        json={"terminal_id": str(test_terminal.id)}
    )

    assert response.status_code == 400
