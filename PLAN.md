# PLAN

Propuesta de correccion para hallazgos de api. Sin cambios de codigo todavia. Aprobacion humana: pendiente.

## Aprobacion Humana
- Raquel
- 2026/10/26
- H-API-02, H-API-03, H-API-04, H-API-05

## Seleccion de alcance (api)

Hallazgos de HALLAZGOS.md en estado "Pendiente" con severidad alta. El campo de seleccion del OBJETIVO llego sin completar; esta seleccion es una inferencia y debe confirmarse.

- H-API-02: token Base64 con secreto embebido (alta). Riesgo: tokens falsificables.
- H-API-03: el cliente elige `owner` (alta). Riesgo: lectura de datos de otro usuario.
- H-API-04: SQL concatenado (alta). Riesgo: consultas alteradas por comillas o entrada maliciosa.
- H-API-05: nombre de archivo sin normalizar, sin limite de tipo ni tamano (alta). Riesgo: escritura fuera de la carpeta de uploads.

Quedan fuera de este plan: H-API-01, H-API-06 a H-API-11 (otros pasos).

## Restricciones comunes

- Contrato observado (no hay `docs/ENDPOINTS.md`): rutas, codigos 201/401 y campos de respuesta en HALLAZGOS.md. Los cambios que afectan el contrato se marcan como "Decision pendiente".
- Consumidores: el frontend (web) usa `/api/tasks`. Cambios de token o de `owner` deben revisarse contra web y auth. Auth no se lee en este paso.
- Dependencias: no se agrega ninguna en este plan sin aprobacion. Si se aprueba PyJWT para H-API-02, la justificacion es verificar firma HS256, `exp` y `iss`/`aud` sin implementar criptografia propia; alternativa sin dependencia: `hmac` de la biblioteca estandar.
- Clean code (AGENTS.md): una responsabilidad por funcion, sin duplicacion, sin anidamiento profundo (guard clauses), sin numeros magicos (constantes con nombre).
- Orden de ejecucion: caracterizacion de todos los puntos, luego H-API-04, H-API-03, H-API-05 y H-API-02. H-API-02 va al final porque depende de la coordinacion con auth.
- Pruebas: `pytest` con cwd `api/`. Datos ficticios y SQLite temporal (`tmp_path`).

## H-API-04: SQL concatenado en filtros e inserts

- Hallazgo: H-API-04 de HALLAZGOS.md. Evidencia: api/app/main.py:70, api/app/main.py:84, api/app/main.py:93.
- Problema: `owner`, `title`, `description`, `status`, `priority` y `owner` se unen a la sentencia. Una comilla rompe la consulta; una entrada elaborada puede alterarla. Hipotesis a confirmar por prueba: una comilla en `owner` produce error no controlado (500).
- Cambio propuesto: usar parametros `?` en `list_tasks`, `create_task` y `summary`. Mover las tres consultas a funciones de repositorio pequenas (`find_tasks_by_owner`, `insert_task`, `find_owner_rows`), sin cambiar la firma de las rutas.
- Clean code: tres funciones de consulta de una sola responsabilidad. Sin duplicacion de la sentencia SELECT de columnas: una constante `TASK_COLUMNS`. Sin numeros magicos.
- Archivos a tocar: api/app/main.py (solo las tres consultas y la de lectura posterior al insert).
- Caracterizacion antes de tocar (api/tests/test_api.py, nuevo archivo de caracterizacion propuesto):
  - C-04a: `GET /api/tasks` sin `owner` devuelve 2 tareas sembradas. Ya cubierto por `test_lists_seeded_tasks`.
  - C-04b: `POST /api/tasks` con titulo `O'Reilly` devuelve el comportamiento actual. Hipotesis: error no controlado. Se registra el resultado real antes de cambiar.
  - C-04c: `POST /api/tasks` con titulo sin comillas devuelve 201 y `owner`. Debe mantenerse.
  - C-04d: `GET /api/summary` devuelve `total`, `byStatus` y `highPriorityOpen` con los datos sembrados. Debe mantenerse.
- Resultado esperado tras el cambio: C-04b devuelve 201 y guarda el titulo literal. C-04c y C-04d no cambian.
- Decision pendiente: ninguna. No cambia el contrato.

## H-API-03: el cliente elige el `owner`

- Hallazgo: H-API-03 de HALLAZGOS.md. Evidencia: api/app/main.py:68-69, api/app/main.py:91-92.
- Problema: `owner or identity["username"]` permite que cualquier usuario autenticado lea tareas y resumen de otro. Hecho observado en el codigo; no se ha ejecutado.
- Cambio propuesto: la identidad sale del token verificado. Si `owner` viene y no coincide con `identity["username"]`, responder 403. Si viene igual o no viene, comportamiento actual.
- Clean code: una funcion `resolve_owner(requested, identity)` con guard clauses. Usada por `list_tasks` y `summary`, sin duplicar el condicional.
- Archivos a tocar: api/app/main.py (`list_tasks`, `summary`, nueva funcion de resolucion).
- Caracterizacion antes de tocar:
  - C-03a: token de `student` sin `owner` lista 2 tareas de `student`. Debe mantenerse.
  - C-03b: token de `student` con `owner=trainer` lista la tarea de `trainer`. Comportamiento actual que se cambia. Se registra antes del cambio.
  - C-03c: token de `student` con `owner=student` lista sus tareas. Debe mantenerse.
- Decision pendiente: confirmar 403 frente a ignorar el parametro. Si web usa `owner` con otro usuario, hay que revisarlo antes de aprobar. Confirmar con web.

## H-API-05: nombre de archivo subido sin normalizar

- Hallazgo: H-API-05 de HALLAZGOS.md. Evidencia: api/app/main.py:109-111.
- Problema: `Path(selected_uploads) / str(file.filename)` acepta el nombre tal cual. Sin limite de extension ni de tamano. `await file.read()` carga todo el contenido en memoria. Hipotesis: un nombre con separadores puede escribir fuera de la carpeta. A confirmar en C-05c.
- Cambio propuesto:
  - Normalizar con `Path(name).name`; rechazar nombre vacio o `.`/`..` con 400.
  - Lista permitida de extensiones (propuesta: `.txt`, `.md`, `.pdf`). Decision pendiente.
  - Tamano maximo como constante con nombre (propuesta: 1 MiB). Decision pendiente.
  - Leer por bloques hasta el limite y rechazar con 413 si se excede.
  - Respuesta: `fileName` sigue siendo el nombre normalizado. Para nombres normales no cambia.
- Clean code: funciones separadas `safe_upload_name(name) -> str` y `read_limited(file, limit) -> bytes`. Sin condicionales anidados.
- Archivos a tocar: api/app/main.py (`upload_requirement` y helpers nuevos). Opcional: api/app/uploads.py si se decide separar.
- Caracterizacion antes de tocar:
  - C-05a: subir `requirements.txt` devuelve 201 y crea el archivo en uploads. Ya cubierto por `test_uploads_requirement`.
  - C-05b: subir `requirements.txt` devuelve `fileName`, `size` y `owner`. Debe mantenerse.
  - C-05c: subir con nombre con separadores de ruta. Se registra el comportamiento real antes de cambiar; no se asume.
  - C-05d: subir sin token devuelve 401. Debe mantenerse.
- Resultado esperado tras el cambio: C-05c no escribe fuera de uploads. Extension no permitida o archivo excesivo responden 400 o 413.
- Decision pendiente: extensiones permitidas y tamano maximo.

## H-API-02: token Base64 con secreto embebido

- Hallazgo: H-API-02 de HALLAZGOS.md. Evidencia: api/app/main.py:14, api/app/main.py:19-22.
- Problema: el token es Base64 con secreto constante en el codigo. Quien lo lea puede fabricar tokens. Sin firma verificada, emisor ni audiencia. Hecho observado en el codigo.
- Cambio propuesto:
  - Secreto desde variable de entorno (por ejemplo `WORKSHOP_JWT_SECRET`), sin valor por defecto en el codigo.
  - Verificacion real de firma HS256, `exp` y claims explicitos (`sub`, `role`, `iss`, `aud`). Ver dependencia en Restricciones comunes.
  - Los errores devuelven 401 con mensaje generico (H-API-08 es otro paso).
- Clean code: un modulo `app/security.py` con `verify_token(raw) -> Identity`. El resto de la app no conoce el formato.
- Archivos a tocar: api/app/main.py (`legacy_identity` pasa a delegar), nuevo api/app/security.py, api/tests/ (ajustar el helper `token`), requirements.txt solo si se aprueba una dependencia.
- Caracterizacion antes de tocar:
  - C-02a: token valido con formato actual devuelve 200 en `GET /api/tasks`. Comportamiento que cambia. Se registra antes de cambiar.
  - C-02b: token con formato invalido (`Bearer invalid`) devuelve 401. Ya cubierto por `test_rejects_invalid_token`. Debe mantenerse.
  - C-02c: token con expiracion pasada devuelve 401. Debe mantenerse.
  - C-02d: token fabricado con el secreto embebido devuelve 200 hoy. Se registra solo como evidencia del riesgo; el resultado esperado tras el cambio es 401.
- Decision pendiente y dependencia externa:
  - Auth emite tokens con su propio formato. El cambio debe coordinarse con auth antes de tocar `legacy_identity`. Sin esa coordinacion, el cambio rompe el login.
  - Confirmar si se aprueba la dependencia PyJWT o la implementacion con `hmac`.
  - Ambos cambios de token afectan a web (que guarda el token). Revisar antes de aprobar.

## Pendientes y decisiones

- Aprobacion humana del alcance (H-API-02, 03, 04, 05) y de las decisiones marcadas.
- Coordinacion con auth para el formato del token (H-API-02). No leida en este paso.
- Confirmar con web el uso de `owner` (H-API-03) y el formato de token (H-API-02).
- Ejecutar la caracterizacion con `pytest` desde `api/` antes de cualquier cambio. No ejecutada en este paso.

## Estado de ejecucion (api)

- H-API-04: ejecutado. Caracterizacion C-04 (api/tests/test_sql_characterization.py) antes del cambio: 6 pasan; C-04b, C-04e y C-04f registran 500 con comillas. Cambio en api/app/main.py. Despues: 10 pasan de 10 (4 existentes + 6 de caracterizacion), cobertura de app/main.py 92%, cwd api/.
- H-API-02, H-API-03, H-API-05: bloqueados. Tienen aprobacion de ID, pero siguen abiertas sus "Decision pendiente" (403 frente a ignorar owner; extensiones y tamano de subida; PyJWT o hmac y coordinacion con auth).
