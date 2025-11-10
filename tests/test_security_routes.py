def test_scan_log_flags_suspicious_players(client, auth_headers):
    payload = {
        "entries": [
            {
                "player_id": 1,
                "action": "aimbot_lock",
                "headshot_rate": 0.95,
                "reaction_time_ms": 80,
            },
            {"player_id": 2, "action": "move", "headshot_rate": 0.2, "reaction_time_ms": 200},
        ]
    }
    response = client.post(
        "/api/security/scan-log", json=payload, headers=auth_headers
    )
    data = response.get_json()
    assert response.status_code == 200
    assert 1 in data["suspicious_players"]
    assert data["anomaly_counts"]["aimbot_lock"] == 1


def test_player_risk_endpoint(client, auth_headers):
    response = client.get("/api/security/player-risk/1", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data["player"]["id"] == 1
    assert 0 <= data["risk_score"] <= 100
    assert data["event_count"] >= 1


def test_report_creation_creates_event(client, auth_headers):
    payload = {"player_id": 2, "reason": "manual_investigation", "severity": "low"}
    response = client.post("/api/security/report", json=payload, headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 201
    assert data["event"]["player_id"] == 2
    assert data["event"]["event_type"] == "manual_investigation"


def test_dashboard_summary(client, auth_headers):
    response = client.get("/api/security/dashboard", headers=auth_headers)
    data = response.get_json()
    assert response.status_code == 200
    assert data["totals"]["players"] >= 2
    assert isinstance(data["metrics"]["avg_actions_per_minute"], float)

