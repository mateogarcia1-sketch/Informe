# Despliegue y Telegram

## Render con PostgreSQL

1. Inicia sesión en [Render](https://dashboard.render.com/) y crea un Blueprint desde el repositorio `Informe`. Selecciona la rama que contiene `render.yaml`.
2. Comprueba que el Blueprint selecciona el plan Free tanto para el servicio web como para PostgreSQL. Verifica el coste en el panel antes de aplicar. La plantilla crea un secreto JWT, conecta la base por la red interna y desactiva el modo de depuración.
3. Espera el estado Live, copia la URL HTTPS asignada y verifica que `/health` devuelve `{"status":"ok","app":"Finanzas App"}`. Abre la raíz y comprueba registro e inicio de sesión.
4. Registra un movimiento de prueba y comprueba que sigue en Historial después de un nuevo despliegue. La base gratuita de Render caduca a los 30 días y el servicio puede necesitar tiempo para despertar tras quedar inactivo. [Límites de Render Free](https://render.com/docs/free)

## Activar el bot

1. Desde tu cuenta de Telegram, abre [BotFather](https://t.me/BotFather). Envía `/newbot` para crear un bot o usa `/mybots` si ya existe. Conserva el token en privado.
2. En el servicio web de Render, agrega `TELEGRAM_BOT_USERNAME` con el nombre del bot sin arroba. Agrega `TELEGRAM_WEBHOOK_SECRET` con un valor generado mediante `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Espera a que el cambio esté activo.
3. Desde la raíz del proyecto, ejecuta `python scripts/register_telegram.py https://TU-SERVICIO.onrender.com`. El script pide el token y el secreto con entrada oculta. Comprueba que el nombre que devuelve coincide con `TELEGRAM_BOT_USERNAME`.
4. En la web, crea una cuenta financiera de prueba. Abre **Asistente → Generar enlace de Telegram** y en el chat pulsa **Iniciar**. Registra un gasto y vuelve al historial web. [Telegram Bot API](https://core.telegram.org/bots/api#setwebhook)

Guarda los secretos en las variables de entorno del alojamiento y conserva el token de BotFather fuera de Git.
