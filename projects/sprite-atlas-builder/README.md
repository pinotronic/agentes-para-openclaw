# Sprite Atlas Builder

Herramienta web para construir sprite sheets (atlas de imágenes) a partir de imágenes individuales.

## Funcionalidades MVP

- Carga de imágenes (PNG, JPG, WEBP)
- Grid Mode (colocación automática en grilla)
- Drag-and-drop para ajustar posiciones
- Preview en tiempo real
- Exportar PNG del atlas
- Exportar JSON con coordenadas

## Estructura del proyecto

```
sprite-atlas-builder/
├── src/                    # Frontend React
│   ├── domain/            # Entidades puras
│   ├── application/        # Casos de uso
│   ├── infrastructure/     # Servicios externos
│   └── interfaces/        # Contratos API
├── backend/               # Backend FastAPI
│   ├── main.py
│   └── requirements.txt
└── tests/                 # Pruebas
```

## Instalación

### Frontend
```bash
npm install
npm run dev
```

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## Uso

1. Abre http://localhost:3000
2. Carga imágenes mediante drag-and-drop o el botón de subir
3. Usa Grid Mode para disponer automáticamente
4. Exporta como PNG o JSON
