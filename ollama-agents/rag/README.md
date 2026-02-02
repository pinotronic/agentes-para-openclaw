# RAG (memoria de trabajo) - diseño

Objetivo: dar a los agentes contexto consistente sobre **cómo trabajamos** y **cómo es el repo** sin meter datos privados.

## Principios
- **Allowlist** (preferido): indexar únicamente rutas seguras.
- Nunca indexar secretos/datos personales/bancarios (ver `../POLICY.md`).
- El RAG asiste; la verificación final siempre es por herramientas (tests/lint/build).

## Colecciones sugeridas
1) `playbook`: guías de rol, Definition of Done, estilo.
2) `repo_docs`: README, docs internas.
3) `code_examples`: snippets ejemplares (sin secretos).
4) `adrs`: decisiones de arquitectura.

## Embeddings
Usar: `nomic-embed-text-v2-moe:latest`.

## Estado
Pendiente: implementar indexador + almacenamiento vectorial (chroma/sqlite/pgvector). Se hará cuando Pinotronic defina el primer repo objetivo.
