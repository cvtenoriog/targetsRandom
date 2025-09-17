import pygame
import random
import socket
import threading
import queue
import time

# --- Configuración ---
SCREEN_W, SCREEN_H = 1920, 1080  # pantalla completa
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
DWELL_TIME = 0.7  # segundos para activar fijación

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
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN)
pygame.display.set_caption("Gaze Game Demo")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 36)

# --- Variables de juego ---
score = 0
fix_start = None
target = None

# Botón de salir
exit_button_rect = pygame.Rect(SCREEN_W - 150, 20, 130, 60)
exit_start = None

# Coordenadas de la mirada
gx, gy = SCREEN_W // 2, SCREEN_H // 2

running = True
while running:
    screen.fill((200, 255, 200))

    # --- Nuevo objetivo si no hay ---
    if target is None:
        x, y = random.randint(50, SCREEN_W - 50), random.randint(50, SCREEN_H - 50)
        target = (x, y)

    x, y = target
    pygame.draw.circle(screen, (0, 150, 0), (x, y), 25)  # objetivo

    # --- Leer coordenadas del gaze ---
    try:
        while True:
            ts, gx, gy = gaze_queue.get_nowait()
    except queue.Empty:
        pass

    # Dibuja punto de mirada
    pygame.draw.circle(screen, (255, 0, 0), (gx, gy), 8)

    # --- Chequeo de dwell para objetivo ---
    if abs(gx - x) < 25 and abs(gy - y) < 25:
        if fix_start is None:
            fix_start = time.time()
        elif time.time() - fix_start > DWELL_TIME:
            score += 1
            target = None
            fix_start = None
    else:
        fix_start = None

    # --- Dibuja botón de salir ---
    pygame.draw.rect(screen, (200, 0, 0), exit_button_rect)
    text_surf = font.render("SALIR", True, (255, 255, 255))
    screen.blit(text_surf, (exit_button_rect.x + 15, exit_button_rect.y + 10))

    # --- Chequeo de dwell en botón salir ---
    if exit_button_rect.collidepoint(gx, gy):
        if exit_start is None:
            exit_start = time.time()
        elif time.time() - exit_start > DWELL_TIME:
            running = False
    else:
        exit_start = None

    # --- Texto de score ---
    score_text = font.render(f"Score: {score}", True, (0, 0, 0))
    screen.blit(score_text, (20, 20))

    # --- Eventos ---
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
