import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT

def play_spiral_cubes_transition(screen, clock, background_surface):
    """
    Reveals a background surface by making black cubes disappear in a spiral.
    """
    cube_size = 40  # Increased cube size for a chunkier effect
    cols = (SCREEN_WIDTH + cube_size - 1) // cube_size
    rows = (SCREEN_HEIGHT + cube_size - 1) // cube_size

    # Generate a spiral path for cube removal
    def generate_inward_spiral(width, height):
        path = []
        left, right, top, bottom = 0, width - 1, 0, height - 1
        while left <= right and top <= bottom:
            for i in range(left, right + 1): path.append((i, top))
            top += 1
            for i in range(top, bottom + 1): path.append((right, i))
            right -= 1
            if top <= bottom:
                for i in range(right, left - 1, -1): path.append((i, bottom))
                bottom -= 1
            if left <= right:
                for i in range(bottom, top - 1, -1): path.append((left, i))
                left += 1
        return path

    spiral_path = generate_inward_spiral(cols, rows)
    spiral_path.reverse() # Reverse to go from center to exterior

    cubes = set((c, r) for c in range(cols) for r in range(rows))
    cubes_to_remove_per_frame = 2  # Slowed down from 3 to 2

    # Draw and hold the initial state (fully covered) for a moment
    screen.blit(background_surface, (0, 0))
    for (c, r) in cubes:
        pygame.draw.rect(screen, (0, 0, 0), (c * cube_size, r * cube_size, cube_size, cube_size))
    pygame.display.flip()
    pygame.time.delay(100) # Hold the initial frame

    while spiral_path:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        for _ in range(cubes_to_remove_per_frame):
            if spiral_path:
                cube_to_remove = spiral_path.pop(0)
                if cube_to_remove in cubes:
                    cubes.remove(cube_to_remove)

        screen.blit(background_surface, (0, 0))
        for (c, r) in cubes:
            pygame.draw.rect(screen, (0, 0, 0), (c * cube_size, r * cube_size, cube_size, cube_size))

        pygame.display.flip()
        clock.tick(60)

    screen.blit(background_surface, (0, 0))
    pygame.display.flip()
    pygame.time.delay(50)
