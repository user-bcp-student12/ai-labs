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

1. Una petición a una ruta protegida con un token firmado válido, vigente y con `iss` y `aud` coincidentes con la configuración es procesada; el usuario es el claim `sub`.
2. Un token alterado después de firmarlo responde `401` con campo `detail`.
3. Un token firmado con una clave distinta a la configurada responde `401`.
4. Un token sin firma, expirado, con claims ausentes o con `iss`/`aud` distintos responde `401` y no procesa la petición.
5. Un token en el formato Base64 anterior responde `401`.
6. Una petición sin cabecera `Authorization` responde `401` con campo `detail`.
7. Si falta `AUTH_JWT_PUBLIC_KEY`, `AUTH_JWT_ISSUER` o `AUTH_JWT_AUDIENCE`, o la clave no es un PEM válido, responde `503` y no procesa la petición, aunque el token sea válido.
8. El código fuente no contiene claves de firma, secretos ni claves públicas embebidas.
9. Los registros y respuestas no contienen valores de tokens ni de claves, salvo el campo `detail`.
10. Las rutas protegidas y `POST /auth/login` mantienen sus formatos de solicitud y respuesta.

Detalle de escenarios: `openspec/changes/hu-01-fortalecer-validacion-token/specs/api-token-authentication/spec.md`.

## Contratos afectados/protegidos

- **Afectado:** autenticación de las rutas protegidas mediante `Authorization`; cambia el criterio por el que la API acepta un token.
- **Protegidos:** nombres de rutas y formatos de solicitud y respuesta existentes de la API que consume el frontend. La autenticación no debe introducir cambios implícitos en dichos contratos.
- **Protegido:** el contrato de `POST /auth/login`; esta especificación no define ni modifica su solicitud, respuesta o emisión de tokens.

## Riesgos, supuestos y preguntas abiertas

- **Riesgo de compatibilidad:** los tokens Base64 anteriores quedan rechazados; no hay periodo de transición porque su autenticidad no es verificable.
- **Riesgo de despliegue:** clave pública, `iss` y `aud` deben alinearse con el emisor; una configuración incorrecta produce `503`.
- **Supuesto:** el servicio `auth` emite JWT compatibles (confirmado por la persona responsable); esta especificación no redefine su comportamiento.
- **Restricción decidida (PLAN.md):** verificación RS256 con clave pública externa; sin criptografía propia.
- **Pregunta abierta:** ¿qué ciclo de rotación de la clave pública se aplicará en despliegue?

## Estado

- Pendiente de revisión humana antes de avanzar a Architect.
