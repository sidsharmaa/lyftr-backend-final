def test_stats_structure(client):
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_messages" in data
    assert "messages_per_sender" in data