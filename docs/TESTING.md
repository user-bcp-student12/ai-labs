# Pruebas de API

## Alcance
- Componente: `api`.
- IDs cubiertos: H-API-01 a H-API-07.
- Fuente ejecutable: [api/tests/test_api.py](../api/tests/test_api.py).
- La API tiene cinco endpoints protegidos por JWT. Las pruebas JWT usan una clave local ficticia, issuer y audience de test.

## Matriz de casos
| endpoint | caso | tipo | resultado esperado |
|---|---|---|---|
| `GET /api/tasks` | Listado de tareas seeded para `student` (`test_lists_seeded_tasks`) | Camino feliz | HTTP 200; lista de dos tareas con los campos del contrato. |
| `GET /api/tasks` | Usuario autenticado sin tareas (`test_lists_no_tasks_for_authenticated_owner_without_tasks`) | Borde | HTTP 200; `[]`. |
| `GET /api/tasks` | Sin autenticación (`test_all_endpoints_reject_missing_authentication[tasks-list]`) | Error | HTTP 401; `{"detail":"Invalid token"}`. |
| `GET /api/tasks` | `owner` diferente al del JWT (`test_rejects_owner_other_than_authenticated_identity`) | Error | HTTP 403; mensaje genérico de propietario. |
| `GET /api/tasks` | Configuración JWT ausente (`test_all_endpoints_report_missing_auth_configuration[tasks-list]`) | Error | HTTP 503; `{"detail":"Authentication is not configured"}`. |
| `GET /api/tasks` | Método incorrecto (`test_all_endpoints_return_405_for_wrong_method[tasks-list]`) | Error | HTTP 405; `{"detail":"Method Not Allowed"}`. |
| `GET /api/tasks` | Excepción no controlada del servicio (`test_all_endpoints_return_generic_500_for_unhandled_errors[tasks-list]`) | Error | HTTP 500; cuerpo `Internal Server Error`, sin el texto interno. |
| `POST /api/tasks` | Crear tarea y consultar resumen (`test_creates_task_and_summary`) | Camino feliz | HTTP 201; respuesta con `id`, campos de tarea y `createdAt`; el resumen refleja la tarea. |
| `POST /api/tasks` | Objeto vacío y defaults (`test_characterizes_task_payload_defaults`) | Borde | HTTP 201; `title`/`description` vacíos, `status=TODO`, `priority=MEDIUM`, owner del JWT. |
| `POST /api/tasks` | Apóstrofos en título y descripción (`test_task_fields_with_quotes_are_stored_as_literal_text`) | Borde | HTTP 201; los textos se almacenan literalmente. |
| `POST /api/tasks` | Tipo incorrecto (`test_rejects_task_payload_with_wrong_field_type`) | Error | HTTP 422; error de validación Pydantic para `title`. |
| `POST /api/tasks` | `owner` ajeno (`test_rejects_owner_other_than_authenticated_identity`) | Error | HTTP 403. |
| `POST /api/tasks` | Sin autenticación/configuración, método incorrecto y excepción no controlada | Error | HTTP 401, 503, 405 y 500, respectivamente; tests parametrizados compartidos para todos los endpoints. |
| `GET /api/summary` | Conteos después de crear tarea (`test_creates_task_and_summary`) | Camino feliz | HTTP 200; `owner`, `total`, `byStatus` y `highPriorityOpen` coinciden con los datos. |
| `GET /api/summary` | Usuario sin tareas (`test_summarizes_empty_task_set`) | Borde | HTTP 200; `total=0`, `byStatus={}`, `highPriorityOpen=0`. |
| `GET /api/summary` | `owner` ajeno (`test_rejects_owner_other_than_authenticated_identity`) | Error | HTTP 403. |
| `GET /api/summary` | Sin autenticación/configuración, método incorrecto y excepción no controlada | Error | HTTP 401, 503, 405 y 500, respectivamente; tests parametrizados compartidos. |
| `POST /api/requirements` | Cargar archivo de texto (`test_uploads_requirement`) | Camino feliz | HTTP 201; respuesta de metadatos y archivo escrito en el directorio configurado. |
| `POST /api/requirements` | Archivo vacío (`test_accepts_empty_upload`) | Borde | HTTP 201; `size=0` y archivo vacío almacenado. |
| `POST /api/requirements` | Falta la parte `file` (`test_rejects_upload_without_file_part`) | Error | HTTP 422; error de campo requerido. |
| `POST /api/requirements` | Multipart malformado (`test_rejects_malformed_multipart_body`) | Error | HTTP 400; `{"detail":"There was an error parsing the body"}`. |
| `POST /api/requirements` | Sin autenticación/configuración, método incorrecto y excepción no controlada | Error | HTTP 401, 503, 405 y 500, respectivamente; tests parametrizados compartidos. |
| `POST /api/requirements` | Extensión sin allowlist, path traversal y límite de tamaño | Pendiente H-API-04 | No se fija resultado esperado: extensión permitida, límite y respuestas de rechazo no están acordados ni implementados. No se prueba la escritura fuera del directorio ni se codifica como éxito. |
| `GET /api/backend-health` | Backend simulado con HTTP 200 (`test_backend_health_returns_downstream_status_and_body`) | Camino feliz | HTTP 200; `status=200` y `body` contiene la respuesta decodificada como texto. |
| `GET /api/backend-health` | Backend simulado con HTTP 503 (`test_backend_health_preserves_downstream_error_status`) | Borde | HTTP 200 de la API; `status=503` y cuerpo downstream preservado. |
| `GET /api/backend-health` | Error de transporte (`test_backend_health_returns_generic_error`) | Error downstream | HTTP 200 de la API; `status=0` y mensaje genérico, sin texto de excepción. |
| `GET /api/backend-health` | Sin autenticación/configuración, método incorrecto y excepción no controlada | Error | HTTP 401, 503, 405 y 500, respectivamente; tests parametrizados compartidos. |

## Código de las pruebas
El archivo enlazado arriba contiene la suite ejecutable completa, incluidos los tests de caracterización previos. Estos fragmentos muestran la matriz común y los casos sensibles añadidos en este paso.

Matriz de endpoints protegidos utilizada por los tests parametrizados:
```python
PROTECTED_ENDPOINTS = (
    ("GET", "/api/tasks", {}),
    ("POST", "/api/tasks", {"json": {}}),
    ("GET", "/api/summary", {}),
    (
        "POST",
        "/api/requirements",
        {"files": {"file": ("requirements.txt", b"Local test", "text/plain")}},
    ),
    ("GET", "/api/backend-health", {}),
)
```

Error de autenticación parametrizado en las cinco rutas:
```python
@pytest.mark.parametrize(
    "method,path,request_kwargs",
    PROTECTED_ENDPOINTS,
    ids=["tasks-list", "tasks-create", "summary", "requirements", "health"],
)
def test_all_endpoints_reject_missing_authentication(
    method: str,
    path: str,
    request_kwargs: dict[str, object],
    tmp_path: Path,
) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.request(method, path, **request_kwargs)
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}
```

Autorización cruzada y borde de resumen vacío:
```python
def test_rejects_owner_other_than_authenticated_identity(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        tasks = client.get("/api/tasks", headers=headers(), params={"owner": "trainer"})
        summary = client.get("/api/summary", headers=headers(), params={"owner": "trainer"})
        created = client.post(
            "/api/tasks",
            headers=headers(),
            json={"title": "Foreign task", "owner": "trainer"},
        )
    assert tasks.status_code == 403
    assert summary.status_code == 403
    assert created.status_code == 403


def test_summarizes_empty_task_set(tmp_path: Path) -> None:
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/summary", headers=headers(username="nobody"))
    assert response.status_code == 200
    assert response.json() == {
        "owner": "nobody",
        "total": 0,
        "byStatus": {},
        "highPriorityOpen": 0,
    }
```

Health downstream exitoso y fallo de transporte:
```python
def test_backend_health_returns_downstream_status_and_body(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class HealthyResponse:
        status = 200
        data = b"{\"status\":\"UP\"}"

    class HealthyPoolManager:
        def request(self, *args: object, **kwargs: object) -> HealthyResponse:
            return HealthyResponse()

    monkeypatch.setattr(health_service.urllib3, "PoolManager", HealthyPoolManager)
    app = create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
    with TestClient(app) as client:
        response = client.get("/api/backend-health", headers=headers())
    assert response.status_code == 200
    assert response.json() == {
        "requestedBy": "student",
        "status": 200,
        "body": "{\"status\":\"UP\"}",
    }
```

## Ejecuciones y cobertura
Todas las pruebas se ejecutaron con cwd `api/`, Python 3.13.15, en Windows. El comando usa el virtualenv existente.

| comando | directorio | código de salida | resultado |
|---|---|---:|---|
| `./.venv/Scripts/python.exe -m pytest -q tests/test_api.py` | `api/` | 0 | 43 passed; un warning deprecado de AnyIO/Starlette. |
| `./.venv/Scripts/python.exe ../tools/lab.py test api` | `api/` | 0 | 43 passed; gate `--cov-fail-under=85` aprobado. HTML: `api/htmlcov/index.html`. |

Coverage.py se ejecutó con `branch=true`, `source=["app"]` y reporte de terminal/HTML. Cobertura global de `app`: **230/234 obligaciones combinadas de sentencia y rama (98,29%)**; equivale a 216/218 sentencias y 14/16 ramas cubiertas. Archivos relevantes: `security.py` 95%, `repositories/tasks.py` 86%; los demás módulos de `app` quedaron al 100% en este reporte. El gate mide la aplicación completa; en este paso no se modificó código de producción, así que no hay un denominador de diff de producción separado.

## Fallos, pendientes y propuestas
- **Fallos finales:** ninguno. En una primera iteración, tres pruebas de 500 devolvieron 422 porque el test usaba un override genérico de dependencia; se corrigieron para simular el error en cada servicio y se reejecutaron correctamente.
- **Pendiente H-API-04:** la suite cubre carga vacía y errores multipart documentados, pero no prueba extensión sin extensión, path traversal ni límite de tamaño. No existe política acordada que permita definir resultados esperados seguros. Tras acordar allowlist, normalización, límite y status de rechazo, añadir pruebas de rechazo para esos casos antes de implementar la validación.
- **Pendiente H-API-02:** JWT firmado con claves ficticias, firma, issuer, audience, expiración y configuración están cubiertos; falta coordinar y verificar un token emitido por el emisor real, que está fuera del alcance.
- **Prueba propuesta:** una vez disponible el contrato real del emisor, añadir un test de interoperabilidad con claims/configuración compartidos, sin secretos reales.