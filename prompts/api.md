## AMBITO
- Trabaja desde la raiz de ai-labs y modifica solo el componente `api/`.
- Lee las instrucciones aplicables, `README.md`, `RETO.md`,
	`docs/GOOD_PRACTICES.md` y la documentacion general necesaria.
- Este pedido requiere cambios en el codigo y sus pruebas. No modifiques
	`auth/` ni `web/`.
- Ejecuta Git desde la raiz. Ejecuta las pruebas desde `api/` o con
	`python tools/lab.py test api`.
- Usa IDs `H-API-NN`.

## CONTEXTO
- La API implementa sus endpoints en `api/app/main.py`.
- Analiza el flujo desde cada ruta HTTP hasta la validacion, la logica de
	negocio, el acceso a SQLite o a archivos y la respuesta.
- Consulta las pruebas existentes antes de refactorizar.
- No des por cierta la lista de endpoints de `RETO.md`: confirma los contratos
	en el codigo y las pruebas.

## OBJETIVO
- Refactoriza `api/app/main.py` para separar responsabilidades en capas:
	rutas HTTP, servicios para la logica de negocio y repositorios para el acceso
	a datos.
- Evita que cada endpoint valide entradas, construya consultas, acceda a SQLite
	y arme respuestas en una sola funcion.
- Sigue los estandares corporativos del repositorio y las mejores practicas de
	Python:
	- codigo legible e idiomatico;
	- responsabilidades claras;
	- tipado adecuado;
	- manejo explicito de errores.
- Mantén la API facil de probar, sin introducir abstracciones innecesarias.

## RESTRICCIONES
- Antes de refactorizar, agrega o ajusta pruebas de caracterizacion.
- Conserva los endpoints, formatos de respuesta y codigos HTTP que use el
	frontend.
- Mantén las consultas parametrizadas y la autorizacion ligada a la identidad.
- Valida nombre, tamaño y extension de los archivos subidos.
- Usa solo datos ficticios locales. No agregues secretos reales ni silencies
	alertas de seguridad.
- Sigue las convenciones, configuraciones de calidad y herramientas ya
	adoptadas por el proyecto. No agregues dependencias ni reglas de exclusion
	sin justificarlo.
- Evita cambios fuera de `api/`. Si falta un archivo o no puedes ejecutar una
	comprobacion, dilo.

## CRITERIOS DE ACEPTACION
- Separa rutas, servicios y repositorios de forma que cada capa tenga una
	responsabilidad definida, cubriendo las rutas y operaciones existentes.
- Conserva el comportamiento observable de la API y agrega pruebas para los
	contratos antes de cambiar su implementacion.
- Mantén consultas SQL parametrizadas, autorizacion por identidad y validacion
	de archivos.
- Ejecuta las pruebas relevantes y reporta sus resultados reales. No afirmes
	que una prueba paso si solo la propusiste.
- Procura una cobertura de 85% o superior para el codigo modificado y señala
	cualquier brecha que quede.

## FORMATO DE RESPUESTA
- Presenta una tabla con las columnas: `cambio | evidencia archivo:linea |
	prueba ejecutada y resultado | pendiente o riesgo`.
- Termina con preguntas abiertas y comandos no ejecutados.