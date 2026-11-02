# Plan de correccion

## Considera todo esto APROBADO

## API

### Base y limites
- Alcance: componente `api/`; los hallazgos H-API-01 a H-API-07 figuran como `Pendiente` en `HALLAZGOS.md`.
- `docs/ENDPOINTS.md` no existe. Se toma como referencia provisional el contrato observado en `HALLAZGOS.md`; no se presenta como contrato acordado.
- Mantener rutas, formatos de respuesta y codigos HTTP observados para casos validos. Las correcciones de autenticacion, autorizacion y errores cambian comportamientos inseguros; documentar sus efectos y resolver las decisiones de compatibilidad antes de implementarlas.
- Escribir y ejecutar la caracterizacion indicada en cada apartado antes de modificar codigo. Registrar resultados reales; no asumir aprobaciones ni resultados.
- Aplicar las capas de ruta, servicio y repositorio de `docs/GOOD_PRACTICES.md`. Cada funcion con una responsabilidad, sin duplicacion ni anidamiento profundo, y sin numeros magicos. Meta de cobertura: 85% o superior del codigo modificado.

### H-API-01 — Consultas SQL construidas por concatenacion
- **Hallazgo:** H-API-01, vulnerabilidad alta, estado `Pendiente`.
- **Problema:** filtros e inserts incorporan directamente valores de `owner` y del payload en SQL.
- **Cambio propuesto:** mover el acceso a datos a un repositorio y usar parametros SQLite en filtros, inserts y consultas posteriores al insert. No interpolar valores recibidos en instrucciones SQL.
- **Archivos previstos:** `api/app/repositories/tasks.py` (nuevo), `api/app/services/tasks.py` (nuevo), `api/app/routes/tasks.py` (nuevo), `api/app/main.py` y `api/tests/test_api.py`.
- **Caracterizacion previa:** en `api/tests/test_api.py`, conservar pruebas de listado y creacion con los formatos actuales; agregar casos con comillas ordinarias en titulo y descripcion que verifiquen que se almacenan y recuperan como texto literal. Ejecutar y registrar la linea base antes de tocar el acceso a datos.
- **Compatibilidad pendiente:** conservar el orden, campos y status HTTP observados en `/api/tasks`; la separacion de capas no debe cambiar la forma de la respuesta.

### H-API-02 — Token Base64 con secreto embebido y sin firma
- **Hallazgo:** H-API-02, vulnerabilidad alta, estado `Pendiente`.
- **Problema:** la dependencia de identidad decodifica Base64 y compara un secreto fijo; no verifica firma, emisor ni audiencia.
- **Cambio propuesto:** encapsular autenticacion en un componente de seguridad que verifique un JWT firmado, con emisor, audiencia y expiracion. Leer la clave desde configuracion externa y usar una clave ficticia aislada en pruebas. Elegir una biblioteca mantenida tras revisar dependencias y justificar cualquier alta en `api/requirements.txt`.
- **Archivos previstos:** `api/app/security.py` (nuevo), `api/app/config.py` (nuevo solo si hace falta para seguir la configuracion existente), `api/app/main.py`, `api/tests/test_api.py` y, si se justifica, `api/requirements.txt`.
- **Caracterizacion previa:** probar que un token actualmente valido permite acceder a una ruta protegida y que un token invalido o expirado recibe HTTP 401. Registrar el formato heredado y los campos de respuesta de error antes de sustituirlo; despues, añadir casos para firma invalida, emisor y audiencia incorrectos, y expiracion.
- **Compatibilidad pendiente:** el emisor actual de tokens no se inspecciono porque esta fuera del alcance. Coordinar con su responsable la migracion del formato antes de cambiar el token aceptado; no inventar una aprobacion ni reemplazar silenciosamente el contrato de autenticacion.

### H-API-03 — Autorizacion permite elegir el propietario
- **Hallazgo:** H-API-03, vulnerabilidad alta, estado `Pendiente`.
- **Problema:** `owner` de query o del cuerpo puede determinar el propietario consultado o asignado, en vez de derivarse de la identidad autenticada.
- **Cambio propuesto:** hacer que el servicio y el repositorio obtengan el propietario exclusivamente de la identidad verificada. No usar el `owner` enviado por el cliente para filtrar o asignar registros. Definir una respuesta consistente para solicitudes que intentan indicar otro propietario.
- **Archivos previstos:** `api/app/routes/tasks.py` (nuevo), `api/app/services/tasks.py` (nuevo), `api/app/repositories/tasks.py` (nuevo), `api/app/main.py` y `api/tests/test_api.py`.
- **Caracterizacion previa:** crear tareas de dos identidades y registrar el comportamiento actual de `GET /api/tasks?owner=...`, `GET /api/summary?owner=...` y `POST /api/tasks` con `owner`. Luego agregar pruebas de regresion que verifiquen que cada identidad solo lee y asigna sus propios registros.
- **Compatibilidad pendiente:** actualmente se acepta `owner` explicito. Acordar antes de implementar si un valor distinto se rechaza con HTTP 403 o se ignora en favor de la identidad; no cambiar silenciosamente el acceso observable. Mantener rutas y formas de respuesta.

### H-API-04 — Nombre de archivo sin normalizar ni limites declarados
- **Hallazgo:** H-API-04, vulnerabilidad alta, estado `Pendiente`.
- **Problema:** el nombre recibido se usa para formar la ruta destino y el archivo se lee completo sin limites visibles de extension o tamaño.
- **Cambio propuesto:** validar y normalizar el nombre, restringir extensiones permitidas y limitar el tamaño antes de guardar. Mantener la escritura dentro del directorio configurado y evitar leer archivos mayores al limite en memoria. Definir allowlist y limite como configuracion con nombres claros, no como valores magicos.
- **Archivos previstos:** `api/app/routes/requirements.py` (nuevo), `api/app/services/requirements.py` (nuevo), `api/app/storage/requirements.py` (nuevo solo si el almacenamiento necesita una capa propia), `api/app/config.py`, `api/app/main.py` y `api/tests/test_api.py`.
- **Caracterizacion previa:** preservar el caso valido existente de `requirements.txt` y registrar status y campos de respuesta. Agregar pruebas para nombre con traversal, extension no permitida y tamaño en el limite y por encima del limite; verificar que los casos rechazados no escriben fuera del directorio de uploads.
- **Compatibilidad pendiente:** acordar allowlist, limite y status/mensaje de rechazo antes de implementar; esos valores no se deducen del contrato actual. Conservar respuesta y almacenamiento para archivos validos admitidos.

### H-API-05 — Dependencias candidatas a revision SCA
- **Hallazgo:** H-API-05, sugerencia baja, estado `Pendiente`.
- **Problema:** `urllib3` y `python-multipart` usan los pines señalados en `RETO.md`, pero todavia no se verifico si un advisory afecta las versiones resueltas.
- **Cambio propuesto:** contrastar versiones y dependencias transitivas con advisories vigentes. Actualizar solo los paquetes afectados a versiones corregidas compatibles; no silenciar alertas ni modificar dependencias sin evidencia.
- **Archivos previstos:** `api/requirements.txt` y `api/tests/test_api.py`; actualizar archivos adicionales de dependencias solo si el analisis confirma que forman parte de la resolucion usada.
- **Caracterizacion previa:** registrar versiones instaladas y resultado de `python -m pip check`; ejecutar y guardar la linea base de `python -m pytest` desde `api/`. La revision de advisories es evidencia SCA, no una prueba funcional ni un CVE confirmado por este plan.
- **Compatibilidad pendiente:** no afirmar vulnerabilidad hasta verificar advisory, rango afectado y version corregida. Mantener la API funcional y sin añadir herramientas de escaneo como dependencia de runtime.

### H-API-06 — Rutas, persistencia y reglas concentradas en `main.py`
- **Hallazgo:** H-API-06, refactor, severidad media, estado `Pendiente`.
- **Problema:** `main.py` crea la base, inicializa datos, registra rutas y mezcla validacion, reglas, SQL y serializacion.
- **Cambio propuesto:** separar routers FastAPI, servicios de negocio y repositorios SQLite. Dejar en `main.py` la composicion de la aplicacion y el registro de routers; mantener inicializacion y cierre de recursos en un ciclo de vida claro. Reutilizar servicios y repositorios en lugar de duplicar consultas.
- **Archivos previstos:** `api/app/main.py`, `api/app/routes/tasks.py` (nuevo), `api/app/routes/requirements.py` (nuevo), `api/app/routes/health.py` (nuevo), `api/app/services/tasks.py` (nuevo), `api/app/services/requirements.py` (nuevo), `api/app/repositories/tasks.py` (nuevo) y `api/tests/test_api.py`.
- **Caracterizacion previa:** antes de mover funciones, completar pruebas de contrato para las cinco rutas observadas: listado, creacion, resumen, carga de requerimiento y health. Verificar campos, valores por defecto, status HTTP, datos iniciales y cierre de la aplicacion con base temporal.
- **Compatibilidad pendiente:** no existe especificacion acordada en `docs/ENDPOINTS.md`; preservar provisionalmente rutas y respuestas observadas y documentar cualquier incompatibilidad antes de implementarla.

### H-API-07 — Tipado incompleto y manejo de errores demasiado amplio
- **Hallazgo:** H-API-07, bug, severidad media, estado `Pendiente`.
- **Problema:** payloads y respuestas usan `dict`/`Any`, hay capturas amplias de `Exception`, se exponen textos de excepcion y el resumen contiene condicionales anidados.
- **Cambio propuesto:** introducir modelos Pydantic de entrada y salida con tipos y defaults compatibles para solicitudes validas; tipar identidad y respuestas; capturar errores esperados y devolver mensajes genericos sin texto interno. Extraer el calculo del resumen a una funcion pequeña, combinar condiciones simples y nombrar constantes de dominio cuando corresponda.
- **Archivos previstos:** `api/app/models.py` (nuevo), `api/app/routes/tasks.py` (nuevo), `api/app/services/tasks.py` (nuevo), `api/app/security.py` (nuevo, coordinado con H-API-02), `api/app/main.py` y `api/tests/test_api.py`.
- **Caracterizacion previa:** fijar con pruebas los campos y defaults de tareas y resumen, el mapeo `created_at` a `createdAt`, status HTTP de requests validos y respuestas actuales ante token invalido y fallo de health. Agregar despues casos para payloads invalidos y comprobar que la respuesta no revela la excepcion interna.
- **Compatibilidad pendiente:** mantener nombres de campos, defaults y respuestas validas. Los errores genericos y la validacion Pydantic pueden cambiar detalles o rechazar entradas que hoy se convierten a texto; acordar ese comportamiento antes de implementarlo. Evitar duplicar modelos o manejo de errores en routers y servicios.

## Pendientes antes de implementar
- Acordar la migracion del token con quien emite las credenciales; ese componente queda fuera del alcance de este plan.
- Definir como responder a un `owner` distinto del usuario autenticado.
- Definir extensiones permitidas, tamaño maximo y respuesta para cargas rechazadas.
- Verificar advisories SCA y registrar versiones afectadas/corregidas solo con evidencia.
- Crear `docs/ENDPOINTS.md` en el paso correspondiente y acordar alli cualquier cambio al contrato observado antes de implementarlo.