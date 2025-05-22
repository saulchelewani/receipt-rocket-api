import pytest
from unittest.mock import patch

mock_response_data = {
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

@patch("core.services.activation.httpx.post")
def test_activate_terminal_mocked(mock_post, client, auth_header):
    # Mock HTTPX post
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = mock_response_data

    response = client.post("/api/v1/activation/activate", headers=auth_header, json={"terminalActivationCode": "MOCK-CODE-1234"})

    assert response.status_code == 200
    assert response.json()["terminal_id"] == "3a6d3703-1c39-41e8-98ce-b38d9574540d"
