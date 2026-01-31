def test_auth_login(client):
    response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "radar"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body


def test_metrics_history_empty(client):
    response = client.get(
        "/metrics/history",
        params={"metric_name": "delivery_delay_minutes"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_latest_anomalies_empty(client):
    response = client.get("/anomalies/latest")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_train_requires_data(client):
    response = client.post(
        "/train",
        json={"metric_name": "delivery_delay_minutes", "source": "logistics"},
    )
    assert response.status_code in {400, 500}


def test_websocket_health(client):
    with client.websocket_connect("/ws/health") as websocket:
        websocket.send_text("ping")
        payload = websocket.receive_json()
        assert payload["status"] == "ok"


def test_websocket_alerts_connect(client):
    with client.websocket_connect("/ws/alerts") as websocket:
        websocket.send_text("ping")
