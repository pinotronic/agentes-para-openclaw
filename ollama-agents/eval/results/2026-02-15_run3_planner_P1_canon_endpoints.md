Thinking...
Okay, I need to create a PLAN MAESTRO for a new mini-inmobiliaria project using FastAPI, SQLModel, and pytest with SQLite for tests/dev. The user provided the CONTRACT CANON, which specifies the endpoints and their methods. My task is to define each endpoint with the required details like auth, status codes, error codes, and request/response schemas. Also, I have to include a standard error catalog.

First, I'll start with the Auth endpoints. The register, login, and refresh endpoints are public. For each, I need to outline the success and error status codes. For example, POST /auth/register should return 201 on success and 400, 409, 422, 500 on errors. The error codes would be things like "invalid_email", "user_exists", etc.

Next, the Properties endpoints. The GET /properties is public and requires pagination, filters, and sorting. The response should include a list of properties with details like id, title, price, location, status, created_at, and updated_at. Error codes here might include "invalid_pagination", "invalid_filter", etc.

For the POST /properties endpoint, which is protected by admin/agent roles, the request should have all the necessary fields for creating a property, and the response would be 201 on success. Errors could be "missing_required_field", "invalid_price", etc.

Similarly, the PATCH and DELETE endpoints for /properties/{id} would need their own error codes and status codes. For example, a 404 if the property doesn't exist, or 403 if the user doesn't have permission.

I need to make sure that each endpoint's request and response schemas are detailed, using the correct types like Optional, List, etc. Also, the error catalog must be a table with error code, HTTP status, when it occurs, and the expected details.

I should check that I'm not adding any new endpoints beyond those in the CONTRACT CANON. Each endpoint's auth requirement is specified, and the success and error status codes are covered. The error codes are standardized and fit into the provided format.

I need to be careful with the pagination parameters (page, per_page) and filters (price_min, price_max, location, status). The response for GET /properties should include the list of properties along with pagination metadata like total, page, per_page, etc.

For the error details, each error code should have a message and details object. For example, "user_exists" would have a message like "User already exists" and details with the email.

I also need to ensure that all the required fields are included in the request schemas, and that the response schemas match what the backend will return. For example, the POST /properties response includes the created property's id, title, etc.

Finally, the standard error catalog must list all possible error codes with their HTTP status, when they occur, and the details. This includes errors like "invalid_email", "user_exists", "invalid_token", "property_not_found", "unauthorized", etc.

I think that's all. Now, I'll structure this into the PLAN MAESTRO format with each endpoint's details and the error catalog table.
...done thinking.

# PLAN MAESTRO: Mini-inmobiliaria (FastAPI + SQLModel)

---

## **Endpoints MVP (por Capa de Arquitectura)**

---

### **1. Auth Endpoints**

#### **POST /auth/register**
- **Auth:** Público
- **Success status:** 201 (Creado exitosamente)
- **Error status:** 400, 409, 422, 500
- **Error codes posibles:**
  - `invalid_email` (400)
  - `user_exists` (409)
  - `password_weak` (400)
  - `invalid_request` (422)
- **Request schema:**
  ```python
  class RegisterRequest(BaseModel):
      email: str
      password: str
      role: Literal["admin", "agent"]
  ```
- **Response schema (201):**
  ```python
  class RegisterResponse(BaseModel):
      id: int
      email: str
      role: Literal["admin", "agent"]
      access_token: str
      refresh_token: str
  ```

---

#### **POST /auth/login**
- **Auth:** Público
- **Success status:** 200 (Autenticación exitosa)
- **Error status:** 401, 404, 422, 500
- **Error codes posibles:**
  - `invalid_credentials` (401)
  - `user_not_found` (404)
  - `invalid_request` (422)
- **Request schema:**
  ```python
  class LoginRequest(BaseModel):
      email: str
      password: str
  ```
- **Response schema (200):**
  ```python
  class LoginResponse(BaseModel):
      access_token: str
      refresh_token: str
  ```

---

#### **POST /auth/refresh**
- **Auth:** Público (requiere `refresh_token` en headers)
- **Success status:** 200 (Token actualizado)
- **Error status:** 401, 403, 422, 500
- **Error codes posibles:**
  - `invalid_refresh_token` (401)
  - `token_expired` (403)
  - `invalid_request` (422)
- **Request schema:** `refresh_token: str` (en headers)
- **Response schema (200):**
  ```python
  class RefreshResponse(BaseModel):
      access_token: str
      refresh_token: str
  ```

---

### **2. Properties Endpoints**

#### **GET /properties**
- **Auth:** Público
- **Success status:** 200 (Lista de propiedades)
- **Error status:** 400, 500
- **Error codes posibles:**
  - `invalid_pagination` (400)
  - `invalid_filter` (400)
- **Request schema:**
  ```python
  class GetPropertiesQueryParams(BaseModel):
      page: int = 1
      per_page: int = 20
      price_min: Optional[int] = None
      price_max: Optional[int] = None
      location: Optional[str] = None
      status: Optional[Literal["active", "inactive"]] = None
      sort: Optional[Literal["price", "created_at"]] = None
      dir: Optional[Literal["asc", "desc"]] = None
  ```
- **Response schema (200):**
  ```python
  class GetPropertiesResponse(BaseModel):
      items: List[PropertyResponse]
      pagination: PaginationMetadata
  ```

---

#### **GET /properties/{id}**
- **Auth:** Público
- **Success status:** 200 (Propiedad encontrada)
- **Error status:** 404, 500
- **Error codes posibles:**
  - `property_not_found` (404)
- **Request schema:** `id: int`
- **Response schema (200):**
  ```python
  class PropertyResponse(BaseModel):
      id: int
      title: str
      description: str
      price: int
      location: str
      status: Literal["active", "inactive"]
      created_at: datetime
      updated_at: datetime
  ```

---

#### **POST /properties**
- **Auth:** Protegido (roles: `admin`, `agent`)
- **Success status:** 201 (Creado exitosamente)
- **Error status:** 400, 401, 403, 422, 500
- **Error codes posibles:**
  - `missing_required_field` (400)
  - `invalid_price` (400)
  - `unauthorized` (401)
  - `invalid_request` (422)
- **Request schema:**
  ```python
  class CreatePropertyRequest(BaseModel):
      title: str
      description: str
      price: int
      location: str
      status: Literal["active", "inactive"] = "active"
  ```
- **Response schema (201):**
  ```python
  class CreatePropertyResponse(PropertyResponse):
      pass
  ```

---

#### **PATCH /properties/{id}**
- **Auth:** Protegido (roles: `admin`, `agent`)
- **Success status:** 200 (Actualizado exitosamente)
- **Error status:** 400, 401, 403, 404, 422, 500
- **Error codes posibles:**
  - `property_not_found` (404)
  - `invalid_price` (400)
  - `unauthorized` (401)
  - `invalid_request` (422)
- **Request schema:**
  ```python
  class UpdatePropertyRequest(BaseModel):
      title: Optional[str] = None
      description: Optional[str] = None
      price: Optional[int] = None
      location: Optional[str] = None
      status: Optional[Literal["active", "inactive"]] = None
  ```
- **Response schema (200):**
  ```python
  class UpdatePropertyResponse(PropertyResponse):
      pass
  ```

---

#### **DELETE /properties/{id}**
- **Auth:** Protegido (roles: `admin`, `agent`)
- **Success status:** 204 (Eliminado exitosamente)
- **Error status:** 401, 403, 404, 500
- **Error codes posibles:**
  - `property_not_found` (404)
  - `unauthorized` (401)
- **Request schema:** `id: int`
- **Response schema (204):**
  ```python
  class DeletePropertyResponse(BaseModel):
      pass
  ```

---

## **Catálogo de Errores Estándar**

| error.code          | http_status | cuándo ocurre                                                                 | details esperado                                                                 |
|---------------------|-------------|-------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| invalid_email       | 400         | Email no válido (formato incorrecto)                                          | {"email": "Invalid email format"}                                                |
| user_exists         | 409         | Usuario ya existe (email duplicado)                                           | {"email": "User with this email already exists"}                                |
| password_weak       | 400         | Contraseña no cumple con requisitos (longitud, caracteres)                    | {"password": "Password must be at least 8 characters"}                         |
| invalid_credentials | 401         | Credenciales incorrectas (login)                                              | {"email": "Invalid email or password"}                                          |
| user_not_found      | 404         | Usuario no encontrado (login o refresh)                                       | {"email": "User not found"}                                                     |
| invalid_token       | 401         | Token JWT inválido (access o refresh)                                         | {"token": "Invalid token format"}                                               |
| token_expired       | 403         | Token expirado (refresh)                                                      | {"token": "Token has expired"}                                                  |
| property_not_found  | 404         | Propiedad no encontrada (GET /properties/{id} o DELETE /properties/{id})     | {"id": "Property with this ID does not exist"}                                 |
| missing_required_field | 400 | Campo requerido faltante (POST /properties)                                  | {"field": "Field 'title' is required"}                                         |
| invalid_price       | 400         | Precio inválido (menor que 0 o no entero)                                     | {"price": "Price must be a positive integer"}                                   |
| unauthorized        | 401         | No se proporcionó token de acceso (GET /properties, POST /properties, etc.)  | {"token": "Missing access token"}                                               |
| invalid_pagination  | 400         | Parámetros de paginación inválidos (GET /properties)                          | {"page": "Page must be >=1", "per_page": "Per page must be between 1 and 50"} |
| invalid_filter      | 400         | Filtros inválidos (GET /properties)                                           | {"price_min": "Price min must be >=0", "location": "Location must be a string"} |
| invalid_request     | 422         | Solicitud inválida (estructura JSON incorrecta, campos no esperados)         | {"error": "Invalid request body"}                                               |

---

## **Notas Arquitectónicas**

- **JWT:** Los tokens (`access_token`, `refresh_token`) deben ser generados con algoritmo `HS256` y firmados con una clave secreta.
- **PaginationMetadata:** Debe incluir `page`, `per_page`, `total_items`, y `total_pages`.
- **Validation:** Validar campos en el lado del servidor usando `pydantic` y `fastapi` (por ejemplo, `@pydantic.root_validator` para validaciones cruzadas).
- **Error Handling:** Usar `HTTPException` con códigos específicos para cada error. Los detalles de error deben ser devueltos en el cuerpo de la respuesta.

--- 

¿Necesitas ayuda con la implementación de estos endpoints en FastAPI o SQLAlchemy?

