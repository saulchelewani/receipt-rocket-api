import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from core.models import Terminal, Tenant
from core.settings import settings
from core.utils import create_fake_mac_address


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
    assert test_db.query(Terminal).first().terminal_id == "3a6d3703-1c39-41e8-98ce-b38d9574540d"
    assert test_db.query(Terminal).first().site_id == "f47ac10b-58cc-4372-a567-0e02b2c3d479"

    assert test_db.query(Tenant).count() == 1
    assert test_db.query(Tenant).first().tin == "20202020"
    assert test_db.query(Tenant).first().vat_registered == True
    assert test_db.query(Tenant).first().config_version == 3


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
def test_confirm_activation(client, auth_header, test_terminal):
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
