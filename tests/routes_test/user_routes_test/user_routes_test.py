from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_user_signup():
    response = client.post("/signup", json={
        "email": "test@email.com",
        "password": "test_password",
    })
    assert response.status_code == 201


def test_user_token():
    response = client.post("/", json={
        "email": "wrong@email.com",
        "password": "test_password",
    })
    assert response.status_code == 400
