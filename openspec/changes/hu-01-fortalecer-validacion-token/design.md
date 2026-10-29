# Design

## Contexto tecnico

- Componente: `api` (FastAPI). Referencia: Issue [#26](https://github.com/user-bcp-student12/ai-labs/issues/26) y H-API-02 en HALLAZGOS.md.
- Estado observado: `api/app/security.py` verifica el token con PyJWT en RS256 usando `AUTH_JWT_PUBLIC_KEY`, `AUTH_JWT_ISSUER` y `AUTH_JWT_AUDIENCE`. Exige los claims `sub`, `role`, `exp`, `iss` y `aud`. Si falta configuracion o la clave es invalida, lanza `AuthenticationConfigurationError`.
- `api/app/main.py` expone la dependencia `authenticated_identity`. Traduce `AuthenticationConfigurationError` a `503` con `Authentication is not configured` y `InvalidTokenError` a `401` con `Invalid token: invalid token`. Se aplica a las cuatro rutas protegidas.
- PLAN.md y HALLAZGOS.md registran H-API-02 como resuelto. Este cambio formaliza ese comportamiento como contrato verificable (proposal.md, specs/api-token-authentication/spec.md). No introduce funcionalidad nueva.
- Cobertura existente: `api/tests/test_authentication.py`, `api/tests/conftest.py` (fixtures con claves RSA generadas en memoria, tokens alterados, expirados, con emisor o audiencia incorrectos, con algoritmo HS256, sin claim `role`, y token legado Base64) y `api/tests/test_endpoints_contract.py`. `docs/TESTING.md` registra la linea base de 80 pruebas aprobadas y 7 `xfail` tras H-API-02, con cobertura de `security.py` en 93%.

## Goals

- Mantener el contrato de la spec `api-token-authentication` sin cambios de comportamiento.
- Convertir las pruebas existentes en regresion explicita de los requisitos de la spec, sin depender de la implementacion.
- Cubrir los huecos de la spec que hoy no tienen prueba: ausencia de valores de token o clave en registros y respuestas, y rechazo de `sub` o `role` vacios o no textuales.
- Mantener la cobertura del codigo modificado en 85% o superior.

## Non-goals

- No modificar `api/app/security.py` ni `api/app/main.py` en este paso.
- No cambiar el emisor de tokens ni el contrato de `POST /auth/login` (componente `auth`).
- No resolver H-API-03, H-API-05, H-API-08 ni H-API-10. Son hallazgos separados. En particular, el texto de `detail` ya es fijo, pero la politica de `owner` queda fuera.
- No introducir JWKS remoto, rotacion de claves ni almacenamiento de secretos.
- No decidir la politica de `Bearer` en minusculas ni de headers sin prefijo (preguntas abiertas de proposal.md). Se documentan como casos de caracterizacion pendientes de decision.

## Contratos protegidos

| Contrato | Fuente | Protegido por |
|---|---|---|
| Header `Authorization: Bearer <token>` | docs/ENDPOINTS.md | `test_authentication.py`, `test_endpoints_contract.py` |
| 401 con campo `detail` para token ausente, invalido, expirado, alterado, sin firma o con claims incorrectos | ENDPOINTS.md, spec | `invalid_auth` fixture en `conftest.py` y pruebas `*_rejects_invalid_token_with_401` |
| 503 con `{"detail": "Authentication is not configured"}` ante configuracion ausente o clave invalida | ENDPOINTS.md, spec | `test_authentication.py` |
| Identidad: `sub` como usuario, `role` como rol | spec | `test_endpoints_contract.py` (`owner` vacio usa identidad del token) |
| Token legado Base64 rechazado | ENDPOINTS.md, spec | `test_known_defects.py::test_legacy_token_is_rejected` |
| Rutas y formatos de `/api/tasks` para el frontend | proposal.md | pruebas de contrato de tareas |

## Componentes afectados

- `api/app/security.py`: verificacion JWT. Sin cambios en esta fase; se caracteriza.
- `api/app/main.py`: dependencia `authenticated_identity` y traduccion a 401 y 503. Sin cambios en esta fase.
- `api/tests/test_authentication.py`, `api/tests/conftest.py`: pruebas de regresion y casos nuevos.
- `docs/TESTING.md`: registro de ejecuciones. Se actualiza solo al ejecutar pruebas, no en este paso.

## Decisiones tecnicas y alternativas

1. **Mantener RS256 con clave publica PEM (decidido).** El servicio solo necesita verificar; la clave privada permanece en `auth`. Alternativa descartada: HS256 con secreto compartido, porque obliga a compartir un secreto de firma entre componentes y reproduce el riesgo original de H-API-02 si se filtra.
2. **Biblioteca PyJWT existente (decidido).** Ya esta en `requirements.txt`. Alternativa descartada: verificacion propia con `cryptography` y parseo manual, por riesgo de errores criptograficos.
3. **Configuracion solo por variables de entorno, sin valores por defecto (decidido).** Falta de configuracion produce 503 (fail closed). Alternativa descartada: valores de prueba por defecto, que podrian llegar a produccion sin configurar.
4. **JWKS remoto (descartado para este cambio).** Obligaria a definir disponibilidad, cache y rotacion, fuera del alcance del Issue.
5. **Dependencia de FastAPI para la traduccion de errores (decidido).** Mantiene la forma `{"detail": ...}` que el frontend y ENDPOINTS.md ya usan.

## Estrategia incremental

1. **Caracterizacion (sin cambios de codigo).** Ejecutar `python tools/lab.py test api` y confirmar la linea base: 80 aprobadas y 7 `xfail`. Registrar el resultado en docs/TESTING.md.
2. **Mapeo spec-prueba.** Por cada requisito de la spec, enlazar al menos una prueba existente. Anotar los escenarios sin prueba: ausencia de token en registros, `sub` o `role` vacios o no textuales, y `alg` distinto de RS256 (ya cubierto por `wrong_algorithm`).
3. **Pruebas nuevas de caracterizacion.** Agregar pruebas para los huecos del punto 2 antes de tocar codigo. Deben fallar solo si el comportamiento cambia.
4. **Verificacion de regresion.** Ejecutar la suite completa con cobertura y confirmar que el modulo `security.py` mantiene 85% o mas.
5. **Decision sobre `Bearer` en minusculas.** Pedir decision humana. Si se decide cambiar, es un cambio de contrato y requiere actualizar ENDPOINTS.md y la spec antes de tocar codigo.
6. **Cierre.** Actualizar docs/TESTING.md con la ejecucion y validar el cambio con `openspec validate`.

Ninguna fase modifica comportamiento. Si la caracterizacion revela un comportamiento distinto al de la spec, se detiene el cambio y se reporta.

## Pruebas de caracterizacion necesarias

Antes de modificar cualquier codigo critico:

- Token firmado valido con `iss`, `aud`, `sub`, `role` y `exp` correctos: 200 (ya cubierto por fixtures).
- Cada rechazo de la spec: 401 con `detail` (ya cubierto por `invalid_auth`).
- Configuracion ausente y clave PEM invalida: 503 (ya cubierto).
- Nuevo: `sub` vacio, `sub` no textual, `role` vacio o no textual: 401. El codigo ya lo rechaza en `verify_token`, pero no hay prueba.
- Nuevo: un token rechazado no aparece en la salida de logs ni en la respuesta, salvo el `detail` fijo. Hoy el servicio no registra logs propios, por lo que la prueba debe verificar la ausencia de salida con `caplog` o equivalente.
- Nuevo: `Authorization` con token en mayusculas o sin prefijo. Solo como caracterizacion del comportamiento actual, marcado como pendiente de decision.

## Riesgos y trade-offs

- **Dependencia de la biblioteca JWT.** Una version nueva podria cambiar el tipo de excepcion (por ejemplo, `InvalidKeyError`). Mitigacion: las pruebas de clave invalida y HS256 detectan el cambio.
- **`authorization.replace("Bearer ", "")` reemplaza en cualquier posicion.** Un valor como `X Bearer Y` se recorta. Mitigacion: caracterizarlo y no cambiarlo sin decision.
- **Mensaje fijo en 401.** Oculta causas reales a quien integra, con coste de diagnostico. Es la postura de H-API-08 y se mantiene.
- **Fail closed sin configuracion.** Un despliegue sin variables cae en 503 en lugar de funcionar. Es intencional y `compose.yaml` ya exige las tres variables.
- **Cobertura.** Los casos nuevos son pocos y no deberian bajar la cobertura, pero hay que medirla.

## Rollback

- Como este cambio no modifica codigo, el rollback consiste en descartar los casos de prueba nuevos y mantener la linea base.
- Si una fase posterior introduce un regreso: revertir solo el commit de esa fase. Revertir la implementacion de H-API-02 reintroduce el token Base64 y el secreto embebido, por lo que no es una opcion aceptable.
- Para deshabilitar la verificacion en un entorno de emergencia sin tocar codigo: quitar `AUTH_JWT_PUBLIC_KEY`. El servicio responde 503 y no acepta tokens. No existe un modo que acepte tokens sin verificar.
