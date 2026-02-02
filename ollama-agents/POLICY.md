# Policy: Private data, secrets, and indexing

## Nunca
- Indexar o guardar en RAG:
  - datos personales (dirección, teléfono, correo personal, IDs)
  - datos bancarios (CLABE, cuentas, tarjetas, CVV, SPEI)
  - secretos/credenciales (API keys, tokens, cookies, `.env`, llaves privadas)

## En caso de detectar
- Si durante logs o archivos aparece un posible secreto/dato sensible:
  - NO se copia al contexto
  - se redacta (REDACTED)
  - se registra un aviso técnico sin el contenido

## Enfoque recomendado
- Allowlist: indexar solo docs/código seguro.
- Excluir por default: `.env*`, `*.pem`, `*.key`, `id_rsa*`, `credentials*`, `secrets*`.
