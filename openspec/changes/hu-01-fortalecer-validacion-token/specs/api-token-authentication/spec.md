# Spec Delta

## Purpose

Define el contrato observable con el que el servicio `api` acepta o rechaza el token de autenticación en cada petición a una ruta protegida.

## ADDED Requirements

### Requirement: Aceptación de token JWT firmado válido

El servicio MUST aceptar una petición protegida cuando el header `Authorization` tenga la forma `Bearer <token>` y el token sea un JWT firmado con la clave pública configurada, con los claims `sub`, `role`, `exp`, `iss` y `aud` válidos y coincidentes con la configuración.

#### Scenario: Token firmado y vigente

- **WHEN** una petición llega a una ruta protegida con un token firmado con la clave configurada, con `iss` y `aud` configurados y `exp` futura
- **THEN** el servicio procesa la petición y usa el claim `sub` como usuario del token

### Requirement: Rechazo de token inválido

El servicio MUST rechazar con `401 Unauthorized` cualquier petición protegida cuyo token no cumpla los requisitos de firma y claims, incluidos los tokens sin firma, firmados con otra clave, alterados después de firmarlos, expirados, con claims ausentes o con `iss` o `aud` distintos a los configurados.

#### Scenario: Token alterado después de firmarlo

- **WHEN** una petición llega con un token firmado cuyo contenido fue modificado después de la firma
- **THEN** el servicio responde `401` con un cuerpo JSON que contiene el campo `detail`

#### Scenario: Token firmado con otra clave

- **WHEN** una petición llega con un token firmado con una clave distinta a la clave pública configurada
- **THEN** el servicio responde `401` con un cuerpo JSON que contiene el campo `detail`

#### Scenario: Token sin firma

- **WHEN** una petición llega con un token sin firma
- **THEN** el servicio responde `401` y no procesa la petición

#### Scenario: Token expirado

- **WHEN** una petición llega con un token cuyo claim `exp` ya venció
- **THEN** el servicio responde `401` y no procesa la petición

#### Scenario: Token con emisor o audiencia distintos

- **WHEN** una petición llega con un token firmado correctamente cuyo `iss` o `aud` no coincide con la configuración
- **THEN** el servicio responde `401` y no procesa la petición

#### Scenario: Token legado en Base64

- **WHEN** una petición llega con un token en el formato Base64 anterior, sin firma JWT
- **THEN** el servicio responde `401` y no procesa la petición

#### Scenario: Header ausente

- **WHEN** una petición a una ruta protegida llega sin header `Authorization`
- **THEN** el servicio responde `401` con un cuerpo JSON que contiene el campo `detail`

### Requirement: Configuración obligatoria de la verificación

El servicio MUST obtener la clave pública, el emisor y la audiencia de configuración externa y MUST NOT aceptar ningún token en rutas protegidas si esa configuración falta o es inválida.

#### Scenario: Configuración ausente

- **WHEN** una petición llega a una ruta protegida y falta alguna de las variables `AUTH_JWT_PUBLIC_KEY`, `AUTH_JWT_ISSUER` o `AUTH_JWT_AUDIENCE`
- **THEN** el servicio responde `503` con el cuerpo `{"detail": "Authentication is not configured"}` y no procesa la petición aunque el token sea válido

#### Scenario: Clave pública inválida

- **WHEN** una petición llega a una ruta protegida y la clave pública configurada no es un PEM válido
- **THEN** el servicio responde `503` y no procesa la petición

### Requirement: Ausencia de secretos en el código fuente

El código del servicio MUST NOT contener claves de firma ni secretos de verificación; estos valores MUST provenir de configuración externa.

#### Scenario: Revisión del código

- **WHEN** se revisa el código fuente del servicio `api`
- **THEN** no aparece ninguna clave privada, secreto de firma ni valor de clave pública embebido

### Requirement: No registrar tokens ni claves

El servicio MUST NOT escribir en sus registros ni en las respuestas valores de tokens, claves o secretos de verificación, salvo el campo `detail` ya documentado.

#### Scenario: Rechazo de token en registros

- **WHEN** una petición es rechazada por un token inválido
- **THEN** los registros del servicio no contienen el valor del token ni de la clave configurada

### Requirement: Contrato de respuesta de rechazo

Las respuestas de rechazo de autenticación MUST conservar el código HTTP y el campo `detail` documentados en docs/ENDPOINTS.md para que los clientes puedan distinguir el caso sin depender del texto de `detail`.

#### Scenario: Cliente distingue rechazo y configuración

- **WHEN** un cliente recibe una respuesta de rechazo de autenticación
- **THEN** puede distinguir un `401` de un `503` por el código HTTP, y el texto de `detail` no es utilizado para la lógica del cliente
