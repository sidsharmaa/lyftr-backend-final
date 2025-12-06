def test_list_messages_pagination(client):
    response = client.get("/messages?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert data["limit"] == 10

def test_list_messages_filter(client):
    response = client.get("/messages?from=+919876543210")
    assert response.status_code == 200
