import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from core.models import TaxRate, Terminal, Tenant
from core.settings import settings

config_response = {
    "statusCode": 1,
    "remark": "Successful",
    "data": {
        "globalConfiguration": {
            "versionNo": 1,
            "taxRates": [
                {
                    "id": "A",
                    "name": "VAT-A",
                    "chargeMode": "G",
                    "ordinal": 5,
                    "rate": 16.5
                },
                {
                    "id": "E",
                    "name": "Excempt",
                    "chargeMode": "G",
                    "ordinal": 2,
                    "rate": 0
                },
                {
                    "id": "TL",
                    "name": "Tourism Levy",
                    "chargeMode": "G",
                    "ordinal": 1,
                    "rate": 1
                }
            ]
        },
        "terminalConfiguration": {
            "versionNo": 2,
            "terminalLabel": "Cashier 1",
            "emailAddress": "taxpayer@example.com",
            "phoneNumber": "+265888123456",
            "tradingName": "TRADING NAME",
            "addressLines": [
                "PO BOX 1234",
                "BLANTYRE",
                "* NAMIWAWA SERVICE CENTRE *"
            ],
            "offlineLimit": {
                "maxTransactionAgeInHours": 48,
                "maxCummulativeAmount": 5000000
            }
        },
        "taxpayerConfiguration": {
            "versionNo": 1,
            "tin": "20202020",
            "isVATRegistered": True,
            "taxOffice": {
                "code": "BLA",
                "name": "Blantyre Station"
            },
            "activatedTaxRateIds": [
                "A", "E", "TL"
            ]
        }
    },
    "errors": [
    ]
}


@pytest.mark.asyncio
@respx.mock
def test_get_new_config(client, device_headers, test_db, test_terminal):
    mock_path = Path(__file__).parent / "data" / "config_response.json"
    mock_data = json.loads(mock_path.read_text())

    respx.get(f"{settings.MRA_EIS_URL}/api/v1/configuration/get-latest-configs").mock(
        return_value=Response(200, json=mock_data))

    response = client.get(f"/api/v1/config", headers=device_headers)
    assert response.status_code == 200
    assert test_db.query(TaxRate).count() == 1
    assert test_db.query(Terminal).count() == 1
    assert test_db.get(Terminal, test_terminal.id).phone_number == '+265888123456'
    assert test_db.query(Tenant).filter(Tenant.id == test_terminal.tenant_id).first().tin == '20202020'
