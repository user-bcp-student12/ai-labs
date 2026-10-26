# TESTING

Registro de pruebas de ai-labs. Esta version documenta solo la seccion `api`. Las secciones `auth` y `web` no existen todavia.

## api

### Entorno y comandos

- **Directorio de ejecucion**: `api/` (cwd).
- **Interprete**: `api/.venv/Scripts/python.exe` (Python 3.13.15, pytest 9.0.2).
- **Comando principal** (desde `api/`):

```bash
.venv/Scripts/python.exe -m pytest --cov=app --cov-branch --cov-report=term-missing -p no:cacheprovider -rxX
```

- **Comando sin cobertura** (desde `api/`): `.venv/Scripts/python.exe -m pytest -p no:cacheprovider`.
- **Comando de defectos conocidos sin marcador** (desde `api/`): `.venv/Scripts/python.exe -m pytest tests/test_known_defects.py --runxfail -p no:cacheprovider -q --tb=line`. Sirve para ver el fallo real de cada defecto.

### Archivos de prueba

| archivo | contenido |
|---|---|
| `api/tests/test_api.py` | Pruebas existentes (4): listado, creacion y resumen, subida, token invalido. |
| `api/tests/test_sql_characterization.py` | Caracterizacion y correccion de H-API-04 (6): comillas en titulo, owner y resumen. |
| `api/tests/test_endpoints_contract.py` | Contrato de `docs/ENDPOINTS.md` (39): camino feliz, casos borde y cada error documentado. |
| `api/tests/test_known_defects.py` | Defectos conocidos (9) con `xfail` estricto y su ID. No adaptan la prueba al bug. |
| `api/tests/conftest.py` | Fixtures comunes: cliente, cabeceras de token, token invalido y builder de tokens. |

### Casos por endpoint

Fuente de los contratos: `docs/ENDPOINTS.md`. Los defectos conocidos se marcan como `xfail` estricto: el resultado esperado es el comportamiento deseado, no el actual.

| endpoint | caso | tipo | resultado esperado |
|---|---|---|---|
| GET /api/tasks | Lista las tareas del usuario del token con los campos documentados | camino feliz | 200, 2 tareas de `student`, claves exactas |
| GET /api/tasks | `owner` vacio usa la identidad del token | caso borde | 200, mismas 2 tareas |
| GET /api/tasks | `owner` sin tareas | caso borde | 200, `[]` |
| GET /api/tasks | `owner` con comilla (`O'Reilly`) | caso borde | 200, `[]` (H-API-04 resuelto) |
| GET /api/tasks | Token ausente, malformado, expirado o con secreto incorrecto (4 casos) | error 401 | 401, `detail` empieza por `Invalid token: ` |
| GET /api/tasks | Un usuario no lee tareas de otro `owner` | defecto conocido H-API-03 | No aparecen tareas de `trainer` (`xfail`) |
| GET /api/tasks | Token firmado con el secreto embebido | defecto conocido H-API-02 | 401 (`xfail`) |
| GET /api/tasks | El `detail` del 401 no contiene texto interno | defecto conocido H-API-08 | Sin `Incorrect padding` (`xfail`) |
| POST /api/tasks | Creacion valida, persiste y aparece en el listado | camino feliz | 201, claves exactas, `owner` = `student`, 3 tareas tras crear |
| POST /api/tasks | Payload vacio | caso borde | 201 con `title` y `description` vacios, `status` TODO, `priority` MEDIUM |
| POST /api/tasks | Comilla en `description` | caso borde | 201, texto literal guardado |
| POST /api/tasks | Token invalido (4 casos) | error 401 | 401, `detail` empieza por `Invalid token: ` |
| POST /api/tasks | Sin cuerpo | error 422 | 422, `detail[0].type` = `missing` |
| POST /api/tasks | Cuerpo lista | error 422 | 422, `detail[0].type` = `dict_type` |
| POST /api/tasks | `owner` de otro usuario en el cuerpo | defecto conocido H-API-03 | No se crea con `owner` ajeno (`xfail`) |
| POST /api/tasks | `status` fuera de dominio (`FOO`) | defecto conocido H-API-10 | 4xx (`xfail`) |
| GET /api/summary | Resumen con datos sembrados | camino feliz | 200, `{"owner":"student","total":2,"byStatus":{"TODO":1,"IN_PROGRESS":1},"highPriorityOpen":1}` |
| GET /api/summary | `owner` desconocido | caso borde | 200, total 0, `byStatus` vacio |
| GET /api/summary | `owner` vacio | caso borde | 200, resumen de `student` |
| GET /api/summary | `owner` con comilla | caso borde | 200, `total` 0 (H-API-04 resuelto) |
| GET /api/summary | Token invalido (4 casos) | error 401 | 401, `detail` empieza por `Invalid token: ` |
| GET /api/summary | Resumen de otro `owner` | defecto conocido H-API-03 | No revela datos de `trainer` (`xfail`) |
| POST /api/requirements | Subida valida | camino feliz | 201, `fileName`, `owner`, `size` 24, archivo guardado en `uploads/` |
| POST /api/requirements | Archivo vacio | caso borde | 201, `size` 0 |
| POST /api/requirements | Archivo sin extension (`notas`) | caso borde | 4xx (`xfail`; hoy 201) |
| POST /api/requirements | Archivo de 2 MiB | caso borde | 413 (`xfail`; hoy 201). Limite pendiente de decision |
| POST /api/requirements | Nombre `../escape.txt` | caso borde (seguridad) | No se escribe fuera de `uploads/` (`xfail`; hoy se escribe) |
| POST /api/requirements | Token invalido (4 casos) | error 401 | 401, `detail` empieza por `Invalid token: ` |
| POST /api/requirements | Sin campo `file` | error 422 | 422, `loc` = `["body","file"]` |
| GET /api/backend-health | Servicio consultado responde 200 | camino feliz | 200, `status` 200, `body` igual a la respuesta |
| GET /api/backend-health | Servicio consultado responde 503 | caso borde | 200, `status` 503 |
| GET /api/backend-health | Servicio inaccesible | error documentado | 200, `status` 0, `body` no vacio |
| GET /api/backend-health | Token invalido (4 casos) | error 401 | 401, `detail` empieza por `Invalid token: ` |

Total de casos: 49 pasan (4 existentes, 6 de H-API-04, 39 de contrato) y 9 defectos conocidos en `xfail`.

### Resultados ejecutados

Todos los resultados se ejecutaron desde `api/`, con el interprete `api/.venv`, el 2026-10-26.

| ejecucion | comando | codigo de salida | resultado |
|---|---|---|---|
| Suite completa con cobertura | `pytest --cov=app --cov-branch --cov-report=term-missing -p no:cacheprovider -rxX` | 0 | 49 passed, 9 xfailed |
| Defectos sin marcador | `pytest tests/test_known_defects.py --runxfail -p no:cacheprovider -q --tb=line` | no capturado (salida filtrada con `grep`) | 9 failed. Cada fallo coincide con su defecto (ver Fallos) |
| Cobertura del diff | `coverage json` + script con `git diff -U0 main -- api/app/main.py` | 0 | Ver Cobertura |

### Cobertura

- **Metodo de medicion**: coverage.py con `--cov-branch` sobre `app/` (origen definido en `api/pyproject.toml`). Reporte de la suite completa.
- **Cobertura global** (`app/main.py`, unico archivo no trivial): sentencias 107/107 (100%), ramas 14/16. Porcentaje reportado por coverage: 98.37% (tabla de la ejecucion: 98%). Las dos ramas no cubiertas (`123->116`, `124->116`) estan en el bloque de `summary` que no cambio en el diff.
- **Cobertura del codigo modificado**: el diff contra `main` solo cambia `api/app/main.py` y anade 29 lineas (`git diff -U0 main -- api/app/main.py`).
  - Numerador: 19 sentencias de las lineas anadidas que estan ejecutadas.
  - Denominador: 19 sentencias de las lineas anadidas.
  - Resultado: 19/19 = 100%.
  - Ramas en las lineas anadidas: 0/0 (ninguna linea anadida es una bifurcacion).
  - Metodo: interseccion de los rangos `+` de los hunks del diff con `executed_lines` y `missing_lines` del JSON de coverage.py.
  - Los tests nuevos no entran en la medicion, porque la meta aplica al codigo modificado de la app.
- **Umbral**: 85% (AGENTS.md). Cumplido en ambas mediciones.

## Registro de ejecuciones

| fecha | componente | IDs | ejecucion | codigo de salida | resultado |
|---|---|---|---|---|---|
| 2026-10-26 | api | H-API-04 | Caracterizacion previa al cambio (`test_sql_characterization.py`) | no capturado en esa ejecucion | 6 pasan; comillas responden 500 |
| 2026-10-26 | api | H-API-04 | Suite tras el cambio | 0 | 10 passed |
| 2026-10-26 | api | H-API-04, H-API-02, H-API-03, H-API-05, H-API-08, H-API-10 | Suite completa con contrato y defectos | 0 | 49 passed, 9 xfailed |
| 2026-10-26 | api | H-API-02, H-API-03, H-API-05, H-API-08, H-API-10 | Defectos sin marcador | no capturado | 9 failed por la causa documentada |

## Fallos

No hay fallos en la suite marcada (codigo de salida 0). Los 9 casos de `test_known_defects.py` son defectos abiertos y su resultado actual es el de la tabla de defectos:

| ID | prueba | resultado actual |
|---|---|---|
| H-API-03 | `test_user_cannot_list_another_owner_tasks` | Devuelve `Trainer notes` a `student` |
| H-API-03 | `test_user_cannot_summarize_another_owner` | Devuelve total 1 para `trainer` |
| H-API-03 | `test_user_cannot_create_task_for_another_owner` | Crea la tarea con `owner` `trainer` (201) |
| H-API-10 | `test_create_task_rejects_unknown_status` | Acepta `status` FOO (201) |
| H-API-05 | `test_upload_rejects_file_without_extension` | Acepta el archivo (201) |
| H-API-05 | `test_upload_rejects_file_over_size_limit` | Acepta 2 MiB (201) |
| H-API-05 | `test_upload_filename_cannot_escape_upload_dir` | Escribe `escape.txt` fuera de `uploads/` |
| H-API-02 | `test_token_built_with_embedded_secret_is_rejected` | Acepta el token (200) |
| H-API-08 | `test_invalid_token_detail_hides_internal_error` | El `detail` contiene `Incorrect padding` |

Estos fallos no se ocultan en el codigo de las pruebas. Se reportan aqui y en HALLAZGOS.md, que sigue con estado "Pendiente".

## Pendientes

- **Limite de tamano de subida**: la prueba espera 413 con 2 MiB. El valor es una propuesta de PLAN.md y sigue pendiente de decision.
- **Extensiones permitidas**: la prueba solo exige 4xx. La lista de extensiones sigue pendiente de decision.
- **Dependencia del entorno**: `test_health_unreachable_upstream_returns_status_zero` usa el puerto 9 en `127.0.0.1`. Si ese puerto esta abierto en la maquina, la prueba fallara.
- **Respuesta 500**: no hay prueba. `docs/ENDPOINTS.md` no la documenta como observada.
- **Secciones auth y web**: no hay pruebas para ellas en este paso.
- **Advertencias de FastAPI**: `on_event` esta deprecado (`app/main.py`, H-API-06). No afecta a los resultados.

## Pruebas propuestas (no ejecutadas)

- Comprobar la respuesta 413 y la lista de extensiones cuando se aprueben sus valores.
- Repetir la suite despues de cada cambio aprobado de H-API-02, H-API-03, H-API-05 y H-API-10. Al corregir un defecto, su `xfail` estricto fallara y debera quitarse el marcador.
- Revisar el puerto usado por la prueba de servicio inaccesible en un entorno sin puertos libres conocidos.
