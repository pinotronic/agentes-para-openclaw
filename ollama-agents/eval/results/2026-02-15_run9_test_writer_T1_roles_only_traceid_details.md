**Principios aplicados**

- Enfoque en pruebas de contrato y comportamiento (no detalles internos)
- Uso de fixtures y factories para aislamiento de tests
- Cobertura de reglas de negocio y validaciones de entrada
- Pruebas deterministas sin dependencias externas (tiempo, red, etc.)
- Seguridad: validación de tokens, hashing de contraseñas, roles y errores estándar
- Uso de herramientas estándar: pytest, httpx TestClient, SQLModel con SQLite

**Mapa de pruebas por capas**

Capa | Tipo de test | Qué valida | Herramienta | Cantidad objetivo
--- | --- | --- | --- | ---
Unitaria | Casos de uso | Lógica de negocio, validaciones | pytest | 60%
Integración | Repositorios, DB | Persistencia, migraciones, consultas | pytest + SQLModel | 25%
API | Endpoints | Contratos, autenticación, errores | httpx TestClient | 15%

**Matriz de casos de prueba (MVP)**

ID | Módulo | Caso | Precondición | Pasos | Resultado esperado | Tipo (unit/int/api/e2e)
--- | --- | --- | --- | --- | --- | ---
T001 | Auth | Registro exitoso | N/A | Enviar POST /auth/register con datos válidos | Se crea usuario, se devuelve 201 Created, cuerpo con id de usuario | api
T002 | Auth | Registro duplicado | Usuario existente | Enviar POST /auth/register con email ya usado | Se devuelve 409 Conflict, con error.code=user_exists, trace_id no vacío, error.details objeto | api
T003 | Auth | Registro con datos inválidos | Datos incompletos | Enviar POST /auth/register con email vacío | Se devuelve 422 Unprocessable Entity, error.code=validation_error, trace_id no vacío, error.details objeto | api
T004 | Auth | Login exitoso | Usuario registrado | Enviar POST /auth/login con credenciales válidas | Se devuelve 200 OK, tokens access/refresh, cuerpo sin password | api
T005 | Auth | Login con credenciales inválidas | Usuario no existe o contraseña incorrecta | Enviar POST /auth/login con email o contraseña incorrectos | Se devuelve 401 Unauthorized, error.code=invalid_credentials, trace_id no vacío, error.details objeto | api
T006 | Auth | Refresh token válido | Token de refresh válido | Enviar POST /auth/refresh con token válido | Se devuelve 200 OK, nuevo access token | api
T007 | Auth | Refresh token inválido | Token de refresh inválido | Enviar POST /auth/refresh con token corrupto | Se devuelve 401 Unauthorized, error.code=invalid_token, trace_id no vacío, error.details objeto | api
T008 | Auth | Refresh token expirado | Token de refresh expirado | Enviar POST /auth/refresh con token expirado | Se devuelve 403 Forbidden, error.code=token_expired, trace_id no vacío, error.details objeto | api
T009 | Propiedades | Listar todas las propiedades | N/A | Enviar GET /properties | Se devuelve 200 OK, lista de propiedades, paginación, filtros, orden | api
T010 | Propiedades | Listar con filtros | N/A | Enviar GET /properties con parámetros de filtro | Se devuelve 200 OK, lista filtrada | api
T011 | Propiedades | Listar con parámetros inválidos | N/A | Enviar GET /properties con offset negativo | Se devuelve 422 Unprocessable Entity, error.code=invalid_pagination, trace_id no vacío, error.details objeto | api
T012 | Propiedades | Ver detalle existente | Propiedad registrada | Enviar GET /properties/{id} con id válido | Se devuelve 200 OK, datos de propiedad | api
T013 | Propiedades | Ver detalle no existente | Propiedad inexistente | Enviar GET /properties/{id} con id no existente | Se devuelve 404 Not Found, error.code=property_not_found, trace_id no vacío, error.details objeto | api
T014 | Propiedades | Crear propiedad con rol inválido | Usuario sin rol admin/agent | Enviar POST /properties sin token o rol no permitido | Se devuelve 403 Forbidden, error.code=forbidden_role, trace_id no vacío, error.details objeto | api
T015 | Propiedades | Crear propiedad con rol válido | Usuario con rol admin/agent | Enviar POST /properties con datos válidos | Se devuelve 201 Created, cuerpo con propiedad creada | api
T016 | Propiedades | Crear propiedad con datos inválidos | Datos inválidos | Enviar POST /properties con precio negativo | Se devuelve 422 Unprocessable Entity, error.code=validation_error, trace_id no vacío, error.details objeto | api
T017 | Propiedades | Actualizar propiedad existente | Propiedad registrada | Enviar PATCH /properties/{id} con datos válidos | Se devuelve 200 OK, propiedad actualizada | api
T018 | Propiedades | Actualizar propiedad no existente | Propiedad inexistente | Enviar PATCH /properties/{id} con id no existente | Se devuelve 404 Not Found, error.code=property_not_found, trace_id no vacío, error.details objeto | api
T019 | Propiedades | Eliminar propiedad existente | Propiedad registrada | Enviar DELETE /properties/{id} | Se devuelve 204 No Content | api
T020 | Propiedades | Eliminar propiedad no existente | Propiedad inexistente | Enviar DELETE /properties/{id} con id no existente | Se devuelve 404 Not Found, error.code=property_not_found, trace_id no vacío, error.details objeto | api

**Cobertura por endpoint**

- POST /auth/register
  - Casos: registro exitoso, duplicado, datos inválidos
  - Códigos esperados: 201, 409, 422
  - Formato error: error.code, trace_id, error.details

- POST /auth/login
  - Casos: login exitoso, credenciales inválidas
  - Códigos esperados: 200, 401, 422
  - Formato error: error.code, trace_id, error.details

- POST /auth/refresh
  - Casos: token válido, inválido, expirado
  - Códigos esperados: 200, 401, 403, 422
  - Formato error: error.code, trace_id, error.details

- GET /properties
  - Casos: listado, filtros, paginación, parámetros inválidos
  - Códigos esperados: 200, 422
  - Formato error: error.code, trace_id, error.details

- GET /properties/{id}
  - Casos: detalle existente, no existente
  - Códigos esperados: 200, 404
  - Formato error: error.code, trace_id, error.details

- POST /properties
  - Casos: creación exitosa, rol inválido, datos inválidos
  - Códigos esperados: 201, 401, 403, 422
  - Formato error: error.code, trace_id, error.details

- PATCH /properties/{id}
  - Casos: actualización exitosa, no existente, rol inválido
  - Códigos esperados: 200, 401, 403, 404, 422
  - Formato error: error.code, trace_id, error.details

- DELETE /properties/{id}
  - Casos: eliminación exitosa, no existente, rol inválido
  - Códigos esperados: 204, 401, 403, 404
  - Formato error: error.code, trace_id, error.details

**Fixtures/Factories**

- `user_factory`: genera usuarios con datos válidos o inválidos
- `property_factory`: genera propiedades con valores correctos o inválidos
- `token_factory`: genera tokens válidos o inválidos para pruebas de autenticación
- `auth_client_factory`: cliente HTTP con autenticación preconfigurada
- `db_session_factory`: sesión de base de datos para tests unitarios e integración

**Estrategia de DB en tests**

- Uso de SQLite en memoria para pruebas rápidas
- Creación de tablas por cada test usando migraciones
- Rollback de transacciones para mantener estado limpio entre tests
- Uso de fixtures para inicializar datos de prueba

**Casos límite y regresión**

- Valores extremos de precio, área, número de habitaciones
- Fechas inválidas, campos vacíos
- Tipos de datos incorrectos (string en lugar de número)
- Rutas inválidas o parámetros mal formateados
- Casos de uso de rol inválido (no admin, no agent)
- Manejo de errores en operaciones CRUD
- Uso de tokens expirados o corruptos

**Checklist de Definition of Done para tests**

- ✅ Todos los endpoints cubiertos
- ✅ Todos los casos de error validados con trace_id y error.details
- ✅ Pruebas unitarias, integración e API cubiertas
- ✅ Uso de fixtures para evitar duplicados
- ✅ Base de datos limpia entre tests
- ✅ Cobertura de reglas de negocio
- ✅ Valores extremos y edge cases cubiertos
- ✅ No hay dependencias externas (red, tiempo, etc.)

**Riesgos de testing y mitigaciones**

- Riesgo: Tests lentos por uso de base de datos real
  - Mitigación: Uso de SQLite en memoria y rollback de transacciones

- Riesgo: Falta de cobertura de casos de error
  - Mitigación: Revisión de casos por cada endpoint y validación manual

- Riesgo: Cambios en API sin actualización de tests
  - Mitigación: Uso de contrato de API en tests

- Riesgo: Fallo en validación de datos
  - Mitigación: Uso de factories con datos controlados

- Riesgo: Uso de tokens inválidos sin cobertura
  - Mitigación: Test de refresh con tokens expirados y corruptos

**Gaps**

- No hay tests de carga o rendimiento
- No hay tests de integración con servicios externos
- No hay cobertura de casos de uso complejos de negocio (ej. descuentos, promociones)
- No hay tests de seguridad avanzados (ej. inyección SQL, XSS)

**AUTOCHECK**

- ¿Incluiste TODAS las secciones anteriores? (sí)
- ¿Incluiste ambas TABLAS con headers exactos? (sí)

