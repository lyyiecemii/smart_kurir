import pygame
import sys
import random
from PIL import Image
import numpy as np

# Inisialisasi Pygame
pygame.init()

# Konstanta
WIDTH, HEIGHT = 1200, 800  # Sesuaikan dengan ukuran peta
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Smart Courier")

# Warna
WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# Variabel global
map_img = None
kurir_pos = [100, 100]  # Posisi awal kurir
kurir_angle = 0  # Sudut hadap kurir (0 = kanan, 90 = atas)
source_pos = [200, 200]  # Posisi bendera kuning
dest_pos = [800, 600]    # Posisi bendera merah

def load_map(file_path):
    """Memuat gambar peta dan konversi ke format Pygame"""
    global map_img
    pil_img = Image.open(file_path)
    map_img = pygame.image.fromstring(pil_img.tobytes(), pil_img.size, pil_img.mode)
    return map_img

def is_road(color):
    """Cek apakah pixel termasuk jalan (warna abu-abu 90-150)"""
    return all(90 <= c <= 150 for c in color[:3])

def randomize_positions():
    """Mengacak posisi kurir, sumber, dan tujuan di area jalan"""
    global kurir_pos, source_pos, dest_pos
    # Implementasi acak posisi di area jalan (contoh sederhana)
    kurir_pos = [random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100)]
    source_pos = [random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100)]
    dest_pos = [random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100)]

def draw_kurir(surface, pos, angle):
    """Menggambar kurir (segitiga) dengan rotasi sesuai arah"""
    points = [
        (pos[0] + 20 * np.cos(np.radians(angle)), pos[1] - 20 * np.sin(np.radians(angle))),
        (pos[0] + 10 * np.cos(np.radians(angle + 120)), pos[1] - 10 * np.sin(np.radians(angle + 120))),
        (pos[0] + 10 * np.cos(np.radians(angle - 120)), pos[1] - 10 * np.sin(np.radians(angle - 120)))
    ]
    pygame.draw.polygon(surface, BLACK, points)

def main():
    global map_img, kurir_pos, kurir_angle

    # Load peta default
    try:
        map_img = load_map("assets/map.png")
    except:
        # Jika peta tidak ada, buat peta sederhana
        map_img = pygame.Surface((WIDTH, HEIGHT))
        map_img.fill(WHITE)
        pygame.draw.rect(map_img, GRAY, (100, 100, WIDTH - 200, HEIGHT - 200))

    # Tombol
    font = pygame.font.SysFont(None, 36)
    btn_random = pygame.Rect(50, 50, 200, 50)
    btn_load = pygame.Rect(50, 120, 200, 50)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_random.collidepoint(event.pos):
                    randomize_positions()
                elif btn_load.collidepoint(event.pos):
                    # Implementasi file dialog untuk memilih peta
                    pass

        # Render
        SCREEN.blit(map_img, (0, 0))
        
        # Gambar bendera
        pygame.draw.circle(SCREEN, YELLOW, source_pos, 15)
        pygame.draw.circle(SCREEN, RED, dest_pos, 15)
        
        # Gambar kurir
        draw_kurir(SCREEN, kurir_pos, kurir_angle)
        
        # Gambar tombol
        pygame.draw.rect(SCREEN, GRAY, btn_random)
        pygame.draw.rect(SCREEN, GRAY, btn_load)
        text_random = font.render("Acak Posisi", True, BLACK)
        text_load = font.render("Load Peta", True, BLACK)
        SCREEN.blit(text_random, (btn_random.x + 20, btn_random.y + 10))
        SCREEN.blit(text_load, (btn_load.x + 20, btn_load.y + 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()