Thinking...
Okay, I need to create a PLAN MAESTRO for a new real estate platform MVP using Clean Architecture. Let's start by understanding the user's requirements. The main features are authentication with JWT, CRUD for properties, public listing with pagination and filters, and error handling with trace_id. The stack is FastAPI, SQLModel, and SQLite for testing.

First, the architecture must follow Clean Architecture, so the layers are Infrastructure, Interfaces (API), Application (Use Cases), and Domain. Each part needs to be defined with specific contracts and interfaces.

For the endpoints, I need to list each one with method, route, auth, status codes, error codes, and request/response schemas. Let's break down the endpoints:

1. Auth endpoints: /auth/login, /auth/refresh. These will handle JWT tokens. Auth required for refresh, public for login. Status codes like 200, 400, 401, etc. Error codes like 1001 for invalid credentials.

2. Property CRUD: /properties. POST for create, GET for list, GET/{id} for detail, PUT for update, DELETE for delete. Auth required for Admin/Agent. Status codes 200, 201, 400, 401, 403, 404, 409, 422, 500. Error codes like 2001 for invalid property data.

3. Public listing: /properties/list. GET with filters and pagination. Public access. Status codes 200, 400, 500. Error codes 3001 for invalid filters.

Next, the error catalog needs to cover all possible error codes with their HTTP status, when they occur, and details. For example, error 1001 is 401 when invalid credentials, details include trace_id.

I also need to ensure that the domain entities are defined first before any infrastructure or API changes. For example, the Property entity in the domain has fields like id, title, description, price, etc. Then, SQLModel tables map these, and Pydantic models for API requests and responses.

I should make sure that each endpoint's request and response schemas are specified with the correct types, like Optional for nullable fields. Also, the auth flow requires handling both access and refresh tokens, so the response for login should include both.

Testing considerations: Each endpoint needs test cases for success and error scenarios. For example, testing a successful login, invalid credentials, and missing required fields.

Finally, the Docker deployment setup is needed, but since the user mentioned it's for MVP, maybe that's covered in infrastructure, but the main focus here is the API contracts and domain models.

I need to structure all this into the PLAN MAESTRO format with the required sections and ensure that all endpoints are covered with their specific details and the error catalog is comprehensive.
...done thinking.

# PLAN MAESTRO: Mini-Inmobiliaria (MVP)

---

## **1. Capas del Arquitectura (Clean Architecture)**

**Flujo de dependencias:**  
`Infraestructura (DB/Web) -> Interfaces (API) -> Aplicación (Casos de Uso) -> Dominio (Entidades Puras)`

---

## **2. Dominio (Core)**

### **Entidad: Property**
```python
from typing import Optional, List
from uuid import UUID

class Property:
    id: UUID
    title: str
    description: Optional[str]
    price: float
    currency: str  # "MXN"
    bedrooms: int
    bathrooms: int
    area_sqm: float
    address: str
    city: str
    state: str
    country: str  # "México"
    is_active: bool
    created_at: datetime
    updated_at: datetime
    tags: List[str]  # Ej: ["venta", "alquiler", "nuevo"]
```

---

## **3. Infraestructura (Persistencia/SQLModel)**

### **Modelo SQL: Property**
```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Property(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    title: str
    description: Optional[str] = None
    price: float
    currency: str = "MXN"
    bedrooms: int
    bathrooms: int
    area_sqm: float
    address: str
    city: str
    state: str
    country: str = "México"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
```

---

## **4. Interfaces (API) - Contratos Pydantic**

### **Request/Response Models**

#### **Auth**
```python
from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
```

#### **Property CRUD**
```python
class PropertyCreate(BaseModel):
    title: str
    description: Optional[str]
    price: float
    bedrooms: int
    bathrooms: int
    area_sqm: float
    address: str
    city: str
    state: str
    tags: Optional[List[str]] = None

class PropertyResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    price: float
    currency: str
    bedrooms: int
    bathrooms: int
    area_sqm: float
    address: str
    city: str
    state: str
    country: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    tags: List[str]
```

#### **Public Listing**
```python
class PropertyListRequest(BaseModel):
    page: int = 1
    per_page: int = 10
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    bedrooms_min: Optional[int] = None
    bedrooms_max: Optional[int] = None
    tags: Optional[List[str]] = None
    sort_by: Optional[str] = "created_at"  # "price", "area", "created_at"
    order: Optional[str] = "desc"  # "asc" or "desc"
```

---

## **5. Endpoints MVP (Fichas por endpoint)**

### **Auth Endpoints**

#### **POST /auth/login**
- **Auth:** Público
- **Success:** 200 (Token generado)
- **Error:** 400 (Datos inválidos), 401 (Credenciales incorrectas)
- **Error Codes:** `1001` (Credenciales inválidas)
- **Request:** `LoginRequest`
- **Response:** `TokenResponse`

#### **POST /auth/refresh**
- **Auth:** Requiere `refresh_token` en headers
- **Success:** 200 (Token renovado)
- **Error:** 401 (Token expirado), 403 (Token inválido)
- **Error Codes:** `1002` (Token expirado), `1003` (Token inválido)

---

### **Property CRUD Endpoints**

#### **POST /properties**
- **Auth:** Requiere rol `Admin` o `Agente`
- **Success:** 201 (Inmueble creado)
- **Error:** 400 (Datos inválidos), 401 (No autorizado), 409 (Inmueble duplicado)
- **Error Codes:** `2001` (Datos inválidos), `2002` (Inmueble ya existe)
- **Request:** `PropertyCreate`
- **Response:** `PropertyResponse`

#### **GET /properties**
- **Auth:** Requiere rol `Admin` o `Agente`
- **Success:** 200 (Lista de inmuebles)
- **Error:** 400 (Filtros inválidos), 500 (Error interno)
- **Error Codes:** `2003` (Filtros inválidos)

#### **GET /properties/{id}**
- **Auth:** Requiere rol `Admin` o `Agente`
- **Success:** 200 (Detalles del inmueble)
- **Error:** 404 (Inmueble no encontrado)
- **Error Codes:** `2004` (Inmueble no encontrado)

#### **PUT /properties/{id}**
- **Auth:** Requiere rol `Admin` o `Agente`
- **Success:** 200 (Inmueble actualizado)
- **Error:** 400 (Datos inválidos), 404 (Inmueble no encontrado)
- **Error Codes:** `2005` (Datos inválidos)

#### **DELETE /properties/{id}**
- **Auth:** Requiere rol `Admin` o `Agente`
- **Success:** 204 (Inmueble eliminado)
- **Error:** 404 (Inmueble no encontrado)
- **Error Codes:** `2006` (Inmueble no encontrado)

---

### **Public Listing Endpoint**

#### **GET /properties/list**
- **Auth:** Público
- **Success:** 200 (Lista de inmuebles públicos)
- **Error:** 400 (Filtros inválidos), 500 (Error interno)
- **Error Codes:** `3001` (Filtros inválidos)
- **Request:** `PropertyListRequest`
- **Response:** `List[PropertyResponse]`

---

## **6. Catálogo de Errores Estándar**

| `error.code` | HTTP Status | Cuándo ocurre | Details esperado |
|--------------|-------------|---------------|------------------|
| `1001`       | 401         | Credenciales inválidas | `{"trace_id": "string", "error": "Invalid credentials"}` |
| `1002`       | 401         | Token expirado | `{"trace_id": "string", "error": "Token expired"}` |
| `1003`       | 403         | Token inválido | `{"trace_id": "string", "error": "Invalid token"}` |
| `2001`       | 400         | Datos inválidos en creación | `{"trace_id": "string", "error": "Invalid property data"}` |
| `2002`       | 409         | Inmueble ya existe | `{"trace_id": "string", "error": "Property already exists"}` |
| `2003`       | 400         | Filtros inválidos en listado | `{"trace_id": "string", "error": "Invalid filters"}` |
| `2004`       | 404         | Inmueble no encontrado | `{"trace_id": "string", "error": "Property not found"}` |
| `2005`       | 400         | Datos inválidos en actualización | `{"trace_id": "string", "error": "Invalid update data"}` |
| `2006`       | 404         | Inmueble no encontrado en eliminación | `{"trace_id": "string", "error": "Property not found"}` |
| `3001`       | 400         | Filtros inválidos en listado público | `{"trace_id": "string", "error": "Invalid filters"}` |
| `5000`       | 500         | Error interno del servidor | `{"trace_id": "string", "error": "Internal server error"}` |

---

## **7. Estrategia de Implementación**

### **Prioridad**
1. **Auth con JWT** (Endpoints `/auth/login`, `/auth/refresh`)
2. **CRUD de inmuebles** (POST/GET/PUT/DELETE `/properties`)
3. **Listado público de inmuebles** (GET `/properties/list`)

### **Tecnologías Clave**
- **Auth:** PyJWT + FastAPI middleware
- **DB:** SQLModel + SQLite (dev/test), PostgreSQL (prod)
- **Testing:** pytest + Pydantic validation
- **Docker:** Compose para dev/prod

---

## **8. Validaciones Críticas**

- **JWT:** Tokens expiran en 1 hora, refresh tokens en 7 días.
- **Migraciones:** Usar `alembic` para migraciones de base de datos.
- **Validaciones:** Todos los campos obligatorios (ej: `title`, `price`) deben ser validados en Pydantic.
- **Seguridad:** `refresh_token` debe ser almacenado en cookies con `HttpOnly` y `Secure`.

---

## **9. Notas Finales**

- **Frontend:** Usar `axios` para manejar tokens en headers.
- **Logs:** Incluir `trace_id` en todos los errores para rastrear solicitudes.
- **Despliegue:** Usar `uvicorn` + `gunicorn` para producción.

