# Spec Delta

## Purpose

Define el contrato observable del inicio de sesión y asegurar que las credenciales recibidas no puedan alterar la decisión de autenticación.

## ADDED Requirements

### Requirement: El login válido conserva su respuesta
El sistema SHALL mantener el contrato observable de `POST /auth/login` para credenciales válidas.

#### Scenario: Login con credenciales válidas
- **WHEN** se envía `username=student`, `password=Workshop123!` y `client=angular-workshop`
- **THEN** la respuesta es HTTP 200, contiene `user.username` igual a `student` y contiene un `token` no vacío
- **AND** conserva los demás campos de la respuesta exitosa existente

### Requirement: Solo una coincidencia literal de credenciales autentica
El sistema SHALL autenticar únicamente cuando el par de credenciales enviado coincide con una cuenta; la entrada no puede alterar las condiciones de autenticación.

#### Scenario: Payload de inyección en username
- **WHEN** se envía `' OR '1'='1` como `username`
- **THEN** la respuesta es HTTP 401
- **AND** la respuesta no contiene `token`

#### Scenario: Payload de inyección en password
- **WHEN** se envía `' OR '1'='1` como `password`
- **THEN** la respuesta es HTTP 401
- **AND** la respuesta no contiene `token`

### Requirement: Credenciales incorrectas no emiten token
El sistema SHALL rechazar credenciales que no correspondan a una cuenta sin emitir un token.

#### Scenario: Usuario o contraseña incorrectos
- **WHEN** se envían credenciales no válidas para una cuenta
- **THEN** la respuesta es HTTP 401
- **AND** la respuesta no contiene `token`

### Requirement: Las validaciones de request existentes se conservan
El sistema SHALL mantener HTTP 400 para un request nulo, un username vacío y un password vacío.

#### Scenario: Request nulo
- **WHEN** se envía un cuerpo JSON nulo
- **THEN** la respuesta es HTTP 400 con el mensaje `Request is null`

#### Scenario: Username ausente o vacío
- **WHEN** se envía un username nulo o en blanco
- **THEN** la respuesta es HTTP 400 con el mensaje `Username is required`

#### Scenario: Password ausente o vacío
- **WHEN** se envía un password nulo o en blanco
- **THEN** la respuesta es HTTP 400 con el mensaje `Password is required`
