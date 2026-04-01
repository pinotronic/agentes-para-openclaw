from PIL import Image
import os

def remove_blue(image_path, output_path):
    print(f"Procesando: {image_path}")
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        pixels = img.load()
        width, height = img.size
        
        count = 0
        total = width * height
        
        # Umbrales para detectar azul (B alto, R y G bajos relativamente)
        # Ajustable: B debe superar a R y G por un margen significativo
        margin = 30
        min_blue = 80
        
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                
                # Criterio simple para azul visible en documentos
                if b > min_blue and b > (r + margin) and b > (g + margin):
                    pixels[x, y] = (255, 255, 255) # Blanco
                    count += 1
                    
        img.save(output_path, quality=95)
        print(f"Completado. Píxeles modificados: {count}/{total}")
        print(f"Guardado en: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    src = "/home/administrador/Descargas/Documento_escaneado.jpg"
    dst = "/home/administrador/Descargas/Documento_escaneado_limpio.jpg"
    
    if os.path.exists(src):
        remove_blue(src, dst)
    else:
        print(f"No se encontró el archivo: {src}")
