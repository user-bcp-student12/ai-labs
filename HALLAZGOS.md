# HALLAZGOS

Seguimiento de hallazgos por componente. Discovery sin cambios de codigo.

## Estado de artefactos

- `docs/ENDPOINTS.md`: no existe. El contrato observado se deriva del codigo (seccion siguiente). No se creo en este paso.
- `docs/TESTING.md`: no existe. No se ejecutaron pruebas en este paso.
- `PLAN.md` y `prompts/`: no existen.
- Filas de otros componentes: el archivo no existia; no hay contenido previo que conservar.
- Git: no consultado en este paso.

## Contrato observado (api, no acordado)

Fuente: `api/app/main.py`. Todas las rutas usan `Authorization: Bearer <token>`, salvo que se indique lo contrario.

- `GET /api/tasks?owner=`: lista tareas. Sin `owner`, usa el usuario del token. Respuesta: lista de tareas (`id`, `title`, `description`, `status`, `owner`, `priority`, `createdAt`). api/app/main.py:67-75
- `POST /api/tasks`: crea tarea con `201`. Campos del cuerpo: `title`, `description`, `status` (por defecto TODO), `priority` (por defecto MEDIUM), `owner` (por defecto el usuario del token). api/app/main.py:77-88
- `GET /api/summary?owner=`: resumen `owner`, `total`, `byStatus`, `highPriorityOpen`. api/app/main.py:90-105
- `POST /api/requirements`: multipart con campo `file`. Responde `201` con `owner`, `fileName`, `storedAt`, `size`. api/app/main.py:107-112
- `GET /api/backend-health`: consulta `AUTH_HEALTH_URL` (por defecto `http://localhost:8080/q/health`). Responde `requestedBy`, `status`, `body`. api/app/main.py:114-121
- Flujo del token: el valor tras `Bearer ` se decodifica como Base64 y debe tener cuatro partes separadas por barra vertical (usuario, rol, expiracion en epoch, secreto). Valida el secreto y la expiracion. Sin firma, emisor ni audiencia. api/app/main.py:14, api/app/main.py:17-26
- Acceso a SQLite: `sqlite3.connect` en `create_app`, ruta por defecto `./data/workshop.db` (variable `WORKSHOP_DB_PATH`). Crea la tabla `tasks` y siembra 3 filas si esta vacia. api/app/main.py:29-45
- CORS: `allow_origins=["*"]` con `allow_credentials=True`. api/app/main.py:48-54

## Matriz de seguimiento

| id | componente | hallazgo | tipo | explicacion | evidencia (archivo:linea) | severidad | estado |
|---|---|---|---|---|---|---|---|
| H-API-02 | api | Token Base64 con secreto embebido | Vulnerabilidad | El token no estaba firmado y el secreto estaba en el codigo, permitiendo fabricar identidades o roles aceptados. | api/app/security.py:17-40, api/tests/test_endpoints_contract.py:88, api/tests/test_known_defects.py:65 | alta | Resuelto. Verificacion JWT RS256 con clave publica y claims `iss`, `aud`, `sub`, `role`, `exp`; tokens legados rechazados. |
| H-API-03 | api | Autorizacion: el cliente elige el `owner` | Vulnerabilidad | El parametro `owner` reemplaza la identidad del token. Cualquier usuario autenticado puede leer tareas y resumen de otro `owner`. | api/app/main.py:68-69, api/app/main.py:91-92 | alta | Pendiente |
| H-API-04 | api | SQL concatenado en filtros e inserts | Vulnerabilidad | `owner`, `title`, `description`, `status`, `priority` y `owner` se concatenan en SQL. Una comilla rompe la sentencia o altera la consulta, en lectura, escritura y resumen. | api/app/main.py:70, api/app/main.py:84, api/app/main.py:93 | alta | Resuelto. Consultas parametrizadas (list_tasks, create_task, summary) con funciones de consulta; caracterizacion en api/tests/test_sql_characterization.py. |
| H-API-05 | api | Nombre de archivo subido usado tal cual | Vulnerabilidad | `file.filename` se une a la carpeta de uploads sin normalizar, sin limite de extension ni de tamano. El nombre puede salir de la carpeta o sobrescribir archivos, y el contenido se carga completo en memoria. | api/app/main.py:109-111 | alta | Pendiente |
| H-API-01 | api | SCA: `urllib3 2.5.0` y `python-multipart 0.0.21` fijados | Vulnerabilidad | Versiones fijas que pueden tener advisories conocidos. El impacto depende del advisory, que no se verifico en este paso. | api/requirements.txt:4, api/requirements.txt:5 | media | Pendiente |
| H-API-06 | api | Rutas, SQL, token y serializacion en un solo archivo | Refactor | Todo vive dentro de `create_app`. Al importar el modulo se abre la base por defecto y se crea la app global. Dificulta pruebas aisladas y cambios seguros. | api/app/main.py:29-35, api/app/main.py:130 | media | Pendiente |
| H-API-08 | api | Detalle interno en respuestas de error | Vulnerabilidad | El 401 devuelve el texto de la excepcion del token y el health devuelve el error de red. Ambos exponen detalles internos al cliente. | api/app/main.py:26, api/app/main.py:121 | media | Pendiente |
| H-API-10 | api | Payload de tareas sin validacion de dominio | Bug | `title`, `status`, `priority` y `owner` se convierten a texto sin validar valores ni longitud. Se aceptan estados arbitrarios y, con `owner` en el cuerpo, se crean tareas para otro usuario. | api/app/main.py:79-83 | media | Pendiente |
| H-API-07 | api | Calidad: dict crudo, excepciones amplias, condicionales anidados y duplicacion | Refactor | Payload como `dict` sin modelo Pydantic, `except Exception` amplio y condicionales anidados. Los errores pueden pasar en silencio y las reglas de resumen son dificiles de verificar. | api/app/main.py:78, api/app/main.py:25, api/app/main.py:97-104, api/app/main.py:120 | baja | Pendiente |
| H-API-09 | api | CORS con origen comodin y credenciales | Vulnerabilidad | Cualquier origen puede llamar a la API con credenciales habilitadas. El riesgo es limitado porque el token va en la cabecera `Authorization`, no en cookies. | api/app/main.py:50-51 | baja | Pendiente |
| H-API-11 | api | Pruebas sin casos de autorizacion, SQL ni archivos maliciosos | Sugerencia | Las pruebas cubren el camino feliz y el token invalido. No cubren `owner` ajeno, comillas, nombres de archivo ni tamano. | api/tests/test_api.py:19, api/tests/test_api.py:27, api/tests/test_api.py:41, api/tests/test_api.py:54 | baja | Pendiente |

Hallazgos de RETO.md para api no encontrados en el codigo: ninguno. Los IDs H-API-08 a H-API-11 no figuran en RETO.md; se observaron en el codigo durante Discovery.

## Pendientes

- Verificar advisories de `urllib3 2.5.0` y `python-multipart 0.0.21` (H-API-01). No consultado.
- Confirmar por ejecucion los riesgos de H-API-03, H-API-04 y H-API-05 con datos ficticios locales. Pendiente.
- Ejecutar pruebas de `api/` con cwd `api/` para registrar la linea base. Pendiente.
- Revision y aprobacion humana de severidades y orden. Pendiente.
