import pygame, random, time, queue, socket, threading, math
from utils.animacion import generar_frames
from utils.tamano import normalizar_imagen

# --- Configuración ---
SCREEN_W, SCREEN_H = 1920, 1080
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
GAME_TIME = 30
DWELL_TIME = 500  # ms de fijación
MIN_DIST = 120    # distancia mínima entre moscas (px)
NUM_MOSCAS_NIVEL2 = 3
FPS = 120

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
pygame.mouse.set_visible(False)  # ocultar mouse

# --- Cargar sprites ---
mosca_frames = {
    'fly1': generar_frames('assets/fly1.png', num_frames=12),
    'fly2': generar_frames('assets/fly2.png', num_frames=12),
    'fly3': generar_frames('assets/fly3.png', num_frames=12),
}
pistola_img = normalizar_imagen(pygame.image.load('assets/pistola.png').convert_alpha(), 50, 50)
boom_sound = pygame.mixer.Sound('assets/boom.wav')

# --- Variables del juego ---
gx, gy = SCREEN_W//2, SCREEN_H//2
scores = {1: 0, 2: 0}   # puntajes por nivel
level = 1
start_time = pygame.time.get_ticks()   # tiempo de inicio del nivel actual
targets = []
# dwell trackers separados
hover_target = None
hover_start = None
hover_btn = None
btn_start = None

show_summary = False
running = True

# --- Funciones auxiliares ---
def crear_moscas(n=1, min_dist=MIN_DIST):
    """Crea n moscas asegurando separación mínima entre ellas (considera solo las nuevas entre sí)."""
    new_targets = []
    tries = 0
    while len(new_targets) < n and tries < 1000:
        tries += 1
        type_fly = random.choice(['fly1', 'fly2', 'fly3'])
        x, y = random.randint(100, SCREEN_W-100), random.randint(100, SCREEN_H-100)
        if all(((x - t['x'])**2 + (y - t['y'])**2)**0.5 > min_dist for t in new_targets):
            new_targets.append({'type': type_fly, 'x': x, 'y': y, 'frame_idx':0})
    return new_targets

def generar_una_mosca_valida(existing_targets, min_dist=MIN_DIST):
    """Genera una mosca que no se solape con existing_targets (intenta varias veces)."""
    tries = 0
    while tries < 500:
        tries += 1
        type_fly = random.choice(['fly1', 'fly2', 'fly3'])
        x, y = random.randint(100, SCREEN_W-100), random.randint(100, SCREEN_H-100)
        if all(((x - t['x'])**2 + (y - t['y'])**2)**0.5 > min_dist for t in existing_targets):
            return {'type': type_fly, 'x': x, 'y': y, 'frame_idx':0}
    return {'type': type_fly, 'x': random.randint(100, SCREEN_W-100), 'y': random.randint(100, SCREEN_H-100), 'frame_idx':0}

def reiniciar_nivel(reset_timer=False):
    """
    Inicializa targets según nivel:
      - level == 1 -> 1 mosca
      - level == 2 -> NUM_MOSCAS_NIVEL2 moscas
    Si reset_timer==True reinicia 'start_time' (usar solo al entrar a un nivel desde resumen/menú).
    """
    global targets, hover_start, hover_target, start_time
    hover_start = None
    hover_target = None
    if level == 1:
        targets = crear_moscas(1)
    else:
        targets = crear_moscas(NUM_MOSCAS_NIVEL2)
    if reset_timer:
        start_time = pygame.time.get_ticks()

def gaze_button(btn_rect, name):
    """Detecta selección por mirada con dwell para botones."""
    global hover_btn, btn_start, gx, gy
    if btn_rect.collidepoint((gx, gy)):
        if hover_btn != name:
            hover_btn = name
            btn_start = pygame.time.get_ticks()
        elif pygame.time.get_ticks() - btn_start >= DWELL_TIME:
            hover_btn = None
            btn_start = None
            return True
    else:
        if hover_btn == name:
            hover_btn = None
            btn_start = None
    return False

# --- Inicia primer nivel (reinicia tiempo aquí al arrancar) ---
reiniciar_nivel(reset_timer=True)

# --- Loop principal ---
while running:
    # fondo verde
    screen.fill((200,255,200))
    elapsed = (pygame.time.get_ticks() - start_time)/1000
    time_left = max(0, GAME_TIME - int(elapsed))

    # --- Actualiza gaze desde cola UDP ---
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

    # --- Dibuja pistola (centro de mirada) ---
    screen.blit(pistola_img, (gx - pistola_img.get_width()//2, gy - pistola_img.get_height()//2))

    # --- Chequea si "mata" mosca (dwell sobre mosca) ---
    current_hover = None
    for t in targets:
        if abs(gx - t['x']) < 25 and abs(gy - t['y']) < 25:
            current_hover = t
            break

    if current_hover:
        if hover_target != current_hover:
            hover_target = current_hover
            hover_start = pygame.time.get_ticks()
        elif pygame.time.get_ticks() - hover_start >= DWELL_TIME:
            boom_sound.play()
            if current_hover['type']=='fly1': scores[level] += 3
            elif current_hover['type']=='fly2': scores[level] += 2
            else: scores[level] += 1

            if level == 1:
                # NO reiniciamos el tiempo al matar una mosca en nivel 1:
                reiniciar_nivel(reset_timer=False)
            else:
                # nivel 2: eliminar solo la mosca y reemplazar por otra manteniendo NUM_MOSCAS_NIVEL2
                try:
                    targets.remove(current_hover)
                except ValueError:
                    pass
                new_m = generar_una_mosca_valida(targets, MIN_DIST)
                targets.append(new_m)

            hover_target = None
            hover_start = None
    else:
        hover_target = None
        hover_start = None

    # --- Mostrar puntaje y tiempo ---
    score_text = font.render(f"Puntaje (nivel {level}): {scores[level]}", True, (0,0,0))
    time_text = font.render(f"Tiempo restante: {time_left}", True, (0,0,0))
    screen.blit(score_text,(10,10))
    screen.blit(time_text,(10,50))

    # --- Manejo de eventos ---
    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False

    # --- Mostrar resumen ---
    if time_left==0 and not show_summary:
        show_summary = True

    if show_summary:
        screen.fill((220,220,220))

        if level == 1:
            txt1 = font.render(f"Puntaje nivel 1: {scores[1]}", True, (0,0,0))
            screen.blit(txt1, (SCREEN_W//2 - txt1.get_width()//2, SCREEN_H//2 - 120))

            btn_nivel2 = pygame.Rect(SCREEN_W//2 - 100, SCREEN_H//2 + 10, 200, 50)
            btn_salir = pygame.Rect(SCREEN_W//2 - 100, SCREEN_H//2 + 80, 200, 50)
            pygame.draw.rect(screen,(0,200,0),btn_nivel2)
            pygame.draw.rect(screen,(200,0,0),btn_salir)
            screen.blit(font.render("Nivel 2", True,(0,0,0)),(btn_nivel2.x+40, btn_nivel2.y+5))
            screen.blit(font.render("Salir", True,(0,0,0)),(btn_salir.x+60, btn_salir.y+5))

            if gaze_button(btn_nivel2,"nivel2"):
                level = 2
                reiniciar_nivel(reset_timer=True)   # <-- reinicia tiempo SOLO al pasar a nivel 2 desde resumen
                show_summary = False
            if gaze_button(btn_salir,"salir"):
                running = False

        else:
            total = scores[1] + scores[2]
            txt1 = font.render(f"Nivel 1: {scores[1]}", True, (0,0,0))
            txt2 = font.render(f"Nivel 2: {scores[2]}", True, (0,0,0))
            txt3 = font.render(f"TOTAL: {total}", True, (0,0,0))
            screen.blit(txt1, (SCREEN_W//2 - txt1.get_width()//2, SCREEN_H//2 - 120))
            screen.blit(txt2, (SCREEN_W//2 - txt2.get_width()//2, SCREEN_H//2 - 70))
            screen.blit(txt3, (SCREEN_W//2 - txt3.get_width()//2, SCREEN_H//2 - 20))

            btn_salir = pygame.Rect(SCREEN_W//2 - 100, SCREEN_H//2 + 60, 200, 50)
            pygame.draw.rect(screen,(200,0,0),btn_salir)
            screen.blit(font.render("Salir", True,(0,0,0)),(btn_salir.x+60, btn_salir.y+5))
            if gaze_button(btn_salir,"salir"):
                running = False

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
