import pygame

def normalizar_imagen(img, width=50, height=50):
    """
    Normaliza una imagen al tamaño dado.
    Args:
        img (pygame.Surface): imagen original
        width (int): ancho en pixeles
        height (int): alto en pixeles
    Returns:
        pygame.Surface: imagen escalada
    """
    return pygame.transform.smoothscale(img, (width, height))
