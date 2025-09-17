import pygame, math
from utils.tamano import normalizar_imagen

def generar_frames(img_path, num_frames=12, rot_angle=15, scale_variation=4):
    """
    Genera frames animados con un aleteo más suave usando interpolación senoidal.
    """
    img = pygame.image.load(img_path).convert_alpha()
    img = normalizar_imagen(img)  # normaliza a tamaño estándar
    frames = []

    for i in range(num_frames):
        # fase de 0 a 2π
        t = (i / num_frames) * 2 * math.pi  

        # oscilación suave con sinusoide
        angle = math.sin(t) * rot_angle
        scale = 1 + (math.sin(t) * scale_variation / 100.0)  # % de variación

        # aplicar escala
        w, h = img.get_size()
        new_w, new_h = int(w * scale), int(h * scale)
        scaled = pygame.transform.smoothscale(img, (new_w, new_h))

        # aplicar rotación
        rotated = pygame.transform.rotate(scaled, angle)
        frames.append(rotated)

    return frames
