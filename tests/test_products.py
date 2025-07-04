import json
from pathlib import Path

import pytest
import respx
from httpx import Response

from core.models import Product
from core.settings import settings


@pytest.mark.asyncio
@respx.mock
def test_get_products(client, device_headers, test_db):
    mock_path = Path(__file__).parent / "data" / "products_response.json"
    mock_data = json.loads(mock_path.read_text())

    respx.post(f"{settings.MRA_EIS_URL}/utilities/get-terminal-site-products").mock(
        return_value=Response(200, json=mock_data))

    response = client.get("/api/v1/products", headers=device_headers)

    print(response.text)
    assert response.status_code == 200
    assert test_db.query(Product).count() == 1

    product = test_db.query(Product).first()
    assert product.code == "6161101860079"
    assert product.description == "Kericho Gold 200g"
    assert product.unit_price == 2300
    assert product.tax_rate_id == "A"


def test_get_product_by_code(client, device_headers, test_db, test_product):
    response = client.get(f"/api/v1/products/{test_product.code}", headers=device_headers)
    assert response.status_code == 200
    assert response.json()["code"] == test_product.code


def test_search_product_by_name(client, device_headers, test_db, test_product):
    response = client.get(f"/api/v1/products/search?name={test_product.name[:4]}", headers=device_headers)
    assert response.status_code == 200
    assert response.json()[0]["code"] == test_product.code
