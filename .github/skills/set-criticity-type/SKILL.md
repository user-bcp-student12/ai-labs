---
name: set-criticity-type
description: Asigna el tipo de criticidad (1, 2 o 3) a una historia de usuario según si implica cambio de código, si requiere pruebas intermedias en ambientes preproductivos y si el cambio va directamente a producción.
---

# Skill: Asignación de criticidad a historias de usuario

## 1) Metadata
- **Skill ID:** set-criticity-type
- **Version:** 0.1.0
- **Purpose:** Asignar un tipo de criticidad (1, 2 o 3) a una historia de usuario con base en reglas explícitas y evidencia de la propia HU.
- **Audience (roles):** Chapter/PO, Tech Lead, QA
- **When to use:** Al planificar o priorizar una HU que ya tiene especificación funcional y criterios de aceptación.
- **When NOT to use:** Incidentes P1 de producción, o cuando falte la especificación funcional o los criterios de aceptación.
- **Sensitive inputs:** No incluyas datos reales de clientes, credenciales, secretos, tokens ni URLs internas no autorizadas.
- **Expected output:** Tipo de criticidad con justificación y citas de la HU.

## 2) Inputs
- **Historia de usuario (HU):** enunciado de la historia.
- **Especificación funcional:** comportamiento esperado del cambio.
- **Criterios de aceptación:** condiciones verificables de la HU.

Si falta alguno de estos elementos, no asignes tipo: indica qué falta bajo **Preguntas abiertas**.

## 3) Reglas de clasificación
Evalúa las condiciones y aplica la primera regla que se cumpla:

1. **Tipo 1:** la HU no implica desarrollo ni cambio de código.
2. **Tipo 2:** la HU implica desarrollo de código, **y** no requiere pruebas intermedias en ambientes preproductivos, **y** el cambio va directamente a producción. Ambas condiciones deben estar confirmadas por la HU.
3. **Tipo 3:** cualquier otro caso.

Si la HU no confirma explícitamente las dos condiciones del Tipo 2, la clasificación es **3** y la duda se registra en **Preguntas abiertas**.

**Validación humana obligatoria para tipos 1 y 2:** la clasificación 1 o 2 solo es efectiva con la aprobación de un revisor humano distinto del desarrollador que implementará la HU. Mientras no exista esa aprobación, la criticidad efectiva es **3**. La propuesta de tipo 1 o 2 del Skill o de cualquier autor no basta para aplicarla.

## 4) Output
Devuelve **solo** un documento Markdown con estas secciones:

1. **Tipo de criticidad:** 1, 2 o 3.
2. **Evaluación de condiciones:**
    - ¿Implica desarrollo o cambio de código? (Sí / No / No determinado)
    - ¿Requiere pruebas intermedias en ambientes preproductivos? (Sí / No / No determinado)
    - ¿El cambio va directamente a producción? (Sí / No / No determinado)
3. **Justificación:** regla aplicada y razón de la clasificación.
4. **Evidencia de la HU:** citas textuales de la especificación o de los criterios de aceptación que sustentan cada respuesta.
5. **Preguntas abiertas:** datos faltantes o ambiguos que podrían cambiar la clasificación.
6. **Validación humana:** solo para tipo 1 o 2, estado (Pendiente / Aprobada / Rechazada), nombre del revisor y fecha. Si el estado no es Aprobada, la criticidad efectiva es 3.

## 5) Constraints
- Clasifica solo con evidencia presente en la HU; no inventes requisitos ni asumas pruebas o despliegues no declarados.
- No modifiques las reglas de clasificación.
- No asignes tipo 2 sin confirmar explícitamente ambas condiciones.
- No cierres ni apliques un tipo 1 o 2 sin aprobación humana registrada; el autor de la implementación no puede aprobar su propia clasificación.
- No incluyas datos sensibles ni secretos.
- Mantén la salida en una página.

## 6) Validation Rules
La salida es válida si:
- Asigna exactamente un tipo (1, 2 o 3), o indica que faltan datos y no asigna tipo.
- Responde las tres condiciones con Sí, No o No determinado.
- Cada respuesta tiene al menos una cita de la HU, o se marca como No determinado.
- Un Tipo 2 tiene ambas condiciones confirmadas por la HU.
- Un Tipo 1 no tiene indicios de cambio de código en la HU.
- Un Tipo 1 o 2 tiene aprobación humana registrada de un revisor distinto del implementador; sin ella, la criticidad efectiva es 3.

## 7) Evidence
Adjunta o referencia estos elementos en el PR o entrega:
- `SKILL.md` versionado.
- La HU clasificada con las citas usadas.
- La salida del Skill con el tipo asignado y su justificación.
- Registro de la validación humana del tipo 1 o 2 (revisor, fecha y decisión).

## 8) Glosario
- **Tipo 1:** la HU no implica desarrollo ni cambio de código. Por ejemplo, un análisis o una actividad documental sin modificar el sistema.
- **Tipo 2:** la HU implica desarrollo de código, no requiere pruebas intermedias en ambientes preproductivos y el cambio va directamente a producción. Ambas condiciones deben estar confirmadas por la HU.
- **Tipo 3:** cualquier HU que no cumpla las condiciones del tipo 1 ni del tipo 2. Incluye los cambios de código que requieren pruebas en preproductivo y los casos con dudas sobre la ruta de despliegue.
- **Ambiente preproductivo:** ambiente de pruebas previo a producción donde se valida un cambio antes de liberarlo.
- **Criticidad efectiva:** tipo que se aplica realmente. Es 3 hasta que un revisor humano apruebe un tipo 1 o 2.
