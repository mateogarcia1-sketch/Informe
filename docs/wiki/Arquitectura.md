# Arquitectura

```mermaid
flowchart LR
    U[Usuario] --> W[Web · inicio de sesión e historial]
    U --> T[Chat privado de Telegram]
    W -->|HTTPS y JWT| API[FastAPI]
    T --> TG[Telegram Bot API]
    TG -->|Webhook HTTPS con secreto| API
    API --> B[Asistente en español]
    API --> S[Servicios de cuentas y reportes]
    B --> M[Servicio de movimientos y alertas]
    S --> DB[(SQLite local · PostgreSQL en Render)]
    M --> DB
    API -->|Vínculos y actualizaciones procesadas| DB
```

## Vinculación y registro

```mermaid
sequenceDiagram
    participant W as Web
    participant A as FastAPI
    participant D as Base SQL
    participant T as Telegram
    W->>A: Solicitar enlace con JWT
    A->>D: Guardar hash y vencimiento
    A-->>W: Enlace de un solo uso
    W->>T: Abrir chat y pulsar Iniciar
    T->>A: /start con código y secreto de webhook
    A->>D: Consumir código y vincular chat
    T->>A: gasté 20.000 en almuerzo
    A->>D: Guardar movimiento y actualización juntos
    A-->>T: Confirmar gasto
    W->>A: Abrir Historial
    A-->>W: Mostrar el movimiento
```

Cada vínculo permite un chat privado por usuario. Un identificador único de actualización impide duplicar el movimiento si Telegram reenvía el webhook. Las contraseñas conservan el almacenamiento con hash del proyecto. Las consultas web comprueban la identidad mediante JWT y filtran por propietario.
