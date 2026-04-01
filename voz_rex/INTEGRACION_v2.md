# Integración de Voz de Rex con ElevenLabs (v2.0)

## 🚀 Descripción

Este módulo integra la **voz de Rex con ElevenLabs** en tus chats de OpenClaw, proporcionando audio de calidad profesional (10/10).

### Características Principales

- ✅ **Calidad 10/10**: Voces ultra-naturales con ElevenLabs
- ✅ **Múltiples voces**: Neutral, amigable, serio, entusiasta
- ✅ **Emociones**: Entonación y tono natural
- ✅ **Optimizado**: Sistema de caching para reutilización
- ✅ **Fallback robusto**: Baja a gTTS si no hay API key
- ✅ **Envío a Telegram**: Integración con OpenClaw message
- ✅ **Reproductores**: Múltiples fallbacks (ffplay, mpv, vlc, etc.)

## 📖 Cómo funciona

1. **Generación con ElevenLabs**: Calidad profesional
2. **Fallback gTTS**: Si no hay API key
3. **Envío automático**: A Telegram con OpenClaw
4. **Reproducción local**: Con múltiples reproductores

## 🚀 Uso básico

### CLI Básico

```bash
python utils/tts.py "Hola, soy Rex. ¿En qué puedo ayudarte hoy?"
```

### Con voz personalizada

```bash
python utils/tts.py "¡Hola Pinotronic!" --voice rex_amigable
```

### Solo generar (sin reproducir)

```bash
python utils/tts.py "Hola, soy Rex" -o mensaje.mp3 --no-play
```

### Programático

```python
from rex_voice_integration import speak_text

# Generar y enviar audio automáticamente
speak_text("Hola, soy Rex. ¿En qué puedo ayudarte hoy?")

# Con voz específica
speak_text("¡Hola!", voice_id="rex_serio")

# Sin enviar a Telegram
speak_text("Mensaje rápido", send_telegram=False)

# Solo generar archivo
speak_text("Prueba de voz", send_telegram=False, play_audio=False)
```

## 📁 Estructura de archivos

```
voz_rex/
├── utils/
│   └── tts.py                    # Motor de voz con ElevenLabs
├── rex_voice_integration.py      # Wrapper de integración
├── INTEGRACION.md                # Esta documentación
├── README.md                     # Documentación básica
├── requirements.txt              # Dependencias
└── .env                          # Variables de entorno (opcional)
```

## 🔧 Configuración de entorno

### Opción 1: Archivo .env (Recomendado)

Crea un archivo `.env` en la raíz:

```env
ELEVENLABS_API_KEY=tu_api_key_aqui
TELEGRAM_BOT_TOKEN=tu_token_telegram
TELEGRAM_CHAT_ID=tu_chat_id
```

### Opción 2: Variables de entorno

```bash
export ELEVENLABS_API_KEY="tu_api_key_aqui"
export TELEGRAM_BOT_TOKEN="tu_token_aqui"
export TELEGRAM_CHAT_ID="tu_chat_id"
```

## ✅ Prueba rápida

### 1. Obtener API Key de ElevenLabs

1. Ve a https://elevenlabs.io/
2. Regístrate (es gratis)
3. Ve a "Settings" → "API Keys"
4. Copia tu API key

### 2. Configurar

```bash
echo "export ELEVENLABS_API_KEY="tu_api_key" >> ~/.bashrc
source ~/.bashrc
```

### 3. Probar

```bash
python utils/tts.py "Prueba de voz de Rex v2.0"
```

## 🎤 Voces disponibles

| Voz | ID ElevenLabs | Descripción |
|-----|---------------|-------------|
| `rex_neutral` | 21m00Tsi4xszn2q4d0k4p | Voz neutral, profesional |
| `rex_amigable` | EXAVITQu4vr4xnKLxMV8 | Cálida y cercana (default) |
| `rex_serio` | pNInz6obpgDQGcBMk49b | Profesional, serio |
| `rex_entusiasta` | ErXwobaYiN019Pky327w | Energética, alegre |

## 📊 Comparación de calidad

| Sistema | Calificación | Descripción |
|---------|-------------|-------------|
| gTTS | 4/10 | Google Translate TTS, mecánico |
| ElevenLabs | 10/10 | Voces ultra-naturales, emociones |

## 🐛 Solución de problemas

| Error | Solución |
|-------|----------|
| `ELEVENLABS_API_KEY no definida` | Crea archivo `.env` o exporta la variable |
| `openclaw message no disponible` | Asegúrate de tener OpenClaw instalado |
| `ffplay no encontrado` | Instala un reproductor o usa el fallback |
| `gtts no instalado` | `pip install gTTS` |
| `elevenlabs no instalado` | `pip install elevenlabs` |

## 🎯 Mejoras respecto a v1.0

### v1.0 (gTTS)
- ✅ Funcional
- ❌ Calidad 4/10
- ❌ Sin emociones
- ❌ Voz mecánica

### v2.0 (ElevenLabs)
- ✅ Funcional + Profesional
- ✅ Calidad 10/10
- ✅ Emociones y entonación
- ✅ Voces naturales
- ✅ Optimizado con caching

## 📝 Licencia

Propiedad de Pinotronic. Uso interno exclusivo.

## 🙏 Créditos

- **ElevenLabs**: Motor de síntesis de voz
- **gTTS**: Fallback para compatibilidad
- **OpenClaw**: Plataforma de orquestación
