# Plan de correccion

## Considera todo esto APROBADO

## API

### Base y limites
- Alcance: componente `api/`; al iniciar, H-API-01 a H-API-07 figuraban como `Pendiente` en `HALLAZGOS.md`. Durante este paso se resolvieron H-API-01, H-API-03 y H-API-05. H-API-02 queda pendiente hasta comprobar interoperabilidad con el emisor real; H-API-04 sigue pendiente por falta de politica de carga.
- `docs/ENDPOINTS.md` no existe. Se toma como referencia provisional el contrato observado en `HALLAZGOS.md`; no se presenta como contrato acordado.
- Mantener rutas, formatos de respuesta y codigos HTTP observados para casos validos. Las correcciones de autenticacion, autorizacion y errores cambian comportamientos inseguros; documentar sus efectos y resolver las decisiones de compatibilidad antes de implementarlas.
- Escribir y ejecutar la caracterizacion indicada en cada apartado antes de modificar codigo. Registrar resultados reales; no asumir aprobaciones ni resultados.
- Aplicar las capas de ruta, servicio y repositorio de `docs/GOOD_PRACTICES.md`. Cada funcion con una responsabilidad, sin duplicacion ni anidamiento profundo, y sin numeros magicos. Meta de cobertura: 85% o superior del codigo modificado.

### Ejecuciones previas a la implementacion
| componente | IDs relacionados | comando | resultado |
|---|---|---|---|
| api | H-API-01 a H-API-07 | `python -m pytest -q` con el Python global | No ejecuto pruebas: ese interprete no tiene instalado `pytest`. |
| api | H-API-02, H-API-06, H-API-07 | `./.venv/Scripts/python.exe -m pytest -q` desde `api/`, antes de agregar caracterizaciones | 4 pruebas pasaron. |
| api | H-API-01, H-API-03, H-API-04, H-API-06, H-API-07 | `./.venv/Scripts/python.exe -m pytest -q` desde `api/`, con caracterizaciones | 9 pruebas pasaron. |
| api | H-API-01 a H-API-07 | `./.venv/Scripts/python.exe ../tools/lab.py test api` desde `api/` | 9 pruebas pasaron; cobertura total de `app`: 95.54%, gate de 85% aprobado. No se midio aun la cobertura del diff, pues todavia no hay cambios de implementacion. |

### Ejecuciones durante implementacion
| componente | IDs relacionados | comando o verificacion | resultado |
|---|---|---|---|
| api | H-API-01 | `./.venv/Scripts/python.exe -m pytest -q tests/test_api.py::test_task_fields_with_quotes_are_stored_as_literal_text` | 1 prueba paso: titulo y descripcion con apostrofos se guardan literalmente. |
| api | H-API-03 | `./.venv/Scripts/python.exe -m pytest -q tests/test_api.py::test_rejects_owner_other_than_authenticated_identity` | 1 prueba paso: query de tareas, resumen y payload de creacion con owner ajeno reciben 403. |
| api | H-API-02 | `./.venv/Scripts/python.exe -m pytest -q tests/test_api.py::test_accepts_signed_jwt` antes de reemplazar el verificador legacy | Caracterizacion roja esperada: el JWT firmado recibio 401; la prueba fijaba el comportamiento objetivo antes del cambio. |
| api | H-API-02 | `./.venv/Scripts/python.exe -m pytest -q tests/test_api.py::test_accepts_signed_jwt tests/test_api.py::test_rejects_invalid_token tests/test_api.py::test_rejects_jwt_with_invalid_claims` | 6 pruebas pasaron: JWT valido aceptado; token invalido, firma, issuer, audience y expiracion incorrectos rechazados. |
| api | H-API-01, H-API-02, H-API-03, H-API-06, H-API-07 | `./.venv/Scripts/python.exe ../tools/lab.py test api` antes de actualizar SCA | 14 pruebas pasaron; cobertura total de `app`: 93.96%, gate de 85% aprobado. |
| api | H-API-05 | `./.venv/Scripts/python.exe -m pip check` antes de actualizar dependencias | No encontro requisitos rotos. |
| api | H-API-05 | PyPI y GitHub/OSV advisories para los pines y versiones actuales | `urllib3==2.5.0` afectado por CVE-2025-66418 y CVE-2025-66471 (fix 2.6.0), y advisories posteriores (fixes 2.6.3, 2.7.0 y 2.8.0). `python-multipart==0.0.21` afectado por CVE-2026-24486, CVE-2026-40347, CVE-2026-42561, CVE-2026-53538/53539/53540; fixes publicados hasta 0.0.31. Se fijaron los releases vigentes 2.8.0 y 0.0.33; PyPI lista `vulnerabilities: []` para ambos al consultarlos. |
| api | H-API-05 | `./.venv/Scripts/python.exe -m pip install -r requirements.txt -r requirements-dev.txt` | Instalados `urllib3==2.8.0` y `python-multipart==0.0.33` en `api/.venv`. |
| api | H-API-05 | `./.venv/Scripts/python.exe -m pytest -q tests/test_api.py::test_uploads_requirement tests/test_api.py::test_characterizes_unrestricted_upload_extension` | 2 pruebas pasaron; las cargas validas mantienen su respuesta observada con la nueva version del parser. |
| api | H-API-05 | `./.venv/Scripts/python.exe -m pip check` despues de actualizar | No encontro requisitos rotos. |
| api | H-API-01, H-API-02, H-API-03, H-API-05, H-API-06, H-API-07 | `./.venv/Scripts/python.exe ../tools/lab.py test api` despues de actualizar | 14 pruebas pasaron; cobertura total de `app`: 93.96%, gate de 85% aprobado. |
| api | H-API-06 | `./.venv/Scripts/python.exe -m pytest -q` despues de extraer routers, servicios y repositorios | 14 pruebas pasaron; rutas, status, respuestas, datos iniciales, archivos y lifecycle conservaron el comportamiento caracterizado. |
| api | H-API-07 | `./.venv/Scripts/python.exe -m pytest -q tests/test_api.py::test_rejects_task_payload_with_wrong_field_type tests/test_api.py::test_backend_health_returns_generic_error` antes de implementar modelos/errores genericos | 2 pruebas fallaron como se esperaba: tipo incorrecto recibia 201 y health exponia `local test failure`. |
| api | H-API-07 | El mismo comando enfocado despues de implementar Pydantic y respuesta generica | 2 pruebas pasaron: tipo incorrecto recibe 422 y health devuelve texto generico. |
| api | H-API-02 | `./.venv/Scripts/python.exe -m pytest -q tests/test_api.py::test_rejects_malformed_authorization_header tests/test_api.py::test_reports_missing_jwt_configuration` | 2 pruebas pasaron: cabecera malformada recibe 401 y configuracion ausente recibe 503 generico. |
| api | H-API-01 a H-API-07 | `./.venv/Scripts/python.exe ../tools/lab.py test api` al cierre de implementacion | 17 pruebas pasaron; cobertura total de `app`: 97.86%. `security.py` 95%, `services/health.py` 94%, `repositories/tasks.py` 86%; demas archivos modificados completos. Gate de 85% aprobado. |
| api | H-API-02, H-API-06, H-API-07 | `./api/.venv/Scripts/python.exe -m pytest -q api/tests/test_api.py::test_creates_task_and_summary` lanzado desde la raiz | Error de recoleccion por `ModuleNotFoundError: app`; no se ejecuto la prueba porque el cwd era incorrecto. |
| api | H-API-07 | `./.venv/Scripts/python.exe -m pytest -q tests/test_api.py::test_creates_task_and_summary` desde `api/` | 1 prueba paso; se verificaron los campos del response y el resumen completo (`byStatus`, `highPriorityOpen`). |

### H-API-01 — Consultas SQL construidas por concatenacion
- **Hallazgo:** H-API-01, vulnerabilidad alta, estado `Resuelto`.
- **Problema:** filtros e inserts incorporan directamente valores de `owner` y del payload en SQL.
- **Cambio propuesto:** mover el acceso a datos a un repositorio y usar parametros SQLite en filtros, inserts y consultas posteriores al insert. No interpolar valores recibidos en instrucciones SQL.
- **Archivos previstos:** `api/app/repositories/tasks.py` (nuevo), `api/app/services/tasks.py` (nuevo), `api/app/routes/tasks.py` (nuevo), `api/app/main.py` y `api/tests/test_api.py`.
- **Caracterizacion previa:** en `api/tests/test_api.py`, conservar pruebas de listado y creacion con los formatos actuales; agregar casos con comillas ordinarias en titulo y descripcion que verifiquen que se almacenan y recuperan como texto literal. Ejecutar y registrar la linea base antes de tocar el acceso a datos.
- **Compatibilidad pendiente:** conservar el orden, campos y status HTTP observados en `/api/tasks`; la separacion de capas no debe cambiar la forma de la respuesta.

### H-API-02 — Token Base64 con secreto embebido y sin firma
- **Hallazgo:** H-API-02, vulnerabilidad alta, estado `Pendiente` hasta comprobar interoperabilidad con el emisor real.
- **Problema:** la dependencia de identidad decodifica Base64 y compara un secreto fijo; no verifica firma, emisor ni audiencia.
- **Cambio implementado, pendiente de resolucion:** `api/app/security.py` valida JWT firmado HS256, emisor, audiencia, expiracion y claims requeridos. Lee `WORKSHOP_JWT_SECRET`, `WORKSHOP_JWT_ISSUER`, `WORKSHOP_JWT_AUDIENCE` y `WORKSHOP_JWT_ALGORITHM` del entorno; el algoritmo admitido en este cambio es HS256. PyJWT 2.15.1 se fijo en `api/requirements.txt` tras revisar advisories.
- **Archivos tocados:** `api/app/security.py`, `api/app/models.py`, routers en `api/app/routes/`, `api/requirements.txt` y `api/tests/test_api.py`.
- **Caracterizacion previa:** probar que un token actualmente valido permite acceder a una ruta protegida y que un token invalido o expirado recibe HTTP 401. Registrar el formato heredado y los campos de respuesta de error antes de sustituirlo; despues, añadir casos para firma invalida, emisor y audiencia incorrectos, y expiracion.
- **Compatibilidad pendiente:** el emisor actual no se inspecciono porque auth esta fuera del alcance. Configurar el emisor y la API con las mismas variables/claims antes del despliegue. Las pruebas usan solo una clave ficticia; no se verifico interoperabilidad real.

### H-API-03 — Autorizacion permite elegir el propietario
- **Hallazgo:** H-API-03, vulnerabilidad alta, estado `Resuelto`.
- **Problema:** `owner` de query o del cuerpo puede determinar el propietario consultado o asignado, en vez de derivarse de la identidad autenticada.
- **Cambio aplicado:** el router obtiene el propietario de la identidad verificada y rechaza con HTTP 403 un `owner` distinto en query o payload. Los filtros SQL usan ese propietario.
- **Archivos previstos:** `api/app/routes/tasks.py` (nuevo), `api/app/services/tasks.py` (nuevo), `api/app/repositories/tasks.py` (nuevo), `api/app/main.py` y `api/tests/test_api.py`.
- **Caracterizacion previa:** crear tareas de dos identidades y registrar el comportamiento actual de `GET /api/tasks?owner=...`, `GET /api/summary?owner=...` y `POST /api/tasks` con `owner`. Luego agregar pruebas de regresion que verifiquen que cada identidad solo lee y asigna sus propios registros.
- **Compatibilidad:** politica confirmada por el usuario: rechazar con HTTP 403; rutas y formas de respuesta se mantienen.

### H-API-04 — Nombre de archivo sin normalizar ni limites declarados
- **Hallazgo:** H-API-04, vulnerabilidad alta, estado `Pendiente`.
- **Problema:** el nombre recibido se usa para formar la ruta destino y el archivo se lee completo sin limites visibles de extension o tamaño.
- **Cambio propuesto:** validar y normalizar el nombre, restringir extensiones permitidas y limitar el tamaño antes de guardar. Mantener la escritura dentro del directorio configurado y evitar leer archivos mayores al limite en memoria. Definir allowlist y limite como configuracion con nombres claros, no como valores magicos.
- **Archivos previstos:** `api/app/routes/requirements.py`, `api/app/services/requirements.py`, `api/app/repositories/requirements.py`, `api/app/main.py` y `api/tests/test_api.py`.
- **Caracterizacion previa:** preservar el caso valido existente de `requirements.txt` y registrar status y campos de respuesta. Agregar pruebas para nombre con traversal, extension no permitida y tamaño en el limite y por encima del limite; verificar que los casos rechazados no escriben fuera del directorio de uploads.
- **Compatibilidad pendiente:** acordar allowlist, limite y status/mensaje de rechazo antes de implementar; esos valores no se deducen del contrato actual. Conservar respuesta y almacenamiento para archivos validos admitidos.

### H-API-05 — Dependencias candidatas a revision SCA
- **Hallazgo:** H-API-05, sugerencia baja, estado `Resuelto`.
- **Problema:** `urllib3` y `python-multipart` usan los pines señalados en `RETO.md`, pero todavia no se verifico si un advisory afecta las versiones resueltas.
- **Cambio aplicado:** PyPI/OSV/GitHub confirmaron advisories para `urllib3==2.5.0` y `python-multipart==0.0.21`. Se actualizaron los pines a las versiones vigentes `urllib3==2.8.0` y `python-multipart==0.0.33`; ambas aparecen sin vulnerabilidades listadas por PyPI al verificarlas.
- **Archivos previstos:** `api/requirements.txt` y `api/tests/test_api.py`; actualizar archivos adicionales de dependencias solo si el analisis confirma que forman parte de la resolucion usada.
- **Caracterizacion y correccion:** `pip check` no encontro conflictos antes ni despues; las pruebas multipart pasan con los pines nuevos y el gate completo queda en 17 pruebas, 97.81% de cobertura total.
- **Advisories:** urllib3 CVE-2025-66418/CVE-2025-66471 y avisos posteriores; python-multipart CVE-2026-24486, CVE-2026-40347, CVE-2026-42561, CVE-2026-53538/53539/53540. Los pines actuales superan las versiones corregidas indicadas por los advisories consultados.

### H-API-06 — Rutas, persistencia y reglas concentradas en `main.py`
- **Hallazgo:** H-API-06, refactor, severidad media, estado `Resuelto`.
- **Problema:** `main.py` crea la base, inicializa datos, registra rutas y mezcla validacion, reglas, SQL y serializacion.
- **Cambio aplicado:** routers FastAPI separados de servicios y repositorios; `main.py` compone la app; el repositorio inicializa SQLite/semillas; lifespan cierra la conexion. Health y archivos tambien tienen servicios/repositorios propios.
- **Archivos tocados:** `api/app/main.py`, `api/app/dependencies.py`, `api/app/models.py`, `api/app/routes/`, `api/app/services/`, `api/app/repositories/` y `api/tests/test_api.py`.
- **Caracterizacion previa:** antes de mover funciones, completar pruebas de contrato para las cinco rutas observadas: listado, creacion, resumen, carga de requerimiento y health. Verificar campos, valores por defecto, status HTTP, datos iniciales y cierre de la aplicacion con base temporal.
- **Compatibilidad pendiente:** no existe especificacion acordada en `docs/ENDPOINTS.md`; preservar provisionalmente rutas y respuestas observadas y documentar cualquier incompatibilidad antes de implementarla.

### H-API-07 — Tipado incompleto y manejo de errores demasiado amplio
- **Hallazgo:** H-API-07, bug, severidad media, estado `Resuelto`.
- **Problema:** payloads y respuestas usan `dict`/`Any`, hay capturas amplias de `Exception`, se exponen textos de excepcion y el resumen contiene condicionales anidados.
- **Cambio aplicado:** modelos Pydantic para requests/responses y `Identity`; defaults y nombres camelCase conservados; tipos invalidos reciben 422; errores de health son genericos y se capturan solo fallos de transporte; resumen usa conteo por status sin anidamiento profundo y constantes de dominio con nombre.
- **Archivos tocados:** `api/app/models.py`, `api/app/routes/`, `api/app/services/`, `api/app/security.py`, `api/app/main.py` y `api/tests/test_api.py`.
- **Caracterizacion previa:** fijar con pruebas los campos y defaults de tareas y resumen, el mapeo `created_at` a `createdAt`, status HTTP de requests validos y respuestas actuales ante token invalido y fallo de health. Agregar despues casos para payloads invalidos y comprobar que la respuesta no revela la excepcion interna.
- **Compatibilidad pendiente:** mantener nombres de campos, defaults y respuestas validas. Los errores genericos y la validacion Pydantic pueden cambiar detalles o rechazar entradas que hoy se convierten a texto; acordar ese comportamiento antes de implementarlo. Evitar duplicar modelos o manejo de errores en routers y servicios.

## Riesgos y pendientes restantes
- H-API-02: la API verifica `WORKSHOP_JWT_SECRET`, `WORKSHOP_JWT_ISSUER`, `WORKSHOP_JWT_AUDIENCE` y `WORKSHOP_JWT_ALGORITHM` (HS256); falta coordinar esos valores/claims con el emisor real, que queda fuera de alcance.
- H-API-04 sigue pendiente: no se eligieron allowlist de extensiones, tamaño maximo ni status de rechazo. No se aplico politica por suposicion.
- `docs/ENDPOINTS.md` no se creo porque este paso lo prohibe; el comportamiento observado queda registrado en `HALLAZGOS.md` y preservado por las pruebas.