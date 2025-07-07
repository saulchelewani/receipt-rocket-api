def test_list_dictionary(client, test_dictionary):
    response = client.get("/api/v1/dictionary")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert all(isinstance(item, dict) for item in data)

    for item in data:
        assert all(key in item for key in ["term", "definition"])
        assert isinstance(item["term"], int)
        assert isinstance(item["definition"], str)

    assert any(item["term"] == test_dictionary.term for item in data)
    assert any(item["definition"] == test_dictionary.definition for item in data)
