import pytest
import respx
from httpx import Response, ConnectTimeout
from starlette import status

from apps.sales.schema import PaymentMethod
from core.models import Product, OfflineTransaction
from core.settings import settings
from core.utils import get_random_number
from tests.conftest import get_mock_data


@pytest.mark.asyncio
@respx.mock
def test_make_a_sale(client, test_db, device_headers, test_terminal, test_product, test_global_config):
    respx.post(f"{settings.MRA_EIS_URL}/sales/submit-sales-transaction").mock(
        return_value=Response(200, json=get_mock_data(filename="sales_response.json")))

    product = Product(
        tenant_id=test_terminal.tenant_id,
        unit_price=300, quantity=4,
        code=test_product.code,
        unit_of_measure="kg",
        tax_rate_id=test_product.tax_rate_id,
        is_product=True
    )
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)

    response = client.post("/api/v1/sales", headers=device_headers, json={
        "payment_method": PaymentMethod.MOBILE_MONEY,
        "buyer_name": "John Doe",
        "buyer_tin": get_random_number(9),
        "buyer_authorization_code": get_random_number(9),
        "invoice_line_items": [
            {
                "product_code": test_product.code,
                "quantity": 1,
            },
            {
                "product_code": product.code,
                "quantity": 2,
            }
        ]
    })

    assert response.status_code == 200
    assert response.json()["validation_url"] is not None
    assert isinstance(response.json()["invoice"], dict)


@pytest.mark.asyncio
@respx.mock
def test_make_an_offline_sale(client, test_db, device_headers, test_terminal, test_product, test_global_config):
    respx.post(f"{settings.MRA_EIS_URL}/sales/submit-sales-transaction").mock(
        side_effect=ConnectTimeout("Connection timed out"))

    response = client.post("/api/v1/sales", headers=device_headers, json={
        "payment_method": PaymentMethod.MOBILE_MONEY,
        "buyer_name": "John Doe",
        "buyer_tin": get_random_number(9),
        "buyer_authorization_code": get_random_number(9),
        "invoice_line_items": [
            {
                "product_code": test_product.code,
                "quantity": 1,
            },
        ]
    })

    assert response.status_code == 200
    assert response.json()["remark"] == "Transaction saved offline"
    assert response.json()["validation_url"] is not None
    assert isinstance(response.json()["invoice"], dict)
    txn = test_db.query(OfflineTransaction).filter(
        OfflineTransaction.transaction_id == response.json()["invoice"]["invoiceHeader"]["invoiceNumber"]).count()
    assert txn is not None


@pytest.mark.asyncio
@respx.mock
def test_make_sale_with_discount(client, test_db, device_headers, test_terminal, test_product, test_global_config):
    respx.post(f"{settings.MRA_EIS_URL}/sales/submit-sales-transaction").mock(
        return_value=Response(200, json=get_mock_data(filename="sales_response.json")))

    response = client.post("/api/v1/sales", headers=device_headers, json={
        "payment_method": PaymentMethod.MOBILE_MONEY,
        "buyer_name": "John Doe",
        "buyer_tin": get_random_number(9),
        "buyer_authorization_code": get_random_number(9),
        "invoice_line_items": [
            {
                "product_code": test_product.code,
                "quantity": 1,
                "discount": 10
            },
        ]
    })

    assert response.status_code == 200
    assert response.json()["validation_url"] is not None
    assert isinstance(response.json()["invoice"], dict)
    assert response.json()["invoice"]["invoiceLineItems"][0]["discount"] == 10
    assert response.json()["invoice"]["invoiceLineItems"][0]["total"] == 90
    assert response.json()["invoice"]["invoiceLineItems"][0]["totalVAT"] == 12.75


@pytest.mark.asyncio
@respx.mock
def test_make_a_sale_without_buyer_details(client, test_db, device_headers, test_terminal, test_product,
                                           test_global_config):
    respx.post(f"{settings.MRA_EIS_URL}/sales/submit-sales-transaction").mock(
        return_value=Response(200, json=get_mock_data(filename="sales_response.json")))

    response = client.post("/api/v1/sales", headers=device_headers, json={
        "payment_method": PaymentMethod.MOBILE_MONEY,
        "invoice_line_items": [
            {
                "product_code": test_product.code,
                "quantity": 1,
            }
        ]
    })

    assert response.status_code == 200
    assert response.json()["validation_url"] is not None
    assert isinstance(response.json()["invoice"], dict)


@pytest.mark.asyncio
@respx.mock
def test_make_a_sale_for_relief_without_certificate(client, test_db, device_headers, test_terminal, test_product,
                                                    test_global_config):
    respx.post(f"{settings.MRA_EIS_URL}/sales/submit-sales-transaction").mock(
        return_value=Response(200, json=get_mock_data(filename="sales_response.json")))

    response = client.post("/api/v1/sales", headers=device_headers, json={
        "payment_method": PaymentMethod.MOBILE_MONEY,
        "is_relief_supply": True,
        "invoice_line_items": [
            {
                "product_code": test_product.code,
                "quantity": 1,
            }
        ]
    })

    assert response.status_code == 400


@pytest.mark.asyncio
@respx.mock
def test_make_a_sale_for_relief(client, test_db, device_headers, test_terminal, test_product,
                                test_global_config):
    respx.post(f"{settings.MRA_EIS_URL}/sales/submit-sales-transaction").mock(
        return_value=Response(200, json=get_mock_data(filename="sales_response.json")))

    response = client.post("/api/v1/sales", headers=device_headers, json={
        "payment_method": PaymentMethod.MOBILE_MONEY,
        "is_relief_supply": True,
        "vat5_certificate_details": {
            "project_number": "123",
            "certificate_number": "1234",
            "quantity": 1
        },
        "invoice_line_items": [
            {
                "product_code": test_product.code,
                "quantity": 1,
            }
        ]
    })

    assert response.status_code == status.HTTP_200_OK
    cert = response.json()["invoice"]["invoiceHeader"]["vat5CertificateDetails"]
    assert cert["projectNumber"] == "123"
    assert cert["certificateNumber"] == "1234"
    assert cert["quantity"] == 1


@pytest.mark.asyncio
@respx.mock
def test_make_a_sale_blocked_terminal(client, test_db, device_headers, test_terminal, test_product,
                                      test_global_config):
    respx.post(f"{settings.MRA_EIS_URL}/sales/submit-sales-transaction").mock(
        return_value=Response(200, json=get_mock_data(filename="sales_response_blocked_terminal.json")))

    respx.post(f"{settings.MRA_EIS_URL}/utilities/get-terminal-blocking-message").mock(
        return_value=Response(200, json=get_mock_data(filename="blocking_message_response.json")))

    response = client.post("/api/v1/sales", headers=device_headers, json={
        "payment_method": PaymentMethod.MOBILE_MONEY,
        "invoice_line_items": [
            {
                "product_code": test_product.code,
                "quantity": 1,
            }
        ]
    })

    reason = "Violation of terms and conditions"
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == reason
    test_db.refresh(test_terminal)
    assert test_terminal.is_blocked
    assert test_terminal.blocking_reason == reason


@pytest.mark.asyncio
@respx.mock
def test_make_a_sale_cached_blocked_terminal(client, test_db, device_headers, test_terminal, test_product,
                                             test_global_config):
    test_terminal.is_blocked = True
    test_terminal.blocking_reason = "Violation of terms and conditions"
    test_db.commit()

    response = client.post("/api/v1/sales", headers=device_headers, json={
        "payment_method": PaymentMethod.CASH,
        "invoice_line_items": [
            {
                "product_code": test_product.code,
                "quantity": 3,
            }
        ]
    })

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Terminal is blocked: Violation of terms and conditions"


@pytest.mark.asyncio
@respx.mock
def test_make_a_sale_outdated_config(client, test_db, device_headers, test_terminal, test_product,
                                     test_global_config):
    respx.post(f"{settings.MRA_EIS_URL}/sales/submit-sales-transaction").mock(
        return_value=Response(200, json=get_mock_data(filename="sales_response_outdated_config.json")))

    response = client.post("/api/v1/sales", headers=device_headers, json={
        "payment_method": PaymentMethod.CARD,
        "invoice_line_items": [
            {
                "product_code": test_product.code,
                "quantity": 4,
            }
        ]
    })

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Update terminal configuration"
