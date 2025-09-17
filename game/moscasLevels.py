import pygame, random, time, queue, socket, threading
from utils.animacion import generar_frames
from utils.tamano import normalizar_imagen

# --- Configuración ---
SCREEN_W, SCREEN_H = 1920, 1080
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
GAME_TIME = 30  # 2 minutos por nivel

# --- Cola para gaze_server ---
gaze_queue = queue.Queue()
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
        except:
            pass

threading.Thread(target=udp_receiver, args=(gaze_queue,), daemon=True).start()

# --- Inicializa pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Gaze Game: Moscas")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 36)

# --- Cargar sprites ---
mosca_frames = {
    'fly1': generar_frames('assets/fly1.png', num_frames=4),
    'fly2': generar_frames('assets/fly2.png', num_frames=4),
    'fly3': generar_frames('assets/fly3.png', num_frames=4),
}
pistola_img = normalizar_imagen(pygame.image.load('assets/pistola.png').convert_alpha(), 50, 50)
boom_sound = pygame.mixer.Sound('assets/boom.wav')

# --- Variables del juego ---
gx, gy = SCREEN_W//2, SCREEN_H//2
score = 0
level = 1
start_time = pygame.time.get_ticks()
targets = []
fix_start = None

# --- Funciones auxiliares ---
def crear_moscas(n=1):
    new_targets = []
    for _ in range(n):
        type_fly = random.choice(['fly1', 'fly2', 'fly3'])
        x, y = random.randint(50, SCREEN_W-50), random.randint(50, SCREEN_H-50)
        new_targets.append({'type': type_fly, 'x': x, 'y': y, 'frame_idx':0})
    return new_targets

def reiniciar_nivel():
    global targets, fix_start
    targets = crear_moscas(level if level==1 else 3)  # nivel2: 3 moscas
    fix_start = None

# --- Inicia primer nivel ---
reiniciar_nivel()
running = True
show_summary = False

# --- Loop principal ---
while running:
    screen.fill((200,255,200))
    elapsed = (pygame.time.get_ticks() - start_time)/1000
    time_left = max(0, GAME_TIME - int(elapsed))

    # --- Actualiza gaze ---
    try:
        while True:
            ts, gx, gy = gaze_queue.get_nowait()
    except queue.Empty:
        pass

    # --- Dibujar moscas ---
    for t in targets:
        frames = mosca_frames[t['type']]
        t['frame_idx'] = (t['frame_idx'] + 1) % len(frames)
        frame_img = frames[t['frame_idx']]
        screen.blit(frame_img, (t['x'] - frame_img.get_width()//2, t['y'] - frame_img.get_height()//2))

    # --- Dibuja pistola ---
    screen.blit(pistola_img, (gx - pistola_img.get_width()//2, gy - pistola_img.get_height()//2))

    # --- Chequea si "mata" mosca ---
    for t in targets:
        if abs(gx - t['x']) < 25 and abs(gy - t['y']) < 25:
            boom_sound.play()
            # Puntuación según tipo
            if t['type']=='fly1': score += 3
            elif t['type']=='fly2': score += 2
            else: score += 1
            reiniciar_nivel()
            break

    # --- Mostrar puntaje y tiempo ---
    score_text = font.render(f"Puntaje: {score}", True, (0,0,0))
    time_text = font.render(f"Tiempo restante: {time_left}", True, (0,0,0))
    screen.blit(score_text,(10,10))
    screen.blit(time_text,(10,50))

    # --- Manejo de eventos ---
    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False

    # --- Mostrar resumen al terminar ---
    if time_left==0 and not show_summary:
        show_summary = True

    if show_summary:
        screen.fill((220,220,220))
        final_text = font.render(f"Puntaje final: {score}", True, (0,0,0))
        screen.blit(final_text, (SCREEN_W//2 - final_text.get_width()//2, SCREEN_H//2 - 50))

        btn_nivel2 = pygame.Rect(SCREEN_W//2 - 100, SCREEN_H//2 + 10, 200, 50)
        btn_salir = pygame.Rect(SCREEN_W//2 - 100, SCREEN_H//2 + 80, 200, 50)
        pygame.draw.rect(screen,(0,200,0),btn_nivel2)
        pygame.draw.rect(screen,(200,0,0),btn_salir)
        screen.blit(font.render("Nivel 2", True,(0,0,0)),(btn_nivel2.x+40, btn_nivel2.y+5))
        screen.blit(font.render("Salir", True,(0,0,0)),(btn_salir.x+60, btn_salir.y+5))

        # --- Eventos botones ---
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            if btn_nivel2.collidepoint(mouse_pos):
                level = 2
                score = 0
                start_time = pygame.time.get_ticks()
                reiniciar_nivel()
                show_summary = False
            elif btn_salir.collidepoint(mouse_pos):
                running = False

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
