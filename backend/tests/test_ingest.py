def test_ingest_metrics(client):
    payload = {
        "timestamp": "2026-01-30T15:45:12Z",
        "source": "finance",
        "metric_name": "daily_expense",
        "value": 25430.75,
        "unit": "usd",
        "tags": ["region=SP", "team=alpha"],
    }
    response = client.post("/metrics/ingest", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["received"] == 1
    assert isinstance(body["anomalies"], list)
