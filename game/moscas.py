import pygame
import random
import time
import queue
import socket
import threading

# --- Configuración ---
SCREEN_W, SCREEN_H = 1920, 1080
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
LEVEL_TIME = 60  # segundos por nivel

# Cola para recibir datos del servidor
gaze_queue = queue.Queue()

# --- Función para recibir UDP ---
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

threading.Thread(target=udp_receiver, args=(gaze_queue,), daemon=True).start()

# --- Inicializa Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
pygame.display.set_caption("Mata Moscas con Mirada")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 36)

# --- Carga imágenes y sonidos ---
# Animaciones de moscas: fly1_1.png, fly1_2.png, fly2_1.png...
mosca_imgs = {
    "fly1": [pygame.image.load(f"assets/fly1_1.png").convert_alpha(),
             pygame.image.load(f"assets/fly1_2.png").convert_alpha()],
    "fly2": [pygame.image.load(f"assets/fly2_1.png").convert_alpha(),
             pygame.image.load(f"assets/fly2_2.png").convert_alpha()],
    "fly3": [pygame.image.load(f"assets/fly3_1.png").convert_alpha(),
             pygame.image.load(f"assets/fly3_2.png").convert_alpha()]
}

pistola_img = pygame.image.load("assets/pistola.png").convert_alpha()

# Escala imágenes a tamaño visual consistente (aprox. 1 grado visual)
MOSCA_SIZE = 80
for k in mosca_imgs:
    mosca_imgs[k] = [pygame.transform.smoothscale(img, (MOSCA_SIZE, MOSCA_SIZE)) for img in mosca_imgs[k]]
PISTOLA_SIZE = 50
pistola_img = pygame.transform.smoothscale(pistola_img, (PISTOLA_SIZE, PISTOLA_SIZE))

# Sonido click
pygame.mixer.init()
click_sound = pygame.mixer.Sound("assets/click.wav")  # se recomienda wav para pygame

# --- Clase Mosca ---
class Mosca:
    def __init__(self, tipo):
        self.tipo = tipo
        self.images = mosca_imgs[tipo]
        self.frame = 0
        self.pos = (random.randint(100, SCREEN_W-100), random.randint(100, SCREEN_H-100))
        self.score_value = {"fly1":3, "fly2":2, "fly3":1}[tipo]

    def draw(self, surf):
        surf.blit(self.images[self.frame], self.pos)

    def animate(self):
        self.frame = (self.frame +1) % len(self.images)

    def reset_pos(self):
        self.pos = (random.randint(100, SCREEN_W-100), random.randint(100, SCREEN_H-100))

# --- Función de nivel ---
def run_level(level=1):
    moscas = []
    if level == 1:
        moscas.append(Mosca("fly1"))
    else:
        moscas = [Mosca(random.choice(["fly1","fly2","fly3"])) for _ in range(5)]

    gx, gy = SCREEN_W//2, SCREEN_H//2
    fix_start = None
    score = 0
    start_time = time.time()
    running = True

    while running:
        screen.fill((200,255,200))

        # Actualiza moscas
        for m in moscas:
            m.animate()
            m.draw(screen)

        # --- Leer coordenadas de gaze ---
        try:
            while True:
                ts, gx, gy = gaze_queue.get_nowait()
        except queue.Empty:
            pass

        # Dibuja pistola en mirada
        screen.blit(pistola_img, (gx-PISTOLA_SIZE//2, gy-PISTOLA_SIZE//2))

        # --- Chequea colisiones ---
        for m in moscas:
            mx, my = m.pos
            if abs(gx-mx)<MOSCA_SIZE//2 and abs(gy-my)<MOSCA_SIZE//2:
                if fix_start is None:
                    fix_start = time.time()
                elif time.time()-fix_start>0.3:
                    score += m.score_value
                    click_sound.play()
                    if level == 1:
                        m.reset_pos()
                    else:
                        # Nivel 2: reposiciona todas
                        for m2 in moscas:
                            m2.reset_pos()
                    fix_start = None
                    break
            else:
                fix_start = None

        # Timer
        elapsed = time.time() - start_time
        remaining = max(0, int(LEVEL_TIME - elapsed))
        timer_text = font.render(f"Tiempo: {remaining}", True, (0,0,0))
        screen.blit(timer_text, (10,10))

        # Score
        score_text = font.render(f"Puntaje: {score}", True, (0,0,0))
        screen.blit(score_text, (SCREEN_W-250,10))

        # Manejo eventos
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"

        pygame.display.flip()
        clock.tick(60)

        if elapsed>=LEVEL_TIME:
            running = False

    # --- Pantalla final ---
    while True:
        screen.fill((180,180,250))
        final_text = font.render(f"Puntaje final: {score}", True, (0,0,0))
        screen.blit(final_text, (SCREEN_W//2 - final_text.get_width()//2, SCREEN_H//2 -100))

        # Botones
        btn_nivel2 = pygame.Rect(SCREEN_W//2-100, SCREEN_H//2, 200,50)
        btn_salir = pygame.Rect(SCREEN_W//2-100, SCREEN_H//2 +70,200,50)
        pygame.draw.rect(screen,(0,200,0),btn_nivel2)
        pygame.draw.rect(screen,(200,0,0),btn_salir)
        screen.blit(font.render("Nivel 2",True,(0,0,0)), (btn_nivel2.x+50,btn_nivel2.y+10))
        screen.blit(font.render("Salir",True,(0,0,0)), (btn_salir.x+70,btn_salir.y+10))

        mx,my = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()[0]
        if click:
            if btn_nivel2.collidepoint(mx,my):
                return "nivel2"
            elif btn_salir.collidepoint(mx,my):
                return "quit"

        pygame.display.flip()
        clock.tick(60)

# --- Main ---
current_level = 1
while True:
    result = run_level(current_level)
    if result == "nivel2":
        current_level = 2
    else:
        break

pygame.quit()
