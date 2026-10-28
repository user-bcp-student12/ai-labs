# PLAN

Seguimiento de correcciones para hallazgos de api. H-API-02 esta implementado; los demas hallazgos conservan su propio estado de aprobacion e implementacion.

## Aprobacion Humana
- Raquel
- 2026/10/26
- H-API-02, H-API-03, H-API-04, H-API-05

## Seleccion de alcance (api)

La seleccion original incluyo H-API-02, H-API-03, H-API-04 y H-API-05. H-API-02 ya fue aprobado e implementado; los otros hallazgos mantienen su propio estado. El campo de seleccion del OBJETIVO llego sin completar.

- H-API-02: token Base64 con secreto embebido (alta). Riesgo: tokens falsificables.
- H-API-03: el cliente elige `owner` (alta). Riesgo: lectura de datos de otro usuario.
- H-API-04: SQL concatenado (alta). Riesgo: consultas alteradas por comillas o entrada maliciosa.
- H-API-05: nombre de archivo sin normalizar, sin limite de tipo ni tamano (alta). Riesgo: escritura fuera de la carpeta de uploads.

Quedan fuera de este plan: H-API-01, H-API-06 a H-API-11 (otros pasos).

## Restricciones comunes

- Contrato observado: rutas, codigos y campos de respuesta estan documentados en `docs/ENDPOINTS.md`; no existe aprobacion formal general de todos los contratos.
- Consumidores: el frontend (web) usa `/api/tasks`. Para H-API-02 se conserva la cabecera y el contrato de las rutas; el emisor auth debe emitir JWT compatibles. No se leyo ni modifico codigo de web o auth.
- Dependencias: H-API-02 usa PyJWT con soporte criptografico para verificar RS256; no se implementa criptografia propia.
- Clean code (AGENTS.md): una responsabilidad por funcion, sin duplicacion, sin anidamiento profundo (guard clauses), sin numeros magicos (constantes con nombre).
- Orden de ejecucion: H-API-04 se corrigio antes; H-API-02 se implemento despues de coordinar el contrato del token con auth. H-API-03 y H-API-05 siguen fuera de este cambio.
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
- Cambio implementado:
  - JWT compacto RS256; la clave publica PEM, emisor y audiencia se obtienen obligatoriamente de `AUTH_JWT_PUBLIC_KEY`, `AUTH_JWT_ISSUER` y `AUTH_JWT_AUDIENCE`.
  - El verificador exige `sub`, `role`, `exp`, `iss` y `aud`, valida `iss`/`aud` y limita el algoritmo a RS256.
  - Tokens Base64 legados se rechazan. Configuracion ausente/invalida devuelve 503; credenciales invalidas devuelven 401 generico.
- Clean code: `app/security.py` contiene la verificacion; la dependencia de ruta mantiene la identidad como `username` y `role`.
- Archivos modificados: `api/app/main.py`, nuevo `api/app/security.py`, pruebas de API, `api/requirements.txt`, `compose.yaml`, `docs/ENDPOINTS.md` y `docs/TESTING.md`.
- Dependencias aprobadas: `PyJWT[crypto]==2.15.1` y `cryptography==50.0.2`.
- Caracterizacion y resultado:
  - Baseline previo: 49 passed, 9 xfailed.
  - Pruebas nuevas de configuracion antes de implementar: 4 fallos esperados por la falta de verificacion JWT y fail-closed.
  - Suite posterior: 80 passed, 7 xfailed; cobertura total 97%, `app/security.py` 93%.
  - C-02a: token firmado valido devuelve 200 en las rutas protegidas; se conserva el comportamiento permitido.
  - C-02b: token con formato invalido (`Bearer invalid`) devuelve 401. Ya cubierto por `test_rejects_invalid_token`. Debe mantenerse.
  - C-02c: token expirado devuelve 401.
  - C-02d: token Base64 legado o JWT con payload alterado devuelve 401.
- Coordinacion externa:
  - El usuario confirmo que auth emitira JWT RS256 compatibles. El servicio auth queda fuera de este alcance y no se inspecciono ni modifico.
  - El despliegue debe alinear la clave publica, `iss` y `aud` con el emisor. Los tokens legados no tienen compatibilidad temporal porque no es posible validar su autenticidad.

## Pendientes y decisiones

- Aprobacion humana de H-API-03 y H-API-05 y de sus decisiones pendientes.
- Confirmar con web el uso de `owner` (H-API-03).
- H-API-02: coordinacion del formato con auth confirmada por el usuario; repetir las pruebas JWT como regresion.

## Estado de ejecucion (api)

- H-API-04: ejecutado. Caracterizacion C-04 (api/tests/test_sql_characterization.py) antes del cambio: 6 pasan; C-04b, C-04e y C-04f registran 500 con comillas. Cambio en api/app/main.py. Despues: 10 pasan de 10 (4 existentes + 6 de caracterizacion), cobertura de app/main.py 92%, cwd api/.
- H-API-02: implementado y validado. H-API-03 y H-API-05 mantienen decisiones pendientes (403 frente a ignorar `owner`; extensiones y tamano de subida).
