# Tasks

Issue: [#24](https://github.com/user-bcp-student12/ai-labs/issues/24) (H-AUTH-01). Todo el código y las pruebas se limitan a `auth/`; los comandos de prueba se ejecutan desde `auth/` y Git/OpenSpec desde la raíz de `ai-labs`.

## 1. Pruebas de caracterización (sin tocar código de producción)

- [ ] 1.1 Ejecutar `mvn test` desde `auth/` sobre el código actual y verificar que la prueba existente `logsInWithWorkshopUser` pasa (línea base).
- [ ] 1.2 En `AuthResourceTest`, ampliar la cobertura del login válido con `student` / `Workshop123!`: verificar 200, `token` no vacío, `user.username`, `user.displayName`, `user.role` y `expiresIn`; la prueba pasa contra el código actual.
- [ ] 1.3 En `AuthResourceTest`, añadir pruebas de credenciales incorrectas (contraseña errónea para `student` y usuario inexistente): verificar 401 y ausencia de `token`; pasan contra el código actual.
- [ ] 1.4 En `AuthResourceTest`, añadir pruebas de `username` y `password` en blanco o ausentes: verificar 400 con `Username is required` y `Password is required`; pasan contra el código actual.
- [ ] 1.5 En `AuthResourceTest`, añadir una prueba con cuerpo JSON nulo o vacío y registrar el estado y mensaje reales; si difieren de la spec (`400` / `Request is null`), detenerse y reconciliar la spec con `openspec-update-change` antes de continuar, sin modificar la prueba para forzar coincidencia.
- [ ] 1.6 Ejecutar `mvn test` desde `auth/` y verificar que todas las pruebas de este grupo pasan; confirmar con `git diff --stat` que solo cambió `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`.

## 2. Pruebas de los escenarios de inyección (rojas contra el código actual)

- [ ] 2.1 En `AuthResourceTest`, añadir la prueba con `' OR '1'='1` como `password` y un `username` existente (`student`): verificar que espera 401 sin `token` y que falla contra el código actual (responde 200).
- [ ] 2.2 En `AuthResourceTest`, añadir la prueba con `' OR '1'='1` como `username` y una contraseña arbitraria: verificar que espera 401 sin `token` y registrar si falla o ya pasa contra el código actual (por la precedencia de `AND`/`OR` puede no explotarse sin el payload también en `password`); si ya pasa, queda como guarda de regresión.
- [ ] 2.3 En `AuthResourceTest`, añadir la prueba con `' OR '1'='1` en `username` y en `password`: verificar que espera 401 sin `token` y que falla contra el código actual (responde 200).
- [ ] 2.4 Ejecutar `mvn test` desde `auth/` y verificar que fallan exactamente las pruebas de inyección que explotan el código actual y que las del grupo 1 siguen pasando.

## 3. Corrección en `LegacyDatabase.findByCredentials`

- [ ] 3.1 Modificar únicamente `findByCredentials` en `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java` para usar `PreparedStatement` con dos parámetros (`username`, `password`), las mismas columnas devueltas, el mismo mapeo a `UserRecord` y el mismo manejo de excepciones (`null`); verificar que firma y tipo de retorno no cambian y que `git diff` no toca otro método.
- [ ] 3.2 Verificar que el SQL ya no concatena `username` ni `password` (revisión del diff y `grep` de concatenación sobre `LegacyDatabase.java`).
- [ ] 3.3 Ejecutar `mvn test` desde `auth/` y verificar que todas las pruebas de los grupos 1 y 2 pasan sin haber editado las de caracterización.

## 4. Verificación final

- [ ] 4.1 Ejecutar `mvn verify` desde `auth/` y verificar en el reporte JaCoCo que el código modificado alcanza el 85% o más de cobertura.
- [ ] 4.2 Verificar con `git status` y `git diff --stat` desde la raíz que los únicos archivos funcionales modificados son `LegacyDatabase.java` y `AuthResourceTest.java`, y que `AuthResource`, `LegacyTokenUtil`, `pom.xml`, `api/` y `web/` no cambiaron.
- [ ] 4.3 Verificar uno por uno los criterios de aceptación del Issue #24 con su evidencia: consulta parametrizada (3.1, 3.2), login válido 200 (1.2), inyección 401 sin `token` (2.1-2.3 en verde), y `mvn test` pasando desde `auth/` (3.3).
- [ ] 4.4 Ejecutar `openspec validate prevent-auth-login-sql-injection` desde la raíz y verificar que el cambio sigue siendo válido.

## Workflow follow-up

- Revisión humana de los cambios y de la ejecución real de pruebas antes de integrar.
- Archivar el cambio OpenSpec cuando se cumplan los requisitos de revisión del proyecto.
