---
name: pr-test-review
description: "Revisa Pull Requests exclusivamente desde la calidad y cobertura de sus pruebas. Usa GitHub MCP para fijar los SHA de base y cabeza, analizar el diff y entregar un informe local sin publicar una revisión."
---

# Revisión de Pull Request: pruebas

## Alcance y criterio

Revisa únicamente si las pruebas del PR ejercitan los comportamientos que el diff agrega o modifica y comprueban resultados y regresiones relevantes. No evalúes seguridad, compatibilidad, estilo ni otros aspectos del PR.

Una prueba aporta evidencia para un comportamiento cuando verifica un resultado observable o una condición relevante, y no solo ejecuta el código o comprueba que no ocurrió una excepción. Considera el contexto de la misma versión antes de señalar una brecha: puede haber cobertura en otra prueba existente.

## Entradas

- URL del PR o propietario, repositorio y número.
- Si no se puede identificar el PR de forma inequívoca, solicita el dato faltante antes de continuar.

## Procedimiento

1. **Consultar el PR mediante GitHub MCP.** Usa `github-mcp-server-pull_request_read` con `method: "get"` para obtener los metadatos. Registra el enlace canónico y los SHA completos de `base.sha` y `head.sha`. No uses nombres de ramas como sustituto de esos SHA.
2. **Fijar la versión revisada.** Usa `github-mcp-server-pull_request_read` con `method: "get_diff"` para obtener el diff. Confirma los SHA del PR otra vez al terminar de recopilar la evidencia. Si la base o la cabeza cambió durante la revisión, vuelve a obtener el diff y revisa la versión nueva desde el comienzo; si no puedes obtener una instantánea coherente, detente y decláralo.
3. **Delimitar los cambios relevantes.** Identifica en el diff los comportamientos agregados o modificados y los cambios de pruebas relacionados. Usa `method: "get_files"` si necesitas el inventario de archivos. No conviertas una observación ajena al criterio de pruebas en un hallazgo.
4. **Comprobar cobertura en la versión exacta.** Si el diff no basta para decidir si existe una prueba, consulta el código relacionado con `github-mcp-server-get_file_contents`, especificando el SHA de cabeza registrado en `sha`. Para comparar con la base, usa el SHA de base. Limita la consulta a los archivos necesarios y no uses la rama actual ni un checkout sin verificar como contexto.
5. **Evaluar cada posible brecha.** Busca una prueba del comportamiento esperado, sus condiciones relevantes y al menos una regresión razonable. Separa la ausencia comprobada de cobertura en los archivos pertinentes de la falta de evidencia en el diff; no declares una brecha solo porque un test no aparece junto al cambio.
6. **Clasificar con prudencia.**
   - **Defecto demostrado en una prueba:** el diff muestra directamente que una prueba nueva o modificada comprueba una condición equivocada, omite una aserción necesaria para lo que afirma cubrir o no puede detectar el fallo descrito. Cita la línea que lo demuestra y explica una aserción o caso que lo confirmaría.
   - **Riesgo por confirmar:** el cambio de comportamiento parece carecer de una prueba suficiente, pero el código consultado no permite demostrar que ninguna prueba existente lo cubre, o el resultado depende de comportamiento de ejecución no comprobado. Explica qué prueba, ejecución o evidencia permitiría confirmarlo.
   - No llames “defecto demostrado” a una posibilidad, una suposición ni a una prueba simplemente ausente del diff.
7. **Ejecutar pruebas solo con evidencia de versión.** Si es viable ejecutarlas localmente, verifica primero que el código probado corresponde al SHA de cabeza y registra el comando exacto, su resultado y cualquier limitación. No cambies archivos del PR para completar la revisión. Si no las ejecutas, indícalo expresamente. Los estados de CI, si se consultan, son resultados remotos y no pruebas ejecutadas localmente; no son necesarios para cumplir este criterio.
8. **Escribir una entrega local.** Crea `PR-REVIEW-<numero>-tests.md` en la raíz del workspace. Incluye la información y secciones descritas en **Formato de entrega**. No escribas la revisión en GitHub: no publiques comentarios, una review, un estado ni una aprobación.

## Evidencia y límites

- Cada observación debe apuntar a un archivo y línea o fragmento **del diff revisado**, y citar suficiente texto para que otra persona lo encuentre. Añade un enlace de GitHub al archivo en el SHA de cabeza cuando sea posible; usa como destino el commit, no una rama móvil.
- Si el contexto adicional no forma parte del diff, identifícalo como contexto de la versión fijada, separado de la evidencia del diff.
- Explica qué comportamientos y pruebas examinaste incluso cuando no encuentres problemas. Un informe sin hallazgos no equivale a aprobación.
- No afirmes que una prueba pasó si no la ejecutaste. No conviertas un estado remoto en ejecución local ni extrapoles un resultado de pruebas a calidad general del PR.
- Si el diff o el acceso MCP no permiten verificar un punto, informa la limitación en vez de rellenar el vacío con una inferencia.
- La entrega es un análisis local, no una revisión formal ni una aprobación del PR.

## Formato de entrega

Guarda el informe local con este esquema:

```markdown
# Revisión de pruebas del PR <número>

- PR: <enlace canónico>
- Repositorio: <propietario>/<repositorio>
- Base revisada: `<SHA completo>`
- Cabeza revisada: `<SHA completo>`
- Criterio: las pruebas ejercitan los comportamientos modificados y verifican resultados y regresiones relevantes.
- Alcance: pruebas; otros aspectos no revisados.

## Comprobaciones realizadas
- <Comportamientos modificados y pruebas/código consultados en la versión fijada>
- Ejecución local: <comando y resultado, o "No ejecutada" con motivo>
- CI remoto: <resultado consultado y SHA, o "No consultado">

## Observaciones
### <ID>: <Defecto demostrado en una prueba | Riesgo por confirmar>
- Evidencia del diff: `<archivo>:<línea(s)>` — `"<fragmento breve>"`
- Contexto en la versión fijada: <solo si se consultó; identificar SHA y archivo>
- Qué indica: <explicación concreta del vacío o defecto>
- Cómo confirmarlo: <caso/assertion o comprobación específica y resultado esperado>
- Confianza: <alta | media | baja, con una razón breve>

## Resultado
<Hallazgos encontrados o "Sin observaciones dentro del criterio revisado", más límites relevantes. No es una aprobación.>
```

Si no hay observaciones, conserva la sección **Observaciones** y escribe “Ninguna”. No inventes evidencia, ejecuciones, resultados ni cobertura.
