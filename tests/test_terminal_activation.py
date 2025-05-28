import pytest
import respx
from httpx import Response

from core.settings import settings
from core.utils import create_fake_mac_address
from tests.conftest import get_test_file

activation_response = {
    "statusCode": 1,
    "remark": "Terminal Activated, pending for confirmation request",
    "data": {
        "activatedTerminal": {
            "terminalId": "3a6d3703-1c39-41e8-98ce-b38d9574540d",
            "activationDate": "2024-05-14T19:25:27.8106046+02:00",
            "terminalCredentials": {
                "jwtToken": "mock.jwt.token",
                "secretKey": "f7542816a0883314a146a6d1276349d9e736a00"
            }
        },
        "configuration": {
            "globalConfiguration": {
                "id": 1,
                "versionNo": 1,
                "taxrates": [
                    {
                        "id": "T",
                        "name": "VAT",
                        "chargeMode": "Item",
                        "ordinal": 100,
                        "rate": 16.5
                    },
                    {
                        "id": "TR",
                        "name": "Tourism Levy",
                        "chargeMode": "Global",
                        "ordinal": 2,
                        "rate": 1.0
                    }
                ]
            },
            "terminalConfiguration": {
                "versionNo": 1,
                "terminalLabel": "Till-03",
                "emailAddress": "test@example.com",
                "phoneNumber": "0881234567",
                "tradingName": "Mock Trader",
                "addressLines": ["123 Market Street"]
            },
            "taxpayerConfiguration": {
                "versionNo": 89,
                "tin": "20202020",
                "isVATRegistered": True,
                "taxOfficeCode": "SWE",
                "taxOffice": {
                    "code": "SWE",
                    "name": "Songwe"
                },
                "activatedTaxRateIds": ["FIN", "VAT"],
                "activatedTaxrates": None
            }
        }
    },
    "errors": None
}

fake_response = get_test_file("activation_response.json")


@pytest.mark.asyncio
@respx.mock
def test_activate_terminal_mocked(client, auth_header):
    respx.post(f"{settings.MRA_EIS_URL}/onboarding/activate-terminal").mock(
        return_value=Response(200, json=activation_response))

    response = client.post(
        "/api/v1/activation/activate",
        headers={
            "Authorization": auth_header["Authorization"],
            "x-mac-address": create_fake_mac_address(),
        }, json={"terminal_activation_code": "MOCK-CODE-1234"})

    assert response.status_code == 200


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
        json={"terminal_activation_code": "MOCK-CODE-1234"})

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
