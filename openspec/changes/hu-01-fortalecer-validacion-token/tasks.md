# Tasks

## 1. Caracterizacion previa al cambio

- [x] 1.1 Ejecutar `python tools/lab.py test api` y registrar en docs/TESTING.md (seccion api) la linea base: exit 0, 80 passed y 7 xfailed. Verificacion: el registro existe con esas cifras.
- [x] 1.2 Registrar en docs/TESTING.md (seccion api) la correspondencia de cada requisito de specs/api-token-authentication/spec.md con al menos una prueba. Verificacion: ningun requisito queda sin prueba o sin marca de hueco.
- [x] 1.3 Agregar en api/tests/test_authentication.py pruebas con `sub` vacio, `sub` no textual, `role` vacio y `role` no textual que esperen 401 con `detail`. Verificacion: `python tools/lab.py test api` pasa con las pruebas nuevas contra el codigo actual.
- [x] 1.4 Agregar en api/tests/test_authentication.py una prueba que, tras un rechazo por token invalido, verifique con `caplog` que ni el token ni la clave configurada aparecen en los registros ni en la respuesta. Verificacion: la prueba pasa contra el codigo actual.
- [x] 1.5 Agregar en api/tests/test_authentication.py pruebas que documenten el comportamiento actual de `Bearer` en minusculas y de un header sin prefijo, marcadas como pendientes de decision. Verificacion: ambas pruebas pasan y su nombre indica que caracterizan comportamiento pendiente.

## 2. Verificacion de contrato sin cambios funcionales

- [x] 2.1 Confirmar que no hay cambios en api/app con `git diff --stat -- api/app`. Verificacion: la salida esta vacia.
- [x] 2.2 Ejecutar `python tools/lab.py test api` con cobertura y confirmar que `app/security.py` y los cambios de pruebas cumplen la meta de 85% o superior. Verificacion: el reporte de cobertura muestra 85% o mas para el codigo modificado.
- [x] 2.3 Si una prueba de 1.3 a 1.5 falla, detener el cambio y reportar la divergencia frente a la spec antes de tocar codigo. Verificacion: el reporte de divergencia queda registrado en docs/TESTING.md.

## 3. Implementacion condicional

- [ ] 3.1 Solo si 2.3 detecta divergencia con la spec: escribir primero la prueba que falla y luego corregir el caso minimo en api/app/security.py o api/app/main.py. Verificacion: la prueba nueva pasa y la suite completa de api no registra regresiones.
- [ ] 3.2 Solo si 3.1 cambia el comportamiento observable: actualizar docs/ENDPOINTS.md en la seccion api para reflejar el cambio. Verificacion: el contrato documentado coincide con el comportamiento probado.

## 4. Documentacion y validacion final

- [x] 4.1 Actualizar la seccion api de docs/TESTING.md con la ejecucion final: comando, fecha y resultados. Verificacion: el registro contiene la ejecucion final con exit 0.
- [x] 4.2 Ejecutar `openspec validate hu-01-fortalecer-validacion-token` desde la raiz. Verificacion: el comando informa que el cambio es valido.

## Workflow follow-up

- Obtener decision humana sobre `Bearer` en minusculas y headers sin prefijo antes de archivar. Si cambia el contrato, reabrir specs y design.
- Revision humana del cambio antes de integrarlo, segun AGENTS.md.
- Archivar el cambio cuando los requisitos de revision se cumplan.
