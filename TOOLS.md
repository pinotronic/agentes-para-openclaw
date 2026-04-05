# TOOLS.md - Notas Locales

Las habilidades definen _cómo_ funcionan las herramientas. Este archivo es para _tus_ detalles: lo que es exclusivo de tu configuración.

## Qué va aquí

Información como:

- Nombres y ubicaciones de las cámaras
- Hosts y alias SSH
- Voces preferidas para TTS
- Nombres de altavoces/salas
- Apodos de los dispositivos
- Cualquier información específica del entorno

## Ejemplos

```markdown
### Cámaras

- Sala de estar → Área principal, ángulo amplio de 180°
- Puerta principal → Entrada, activada por movimiento

### SSH

- Servidor doméstico → 192.168.1.100, usuario: admin

### TTS

- Voz preferida: "Nova" (cálida, ligeramente británica)
- Altavoz predeterminado: HomePod de la cocina
```

## ¿Por qué separar?

Las habilidades se comparten. Tu configuración es tuya. Mantenerlas separadas te permite actualizar habilidades sin perder tus notas y compartirlas sin filtrar tu infraestructura.

---

## Trabajo

- **Carpeta de trabajo:** `/media/administrador/IA2/compartida/` (SIEMPRE usar esta, no `~/.openclaw/workspace/` para proyectos)
- Cuando ejecutes comandos con `exec`, usar `workdir=/media/administrador/IA2/compartida/` por defecto

Agrega lo que te ayude a realizar tu trabajo. Esta es tu hoja de referencia.

## MiniMax TTS (Text-to-Speech)

**API:** `https://api.minimax.io/v1/t2a_v2`
**Modelo:** `speech-2.8-hd`
**Auth:** Bearer token desde `~/.openclaw/.env` → `MINIMAX_API_KEY`

**Voces favoritas (Standard Spanish):**
- `Spanish_MaturePartner` — masculino maduro (01)
- `Spanish_ConfidentWoman` — femenino, seguro (04) ← **favorita**

**Voz recomendada para mexicano:** `Spanish_ConfidentWoman`

**Generar audio:**
```bash
source ~/.openclaw/.env
curl -s -X POST "https://api.minimax.io/v1/t2a_v2" \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "speech-2.8-hd", "text": "texto", "voice_setting": {"voice_id": "Spanish_ConfidentWoman"}, "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"}}' \
  | python3 -c "import sys,json;hex=json.load(sys.stdin)['data']['audio'];open('/tmp/output.mp3','wb').write(bytes.fromhex(hex))"
```

**Lista completa de voces:** `POST https://api.minimax.io/v1/get_voice` con `{"voice_type": "all"}`
