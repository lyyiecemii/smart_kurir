import pygame
import sys
import random
from PIL import Image
import numpy as np

# Inisialisasi Pygame
pygame.init()

# Ukuran asli peta
WIDTH, HEIGHT = 1120, 1120
SCALE = 0.7  # Skala tampilan
SCALED_WIDTH, SCALED_HEIGHT = int(WIDTH * SCALE), int(HEIGHT * SCALE)

SCREEN = pygame.display.set_mode((SCALED_WIDTH, SCALED_HEIGHT))
pygame.display.set_caption("Smart Courier")

# Warna
WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Variabel global
map_img = None
kurir_pos = [100, 100]
kurir_angle = 0
source_pos = [200, 200]
dest_pos = [800, 600]
kurir_speed = 3

# Fungsi bantu

def scale_pos(pos):
    return [int(pos[0] * SCALE), int(pos[1] * SCALE)]

def load_map(file_path):
    global map_img
    pil_img = Image.open(file_path)
    map_img = pygame.image.fromstring(pil_img.tobytes(), pil_img.size, pil_img.mode)
    return map_img

def is_road(color):
    return all(90 <= c <= 150 for c in color[:3])

def get_pixel_color(pos):
    x, y = pos
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        return map_img.get_at((int(x), int(y)))[:3]
    return (0, 0, 0)

def random_road_position():
    while True:
        x = random.randint(0, WIDTH - 1)
        y = random.randint(0, HEIGHT - 1)
        if is_road(get_pixel_color((x, y))):
            return [x, y]

def randomize_positions():
    global kurir_pos, source_pos, dest_pos
    kurir_pos = random_road_position()
    source_pos = random_road_position()
    dest_pos = random_road_position()

def draw_kurir(surface, pos, angle):
    x, y = scale_pos(pos)
    points = [
        (x + 15 * np.cos(np.radians(angle)), y - 15 * np.sin(np.radians(angle))),
        (x + 10 * np.cos(np.radians(angle + 120)), y - 10 * np.sin(np.radians(angle + 120))),
        (x + 10 * np.cos(np.radians(angle - 120)), y - 10 * np.sin(np.radians(angle - 120)))
    ]
    pygame.draw.polygon(surface, BLACK, points)

def main():
    global kurir_pos, kurir_angle

    try:
        load_map("assets/map.png")
    except:
        print("Gagal memuat peta.")
        sys.exit()

    font = pygame.font.SysFont(None, 30)
    btn_reset = pygame.Rect(20, 20, 160, 40)
    randomize_positions()

    clock = pygame.time.Clock()
    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_reset.collidepoint(event.pos):
                    randomize_positions()

        keys = pygame.key.get_pressed()
        move_x, move_y = 0, 0

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move_y = -kurir_speed
            kurir_angle = 90
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move_y = kurir_speed
            kurir_angle = 270
        elif keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move_x = -kurir_speed
            kurir_angle = 180
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move_x = kurir_speed
            kurir_angle = 0

        next_pos = [kurir_pos[0] + move_x, kurir_pos[1] + move_y]
        if is_road(get_pixel_color(next_pos)):
            kurir_pos = next_pos

        SCREEN.fill(WHITE)
        scaled_map = pygame.transform.scale(map_img, (SCALED_WIDTH, SCALED_HEIGHT))
        SCREEN.blit(scaled_map, (0, 0))

        pygame.draw.circle(SCREEN, YELLOW, scale_pos(source_pos), 12)
        pygame.draw.circle(SCREEN, RED, scale_pos(dest_pos), 12)
        draw_kurir(SCREEN, kurir_pos, kurir_angle)

        pygame.draw.rect(SCREEN, GRAY, btn_reset)
        text = font.render("Reset Posisi", True, BLACK)
        SCREEN.blit(text, (btn_reset.x + 10, btn_reset.y + 8))

        if np.linalg.norm(np.array(kurir_pos) - np.array(dest_pos)) < 15:
            msg = font.render("Kurir sampai tujuan!", True, RED)
            SCREEN.blit(msg, (400, 20))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
