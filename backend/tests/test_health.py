def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
