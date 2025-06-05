from apps.sales.schema import PaymentMethod


def test_make_a_sale(client, auth_header_global_admin, test_terminal, test_product, test_tax_rate):
    response = client.post("/api/v1/sales", headers={
        "Authorization": auth_header_global_admin['Authorization'],
        "x-device-id": test_terminal.device_id,
    }, json={
        "payment_method": PaymentMethod.MOBILE_MONEY,
        "invoice_line_items": [
            {
                "product_code": test_product.item.code,
                "quantity": 1,
                "tax_rate_id": str(test_tax_rate.id),
                "is_product": True
            }
        ]

    })
    # print(response.json())
    # assert response.status_code == 400
