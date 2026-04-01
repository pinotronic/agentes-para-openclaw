**Principales Tablas de Implementación**

**1. Tabla de Endpoints y Códigos de Estado**

| endpoint                         | método | auth_required | status_codes                         | notas                                       |
|----------------------------------|--------|----------------|--------------------------------------|---------------------------------------------|
| /properties                      | GET    | no             | 200, 400, 500                        | Paginación y filtros                        |
| /properties/{id}                | GET    | no             | 200, 404, 500                        | Obtener propiedad por ID                    |
| /properties                      | POST   | sí             | 201, 400, 401, 403, 422, 500         | Requiere rol admin o agent                  |
| /properties/{id}                | PATCH  | sí             | 200, 400, 401, 403, 404, 422, 500    | Requiere rol admin o agent                  |
| /properties/{id}                | DELETE | sí             | 204, 401, 403, 404, 500              | Requiere rol admin o agent                  |
| /auth/login                      | POST   | no             | 200, 401, 422, 500                   |                                             |
| /auth/refresh                    | POST   | no             | 200, 401, 403, 422, 500              | Requiere refresh_token en headers           |

**2. Tabla de Errores Estándar**

| error.code          | http_status | cuándo ocurre                                                                 | details esperado                                                                 |
|---------------------|-------------|--------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| invalid_email       | 400         | Email no válido (formato incorrecto)                                          | {"email": "Invalid email format"}                                                |
| user_exists         | 409         | Usuario ya existe (email duplicado)                                           | {"email": "User with this email already exists"}                                |
| password_weak       | 400         | Contraseña no cumple con requisitos (longitud, caracteres)                    | {"password": "Password must be at least 8 characters"}                         |
| invalid_credentials | 401         | Credenciales incorrectas (login)                                              | {"email": "Invalid email or password"}                                          |
| user_not_found      | 404         | Usuario no encontrado (login o refresh)                                       | {"email": "User not found"}                                                     |
| invalid_token       | 401         | Token JWT inválido (access o refresh)                                         | {"token": "Invalid token format"}                                               |
| token_expired       | 403         | Token expirado (refresh)                                                      | {"token": "Token has expired"}                                                  |
| property_not_found  | 404         | Propiedad no encontrada (GET /properties/{id} o DELETE /properties/{id})     | {"id": "Property with this ID does not exist"}                                 |
| missing_required_field | 400      | Campo requerido faltante (POST /properties)                                  | {"field": "Field 'title' is required"}                                         |
| invalid_price       | 400         | Precio inválido (menor que 0 o no entero)                                     | {"price": "Price must be a positive integer"}                                   |
| unauthorized        | 401         | No se proporcionó token de acceso (GET /properties, POST /properties, etc.)  | {"token": "Missing access token"}                                               |
| invalid_pagination  | 400         | Parámetros de paginación inválidos (GET /properties)                          | {"page": "Page must be >=1", "per_page": "Per page must be between 1 and 50"} |
| invalid_filter      | 400         | Filtros inválidos (GET /properties)                                           | {"price_min": "Price min must be >=0", "location": "Location must be a string"} |
| invalid_request     | 422         | Solicitud inválida (estructura JSON incorrecta, campos no esperados)         | {"error": "Invalid request body"}                                               |

