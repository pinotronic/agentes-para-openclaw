from PIL import Image
import os

def is_blue(rgb, min_blue=80, margin=30):
    r, g, b = rgb
    # Criterio: B dominante sobre R y G
    return b > min_blue and b > (r + margin) and b > (g + margin)

def get_safe_color(img, x, y, width, height, pixels):
    # Intenta encontrar un color de fondo cercano (izquierda, derecha, arriba, abajo)
    offsets = [(-5, 0), (5, 0), (0, -5), (0, 5), (-10, 0), (10, 0)]
    
    for dx, dy in offsets:
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            color = pixels[nx, ny]
            if not is_blue(color):
                return color
    
    # Fallback: Color de la esquina superior izquierda (asumiendo que es margen/papel)
    # O un promedio simple de la imagen si se pudiera calcular rápido, pero esto suele bastar.
    try:
        return pixels[10, 10]
    except:
        return (245, 245, 245) # Un gris muy claro por defecto

def remove_blue_smart(image_path, output_path):
    print(f"Procesando (modo inpainting simple): {image_path}")
    try:
        img = Image.open(image_path)
        img = img.convert("RGB")
        pixels = img.load()
        width, height = img.size
        
        count = 0
        
        # Primero detectamos todos los azules para no usar un azul como referencia de otro
        # Como iteramos secuencialmente y modificamos 'in-place', si tomamos de "atrás" (izquierda/arriba)
        # tomaremos un píxel YA corregido, lo cual es BUENO (propaga el fondo).
        
        for y in range(height):
            for x in range(width):
                current_color = pixels[x, y]
                
                if is_blue(current_color):
                    # Buscar reemplazo
                    # Prioridad: Píxel a la izquierda (ya procesado y probablemente fondo)
                    if x > 2:
                        replacement = pixels[x-2, y]
                        # Si el de la izquierda ERA azul, ahora ya es fondo, así que sirve.
                        # Pero si estamos en un bloque azul grande, el de la izquierda podría ser un "falso fondo" plano.
                        # Aún así es mejor que blanco puro.
                        
                        # Verificación extra: si el reemplazo parece "muy oscuro" o extraño, buscar otro.
                        pixels[x, y] = replacement
                    else:
                        # Borde izquierdo: tomar de la derecha (aún no procesado, verificar no azul)
                        replacement = get_safe_color(img, x, y, width, height, pixels)
                        pixels[x, y] = replacement
                        
                    count += 1
                    
        img.save(output_path, quality=95)
        print(f"Completado. Píxeles corregidos: {count}")
        print(f"Guardado en: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    src = "/home/administrador/Descargas/Documento_escaneado.jpg"
    dst = "/home/administrador/Descargas/Documento_escaneado_limpio_v2.jpg"
    
    if os.path.exists(src):
        remove_blue_smart(src, dst)
    else:
        print(f"No se encontró el archivo: {src}")
