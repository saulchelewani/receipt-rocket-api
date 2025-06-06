from apps.sales.schema import PaymentMethod
from core.models import Product, Item
from core.utils import get_random_number


def test_make_a_sale(client, test_db, auth_header_global_admin, test_terminal, test_product, test_tax_rate):
    item = Item(code=get_random_number(), name="Boom paste")
    test_db.add(item)
    test_db.commit()
    test_db.refresh(item)

    product = Product(item_id=item.id, tenant_id=test_terminal.tenant_id, unit_price=300, quantity=4, code=item.code)
    test_db.add(product)
    test_db.commit()
    test_db.refresh(product)

    response = client.post("/api/v1/sales", headers={
        "Authorization": auth_header_global_admin['Authorization'],
        "x-device-id": test_terminal.device_id,
    }, json={
        "payment_method": PaymentMethod.MOBILE_MONEY,
        "buyer_name": "John Doe",
        "buyer_tin": get_random_number(9),
        "buyer_authorization_code": get_random_number(9),
        "invoice_line_items": [
            {
                "product_code": test_product.item.code,
                "quantity": 1,
                "tax_rate_id": str(test_tax_rate.id),
            },
            {
                "product_code": product.code,
                "quantity": 2,
                "tax_rate_id": str(test_tax_rate.id),
            }
        ]
    })

    # assert response.status_code == 400
