# voz_rex

Script mínimo de síntesis de voz en español usando gTTS.

## Requisitos

- Python 3.12+

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

```bash
python utils/tts.py
```

Al terminar, el script intenta reproducir automáticamente el MP3 generado.

### Con texto personalizado

```bash
python utils/tts.py "Hola, esta es una prueba" -o prueba.mp3
```

### Solo generar (sin reproducir)

```bash
python utils/tts.py "Hola, esta es una prueba" -o salida.mp3 --no-play
```

## Salida

Genera el archivo indicado (por defecto `rex_voice.mp3`) en la raíz del proyecto.

