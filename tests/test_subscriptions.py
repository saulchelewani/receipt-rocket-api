def test_get_subscriptions(client, auth_header, test_subscription, test_tenant, test_db):
    test_subscription.tenant = test_tenant
    test_db.commit()
    response = client.get("/api/v1/subscriptions", headers=auth_header)
    assert response.status_code == 200
