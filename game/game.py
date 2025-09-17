import pygame, random, time
from tobii_research import find_all_eyetrackers

pygame.init()
screen=pygame.display.set_mode((800,600))
font=pygame.font.SysFont(None,36)
clock=pygame.time.Clock()

eyetracker=find_all_eyetrackers()[0]

score=0
fix_start=None
target=None

running=True
while running:
    screen.fill((200,255,200))
    # Nuevo bicho si no hay
    if target is None:
        x,y=random.randint(50,750),random.randint(50,550)
        target=(x,y)

    x,y=target
    pygame.draw.circle(screen,(0,150,0),(x,y),25)  # bicho

    # Gaze
    gaze_data=eyetracker.get_gaze_data()
    gx,gy=gaze_data['left_gaze_point_on_display_area']
    gx*=800; gy*=600
    pygame.draw.circle(screen,(255,0,0),(int(gx),int(gy)),5)

    # dwell
    if abs(gx-x)<25 and abs(gy-y)<25:
        if fix_start is None:
            fix_start=time.time()
        elif time.time()-fix_start>0.5:
            score+=1
            target=None
            fix_start=None
    else:
        fix_start=None

    score_text=font.render(f"Score: {score}",True,(0,0,0))
    screen.blit(score_text,(10,10))

    for e in pygame.event.get():
        if e.type==pygame.QUIT: running=False

    pygame.display.flip()
    clock.tick(60)
pygame.quit()
