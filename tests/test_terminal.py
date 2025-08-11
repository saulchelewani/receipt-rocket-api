import pytest
import respx
from httpx import Response

from core.settings import settings
from tests.conftest import get_mock_data


@pytest.mark.asyncio
@respx.mock
def test_get_unblock_status_unblocked(client, device_headers, test_db, test_terminal):
    test_terminal.is_blocked = True
    test_terminal.blocking_reason = "Violation of terms and conditions"
    test_db.commit()

    respx.post(f"{settings.MRA_EIS_URL}/utilities/check-terminal-unblock-status").mock(
        return_value=Response(200, json=get_mock_data(filename="unblock_status_unblocked_response.json")))

    response = client.get("/api/v1/terminals/unblock-status", headers=device_headers)
    assert response.status_code == 200

    test_db.refresh(test_terminal)
    assert test_terminal.is_blocked == False
    assert test_terminal.blocking_reason is None


@pytest.mark.asyncio
@respx.mock
def test_get_unblock_status_still_blocked(client, device_headers, test_db, test_terminal):
    test_terminal.is_blocked = True
    test_terminal.blocking_reason = "Violation of terms and conditions"
    test_db.commit()

    respx.post(f"{settings.MRA_EIS_URL}/utilities/check-terminal-unblock-status").mock(
        return_value=Response(200, json=get_mock_data(filename="unblock_status_blocked_response.json")))

    response = client.get("/api/v1/terminals/unblock-status", headers=device_headers)
    assert response.status_code == 200
    assert response.json()["is_unblocked"] == False

    test_db.refresh(test_terminal)
    assert test_terminal.is_blocked == True
    assert test_terminal.blocking_reason == "Violation of terms and conditions"


def test_list_terminals(client, device_headers, test_db, test_terminal):
    response = client.get("/api/v1/terminals", headers=device_headers)
    assert response.status_code == 200
    assert response.json()[0]["id"] == str(test_terminal.id)
