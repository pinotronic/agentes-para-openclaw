# API Contract (source of truth)

> Regla: si se toca un endpoint, se actualiza aquí (o en OpenAPI) **antes** de implementar.

## Convenciones globales
- Base URL: `/api`
- Auth:
- Errores estándar:
  - 400 validation_error
  - 401 unauthorized
  - 403 forbidden
  - 404 not_found
  - 409 conflict
  - 422 unprocessable
  - 500 internal
- Paginación:
  - `page`, `page_size`
- Orden:
  - `sort` (ej: `created_at:desc`)

## Endpoints

### [MVP-01] (ejemplo) Crear recurso X
- `POST /x`
- Request:
```json
{}
```
- Response 201:
```json
{}
```
- Errores:
  - 400 ...

(duplica secciones por endpoint)
