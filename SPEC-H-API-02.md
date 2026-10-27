# Validación de integridad de tokens de autenticación

## Fuente

- Hallazgo aprobado: **H-API-02 — Token Base64 con secreto embebido**.
- Evidencia: `api/app/main.py:14`, `api/app/main.py:19-22`.
- Impacto: al no estar firmado el token y estar el secreto en el código, una persona que conozca ese secreto puede fabricar tokens aceptados con identidades o roles arbitrarios y una expiración futura.

## Contexto actual

Las rutas protegidas de la API reciben un token mediante la cabecera `Authorization`. El token se decodifica como Base64, contiene usuario, rol, expiración y secreto, y se valida el secreto y la expiración. No se verifica una firma criptográfica; el secreto está embebido en el código.

## Problema confirmado

La validación actual no permite comprobar que los datos del token fueron emitidos por una autoridad confiable y no fueron modificados. Además, el secreto embebido puede conocerse leyendo el código. Por ello, un token fabricado puede ser aceptado como una identidad o rol arbitrarios.

## Comportamiento a preservar

- Las rutas existentes y sus formatos de solicitud y respuesta consumidos por el frontend no deben cambiar como consecuencia de esta especificación.
- Las rutas protegidas deben continuar requiriendo autenticación mediante la cabecera `Authorization`.
- Las solicitudes con tokens auténticos, vigentes y aceptados por la política de autenticación deben conservar el acceso que ya les corresponde.

## Alcance

- Evitar que tokens fabricados o alterados sean aceptados como auténticos.
- Evitar que el secreto usado para validar la autenticidad de tokens permanezca embebido en el código fuente.
- Especificar resultados verificables para tokens auténticos, alterados y fabricados, sin definir la implementación técnica.

## Fuera de alcance

- Cambiar rutas, formatos de solicitudes o respuestas de la API.
- Cambiar los permisos que corresponden a cada identidad o rol.
- Definir el mecanismo, algoritmo o formato técnico para emitir y validar tokens.
- Cambiar el flujo o el contrato de `POST /auth/login`.

## Criterios de aceptación

1. Una solicitud autenticada con un token auténtico y vigente puede acceder a las rutas protegidas conforme a los permisos que ya le corresponden.
2. Un token cuyos datos de identidad, rol o expiración hayan sido alterados después de su emisión es rechazado.
3. Un token fabricado sin autenticidad verificable es rechazado, aunque contenga una identidad, un rol y una expiración válidos en apariencia.
4. El secreto de validación no está incorporado en el código fuente.
5. Las rutas y los formatos de solicitud y respuesta protegidos existentes permanecen compatibles con sus consumidores.

## Contratos afectados/protegidos

- **Afectado:** autenticación de las rutas protegidas mediante `Authorization`; cambia el criterio por el que la API acepta un token.
- **Protegidos:** nombres de rutas y formatos de solicitud y respuesta existentes de la API que consume el frontend. La autenticación no debe introducir cambios implícitos en dichos contratos.
- **Protegido:** el contrato de `POST /auth/login`; esta especificación no define ni modifica su solicitud, respuesta o emisión de tokens.

## Riesgos, supuestos y preguntas abiertas

- **Riesgo de compatibilidad:** tokens emitidos antes de aplicar la nueva validación podrían dejar de ser aceptados.
- **Supuesto:** existe un emisor confiable de tokens para las solicitudes legítimas; esta especificación no redefine su comportamiento.
- **Pregunta abierta:** ¿cómo se gestionará la transición de tokens existentes para evitar interrupciones a clientes legítimos?
- **Pregunta abierta:** ¿qué mecanismo de configuración y ciclo de rotación se usará para el secreto fuera del código fuente?
- **Pregunta abierta:** ¿qué algoritmo, formato de token y política de rechazo se adoptarán? Deben decidirse durante el diseño técnico, sin cambiar los contratos protegidos aquí.
