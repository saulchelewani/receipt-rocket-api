import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from core.models import TaxRate, Terminal, Tenant
from core.settings import settings


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
