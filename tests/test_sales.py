from apps.sales.schema import PaymentMethod


def test_make_a_sale(client, auth_header_global_admin, test_terminal, test_product, test_tax_rate):
    response = client.post("/api/v1/sales", headers={
        "Authorization": auth_header_global_admin['Authorization'],
        "x-device-id": test_terminal.device_id,
    }, json={
        "payment_method": PaymentMethod.MOBILE_MONEY,
        "buyer_name": "John Doe",
        "buyer_tin": "1234567890",
        "buyer_authorization_code": "1234567890",
        "invoice_line_items": [
            {
                "product_code": test_product.item.code,
                "quantity": 1,
                "tax_rate_id": str(test_tax_rate.id),
                "is_product": True
            }
        ]
    })

    # assert response.status_code == 400
