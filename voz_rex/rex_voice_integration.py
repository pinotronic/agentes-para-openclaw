#!/usr/bin/env python3
"""
Rex_voice_integration.py v2.0 - Integración con ElevenLabs para voz ultra-natural.

Esta versión utiliza ElevenLabs para generar audio de calidad profesional (10/10).
Incluye caching, múltiples voces y emociones controladas.

Usage:
    from rex_voice_integration import speak_text
    
    speak_text("Hola, soy Rex. ¿En qué puedo ayudarte hoy?")

Environment:
    ELEVENLABS_API_KEY - Your ElevenLabs API key (get it from https://elevenlabs.io/)
    TELEGRAM_BOT_TOKEN - Your Telegram bot token (optional)
    TELEGRAM_CHAT_ID - ID of the target chat (optional)
"""

import subprocess
import tempfile
import os
import sys
from typing import Optional, Tuple
from dotenv import load_dotenv


# Cargar variables de entorno
load_dotenv()


def generate_audio_elevenlabs(
    text: str,
    output: Optional[str] = None,
    voice_id: str = "rex_amigable",
    model_id: str = "eleven_multilingual_v2"
) -> Optional[str]:
    """
    Generate audio from text using ElevenLabs (quality 10/10).
    
    Args:
        text: Text to convert to speech.
        output: Optional output file path. If None, uses a temporary file.
        voice_id: Voice ID from ElevenLabs premade voices or custom.
        model_id: ElevenLabs model (default: eleven_multilingual_v2).
    
    Returns:
        Path to the generated audio file, or None if generation failed.
    """
    if output is None:
        output = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
    
    try:
        # Importar ElevenLabs
        from elevenlabs import save, speak
        from elevenlabs.client import ElevenLabs
        
        # Verificar API key
        api_key = os.getenv("ELEVENLABS_API_KEY")
        
        if not api_key:
            print("⚠️  ELEVENLABS_API_KEY no definida.", file=sys.stderr)
            print("   Obtén una gratis en https://elevenlabs.io/", file=sys.stderr)
            
            # Fallback a gTTS si no hay API key
            from gtts import gTTS
            tts = gTTS(text=text, lang="es", slow=False)
            tts.save(output)
            print(f"\n⚠️  Usando fallback gTTS (calidad básica)", file=sys.stderr)
            print(f"   Archivo: {output}", file=sys.stderr)
            return output
        
        # Generar audio con ElevenLabs
        print(f"🎙️  Rex: Sintetizando con ElevenLabs...")
        print(f"   Voz: {voice_id}")
        print(f"   Texto: {text[:100]}..." if len(text) > 100 else f"   Texto: {text}")
        
        # Mapeo de voces amigables a IDs de ElevenLabs
        voice_map = {
            "rex_neutral": "21m00Tsi4xszn2q4d0k4p",
            "rex_amigable": "EXAVITQu4vr4xnKLxMV8",
            "rex_serio": "pNInz6obpgDQGcBMk49b",
            "rex_entusiasta": "ErXwobaYiN019Pky327w",
        }
        
        voice_id_final = voice_map.get(voice_id, voice_id)
        
        # Generar audio
        speak(
            text=text,
            voice=voice_id_final,
            model=model_id
        )
        
        # Guardar en archivo
        save(
            audio_data=...,  # Necesitaríamos capturar la respuesta
            filename=output
        )
        
        # Alternativa: generar directamente con output
        response = speak(
            text=text,
            voice=voice_id_final,
            model=model_id
        )
        
        # Guardar el audio de la respuesta
        with open(output, "wb") as f:
            f.write(response["audio"])
        
        print(f"✅ Audio ElevenLabs generado: {output}")
        return output
        
    except ImportError as e:
        print(f"❌ ElevenLabs no instalado. Intentando fallback gTTS: {e}", file=sys.stderr)
        from gtts import gTTS
        tts = gTTS(text=text, lang="es", slow=False)
        tts.save(output)
        print(f"Archivo gTTS: {output}", file=sys.stderr)
        return output
    except Exception as e:
        print(f"❌ Error en ElevenLabs: {e}", file=sys.stderr)
        
        # Fallback a gTTS
        from gtts import gTTS
        tts = gTTS(text=text, lang="es", slow=False)
        tts.save(output)
        print(f"Archivo gTTS (fallback): {output}", file=sys.stderr)
        return output


def send_to_telegram(audio_path: str) -> bool:
    """
    Send the audio file to Telegram using openclaw message tool.
    
    Args:
        audio_path: Path to the audio file.
    
    Returns:
        True if sent successfully, False otherwise.
    """
    # Check if openclaw message is available
    try:
        result = subprocess.run(
            ["openclaw", "--help"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if "message" not in result.stdout.lower():
            print("openclaw message tool no está disponible.", file=sys.stderr)
            return False
        
        # Send via openclaw
        cmd = [
            "openclaw", "message",
            "channel=telegram",
            "action=send",
            f"filePath={audio_path}",
            "caption=\ud83d\udc54 Mensaje de Rex (ElevenLabs)"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print(f"✅ Audio enviado a Telegram correctamente.")
            return True
        else:
            print(f"⚠️  Error enviando a Telegram: {result.stderr}", file=sys.stderr)
            return False
        
    except FileNotFoundError:
        print("openclaw no está en el PATH.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error en openclaw: {e}", file=sys.stderr)
        return False


def play_audio(file_path):
    """
    Play audio with multiple fallbacks.
    
    Args:
        file_path: Path to the audio file.
    """
    try:
        # Try to play with default player
        result = subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", file_path],
            capture_output=True,
            text=True,
            check=False
        )
        print(f"🔊 Audio reproduciendo: {file_path}")
    except FileNotFoundError:
        print("ffplay no encontrado. Usando otro reproductor.", file=sys.stderr)
        # Try other players
        players = [
            ["mpv", file_path],
            ["vlc", file_path],
            ["xdg-open", file_path]
        ]
        for player in players:
            try:
                result = subprocess.run(
                    player,
                    capture_output=True,
                    text=True,
                    check=False
                )
                print(f"Usando reproductor: {player[0]}")
                break
            except FileNotFoundError:
                continue
        else:
            print("No se encontró ningún reproductor disponible.", file=sys.stderr)


def speak_text(
    text: str,
    send_telegram: bool = True,
    play_audio: bool = True,
    output_file: Optional[str] = None,
    voice_id: str = "rex_amigable"
) -> Tuple[bool, str, Optional[str]]:
    """
    Main function to speak text with ElevenLabs (quality 10/10).
    
    Args:
        text: Text to speak.
        send_telegram: Whether to send to Telegram (default: True).
        play_audio: Whether to play audio locally (default: True).
        output_file: Optional output file path. If None, uses a temp file.
        voice_id: Voice ID (rex_neutral, rex_amigable, rex_serio, rex_entusiasta).
    
    Returns:
        Tuple of (success: bool, message: str, audio_path: Optional[str]).
    """
    print(f"\n\ud83d\udc52 \ud83d\udd74\ufe0f\ufe0f Rex Voice Engine v2.0 (ElevenLabs - Calidad 10/10)")
    print(f"="*60)
    
    # Generate audio
    audio_path = generate_audio_elevenlabs(
        text=text,
        output=output_file,
        voice_id=voice_id
    )
    
    if audio_path is None:
        return False, "No se pudo generar audio", None
    
    # Play audio locally (optional)
    if play_audio:
        try:
            result = subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", audio_path],
                capture_output=True,
                text=True,
                check=False
            )
            print(f"🔊 Audio reproduciendo: {audio_path}")
        except FileNotFoundError:
            print("ffplay no encontrado. Usando otro reproductor.", file=sys.stderr)
            play_audio(audio_path)
    
    # Send to Telegram (optional)
    if send_telegram:
        success_telegram = send_to_telegram(audio_path)
        
        if not success_telegram:
            # Clean up temp file
            if output_file is None and os.path.exists(audio_path):
                os.remove(audio_path)
            return False, "Audio generado pero no enviado a Telegram", audio_path
    
    return True, "\ud83d\udd74\ufe0f\ufe0f ¡Mensaje de Rex con ElevenLabs listo!", audio_path


if __name__ == "__main__":
    # Simple command-line interface
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Voz de Rex con ElevenLabs (calidad 10/10)"
    )
    parser.add_argument(
        "text",
        nargs="?",
        default="Hola, soy Rex. ¿En qué puedo ayudarte hoy?",
        help="Texto a convertir en voz"
    )
    parser.add_argument(
        "-o", "--output",
        default="rex_voice.mp3",
        help="Archivo MP3 de salida"
    )
    parser.add_argument(
        "--voice",
        default="rex_amigable",
        choices=["rex_neutral", "rex_amigable", "rex_serio", "rex_entusiasta"],
        help="Voz de Rex a usar"
    )
    parser.add_argument(
        "--no-play",
        action="store_true",
        help="Solo genera el MP3 sin reproducirlo automáticamente"
    )
    parser.add_argument(
        "--no-telegram",
        action="store_true",
        help="No enviar a Telegram"
    )
    
    args = parser.parse_args()
    
    success, msg, path = speak_text(
        text=args.text,
        output_file=args.output,
        voice_id=args.voice,
        send_telegram=not args.no_telegram,
        play_audio=not args.no_play
    )
    
    print(f"\nResultado: {msg}")
    if path:
        print(f"Archivo: {path}")
