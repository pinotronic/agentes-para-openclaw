# Integración de Voz de Rex en Chats de OpenClaw

## 📖 Cómo funciona

Este módulo integra la **voz de Rex** en tus chats de OpenClaw, permitiendo que el asistente genere audio automáticamente.

## 🚀 Uso básico

```python
from voz_rex_integration import speak_text

# Generar y enviar audio automáticamente
speak_text("Hola, soy Rex. ¿En qué puedo ayudarte hoy?")
```

## 📁 Estructura de archivos

```
voz_rex/
├── utils/
│   └── tts.py                    # Script original de síntesis de voz
├── rex_voice_integration.py      # Wrapper de integración
└── README.md                     # Documentación
```

## 🔧 Configuración de entorno

```bash
export TELEGRAM_BOT_TOKEN="tu_token_aqui"
export TELEGRAM_CHAT_ID="tu_chat_id"
```

## ✅ Prueba rápida

```bash
python3 /home/administrador/.openclaw/workspace/voz_rex/rex_voice_integration.py "Prueba de voz de Rex"
```

## 📊 Salidas esperadas

- **Texto generado**: `Hola, soy Rex. ¿En qué puedo ayudarte hoy?`
- **Archivo MP3**: Generado en `/tmp` o ruta especificada
- **Telegram**: Envío automático del audio con caption "Mensaje de Rex"

## 🐛 Solución de problemas

| Error | Solución |
|-------|---------|
| `openclaw message no disponible` | Asegúrate de tener OpenClaw instalado |
| `ffplay no encontrado` | Instala un reproductor de audio |
| `TELEGRAM_BOT_TOKEN no definido` | Exporta la variable de entorno |

## 📝 Licencia

Propiedad de Pinotronic. Uso interno exclusivo.
