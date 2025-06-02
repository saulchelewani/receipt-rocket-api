from core.settings import settings


def test_login(test_user_with_routes, client, test_db, test_route):
    response = client.post("/auth/login",
                           data={"username": test_user_with_routes.email, "password": settings.TEST_SECRET})
    assert response.status_code == 200

    json_data = response.json()
    assert "access_token" in json_data
    assert "token_type" in json_data


def test_login_wrong_password(client):
    response = client.post("/auth/login", data={"username": "some@email.io", "password": "wrong_password"})
    assert response.status_code == 401
