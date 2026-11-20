# Pruebas y demostración

Ejecuta `python -m pytest` desde la raíz. La suite usa una base SQLite nueva en memoria por prueba. Cubre autenticación, cuentas, movimientos, reportes, presupuestos, alertas y el asistente.

La prueba de Telegram simula actualizaciones de su API. Comprueba autorización del webhook, exclusión de chats de grupo, enlace de un solo uso, registro en el historial, aislamiento entre usuarios, rechazo de duplicados y desvinculación.

## Prueba manual en la URL desplegada

| Paso | Resultado esperado |
|---|---|
| Registra una cuenta web de prueba. Cierra sesión e ingresa con ella. | El panel se abre y el usuario permanece autenticado al navegar. |
| Agrega una cuenta financiera de prueba y abre Asistente. | Se puede generar un enlace personal. |
| Abre el enlace, pulsa Iniciar y envía «gasté 20.000 en almuerzo». | Telegram confirma un gasto de 20.000. |
| En la web abre o recarga Historial. | Aparece una sola fila con el gasto y la cuenta seleccionada. |
| Desde Telegram consulta «cuánto tengo». | El saldo refleja el gasto. |
| Desvincula el chat en Asistente y pregunta por el saldo otra vez. | Telegram pide iniciar sesión y vincular el chat. |
| Redespliega el servicio y vuelve a iniciar sesión. | El movimiento previo sigue disponible en PostgreSQL. |

## Retos del proyecto

- Registrar el mismo gasto desde dos interfaces exigía compartir la lógica de categorías, saldos y alertas.
- Vincular Telegram con el usuario web exigía un enlace con vencimiento que se consuma una sola vez.
- Los reintentos del webhook exigían guardar el identificador y el movimiento en la misma transacción.
- El alojamiento gratuito tiene un sistema de archivos efímero. PostgreSQL permite conservar los datos entre despliegues.
