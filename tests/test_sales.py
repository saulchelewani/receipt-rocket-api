import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from apps.sales.schema import PaymentMethod
from core.models import Product
from core.settings import settings
from core.utils import get_random_number


@pytest.mark.asyncio
@respx.mock
def test_make_a_sale(client, test_db, device_headers, test_terminal, test_product, test_global_config):
    mock_path = Path(__file__).parent / "data" / "sales_response.json"
    mock_data = json.loads(mock_path.read_text())

    respx.post(f"{settings.MRA_EIS_URL}/sales/submit-sales-transaction").mock(
        return_value=Response(200, json=mock_data))

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

    print(response.json())
    # assert response.status_code == 200

    # assert response.status_code == 400
