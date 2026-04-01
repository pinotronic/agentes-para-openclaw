import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Dict
from elevenlabs import save, speak
from elevenlabs.client import ElevenLabs


# Configuración de voces de Rex
REX_VOICES: Dict[str, str] = {
    "rex_neutral": "premade/21m00Tsi4xszN_cache00. mp3",
    "rex_amigable": "premade/BXgXV8z8a8m9_cache00.mp3",  # Cálida y cercana
    "rex_serio": "premade/pNInz6obpgDQGcBMk49b.mp3",  # Profesional
    "rex_entusiasta": "premade/D2fcSpgtYr4gX44d7g8g.mp3",  # Energética
}


def get_elevenlabs_client(api_key: Optional[str] = None):
    """Obtener cliente de ElevenLabs con API key del entorno."""
    api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
    
    if not api_key:
        print("⚠️  ELEVENLABS_API_KEY no definida.")
        print("   Obtén una gratis en https://elevenlabs.io/ y configúrala.")
        return None
    
    return ElevenLabs(api_key=api_key)


def synthesize_speech_elevenlabs(
    text: str,
    voice_id: str = "rex_amigable",
    output_file: str = "rex_voice.mp3",
    model_id: str = "eleven_multilingual_v2"
) -> Optional[str]:
    """
    Generar audio con ElevenLabs (calidad 10/10).
    
    Args:
        text: Texto a sintetizar
        voice_id: ID de voz personalizado o predefinido de ElevenLabs
        output_file: Ruta de salida del archivo MP3
        model_id: Modelo de ElevenLabs (eleven_multilingual_v2 para español)
    
    Returns:
        Path al archivo generado o None si falló
    """
    try:
        # Si es una voz predefinida de ElevenLabs, usar su ID oficial
        # Si es un nombre de Rex, usaremos una voz genérica que ajustaremos
        
        # ElevenLabs voces populares (IDs oficiales)
        voice_map = {
            "rex_neutral": "21m00Tsi4xszn2q4d0k4p",
            "rex_amigable": "EXAVITQu4vr4xnKLxMV8",
            "rex_serio": "pNInz6obpgDQGcBMk49b",
            "rex_entusiasta": "ErXwobaYiN019Pky327w",
        }
        
        voice_id_final = voice_map.get(voice_id, voice_id)
        
        # Generar audio
        print(f"🎙️  Rex: Sintetizando con ElevenLabs...")
        print(f"   Voz: {voice_id}")
        print(f"   Texto: {text[:100]}..." if len(text) > 100 else f"   Texto: {text}")
        
        speak(
            text=text,
            voice=voice_id_final,
            model=model_id,
            output=output_file
        )
        
        if os.path.exists(output_file):
            print(f"✅ Audio generado: {output_file}")
            return output_file
        else:
            print(f"❌ Error: No se creó el archivo {output_file}")
            return None
            
    except Exception as e:
        print(f"❌ Error en ElevenLabs: {e}")
        return None


def synthesize_speech_gTTS(text, output_file="rex_voice.mp3"):
    """Fallback a gTTS si ElevenLabs no está disponible."""
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="es", slow=False)
        tts.save(output_file)
        print(f"Archivo guardado (fallback gTTS): {output_file}")
        return output_file
    except Exception as e:
        print(f"Fallback gTTS falló: {e}")
        return None


def play_audio(file_path):
    """Reproducir audio con múltiples fallbacks."""
    players = [
        (["xdg-open", file_path], False),
        (["ffplay", "-nodisp", "-autoexit", file_path], True),
        (["mpg123", file_path], True),
        (["mpv", file_path], True),
        (["cvlc", "--play-and-exit", file_path], True),
        (["vlc", "--play-and-exit", file_path], False),
    ]

    for command, wait_for_end in players:
        if __import__("shutil").which(command[0]):
            if wait_for_end:
                __import__("subprocess").run(command, check=False)
            else:
                __import__("subprocess").Popen(command)
            print(f"🔊 Reproduciendo audio con: {command[0]}")
            return

    print("⚠️  No se encontró un reproductor compatible.")


def parse_args():
    """Parsear argumentos de CLI."""
    parser = argparse.ArgumentParser(
        description="Sintetiza texto a voz con ElevenLabs (calidad 10/10)"
    )
    parser.add_argument(
        "text",
        nargs="?",
        default="Hola, soy Rex. ¿En qué puedo ayudarte?",
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
        help="Solo genera el MP3 sin reproducirlo"
    )
    parser.add_argument(
        "--gtts",
        action="store_true",
        help="Usar fallback gTTS (calidad baja)"
    )
    return parser.parse_args()


def main():
    """Función principal."""
    args = parse_args()
    
    print(f"\n🦖 Rex Voice Engine - v2.0 (ElevenLabs)")
    print(f"="*50)
    
    if args.gtts:
        audio_path = synthesize_speech_gTTS(
            args.text,
            output_file=args.output
        )
    else:
        # Verificar API key
        if not os.getenv("ELEVENLABS_API_KEY"):
            print("⚠️  ELEVENLABS_API_KEY no definida.")
            respuesta = input("¿Quieres usar fallback gTTS (calidad baja)? [s]/n: ")
            if respuesta.lower() == "s":
                audio_path = synthesize_speech_gTTS(
                    args.text,
                    output_file=args.output
                )
            else:
                print("\nSin API key de ElevenLabs.")
                return
        else:
            audio_path = synthesize_speech_elevenlabs(
                text=args.text,
                voice_id=args.voice,
                output_file=args.output
            )
    
    # Reproducir si no se pidió lo contrario
    if args.output != "-" and not args.no_play and audio_path:
        print(f"\n🔊 Reproductor automático:")
        play_audio(args.output)
    
    if audio_path:
        print(f"\n✅ ¡Voz de Rex lista!")
    
    print("="*50)


if __name__ == "__main__":
    main()
