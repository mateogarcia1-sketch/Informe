"""Registra el webhook sin imprimir el token del bot ni el secreto."""
import getpass
import re
import sys
from urllib.parse import urlparse

import httpx


def main() -> None:
    if len(sys.argv) != 2 or urlparse(sys.argv[1]).scheme != "https":
        raise SystemExit("Uso: python scripts/register_telegram.py https://tu-app.onrender.com")
    base_url = sys.argv[1].rstrip("/")
    token = getpass.getpass("Token de BotFather: ").strip()
    secret = getpass.getpass("TELEGRAM_WEBHOOK_SECRET del alojamiento: ").strip()
    if not re.fullmatch(r"[0-9]+:[A-Za-z0-9_-]+", token):
        raise SystemExit("El formato del token no es válido.")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", secret):
        raise SystemExit("El secreto debe contener letras, números, guion o guion bajo.")
    try:
        with httpx.Client(timeout=20) as client:
            identity = client.get(f"https://api.telegram.org/bot{token}/getMe").json()
            if not identity.get("ok"):
                raise SystemExit("Telegram rechazó el token.")
            result = client.post(
                f"https://api.telegram.org/bot{token}/setWebhook",
                json={
                    "url": f"{base_url}/telegram/webhook",
                    "secret_token": secret,
                    "allowed_updates": ["message"],
                },
            ).json()
    except (httpx.HTTPError, ValueError):
        raise SystemExit("No se pudo contactar con Telegram.") from None
    if not result.get("ok"):
        raise SystemExit("Telegram rechazó el registro del webhook.")
    print("Webhook registrado para @" + identity["result"]["username"])


if __name__ == "__main__":
    main()
