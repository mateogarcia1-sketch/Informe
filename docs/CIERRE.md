# Cierre del proyecto

Finanzas App reúne el registro de gastos y el historial en una sola aplicación. Desde la web se puede crear una cuenta, iniciar sesión y consultar movimientos. Telegram permite registrar un gasto en lenguaje natural y verlo después en ese mismo historial.

## Qué entregamos

- Una web publicada por HTTPS en Render, con FastAPI y PostgreSQL.
- El bot [@FinanzasInformeBot](https://t.me/FinanzasInformeBot), vinculado a la cuenta web mediante un enlace temporal de un solo uso.
- Una guía de instalación, diagramas de arquitectura y secuencia, un plan de pruebas y diapositivas para la exposición.

## Qué verificamos

Pasaron 78 pruebas automatizadas. En producción comprobamos el registro, el inicio de sesión y la consulta de movimientos. También vinculamos una cuenta ficticia y enviamos «gasté 20.000 en almuerzo» desde Telegram. El bot confirmó el gasto y el historial mostró una sola entrada de 20.000 COP. Al terminar, desvinculamos la cuenta de prueba.

## Qué aprendimos

- Compartir la lógica de movimientos entre la web y Telegram permite aplicar las mismas validaciones, categorías y alertas en ambos canales.
- Guardar el identificador del webhook y el gasto en una sola transacción evita que un reintento registre el mismo movimiento dos veces.
- PostgreSQL conserva los datos fuera del sistema de archivos del servicio web. Las variables de entorno permiten configurar el webhook sin guardar secretos en Git.
- La prueba de extremo a extremo permite comprobar la comunicación entre Telegram y el servicio desplegado, además de verificar que el movimiento quede disponible en la web.

[Aplicación desplegada](https://informe-finanzas-app.onrender.com/) · [Wiki del proyecto](https://github.com/mateogarcia1-sketch/Informe/wiki)
