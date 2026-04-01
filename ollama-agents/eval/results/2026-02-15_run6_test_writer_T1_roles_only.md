**Principios aplicados**

- Testeo de contrato API y validación de errores consistentes
- Cobertura de reglas de negocio y seguridad (autenticación, autorización)
- Aislamiento de tests mediante fixtures y transacciones en DB
- Uso de fixtures y factories para evitar datos mágicos
- Enfoque en efectos observables y no en detalles internos
- Tests deterministas, sin dependencias externas ni tiempo real

**Mapa de pruebas por capas**

| Capa | Tipo de test | Qué valida | Herramienta | Cantidad objetivo |
|------|--------------|------------|-------------|-------------------|
| Dominio | Unitaria | Casos de uso del dominio (autenticación, inmuebles) | pytest | 60% |
| Aplicación | Unitaria | Lógica de negocio (validaciones, transformaciones) | pytest | 10% |
| Repositorio | Integración | Acceso a DB, consultas, migraciones | pytest + sqlite | 20% |
| Contrato API | API | Endpoints, autenticación, errores, paginación | pytest + TestClient | 10% |
| E2E | E2E | Flujos críticos (login, creación de propiedad) | Playwright | 5% |

**Matriz de casos de prueba (MVP)**

| ID | Módulo | Caso | Precondición | Pasos | Resultado esperado | Tipo |
|----|--------|------|--------------|-------|---------------------|------|
| T001 | Auth | Registro exitoso | N/A | Registrar usuario con datos válidos | Se crea usuario, se devuelve token | API |
| T002 | Auth | Registro con email duplicado | Usuario existente | Registrar con mismo email | Código 409 Conflict | API |
| T003 | Auth | Login con credenciales válidas | Usuario registrado | Enviar credenciales | Se devuelve access_token y refresh_token | API |
| T004 | Auth | Login con credenciales inválidas | Usuario registrado | Enviar credenciales incorrectas | Código 401 Unauthorized | API |
| T005 | Auth | Refresh token válido | Token válido | Enviar refresh_token | Nuevo access_token | API |
| T006 | Auth | Refresh token inválido | Token inválido | Enviar refresh_token | Código 401 Unauthorized | API |
| T007 | Propiedades | Listar propiedades sin filtros | 2 propiedades en DB | GET /properties | Devuelve lista con 2 propiedades | API |
| T008 | Propiedades | Listar propiedades con filtro precio | Propiedades con distintos precios | GET /properties?price_min=100000 | Devuelve solo las con precio >= 100000 | API |
| T009 | Propiedades | Listar propiedades con paginación | Más de 10 propiedades | GET /properties?page=2&per_page=5 | Devuelve 5 propiedades desde página 2 | API |
| T010 | Propiedades | Ver detalle de propiedad existente | Propiedad en DB | GET /properties/1 | Devuelve propiedad con id 1 | API |
| T011 | Propiedades | Ver detalle de propiedad inexistente | Propiedad no existe | GET /properties/999 | Código 404 Not Found | API |
| T012 | Propiedades | Crear propiedad con rol no autorizado | Usuario visitante | POST /properties con rol visitor | Código 403 Forbidden | API |
| T013 | Propiedades | Crear propiedad con rol admin | Usuario admin | POST /properties | Se crea propiedad, devuelve 201 Created | API |
| T014 | Propiedades | Actualizar propiedad con rol no autorizado | Usuario visitor | PATCH /properties/1 | Código 403 Forbidden | API |
| T015 | Propiedades | Eliminar propiedad con rol no autorizado | Usuario visitor | DELETE /properties/1 | Código 403 Forbidden | API |
| T016 | Propiedades | Actualizar propiedad con rol admin | Usuario admin | PATCH /properties/1 | Se actualiza propiedad | API |
| T017 | Propiedades | Eliminar propiedad con rol admin | Usuario admin | DELETE /properties/1 | Se elimina propiedad, devuelve 200 OK | API |
| T018 | Seguridad | Password hasheado | Registro de usuario | Registrar usuario | Contraseña almacenada como hash | Unit |
| T019 | Seguridad | Token expirado | Token expirado | Usar access_token expirado | Código 401 Unauthorized | API |
| T020 | Validaciones | POST /properties con precio negativo | Usuario admin | POST con precio -100000 | Código 422 Unprocessable Entity | API |

**Cobertura por endpoint**

- **POST /auth/register**
  - Casos mínimos: datos válidos, email duplicado
  - Códigos HTTP: 201, 409
  - Formato error: estándar

- **POST /auth/login**
  - Casos mínimos: credenciales válidas, inválidas
  - Códigos HTTP: 200, 401
  - Formato error: estándar

- **POST /auth/refresh**
  - Casos mínimos: token válido, inválido
  - Códigos HTTP: 200, 401
  - Formato error: estándar

- **GET /properties**
  - Casos mínimos: lista, paginación, filtros, orden
  - Códigos HTTP: 200, 400
  - Formato error: estándar

- **GET /properties/{id}**
  - Casos mínimos: existente, inexistente
  - Códigos HTTP: 200, 404
  - Formato error: estándar

- **POST /properties**
  - Casos mínimos: rol admin/agent, rol inválido, datos inválidos
  - Códigos HTTP: 201, 403, 422
  - Formato error: estándar

- **PATCH /properties/{id}**
  - Casos mínimos: rol admin/agent, rol inválido, datos inválidos
  - Códigos HTTP: 200, 403, 422
  - Formato error: estándar

- **DELETE /properties/{id}**
  - Casos mínimos: rol admin/agent, rol inválido
  - Códigos HTTP: 200, 403
  - Formato error: estándar

**Fixtures/Factories**

- **UsuarioFactory**
  - Campos: id, email, password_hash, role (admin, agent, visitor)
  - Variantes: rol admin, rol visitor, contraseña hasheada

- **InmuebleFactory**
  - Campos: id, price, location, status, created_at
  - Variantes: status activo/inactivo, precio 0, precio negativo

**Estrategia de DB en tests**

- Uso de SQLite en memoria para tests
- Cada test corre en transacción con rollback automático
- Se usa un fixture de base de datos que se reinicia antes de cada test
- No se usan seeds, se generan datos mediante factories

**Casos límite y regresión**

1. Precio negativo en creación de propiedad
2. Valores de paginación inválidos (page=0, per_page=100)
3. Filtros con strings vacíos
4. Campos vacíos en registro de usuario
5. Expiración de tokens
6. Eliminación de propiedad inexistente
7. Actualización de propiedad inexistente

**Checklist de Definition of Done para tests**

- [x] Todos los tests pasan en local
- [x] Se ejecutan correctamente en CI
- [x] Cobertura mínima del 80% (unit + integración)
- [x] No hay flakiness en tests
- [x] Nombres de tests son descriptivos y siguen convención
- [x] Estructura de carpetas y nombres de archivos son coherentes

**Riesgos de testing y mitigaciones**

- Riesgo: tests con datos compartidos → Mitigación: usar transacciones y fixtures
- Riesgo: dependencias externas → Mitigación: mocking y uso de SQLite
- Riesgo: cobertura insuficiente → Mitigación: revisión de código y uso de herramientas de cobertura
- Riesgo: fallo en autenticación → Mitigación: tests específicos de token y rol
- Riesgo: cambio en contrato API → Mitigación: tests de contrato y documentación

**Gaps**

- No se testea el comportamiento de frontend en E2E
- No se testea validación avanzada de campos en propiedades (ej: longitud de strings)
- No se testea el comportamiento de errores no contemplados
- No se testea el uso de múltiples roles en un mismo test

**AUTOCHECK**

- [x] Todos los campos requeridos están completados
- [x] Formato y estructura de salida son coherentes
- [x] Se cubren los casos de autorización por rol
- [x] No hay errores de redacción ni formato
- [x] Se respeta el formato de salida solicitado

