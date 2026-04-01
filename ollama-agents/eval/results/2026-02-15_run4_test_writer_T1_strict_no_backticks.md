**1. Arquitectura General**

Capas (de dependencia):
Infraestructura (SQLModel, FastAPI)  
→ Interfaces (Pydantic, FastAPI Endpoints)  
→ Aplicación (Casos de Uso)  
→ Dominio (Entidades Puras)

Tecnologías:
- Backend: FastAPI (ASGI), SQLModel (ORM), Pydantic (validación)
- DB: PostgreSQL (producción), SQLite (tests/dev)
- Auth: JWT (access + refresh tokens)
- Tests: pytest, pytest-asyncio, pytest-docker
- Deploy: Docker (app + DB + Redis)

**2. Modelos de Dominio (Core)**

Entidad `User`
id: int
email: str
password_hash: str
role: str  # "admin", "agent", "visitor"
created_at: datetime

Entidad `Property`
id: int
title: str
description: str
price: float  # MXN
location: str
status: str  # "active", "inactive"
created_at: datetime

Entidad `Token`
access_token: str
refresh_token: str
expires_in: int

**3. Casos de Uso (Aplicación)**

Módulo de Autenticación
RegisterUser
Input: UserCreate (email, password, role)
Output: Token
Firma: def register_user(user: UserCreate) -> Token

AuthenticateUser
Input: UserLogin (email, password)
Output: Token
Firma: def authenticate_user(email: str, password: str) -> Token

RefreshToken
Input: TokenRefreshRequest (refresh_token)
Output: Token
Firma: def refresh_token(refresh_token: str) -> Token

Módulo de Inmuebles
CreateProperty
Input: PropertyCreate (title, description, price, location)
Output: PropertyResponse
Firma: def create_property(property: PropertyCreate) -> PropertyResponse

UpdateProperty
Input: PropertyUpdate (id, title, description, price, location, status)
Output: PropertyResponse
Firma: def update_property(id: int, property: PropertyUpdate) -> PropertyResponse

DeleteProperty
Input: id: int
Output: SuccessResponse
Firma: def delete_property(id: int) -> SuccessResponse

ListProperties
Input: ListPropertyParams (page, per_page, filters)
Output: PropertyListResponse
Firma: def list_properties(params: ListPropertyParams) -> PropertyListResponse

GetProperty
Input: id: int
Output: PropertyResponse
Firma: def get_property(id: int) -> PropertyResponse

**4. Contratos API (Interfaces)**

Módulo de Autenticación
UserCreate
email: EmailStr
password: str
role: str  # "admin", "agent", "visitor"

UserLogin
email: EmailStr
password: str

Token
access_token: str
refresh_token: str
expires_in: int

TokenRefreshRequest
refresh_token: str

TokenRefreshResponse
access_token: str
expires_in: int

Módulo de Inmuebles
PropertyCreate
title: str
description: str
price: float
location: str

PropertyUpdate
title: Optional[str] = None
description: Optional[str] = None
price: Optional[float] = None
location: Optional[str] = None
status: Optional[str] = None

PropertyResponse
id: int
title: str
description: str
price: float
location: str
status: str
created_at: datetime

PropertyListResponse
items: List[PropertyResponse]
total: int
page: int
per_page: int

ListPropertyParams
page: int = 1
per_page: int = 10
filters: Optional[Dict[str, Any]] = None

**5. Estrategia de Pruebas**

Pruebas Unitarias (pytest)
Autenticación:
test_register_user_success → Verifica creación de usuario y token.
test_login_invalid_password → Verifica error 401.
test_refresh_token_expired → Verifica error 401.

Inmuebles:
test_create_property_success → Verifica creación y retorno de PropertyResponse.
test_list_properties_pagination → Verifica paginación (10 items/page).
test_get_property_not_found → Verifica error 404.

Pruebas de Integración (pytest-asyncio)
API Endpoints:
test_auth_register_endpoint → Verifica flujo completo de registro.
test_property_list_filters → Verifica filtros por precio y ubicación.

Pruebas de Excepciones:
test_invalid_email_format → Verifica error 422 (Pydantic).
test_unauthorized_access → Verifica error 403 para usuarios no autorizados.

**6. Estrategia de Implementación**

Fase 1: Autenticación
1. Implementar User en Dominio.
2. Crear UserSQL en Infraestructura (SQLModel).
3. Implementar RegisterUser y AuthenticateUser en Aplicación.
4. Crear endpoints /auth/register y /auth/login en Interfaces.

Fase 2: Inmuebles CRUD
1. Implementar Property en Dominio.
2. Crear PropertySQL en Infraestructura.
3. Implementar CreateProperty, ListProperties, GetProperty en Aplicación.
4. Crear endpoints /properties y /properties/{id} en Interfaces.

Fase 3: Error Handling
1. Implementar CustomException con trace_id en Interfaces.
2. Configurar middleware de FastAPI para añadir trace_id en todas las respuestas.

**7. Estrategia de Pruebas - Pirámide de Pruebas**

Pruebas Unitarias (pytest)
- 70% del total
- Test de casos de uso, lógica de negocio

Pruebas de Integración (pytest-asyncio)
- 20% del total
- Test de endpoints, integración de capas

Pruebas de Excepciones
- 10% del total
- Validaciones, errores, edge cases

**8. Cobertura por Endpoint**

Endpoint
Método
Cobertura
/auth/register
POST
100%
/auth/login
POST
100%
/auth/refresh
POST
100%
/properties
GET
100%
/properties
POST
100%
/properties/{id}
GET
100%
/properties/{id}
PUT
100%
/properties/{id}
DELETE
100%

**9. Factories para Pruebas**

UserFactory
email: str = "test@example.com"
password: str = "password123"
role: str = "visitor"
created_at: datetime = datetime.utcnow()

PropertyFactory
title: str = "Test Property"
description: str = "Test Description"
price: float = 1000000.0
location: str = "Test Location"
status: str = "active"
created_at: datetime = datetime.utcnow()

TokenFactory
access_token: str = "access_token_123"
refresh_token: str = "refresh_token_456"
expires_in: int = 3600

**10. Estrategia de Base de Datos (SQLite para Tests)**

Configuración de Test
Usar SQLite en memoria para pruebas.
Cada test se ejecuta en transacción aislada.
Se resetea el estado entre tests.

Repositorios
Implementar repositorios SQLModel para User y Property.
Utilizar sesiones de SQLAlchemy para transacciones.

Migraciones
Usar Alembic para migraciones en producción.
En tests, usar migraciones de prueba con base de datos temporal.

**11. DoD (Done Definition)**

✅ Todos los endpoints funcionan según contratos API.
✅ Tests unitarios e integración cubren >80% de cobertura.
✅ Docker funciona (app + DB + Redis).
✅ Autenticación JWT con refresh tokens.
✅ Paginación y filtros en listado de inmuebles.
✅ Documentación en docs/ con mkdocs (solo lectura).
✅ Validaciones en Pydantic y SQLModel.
✅ Errores personalizados con trace_id.

**12. Riesgos y Gaps**

Riesgos
- Falta de cobertura en casos de uso complejos de actualización de inmuebles.
- Posible duplicación de lógica entre casos de uso.
- Complejidad en manejo de errores en endpoints de actualización.

Gaps
- No hay tests de carga ni rendimiento.
- Falta de integración con sistemas externos.
- No hay logging detallado en producción.

**13. AUTOCHECK**

✅ Arquitectura sigue capas claras.
✅ Modelos de dominio completos.
✅ Casos de uso bien definidos.
✅ Contratos API completos.
✅ Estrategia de pruebas completa.
✅ Estrategia de implementación clara.
✅ DoD completo.
✅ Cobertura por endpoint completa.
✅ Factories para pruebas completas.
✅ Estrategia DB SQLite para tests completa.
✅ Riesgos y gaps identificados.
✅ Formato obligatorio completado.

