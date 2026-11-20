from urllib.parse import parse_qs, urlparse

from app.core.config import settings


def test_telegram_records_once_and_can_unlink(client, auth_headers, account_id, make_headers, monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_username", "FinanzasDemoBot")
    monkeypatch.setattr(settings, "telegram_webhook_secret", "secreto-de-prueba")
    headers = {"X-Telegram-Bot-Api-Secret-Token": "secreto-de-prueba"}

    def message(update_id, text, chat_id=12345678901, chat_type="private", signed=True):
        return client.post(
            "/telegram/webhook",
            json={"update_id": update_id, "message": {
                "text": text, "chat": {"id": chat_id, "type": chat_type},
            }},
            headers=headers if signed else {},
        )

    assert client.post("/telegram/link").status_code == 401
    link = client.post("/telegram/link", headers=auth_headers).json()["url"]
    code = parse_qs(urlparse(link).query)["start"][0]
    assert message(1, f"/start {code}", signed=False).status_code == 403
    assert message(1, f"/start {code}", chat_type="group").json() == {}
    assert "Cuenta vinculada" in message(1, f"/start {code}").json()["text"]
    assert "vencido o usado" in message(2, f"/start {code}", chat_id=99).json()["text"]
    assert "registré un gasto" in message(3, "gasté 20.000 en almuerzo").json()["text"]
    assert message(3, "gasté 20.000 en almuerzo").json() == {}

    history = client.get("/transactions", headers=auth_headers).json()
    assert history["total"] == 1
    assert history["items"][0]["account_id"] == account_id
    assert client.get("/transactions", headers=make_headers("otra@example.com")).json()["total"] == 0

    assert client.delete("/telegram/link", headers=auth_headers).status_code == 204
    assert not client.get("/telegram/link", headers=auth_headers).json()["linked"]
    assert "Inicia sesión" in message(4, "cuánto tengo").json()["text"]
