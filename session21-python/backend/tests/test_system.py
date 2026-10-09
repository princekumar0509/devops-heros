def test_root_reports_service_name(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "HelpDesk API"


def test_health_is_up(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_ready_checks_database(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY"}


def test_metrics_exposes_prometheus_format(client):
    client.get("/api/tickets")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
