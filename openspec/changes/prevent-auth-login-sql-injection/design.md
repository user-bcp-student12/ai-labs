# Design

## Context

Motivación y alcance en `proposal.md`; requisitos en `specs/auth-login/spec.md`. Componente afectado: `auth/` (Quarkus 3.27, Java 21, SQLite vía `sqlite-jdbc`, JUnit 5 + RestAssured, JaCoCo ya configurado).

Estado actual relevante (observado en el código):

- `AuthResource.login` valida request, `username` y `password` (400), llama a `LegacyDatabase.findByCredentials` y responde 401 si devuelve `null`; si no, emite el token con `LegacyTokenUtil.create` y responde 200 (`token`, `expiresIn`, `user{username, displayName, role}`, `debug`).
- `LegacyDatabase.findByCredentials` (`LegacyDatabase.java:32`) concatena `username` y `password` en el SQL y ejecuta con `Statement`. Cualquier excepción se imprime y el método devuelve `null`, es decir, termina en 401 (falla cerrada).
- `username` es `UNIQUE`, así que la consulta devuelve como máximo una fila. Las contraseñas están en texto plano en `legacy_users`.
- La conexión usa `AUTH_DB_URL` (por defecto `jdbc:sqlite:./data/workshop.db`, relativo al directorio de trabajo `auth/`). La única prueba actual (`AuthResourceTest`) cubre solo el login válido.
- `docs/ENDPOINTS.md` documenta solo `api/`; el contrato de `POST /auth/login` proviene del código, la prueba existente y el Issue #24.

## Goals / Non-Goals

**Goals:**
- Que `username` y `password` lleguen a la base de datos únicamente como valores enlazados, nunca como parte del texto SQL.
- Que los payloads de inyección produzcan el mismo resultado que cualquier credencial incorrecta (401, sin `token`).
- Dejar el comportamiento observable de los demás escenarios de la spec sin cambios, demostrado por pruebas.

**Non-Goals:**
- Refactorizar `AuthResource.login` (anidamiento, capas API/servicio/repositorio) o mover lógica entre clases; es un cambio revisable aparte según el contrato de `auth` en `AGENTS.md`.
- Hash de contraseñas, endurecimiento del token, secretos, CORS, mensajes de error o el `debug` de la respuesta.
- Cambiar el manejo de excepciones de `findByCredentials` (sigue devolviendo `null` ante fallos).
- Tocar `initialize()`, el esquema, los usuarios semilla o cualquier otro componente.

## Contratos protegidos

Se preservan, con prueba que los ancle antes del cambio:

| Contrato | Fuente |
|---|---|
| `POST /auth/login` con `student` / `Workshop123!` → 200, `user.username`, `token` no vacío, y demás campos de la respuesta (`expiresIn`, `user.displayName`, `user.role`) | Spec, requisito 1; `AuthResource.java` |
| Credenciales incorrectas → 401 sin `token` | Spec, requisito 3 |
| Request nulo / username vacío / password vacío → 400 con los mensajes actuales | Spec, requisito 4 |
| Ruta, método, `Content-Type` JSON y forma del request (`username`, `password`, `client`) | Issue #24 |

## Componentes afectados

- **Modificado:** `auth/src/main/java/com/bcp/workshop/auth/LegacyDatabase.java`, solo el método `findByCredentials`; firma pública y tipo de retorno (`UserRecord` o `null`) sin cambios.
- **Modificado (pruebas):** `auth/src/test/java/com/bcp/workshop/auth/AuthResourceTest.java`.
- **Sin cambios:** `AuthResource`, `LegacyTokenUtil`, `LoginRequest`, `UserRecord`, `pom.xml`, `application.properties`, `api/`, `web/`, `docs/`.

## Decisions

### D1. Consulta parametrizada con `PreparedStatement`
`findByCredentials` usará una sola consulta con dos marcadores (`username` y `password`) y enlazará ambos valores. Se conserva la misma sentencia lógica (igualdad de ambas columnas, mismas columnas devueltas) y el mismo mapeo a `UserRecord`.

- **Por qué:** es el criterio de aceptación del Issue, elimina la causa raíz y mantiene la semántica de coincidencia actual (comparación exacta, sensible a mayúsculas, una fila).
- **Alternativas descartadas:**
  - *Escapar o filtrar comillas/caracteres especiales:* frágil, incompleto por naturaleza y rompería contraseñas legítimas con caracteres especiales (p. ej. `Workshop123!`).
  - *Validar con lista de caracteres permitidos:* cambia el contrato para entradas válidas, lo cual está fuera de alcance.
  - *Buscar por `username` y comparar la contraseña en Java:* añade una segunda vía de comparación y cambia detalles de semántica sin ganancia para este hallazgo.
  - *ORM/Panache u otra librería:* dependencia nueva y cambio arquitectónico desproporcionado para una sola consulta.

### D2. Mantener el manejo de errores existente
Una excepción en la consulta sigue resultando en `null` y, por tanto, 401. Con esto, un fallo de la base de datos no puede conceder acceso (falla cerrada). Mejorar el diagnóstico queda fuera de este cambio.

### D3. Los escenarios de inyección se verifican por la API HTTP
Las pruebas nuevas usan el endpoint real (`@QuarkusTest` + RestAssured), como la prueba actual, para que validen el comportamiento observable de la spec y no el detalle interno. La verificación de que no hay concatenación se hace por revisión del diff del método y por el resultado de los escenarios de inyección.

## Estrategia incremental

Cambios pequeños y revisables por separado, todos dentro de `auth/`:

1. **Caracterización (sin tocar código de producción):** añadir pruebas que fijen el comportamiento actual que debe preservarse. Deben pasar contra el código actual.
2. **Prueba de la vulnerabilidad:** añadir los escenarios de inyección en `username` y en `password`. Deben fallar contra el código actual (devuelven 200), lo que demuestra que la prueba detecta el defecto.
3. **Corrección:** cambiar solo `findByCredentials` (D1).
4. **Verificación:** ejecutar `mvn test` desde `auth/`; todas las pruebas de pasos 1 y 2 deben pasar y no deben haberse modificado las de caracterización. Revisar la cobertura JaCoCo del código modificado (meta del repo: 85% o más).

## Pruebas de caracterización necesarias antes de modificar

Ejecutar y registrar primero el comportamiento real; esto fija la línea base:

- Login válido (`student`, y opcionalmente `trainer`): 200, `token` no vacío, `user.username`, `user.displayName`, `user.role`, `expiresIn`.
- Usuario válido con contraseña incorrecta, y usuario inexistente: 401 y sin `token`.
- `username` y `password` en blanco o ausentes: 400 con `Username is required` y `Password is required`.
- Cuerpo JSON nulo: registrar el estado y mensaje reales (ver Open Questions).
- Nuevas, tras la línea base: `' OR '1'='1` como `username` y como `password` → 401 y sin `token`.

## Risks / Trade-offs

- **[Los escenarios de la spec no coinciden con el comportamiento real en algún borde, p. ej. cuerpo nulo]** → La caracterización del paso 1 lo detecta antes de cambiar código; si hay diferencia se reconcilia la spec en lugar de modificar el comportamiento en silencio.
- **[Las pruebas comparten `./data/workshop.db` y los usuarios semilla]** → Las pruebas nuevas son de solo lectura sobre usuarios existentes; no insertan ni borran datos.
- **[Entradas con comillas ahora se tratan como texto literal]** → Es el efecto deseado; una contraseña legítima con `'` seguiría funcionando, lo cual se mejora respecto a hoy.
- **[Mensaje 401 que refleja el `username` recibido (`Invalid user <username> or password`)]** → Comportamiento preexistente fuera de alcance; no incluye `token`, por lo que cumple la spec. Se deja anotado para un hallazgo separado.
- **[Contraseñas en texto plano y token legado]** → Fuera de alcance; no se agravan con este cambio.
- **[Cobertura menor al 85% en el código modificado]** → El método modificado queda cubierto por las pruebas de login válido, inválido e inyección.

## Rollback

El cambio es local a un método y no toca esquema, datos, configuración ni contratos externos. Para revertirlo basta revertir el commit de la corrección (paso 3); no requiere migración. Revertirlo reintroduce la vulnerabilidad de H-AUTH-01, por lo que solo debe hacerse ante una regresión funcional demostrada y con el Issue #24 reabierto.

## Open Questions

- Comportamiento real de `POST /auth/login` con cuerpo vacío o JSON nulo (si llega a `AuthResource` como `null` o Quarkus responde antes). Se resuelve con la caracterización del paso 1; si difiere de la spec, se ajusta la spec sin cambiar la corrección propuesta.
