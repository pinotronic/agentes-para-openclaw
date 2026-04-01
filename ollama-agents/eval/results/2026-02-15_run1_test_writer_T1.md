# PLAN DE PRUEBAS MVP v1.0 - Mini-Inmobiliaria

## Principios aplicados

- **Cobertura por capas de pirámide de pruebas**: 70% unitarias, 25% integración, 10% contrato/API.
- **Aislamiento de datos**: Uso de transacciones por test o base efímera (SQLite en memoria).
- **Testeos determinísticos**: Uso de `freezegun` para tiempo, evitando dependencias externas.
- **Validación de contratos**: Todos los endpoints se testean con formatos de error estándar.
- **Seguridad y autenticación**: Se verifican tokens, errores de autenticación y rol.
- **Pruebas de dominio y casos de uso**: Se cubren todos los casos de uso del MVP.

---

## 1. Arquitectura del sistema

```
Infraestructura (SQLModel, FastAPI)  
→ Interfaces (Pydantic, FastAPI Endpoints)  
→ Aplicación (Casos de Uso)  
→ Dominio (Entidades Puras)
```

---

## 2. Modelos de Dominio

### Entidad `User`
```python
class User:
    id: int
    email: str
    password_hash: str
    role: str  # "admin", "agent", "visitor"
    created_at: datetime
```

### Entidad `Property`
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

### Entidad `Token`
```python
class Token:
    access_token: str
    refresh_token: str
    expires_in: int
```

---

## 3. Casos de Uso

### Módulo de Autenticación

- `RegisterUser` → `def register_user(user: UserCreate) -> Token`
- `AuthenticateUser` → `def authenticate_user(email: str, password: str) -> Token`
- `RefreshToken` → `def refresh_token(refresh_token: str) -> Token`

### Módulo de Inmuebles

- `CreateProperty` → `def create_property(property: PropertyCreate) -> PropertyResponse`
- `UpdateProperty` → `def update_property(id: int, property: PropertyUpdate) -> PropertyResponse`
- `DeleteProperty` → `def delete_property(id: int) -> SuccessResponse`
- `ListProperties` → `def list_properties(params: ListPropertyParams) -> PropertyListResponse`
- `GetProperty` → `def get_property(id: int) -> PropertyResponse`

---

## 4. Contratos API

### Módulo de Autenticación

```python
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

### Módulo de Inmuebles

```python
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

## 5. Estrategia de Pruebas

### 5.1 Pruebas Unitarias (70%)

#### Módulo de Autenticación

- `test_register_user_success` → Verifica creación de usuario y token.
- `test_register_user_invalid_email` → Verifica error 422.
- `test_login_invalid_password` → Verifica error 401.
- `test_refresh_token_expired` → Verifica error 401.
- `test_refresh_token_valid` → Verifica éxito de refresh.

#### Módulo de Inmuebles

- `test_create_property_success` → Verifica creación y retorno de `PropertyResponse`.
- `test_create_property_invalid_price` → Verifica error 422.
- `test_list_properties_pagination` → Verifica paginación (10 items/page).
- `test_list_properties_filters` → Verifica filtro por precio y ubicación.
- `test_get_property_not_found` → Verifica error 404.
- `test_update_property_success` → Verifica actualización.
- `test_delete_property_success` → Verifica eliminación.

### 5.2 Pruebas de Integración (25%)

- `test_auth_register_endpoint` → Verifica flujo completo de registro.
- `test_auth_login_endpoint` → Verifica login y token.
- `test_property_list_endpoint` → Verifica listado de inmuebles.
- `test_property_crud_endpoint` → Verifica CRUD completo.

### 5.3 Pruebas de Excepciones (10%)

- `test_invalid_email_format` → Verifica error 422.
- `test_unauthorized_access` → Verifica error 403 para usuarios no autorizados.
- `test_missing_token` → Verifica error 401.

---

## 6. Comandos pytest

### Ejecutar todas las pruebas

```bash
pytest -v
```

### Ejecutar solo pruebas unitarias

```bash
pytest tests/unit/ -v
```

### Ejecutar solo pruebas de integración

```bash
pytest tests/integration/ -v
```

### Ejecutar pruebas con cobertura

```bash
pytest --cov=src --cov-report=html
```

### Ejecutar pruebas con SQLite en memoria (tests)

```bash
pytest tests/ --db-type=sqlite-memory
```

---

## 7. Cobertura de pruebas por módulo

| Módulo             | Pruebas Unitarias | Pruebas Integración | Excepciones |
|--------------------|-------------------|---------------------|-------------|
| Autenticación      | 5                 | 2                   | 2           |
| Inmuebles CRUD     | 6                 | 2                   | 1           |
| Errores y validación | 3                 | 0                   | 3           |
| **Total**          | **14**            | **4**               | **6**       |

---

## 8. Ejemplo de estructura de directorios de pruebas

```
tests/
├── conftest.py
├── unit/
│   ├── test_auth.py
│   └── test_property.py
├── integration/
│   ├── test_auth_endpoint.py
│   └── test_property_endpoint.py
└── fixtures/
    ├── user_fixtures.py
    └── property_fixtures.py
```

---

## 9. Ejemplo de test unitario

```python
# tests/unit/test_auth.py
import pytest
from unittest.mock import Mock, patch
from src.auth import RegisterUser, AuthenticateUser
from src.models import UserCreate

def test_register_user_success():
    # Arrange
    user_create = UserCreate(email="test@example.com", password="password", role="visitor")
    mock_repo = Mock()
    mock_repo.create_user.return_value = {"id": 1, "email": "test@example.com"}

    # Act
    service = RegisterUser(mock_repo)
    result = service.register_user(user_create)

    # Assert
    assert result.access_token is not None
    assert result.refresh_token is not None
```

---

## 10. Ejemplo de test de integración

```python
# tests/integration/test_auth_endpoint.py
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_register_endpoint_success():
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password",
        "role": "visitor"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

---

## 11. Consideraciones de seguridad

- Todos los tests validan el uso de `bcrypt` para hashing de contraseñas.
- Los tokens se generan con `JWT` y se verifican por caducidad.
- Se evita la exposición de información sensible en logs o respuestas.

---

## 12. Comandos de ejecución para ambiente local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar tests
pytest -v

# Ejecutar con cobertura
pytest --cov=src --cov-report=term-missing

# Ejecutar con DB en memoria
pytest tests/ --db-type=sqlite-memory
```

---

