import pygame
import random
import socket
import threading
import queue

# --- Configuración ---
SCREEN_W, SCREEN_H = 1920, 1080
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

# Cola para recibir datos de gaze_server
gaze_queue = queue.Queue()

# --- Función para recibir datos UDP ---
def udp_receiver(q):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    while True:
        data, _ = sock.recvfrom(1024)
        try:
            ts_str, x_str, y_str = data.decode().split(",")
            ts = int(ts_str)
            x = int(float(x_str))
            y = int(float(y_str))
            q.put((ts, x, y))
        except Exception as e:
            print("Error parseando UDP:", e)

# Lanza hilo receptor
threading.Thread(target=udp_receiver, args=(gaze_queue,), daemon=True).start()

# --- Inicializa Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Gaze Target Demo")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)

# Variables de estímulo y mirada
fix_target = None
gx, gy = SCREEN_W // 2, SCREEN_H // 2
fix_start = None

# Botón SALIR
button_rect = pygame.Rect(SCREEN_W-120, 20, 100, 50)
button_color = (200,0,0)
button_hover = False
button_gaze_start = None

running = True
while running:
    screen.fill((255, 255, 255))

    # --- Dibuja estímulo ---
    if fix_target is None:
        shape_type = random.choice(['circle', 'square', 'triangle'])
        x, y = random.randint(100, SCREEN_W-100), random.randint(100, SCREEN_H-100)
        fix_target = (shape_type, x, y)

    shape_type, x, y = fix_target
    color = (0,0,255)
    if shape_type == 'circle':
        pygame.draw.circle(screen, color, (x, y), 40)
    elif shape_type == 'square':
        pygame.draw.rect(screen, color, pygame.Rect(x-40, y-40, 80, 80))
    else:
        pygame.draw.polygon(screen, color, [(x, y-50), (x-50, y+50), (x+50, y+50)])

    # --- Leer coordenadas desde gaze_queue ---
    try:
        while True:
            ts, gx, gy = gaze_queue.get_nowait()
    except queue.Empty:
        pass

    # Dibuja punto de mirada
    pygame.draw.circle(screen, (255,0,0), (gx, gy), 8)

    # --- Chequea dwell time estímulo 700ms ---
    if abs(gx - x) < 40 and abs(gy - y) < 40:
        if fix_start is None:
            fix_start = pygame.time.get_ticks()
        elif pygame.time.get_ticks() - fix_start > 700:
            fix_target = None
            fix_start = None
    else:
        fix_start = None

    # --- Dibuja botón SALIR ---
    mouse_pos = pygame.mouse.get_pos()
    button_hover = button_rect.collidepoint(mouse_pos)
    pygame.draw.rect(screen, button_color if not button_hover else (255,0,0), button_rect)
    text_surf = font.render("SALIR", True, (255,255,255))
    screen.blit(text_surf, (button_rect.x+10, button_rect.y+10))

    # --- Chequea gaze sobre botón ---
    if button_rect.collidepoint(gx, gy):
        if button_gaze_start is None:
            button_gaze_start = pygame.time.get_ticks()
        elif pygame.time.get_ticks() - button_gaze_start > 700:
            running = False
    else:
        button_gaze_start = None

    # Manejo de eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if button_rect.collidepoint(event.pos):
                running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
