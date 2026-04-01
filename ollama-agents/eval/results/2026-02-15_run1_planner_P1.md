Thinking...
Okay, let's tackle this. The user wants a PLAN MAESTRO for a new project, the MVP v1.0 of a mini-real estate app. They mentioned using Clean Architecture with FastAPI and SQLModel. So first, I need to outline the main components based on the architecture layers.

Starting with the Domain layer. The core entities here would be User, Property, and maybe Token for JWT. Each needs to have their attributes. For User, fields like id, email, password, role, and created_at. Property would have id, title, description, price, location, and maybe status. Token should handle access and refresh tokens.

Next, the Application layer. This is where the use cases live. For authentication, there's RegisterUser, AuthenticateUser, RefreshToken. For properties, CRUD operations: CreateProperty, UpdateProperty, DeleteProperty, ListProperties, GetProperty. Each use case should have clear inputs and outputs, like UserCreate and UserResponse for authentication.

Then, the Interfaces layer. Here, the API contracts using Pydantic models. For authentication, models like UserCreate, UserResponse, Token, TokenRefreshRequest, TokenRefreshResponse. For properties, PropertyCreate, PropertyUpdate, PropertyResponse, PropertyListResponse. These models need to align with the domain entities but be tailored for API requests and responses.

Infraestructura (Persistence) with SQLModel. The database models should mirror the domain entities but include SQLModel-specific fields like id as the primary key. For example, UserSQL with id, email, hashed_password, role, created_at. PropertySQL with similar fields. The Token model might not be stored in the DB, but the refresh token could be handled in a separate table if needed, but the user didn't mention that, so maybe just focus on the main entities.

Testing strategy: Use pytest with fixtures for database setup. Mock external services if needed, but since there are no integrations in MVP, maybe just focus on unit and integration tests. Each use case should have tests, and the API endpoints should be tested with requests.

Deployment: Docker setup with FastAPI, PostgreSQL, and Redis for JWT refresh tokens. The Dockerfile and docker-compose.yml would need to be structured to run the app and the database.

DoD (Done Definition): All features implemented, tests passing, code reviewed, Docker working, documentation in place.

Wait, but the user mentioned that the MVP includes Auth with JWT, CRUD for properties, public listing with pagination, and error handling. So the models and use cases need to cover those. Also, the error handling with trace_id should be part of the API responses, maybe through a custom exception handler in FastAPI that adds the trace_id to the response.

I should make sure that each layer is properly separated. The domain entities are pure, no dependencies. The application layer handles the business logic, using the domain models. The interfaces layer (API) maps the request and response models. The infrastructure layer maps to the database models.

Also, the User role has Admin, Agent, and Visitor. So in the User model, the role should be an enum with those values. For the Property, maybe a status field like 'active', 'inactive', etc.

For the API endpoints, the authentication endpoints would be /auth/register, /auth/login, /auth/refresh. The property endpoints would be /properties with methods for create, update, delete, list, and /properties/{id} for detail.

Testing each endpoint with pytest, using async clients, and mocking the database if needed. Also, ensuring that the JWT tokens are properly generated and validated.

Deployment with Docker, so the Dockerfile should include the app and dependencies, and the docker-compose.yml should set up the PostgreSQL and Redis services.

I think that's a solid outline. Now, structure all this into the PLAN MAESTRO format with the required sections: Arquitectura, Modelos de Dominio, Casos de Uso, Contratos API, Estrategia de Pruebas, Estrategia de Implementación, DoD, y Notas.
...done thinking.

## PLAN MAESTRO: MVP v1.0 - Mini-Inmobiliaria

---

### 1. Arquitectura General
**Capas (de dependencia):**
```
Infraestructura (SQLModel, FastAPI)  
→ Interfaces (Pydantic, FastAPI Endpoints)  
→ Aplicación (Casos de Uso)  
→ Dominio (Entidades Puras)
```

**Tecnologías:**
- **Backend:** FastAPI (ASGI), SQLModel (ORM), Pydantic (validación)
- **DB:** PostgreSQL (producción), SQLite (tests/dev)
- **Auth:** JWT (access + refresh tokens)
- **Tests:** pytest, pytest-asyncio, pytest-docker
- **Deploy:** Docker (app + DB + Redis)

---

### 2. Modelos de Dominio (Core)
#### Entidad `User`
```python
class User:
    id: int
    email: str
    password_hash: str
    role: str  # "admin", "agent", "visitor"
    created_at: datetime
```

#### Entidad `Property`
```python
class Property:
    id: int
    title: str
    description: str
    price: float  # MXN
    location: str
    status: str  # "active", "inactive"
    created_at: datetime
```

#### Entidad `Token`
```python
class Token:
    access_token: str
    refresh_token: str
    expires_in: int
```

---

### 3. Casos de Uso (Aplicación)
#### Módulo de Autenticación
- **RegisterUser**  
  *Input:* `UserCreate` (email, password, role)  
  *Output:* `Token`  
  *Firma:* `def register_user(user: UserCreate) -> Token`

- **AuthenticateUser**  
  *Input:* `UserLogin` (email, password)  
  *Output:* `Token`  
  *Firma:* `def authenticate_user(email: str, password: str) -> Token`

- **RefreshToken**  
  *Input:* `TokenRefreshRequest` (refresh_token)  
  *Output:* `Token`  
  *Firma:* `def refresh_token(refresh_token: str) -> Token`

#### Módulo de Inmuebles
- **CreateProperty**  
  *Input:* `PropertyCreate` (title, description, price, location)  
  *Output:* `PropertyResponse`  
  *Firma:* `def create_property(property: PropertyCreate) -> PropertyResponse`

- **UpdateProperty**  
  *Input:* `PropertyUpdate` (id, title, description, price, location, status)  
  *Output:* `PropertyResponse`  
  *Firma:* `def update_property(id: int, property: PropertyUpdate) -> PropertyResponse`

- **DeleteProperty**  
  *Input:* `id: int`  
  *Output:* `SuccessResponse`  
  *Firma:* `def delete_property(id: int) -> SuccessResponse`

- **ListProperties**  
  *Input:* `ListPropertyParams` (page, per_page, filters)  
  *Output:* `PropertyListResponse`  
  *Firma:* `def list_properties(params: ListPropertyParams) -> PropertyListResponse`

- **GetProperty**  
  *Input:* `id: int`  
  *Output:* `PropertyResponse`  
  *Firma:* `def get_property(id: int) -> PropertyResponse`

---

### 4. Contratos API (Interfaces)
#### Módulo de Autenticación
```python
# models.py
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str  # "admin", "agent", "visitor"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRefreshResponse(BaseModel):
    access_token: str
    expires_in: int
```

#### Módulo de Inmuebles
```python
# models.py
class PropertyCreate(BaseModel):
    title: str
    description: str
    price: float
    location: str

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    status: Optional[str] = None

class PropertyResponse(BaseModel):
    id: int
    title: str
    description: str
    price: float
    location: str
    status: str
    created_at: datetime

class PropertyListResponse(BaseModel):
    items: List[PropertyResponse]
    total: int
    page: int
    per_page: int

class ListPropertyParams(BaseModel):
    page: int = 1
    per_page: int = 10
    filters: Optional[Dict[str, Any]] = None
```

---

### 5. Estrategia de Pruebas
**Pruebas Unitarias (pytest):**
- **Autenticación:**
  - `test_register_user_success` → Verifica creación de usuario y token.
  - `test_login_invalid_password` → Verifica error 401.
  - `test_refresh_token_expired` → Verifica error 401.

- **Inmuebles:**
  - `test_create_property_success` → Verifica creación y retorno de `PropertyResponse`.
  - `test_list_properties_pagination` → Verifica paginación (10 items/page).
  - `test_get_property_not_found` → Verifica error 404.

**Pruebas de Integración (pytest-asyncio):**
- **API Endpoints:**
  - `test_auth_register_endpoint` → Verifica flujo completo de registro.
  - `test_property_list_filters` → Verifica filtros por precio y ubicación.

**Pruebas de Excepciones:**
- `test_invalid_email_format` → Verifica error 422 (Pydantic).
- `test_unauthorized_access` → Verifica error 403 para usuarios no autorizados.

---

### 6. Estrategia de Implementación
**Fase 1: Autenticación**
1. Implementar `User` en Dominio.
2. Crear `UserSQL` en Infraestructura (SQLModel).
3. Implementar `RegisterUser` y `AuthenticateUser` en Aplicación.
4. Crear endpoints `/auth/register` y `/auth/login` en Interfaces.

**Fase 2: Inmuebles CRUD**
1. Implementar `Property` en Dominio.
2. Crear `PropertySQL` en Infraestructura.
3. Implementar `CreateProperty`, `ListProperties`, `GetProperty` en Aplicación.
4. Crear endpoints `/properties` y `/properties/{id}` en Interfaces.

**Fase 3: Error Handling**
1. Implementar `CustomException` con `trace_id` en Interfaces.
2. Configurar middleware de FastAPI para añadir `trace_id` en todas las respuestas.

---

### 7. DoD (Done Definition)
- ✅ Todos los endpoints funcionan según contratos API.
- ✅ Tests unitarios e integración cubren >80% de cobertura.
- ✅ Docker funciona (app + DB + Redis).
- ✅ Autenticación JWT con refresh tokens.
- ✅ Paginación y filtros en listado de inmuebles.
- ✅ Documentación en `docs/` con `mkdocs` (solo lectura).
- ✅ Validaciones en Pydantic y SQLModel.
- ✅ Errores personalizados con `trace_id`.

---

### 8. Notas
- **Seguridad:** Usar `bcrypt` para hashear contraseñas en Infraestructura.
- **Logs:** Configurar `logging` con `trace_id` en todas las capas.
- **Migraciones:** Usar `alembic` para migraciones de DB en producción.
- **Deploy:** Usar `docker-compose` para levantar DB y Redis en desarrollo.

