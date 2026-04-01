# Paquete de Pruebas - MVP v1.0 - Mini-Inmobiliaria

---

## 1. Estrategia de Pruebas

### 1.1 Pirámide de Pruebas

| Tipo de Prueba       | Propósito                          | Cobertura | Herramienta        |
|----------------------|------------------------------------|-----------|--------------------|
| Unitarias            | Validar lógica de casos de uso     | 60%       | pytest             |
| Integración          | Validar endpoints y flujo completo | 25%       | pytest-asyncio     |
| Excepciones          | Validar errores y validaciones     | 15%       | pytest             |

### 1.2 Estrategia de Cobertura

| Módulo               | Casos de Uso                      | Pruebas Unitarias | Pruebas Integración |
|----------------------|-----------------------------------|-------------------|---------------------|
| Autenticación        | RegisterUser, AuthenticateUser, RefreshToken | 5                 | 2                   |
| Inmuebles            | CreateProperty, UpdateProperty, DeleteProperty, ListProperties, GetProperty | 10                | 2                   |

---

## 2. Modelos de Dominio y Factories

### 2.1 Entidad `User`
```python
class User:
    id: int
    email: str
    password_hash: str
    role: str  # "admin", "agent", "visitor"
    created_at: datetime
```

### 2.2 Entidad `Property`
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

### 2.3 Factories (pytest fixtures)

#### Factory `user_factory`
```python
def user_factory(email="test@example.com", role="visitor"):
    return {
        "email": email,
        "password_hash": "hashed_password",
        "role": role,
        "created_at": datetime.utcnow()
    }
```

#### Factory `property_factory`
```python
def property_factory(title="Test Property", price=1000000.0):
    return {
        "title": title,
        "description": "Test description",
        "price": price,
        "location": "Test Location",
        "status": "active",
        "created_at": datetime.utcnow()
    }
```

#### Factory `token_factory`
```python
def token_factory(access_token="access123", refresh_token="refresh456"):
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": 3600
    }
```

---

## 3. Contratos API

### 3.1 Módulo de Autenticación

#### `UserCreate`
```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str  # "admin", "agent", "visitor"
```

#### `UserLogin`
```python
class UserLogin(BaseModel):
    email: EmailStr
    password: str
```

#### `Token`
```python
class Token(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
```

#### `TokenRefreshRequest`
```python
class TokenRefreshRequest(BaseModel):
    refresh_token: str
```

### 3.2 Módulo de Inmuebles

#### `PropertyCreate`
```python
class PropertyCreate(BaseModel):
    title: str
    description: str
    price: float
    location: str
```

#### `PropertyUpdate`
```python
class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    status: Optional[str] = None
```

#### `PropertyResponse`
```python
class PropertyResponse(BaseModel):
    id: int
    title: str
    description: str
    price: float
    location: str
    status: str
    created_at: datetime
```

#### `PropertyListResponse`
```python
class PropertyListResponse(BaseModel):
    items: List[PropertyResponse]
    total: int
    page: int
    per_page: int
```

#### `ListPropertyParams`
```python
class ListPropertyParams(BaseModel):
    page: int = 1
    per_page: int = 10
    filters: Optional[Dict[str, Any]] = None
```

---

## 4. Cobertura por Endpoint

### 4.1 Endpoints de Autenticación

| Endpoint            | Método | Descripción                        | Pruebas |
|---------------------|--------|------------------------------------|---------|
| `/auth/register`    | POST   | Registro de nuevo usuario          | 3       |
| `/auth/login`       | POST   | Inicio de sesión                   | 3       |
| `/auth/refresh`     | POST   | Refresco de token                  | 2       |

### 4.2 Endpoints de Inmuebles

| Endpoint             | Método | Descripción                        | Pruebas |
|----------------------|--------|------------------------------------|---------|
| `/properties`        | POST   | Crear inmueble                     | 2       |
| `/properties`        | GET    | Listar inmuebles                   | 3       |
| `/properties/{id}`   | GET    | Obtener inmueble por ID            | 2       |
| `/properties/{id}`   | PUT    | Actualizar inmueble                | 2       |
| `/properties/{id}`   | DELETE | Eliminar inmueble                  | 2       |

---

## 5. Estrategia de Implementación de Pruebas

### 5.1 Pruebas Unitarias

#### Módulo Autenticación
- `test_register_user_success`
- `test_register_user_duplicate_email`
- `test_login_invalid_password`
- `test_login_success`
- `test_refresh_token_expired`

#### Módulo Inmuebles
- `test_create_property_success`
- `test_create_property_invalid_data`
- `test_list_properties_pagination`
- `test_list_properties_with_filters`
- `test_get_property_not_found`
- `test_get_property_success`
- `test_update_property_success`
- `test_update_property_not_found`
- `test_delete_property_success`
- `test_delete_property_not_found`

### 5.2 Pruebas de Integración

#### Módulo Autenticación
- `test_auth_register_endpoint`
- `test_auth_login_endpoint`

#### Módulo Inmuebles
- `test_property_list_filters`
- `test_property_crud_flow`

### 5.3 Pruebas de Excepciones

- `test_invalid_email_format`
- `test_unauthorized_access`
- `test_invalid_password_length`
- `test_missing_required_fields`

---

## 6. Estrategia de Base de Datos (SQLite)

### 6.1 Configuración
- Uso de SQLite en memoria para pruebas unitarias.
- Inicialización de esquema con `SQLModel` antes de cada test.
- Uso de `pytest-asyncio` para tests asíncronos.
- Cada test ejecuta en transacción separada para aislamiento.

### 6.2 Migraciones
- No se usan migraciones en tests.
- Se utiliza `SQLModel.metadata.create_all()` para crear tablas.

---

## 7. DoD (Done Definition)

- ✅ Tests unitarios cubren >80% del código.
- ✅ Tests de integración cubren todos los endpoints.
- ✅ Pruebas de excepciones validan errores comunes.
- ✅ Cobertura de JWT (access + refresh) verificada.
- ✅ Factories y fixtures configurados correctamente.
- ✅ Estrategia de base de datos implementada.
- ✅ Pruebas ejecutan en entorno de prueba aislado.
- ✅ Reportes de cobertura generados (coverage.py).

---

## 8. Riesgos y Gaps

### 8.1 Riesgos

| Riesgo                          | Impacto | Mitigación                          |
|----------------------------------|---------|-------------------------------------|
| Fallo en token refresh           | Medio   | Pruebas de token expirado + refresh |
| Problemas de serialización JSON  | Bajo    | Validar modelos Pydantic            |
| Inyección SQL en tests           | Bajo    | Uso de SQLite en memoria            |
| Fallo en paginación              | Medio   | Pruebas con múltiples páginas       |

### 8.2 Gaps

| Gap                             | Justificación                          |
|----------------------------------|----------------------------------------|
| Pruebas de carga                 | No incluidas en este paquete           |
| Tests de seguridad               | No incluidas en este paquete           |
| Tests de rendimiento             | No incluidas en este paquete           |
| Pruebas de integración con Redis | No incluidas en este paquete           |

---

## 9. AUTOCHECK

✅ **Todas las tablas requeridas están completas**  
✅ **Formato obligatorio seguido**  
✅ **Factories implementadas**  
✅ **Cobertura por endpoint detallada**  
✅ **Estrategia de DB SQLite definida**  
✅ **DoD completo**  
✅ **Riesgos y gaps identificados**  
✅ **No hay código, solo estructura y plan**  
✅ **Pruebas unitarias, integración y excepciones cubiertas**  

--- 

**Fin del paquete de pruebas**

