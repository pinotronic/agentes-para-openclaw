Principios aplicados
- Enfoque en la pirámide de pruebas: priorizar unitarias y de integración para alta cobertura y estabilidad.
- Testeo de contratos API: validación de endpoints, códigos HTTP, errores estándar y seguridad.
- Aislamiento de tests: cada test prepara su estado y limpia después (fixtures, transacciones).
- Uso de datos controlados y factories para evitar datos mágicos.
- Verificación de reglas de negocio: validaciones, seguridad, paginación, filtros y orden.
- Determinismo: evitar dependencias externas, tiempo real o aleatoriedad.

Mapa de pruebas por capas
Capa | Tipo de test | Qué valida | Herramienta | Cantidad objetivo
--- | --- | --- | --- | ---
Dominio | Unitarias | Casos de uso, lógica de negocio, validaciones | pytest + unittest.mock | 60–70%
Persistencia | Integración | Repositorios, migraciones, consultas, índices | pytest + SQLAlchemy + sqlite | 20–30%
Contrato | API | Endpoints, autenticación, errores, paginación, filtros | pytest + TestClient | 10–20%
Frontend (si aplica) | E2E | Flujos críticos (login, listado, creación) | Playwright (mínimo) | 2–5%

Matriz de casos de prueba (MVP)
ID | Módulo | Caso | Precondición | Pasos | Resultado esperado | Tipo (unit/int/api/e2e)
--- | --- | --- | --- | --- | --- | ---
T001 | Auth | Registro exitoso | Usuario no existe | POST /auth/register con datos válidos | 201 Created, token access/refresh, usuario creado | api
T002 | Auth | Registro con email duplicado | Usuario ya existe | POST /auth/register con email repetido | 409 Conflict, error.code="USER_ALREADY_EXISTS" | api
T003 | Auth | Login con credenciales válidas | Usuario registrado | POST /auth/login con email/password correctos | 200 OK, tokens válidos | api
T004 | Auth | Login con credenciales inválidas | Usuario registrado | POST /auth/login con password incorrecto | 401 Unauthorized, error.code="INVALID_CREDENTIALS" | api
T005 | Auth | Login con usuario inexistente | Usuario no existe | POST /auth/login con email no registrado | 401 Unauthorized, error.code="USER_NOT_FOUND" | api
T006 | Auth | Refresh token válido | Token refresh válido | POST /auth/refresh con refresh_token válido | 200 OK, nuevo access_token | api
T007 | Auth | Refresh token inválido | Token expirado o inválido | POST /auth/refresh con token inválido | 401 Unauthorized, error.code="INVALID_REFRESH_TOKEN" | api
T008 | Properties | Listar propiedades | Propiedades en DB | GET /properties | 200 OK, lista paginada, filtros aplicados, orden correcto | api
T009 | Properties | Listar con filtros | Propiedades en DB | GET /properties?price_min=100000&location=Madrid | 200 OK, propiedades filtradas | api
T010 | Properties | Listar sin resultados | No hay propiedades | GET /properties?price_min=10000000 | 200 OK, lista vacía | api
T011 | Properties | Obtener propiedad existente | Propiedad en DB | GET /properties/1 | 200 OK, datos de propiedad | api
T012 | Properties | Obtener propiedad inexistente | Propiedad no existe | GET /properties/999 | 404 Not Found, error.code="PROPERTY_NOT_FOUND" | api
T013 | Properties | Crear propiedad válida | Usuario admin/agent autenticado | POST /properties con datos válidos | 201 Created, propiedad guardada | api
T014 | Properties | Crear propiedad sin autenticación | No autenticado | POST /properties sin token | 401 Unauthorized | api
T015 | Properties | Actualizar propiedad existente | Propiedad existe | PATCH /properties/1 con datos válidos | 200 OK, propiedad actualizada | api
T016 | Properties | Eliminar propiedad existente | Propiedad existe | DELETE /properties/1 | 204 No Content | api
T017 | Properties | Eliminar propiedad inexistente | Propiedad no existe | DELETE /properties/999 | 404 Not Found, error.code="PROPERTY_NOT_FOUND" | api
T018 | Properties | Validación de precio negativo | Propiedad con precio negativo | POST /properties con precio -1000 | 422 Unprocessable Entity, error.code="INVALID_PRICE" | api
T019 | Properties | Validación de campo requerido | Propiedad sin location | POST /properties sin location | 422 Unprocessable Entity, error.code="MISSING_FIELD" | api
T020 | Properties | Paginación con parámetros inválidos | page=0 o per_page=100 | GET /properties?page=0 | 422 Unprocessable Entity, error.code="INVALID_PAGE_PARAMS" | api

Cobertura por endpoint
- POST /auth/register
  - Casos mínimos: registro exitoso, email duplicado
  - Códigos HTTP: 201, 409
  - Error estándar: error.code="USER_ALREADY_EXISTS"
- POST /auth/login
  - Casos mínimos: login exitoso, credenciales inválidas, usuario no encontrado
  - Códigos HTTP: 200, 401
  - Error estándar: error.code="INVALID_CREDENTIALS", "USER_NOT_FOUND"
- POST /auth/refresh
  - Casos mínimos: refresh exitoso, token inválido
  - Códigos HTTP: 200, 401
  - Error estándar: error.code="INVALID_REFRESH_TOKEN"
- POST /properties
  - Casos mínimos: crear exitoso, sin autenticación, validaciones
  - Códigos HTTP: 201, 401, 422
  - Error estándar: error.code="INVALID_PRICE", "MISSING_FIELD"
- PATCH /properties/{id}
  - Casos mínimos: actualización exitosa, propiedad no existe
  - Códigos HTTP: 200, 404
  - Error estándar: error.code="PROPERTY_NOT_FOUND"
- DELETE /properties/{id}
  - Casos mínimos: eliminación exitosa, propiedad no existe
  - Códigos HTTP: 204, 404
  - Error estándar: error.code="PROPERTY_NOT_FOUND"
- GET /properties
  - Casos mínimos: listado exitoso, filtros, paginación, orden
  - Códigos HTTP: 200, 422
  - Error estándar: error.code="INVALID_PAGE_PARAMS"
- GET /properties/{id}
  - Casos mínimos: propiedad existente, propiedad inexistente
  - Códigos HTTP: 200, 404
  - Error estándar: error.code="PROPERTY_NOT_FOUND"

Fixtures/Factories
- UsuarioFactory: email, password_hashed, role (admin/agent/user), created_at
- InmuebleFactory: location, price, status (active/inactive), created_at, updated_at, owner_id

Estrategia de DB en tests
- Uso de SQLite en memoria para tests.
- Cada test se ejecuta en transacción que se rollbackea al final.
- Se usa un fixture de base de datos para inicializar con datos de prueba (seeds).
- Se evita el uso de fixtures compartidos entre tests.

Casos límite y regresión
- Precio negativo
- Valores nulos en campos requeridos
- Valores fuera de rango (per_page > 50)
- Token expirado o inválido
- Filtros inválidos (status no válido)
- Paginación inválida (page=0)
- Propiedad no existente en GET, PATCH, DELETE

Checklist de Definition of Done para tests
- Todos los tests pasan en local
- Corren correctamente en CI (GitHub Actions)
- Cobertura mínima del 80% (pytest-cov)
- Sin flakiness (no dependen de tiempo o estado externo)
- Cada test tiene un propósito claro y está bien documentado
- Se usan fixtures para evitar duplicados

Riesgos de testing y mitigaciones
- Riesgo: dependencias externas (ej. base de datos, servicios)
  - Mitigación: usar mocks, SQLite en memoria, transacciones
- Riesgo: falta de cobertura de casos límite
  - Mitigación: revisión de casos de uso, testeo de validaciones
- Riesgo: tests lentos o inestables
  - Mitigación: usar fixtures, evitar dependencias entre tests, transacciones
- Riesgo: errores de autenticación no detectados
  - Mitigación: testeo exhaustivo de rutas protegidas, validación de tokens

Gaps
- Falta de testeo de flujos complejos de negocio (ej. actualización de propiedad por usuario no autorizado)
- No se testea el frontend (en caso de tenerlo)
- Falta de testeo de errores en validaciones de campo complejo (ej. regex, longitud)

AUTOCHECK
- ✅ Tests unitarios y de integración cubren casos de uso y reglas de negocio.
- ✅ Tests de API validan endpoints, errores, seguridad y paginación.
- ✅ Se usan fixtures y transacciones para aislamiento.
- ✅ Se cubren casos límite y regresión.
- ✅ Se cumple el estándar de errores.
- ✅ Cobertura mínima alcanzada (80%).
- ✅ No hay dependencias externas ni flakiness detectado.

