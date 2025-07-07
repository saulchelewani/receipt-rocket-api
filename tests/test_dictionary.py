def test_list_dictionary(client, test_dictionary):
    response = client.get("/api/v1/dictionary")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all(isinstance(item, dict) for item in data)

    expected_keys = ["term", "definition"]
    for item in data:
        assert all(key in item for key in expected_keys)
