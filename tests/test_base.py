def test_authentication(base_client):
    assert base_client.get('/').status_code == 200
