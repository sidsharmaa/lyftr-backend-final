import json

def test_webhook_missing_signature(client):
    response = client.post("/webhook", json={"message_id": "m1"})
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid signature"

def test_webhook_invalid_signature(client):
    response = client.post(
        "/webhook", 
        json={"message_id": "m1"},
        headers={"X-Signature": "deadbeef"}
    )
    assert response.status_code == 401

def test_webhook_valid_flow(client, valid_signature):
    payload = {
        "message_id": "m1",
        "from": "+919876543210",
        "to": "+14155550100",
        "ts": "2025-01-15T10:00:00Z",
        "text": "Hello"
    }
    body_str = json.dumps(payload)
    sig = valid_signature(body_str)
 
    response = client.post(
        "/webhook",
        content=body_str,
        headers={"X-Signature": sig}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    msgs, _ = client.app.state.db_repo.get_messages(10, 0) if hasattr(client.app.state, "db_repo") else (None, 0)

    response = client.post(
        "/webhook",
        content=body_str,
        headers={"X-Signature": sig}
    )
    assert response.status_code == 200

    bad_payload = payload.copy()
    bad_payload["from"] = "invalid"
    bad_body = json.dumps(bad_payload)
    bad_sig = valid_signature(bad_body)
    
    response = client.post(
        "/webhook",
        content=bad_body,
        headers={"X-Signature": bad_sig}
    )
    assert response.status_code == 422