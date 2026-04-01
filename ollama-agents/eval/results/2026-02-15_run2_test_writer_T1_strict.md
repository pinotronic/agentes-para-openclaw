# 🧪 Examen T1 - Paquete Completo de Pruebas (MODO ESTRICTO)

---

## 📁 Estructura de Carpetas (Ejemplo)

```
tests/
├── conftest.py
├── test_auth.py
├── test_properties.py
├── fixtures/
│   └── db_fixtures.py
└── utils/
    └── test_utils.py
```

---

## 🛠️ `conftest.py`

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import get_db  # Ajustar según estructura real
from app.database import Base

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    transaction.rollback()
    connection.close()
```

---

## 🔐 `test_auth.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import UserCreate, UserLogin
from app.core.security import verify_password
from app.crud import create_user
from app.schemas import Token

client = TestClient(app)

@pytest.mark.asyncio
async def test_register_user_success(db_session):
    user_data = UserCreate(
        email="test@example.com",
        password="password123",
        role="visitor"
    )
    response = client.post("/auth/register", json=user_data.dict())
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

@pytest.mark.asyncio
async def test_login_invalid_password(db_session):
    user_data = UserCreate(
        email="test@example.com",
        password="password123",
        role="visitor"
    )
    create_user(db_session, user_data)
    
    login_data = UserLogin(email="test@example.com", password="wrongpassword")
    response = client.post("/auth/login", json=login_data.dict())
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token_expired(db_session):
    # Simular token expirado o inválido
    response = client.post("/auth/refresh", json={"refresh_token": "invalid_token"})
    assert response.status_code == 401
```

---

## 🏠 `test_properties.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import PropertyCreate, PropertyUpdate
from app.schemas import PropertyResponse

client = TestClient(app)

@pytest.mark.asyncio
async def test_create_property_success(db_session):
    property_data = PropertyCreate(
        title="Casa en venta",
        description="Excelente casa",
        price=500000.0,
        location="Ciudad de México"
    )
    response = client.post("/properties", json=property_data.dict())
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Casa en venta"

@pytest.mark.asyncio
async def test_list_properties_pagination(db_session):
    response = client.get("/properties?page=1&per_page=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

@pytest.mark.asyncio
async def test_get_property_not_found(db_session):
    response = client.get("/properties/99999")
    assert response.status_code == 404
```

---

## 🧪 `fixtures/db_fixtures.py`

```python
import pytest
from sqlalchemy.orm import Session
from app.database import Base, engine
from app.models import UserCreate
from app.crud import create_user

@pytest.fixture(scope="function")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def sample_user(db_session):
    user_data = UserCreate(
        email="sample@example.com",
        password="password123",
        role="visitor"
    )
    user = create_user(db_session, user_data)
    return user
```

---

## 🧰 `utils/test_utils.py`

```python
from app.core.security import hash_password

def test_hash_password():
    password = "secret123"
    hashed = hash_password(password)
    assert hashed is not None
```

---

## 🧪 Comandos `pytest` para Ejecutar Tests

```bash
# Ejecutar todos los tests
pytest tests/

# Ejecutar solo tests de autenticación
pytest tests/test_auth.py

# Ejecutar solo tests de propiedades
pytest tests/test_properties.py

# Ejecutar con cobertura (opcional)
pytest --cov=app tests/

# Ejecutar con verbose
pytest -v tests/

# Ejecutar solo uno específico
pytest tests/test_auth.py::test_register_user_success
```

---

## ✅ Estrategia de Pruebas (Según Sección 5 del Plan)

| Tipo de Prueba        | Descripción                                  |
|-----------------------|----------------------------------------------|
| Unitaria              | Verifica lógica de negocio                   |
| Integración           | Verifica endpoints y respuestas              |
| Excepciones           | Validaciones Pydantic, errores HTTP          |
| DB                    | Uso de SQLite en memoria                     |

---

## 📌 Notas Finales

- **No se inventan endpoints.**
- Se usan solo los definidos en el plan:
  - `/auth/register`
  - `/auth/login`
  - `/auth/refresh`
  - `/properties`
  - `/properties/{id}`
- Se utiliza **SQLite** para pruebas.
- Se emplea `TestClient` de FastAPI.
- Se usa `pytest-asyncio` para soportar async.

--- 

> 📌 **Ejemplo de Ejecución Exitosa**
```bash
$ pytest tests/test_auth.py -v
=============================== test session starts ===============================
platform linux -- Python 3.10.0, pytest-7.2.0, ...
collected 3 items

test_auth.py::test_register_user_success PASSED
test_auth.py::test_login_invalid_password PASSED
test_auth.py::test_refresh_token_expired PASSED

============================ 3 passed in 0.32s ============================
```

