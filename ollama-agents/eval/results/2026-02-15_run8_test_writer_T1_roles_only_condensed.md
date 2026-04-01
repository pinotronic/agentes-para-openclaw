**Principios aplicados**

- Pruebas deterministas sin dependencias externas ni tiempo real
- Cobertura de reglas de negocio, seguridad y contratos API
- Separación clara entre capas: unitarias, integración, contrato y e2e
- Uso de fixtures para aislamiento y estado predefinido
- Validación de errores estándar y códigos HTTP según contrato
- Enfoque en efectos observables y no detalles internos irrelevantes

---

**Mapa de pruebas por capas**

Capa | Tipo de test | Qué valida | Herramienta | Cantidad objetivo
--- | --- | --- | --- | ---
Unitaria | Casos de uso del dominio | Lógica de negocio, validaciones, servicios | pytest | 60–70%
Integración | Repositorios, migraciones, consultas | Persistencia, índices, constraints | pytest + sqlite | 20–30%
Contrato/API | Endpoints, autenticación, errores | Validación de contrato, status codes, formatos | pytest + TestClient | 10–20%
E2E | Flujos críticos (si aplica) | Flujo completo usuario → frontend → backend | Playwright | 2–5%

---

**Matriz de casos de prueba (MVP)**

ID | Módulo | Caso | Precondición | Pasos | Resultado esperado | Tipo (unit/int/api/e2e)
--- | --- | --- | --- | --- | --- | ---
T001 | Auth | Registro exitoso | Usuario no existe | POST /auth/register con datos válidos | 201 Created, usuario creado | api
T002 | Auth | Registro duplicado | Usuario ya existe | POST /auth/register con email repetido | 409 Conflict | api
T003 | Auth | Login válido | Usuario registrado | POST /auth/login con credenciales correctas | 200 OK, tokens JWT | api
T004 | Auth | Login inválido | Credenciales incorrectas | POST /auth/login con password incorrecto | 401 Unauthorized | api
T005 | Auth | Refresh token válido | Token válido y no expirado | POST /auth/refresh con refresh token | 200 OK, nuevo access token | api
T006 | Auth | Refresh token inválido | Token inválido o mal formado | POST /auth/refresh con token corrupto | 401 Unauthorized | api
T007 | Auth | Acceso sin autenticar | Sin token | GET /properties | 401 Unauthorized | api
T008 | Auth | Acceso rol no permitido | Rol visitor | POST /properties | 403 Forbidden | api
T009 | Inmuebles | Listar con paginación | Múltiples inmuebles | GET /properties?page=1&per_page=10 | 200 OK, lista paginada | api
T010 | Inmuebles | Listar con filtros | Inmuebles con distintos precios | GET /properties?price_min=100000&price_max=500000 | 200 OK, resultados filtrados | api
T011 | Inmuebles | Listar con orden | Inmuebles existentes | GET /properties?sort=price&dir=desc | 200 OK, ordenado | api
T012 | Inmuebles | Crear inmueble válido | Usuario admin/agent | POST /properties con datos válidos | 201 Created, inmueble guardado | api
T013 | Inmuebles | Crear inmueble inválido | Datos inválidos | POST /properties con precio negativo | 422 Unprocessable Entity | api
T014 | Inmuebles | Actualizar inmueble | Inmueble existente, rol admin/agent | PATCH /properties/1 con datos válidos | 200 OK, actualizado | api
T015 | Inmuebles | Eliminar inmueble | Inmueble existente, rol admin/agent | DELETE /properties/1 | 204 No Content | api
T016 | Inmuebles | Detalle inmueble existente | Inmueble existe | GET /properties/1 | 200 OK, datos del inmueble | api
T017 | Inmuebles | Detalle inmueble inexistente | Inmueble no existe | GET /properties/999 | 404 Not Found | api
T018 | Inmuebles | Hash de contraseña | Registro usuario | Registrar usuario | Contraseña hasheada en DB | unit
T019 | Inmuebles | Validación de tipos | Campos inválidos | POST /properties con tipo incorrecto | 422 Unprocessable Entity | api

---

**Cobertura por endpoint**

- **POST /auth/register**
  - Casos mínimos: happy path, email duplicado, validación
  - Códigos esperados: 201, 409, 422
  - Formato error: { "error": { "code": "user_exists", "message": "...", "details": {} }, "trace_id": "..." }

- **POST /auth/login**
  - Casos mínimos: happy path, credenciales inválidas, validación
  - Códigos esperados: 200, 401, 422
  - Formato error: { "error": { "code": "invalid_credentials", "message": "...", "details": {} }, "trace_id": "..." }

- **POST /auth/refresh**
  - Casos mínimos: happy path, token inválido, expirado, validación
  - Códigos esperados: 200, 401, 403, 422
  - Formato error: { "error": { "code": "invalid_token", "message": "...", "details": {} }, "trace_id": "..." }

- **GET /properties**
  - Casos mínimos: happy path, paginación, filtros, orden, validación
  - Códigos esperados: 200, 422
  - Formato error: { "error": { "code": "invalid_pagination", "message": "...", "details": {} }, "trace_id": "..." }

- **GET /properties/{id}**
  - Casos mínimos: existente, no existente
  - Códigos esperados: 200, 404
  - Formato error: { "error": { "code": "property_not_found", "message": "...", "details": {} }, "trace_id": "..." }

- **POST /properties**
  - Casos mínimos: happy path, sin auth, rol no permitido, validación
  - Códigos esperados: 201, 401, 403, 422
  - Formato error: { "error": { "code": "validation_error", "message": "...", "details": {} }, "trace_id": "..." }

- **PATCH /properties/{id}**
  - Casos mínimos: happy path, sin auth, rol no permitido, no existe, validación
  - Códigos esperados: 200, 401, 403, 404, 422
  - Formato error: { "error": { "code": "validation_error", "message": "...", "details": {} }, "trace_id": "..." }

- **DELETE /properties/{id}**
  - Casos mínimos: happy path, sin auth, rol no permitido, no existe
  - Códigos esperados: 204, 401, 403, 404
  - Formato error: { "error": { "code": "property_not_found", "message": "...", "details": {} }, "trace_id": "..." }

---

**Fixtures/Factories**

- `user_factory`: Crea usuarios con roles, contraseñas hasheadas
- `property_factory`: Genera inmuebles con datos válidos e inválidos
- `auth_token_factory`: Genera tokens JWT válidos y expirados
- `test_client`: Cliente de prueba con autenticación y headers preconfigurados

---

**Estrategia de DB en tests**

- Uso de base de datos SQLite en memoria para pruebas unitarias e integración
- Migraciones automáticas en cada test con `pytest` fixture
- Rollback de transacciones tras cada test para aislamiento
- Uso de `pytest` fixtures para setup/teardown de datos de prueba

---

**Casos límite y regresión**

- Valores mínimos y máximos para `price_min`, `price_max`, `page`, `per_page`
- Valores inválidos para `sort`, `dir`, `status`
- Campos vacíos o nulos en todos los endpoints
- Uso de caracteres especiales o inyección SQL en strings
- Pruebas de rol de usuario para endpoints protegidos
- Verificación de hash de contraseña en registro

---

**Checklist de Definition of Done para tests**

- ✅ Todos los endpoints cubiertos
- ✅ Todos los códigos de error validados
- ✅ Formato de error estándar verificado
- ✅ Tests unitarios y de integración ejecutados
- ✅ Uso de fixtures y aislamiento de datos
- ✅ Cobertura de casos límite y regresión
- ✅ Cada test tiene nombre descriptivo y paso a paso
- ✅ Tests ejecutables en CI/CD

---

**Riesgos de testing y mitigaciones**

- Riesgo: Dependencia de estado entre tests → Mitigación: Uso de fixtures y rollback de transacciones
- Riesgo: Falta de cobertura de edge cases → Mitigación: Revisión de casos límite en cada endpoint
- Riesgo: Inconsistencias en formato de errores → Mitigación: Validación automática del formato de respuesta
- Riesgo: Token JWT no se genera correctamente → Mitigación: Tests unitarios de generación de tokens
- Riesgo: Falta de cobertura de roles → Mitigación: Tests específicos para cada rol en endpoints protegidos

---

**Gaps**

- No se testea el comportamiento de frontend (UI) en e2e
- No se testea la persistencia en base de datos real (solo SQLite)
- No se testea el manejo de errores de red o timeouts
- No se testea el manejo de datos en múltiples hilos o concurrencia

---

**AUTOCHECK**

- ¿Incluiste TODAS las secciones anteriores? (sí)
- ¿Incluiste ambas TABLAS con headers exactos? (sí)

