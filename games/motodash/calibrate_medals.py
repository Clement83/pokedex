"""Bot deterministe qui parcourt chaque niveau, mesure le temps, et propose des medailles.

Strategie : throttle constant, lean correctif anti-flip selon angle de la moto et pente devant.
Reset au checkpoint sur crash (comme le jeu reel) → temps incluant penalites.

Usage : SDL_VIDEODRIVER=dummy python calibrate_medals.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((480, 320))

import scene_game
import levels


def run_bot(level_id, max_sim_seconds=240.0, dt=1.0 / 60.0):
    sc = scene_game.GameScene(pygame.display.get_surface(), level_id)
    # Skip countdown
    sc.countdown = 0.0
    sc.go_hold = 1.0

    crashes = 0
    sim_t = 0.0
    last_x = sc.bike.x
    stuck_t = 0.0

    while sim_t < max_sim_seconds:
        bike = sc.bike
        angle_deg = math.degrees((bike.angle + math.pi) % (2 * math.pi) - math.pi)
        speed = math.hypot(bike.vx, bike.vy)

        lean = 0
        if angle_deg > 25:
            lean = -1
        elif angle_deg < -25:
            lean = 1

        # Lookahead : maintenir vitesse cible jusqu'a sortie complete du rect d'obstacle
        target_speed = 999.0
        for s in sc.level.get("hazards", []):
            if s.get("kind") != "obstacle":
                continue
            ox, _, ow, _ = s["rect"]
            if bike.x > ox + ow + 20:
                continue
            if bike.x < ox - 300:
                continue
            if bike.x >= ox - 30:
                ts = 60.0  # dans ou tout proche : on reste sous le seuil de crash
            else:
                dist = ox - bike.x
                ts = 50.0 + max(0, dist - 60) * 0.3
            if ts < target_speed:
                target_speed = ts

        if speed > target_speed:
            sc.input_throttle = False
            sc.input_brake = bike.on_ground and speed > target_speed + 5
        else:
            sc.input_throttle = True
            sc.input_brake = False
        sc.input_lean = lean

        was_crashed = bike.crashed
        result = sc.update(dt)
        if bike.crashed and not was_crashed:
            crashes += 1
        sim_t += dt

        if result and result.get("finished"):
            return {"time": result["time"], "crashes": crashes, "finished": True}

        # Detection d'enlisement (si la moto reste plus de 5s sans avancer)
        if abs(bike.x - last_x) < 1.0:
            stuck_t += dt
            if stuck_t > 5.0:
                # Force un reset au checkpoint
                bike.crashed = True
                stuck_t = 0.0
        else:
            stuck_t = 0.0
            last_x = bike.x

    return {"time": sim_t, "crashes": crashes, "finished": False}


def main():
    print(f"{'level':12s} {'biome':8s} {'time':>7s} {'crash':>5s}  proposed (gold/silver/bronze)")
    print("-" * 80)
    proposals = {}
    for l in levels.LEVELS:
        lid = l["id"]
        r = run_bot(lid)
        if not r["finished"]:
            print(f"{lid:12s} {l['biome']:8s}  TIMEOUT t={r['time']:.1f} crashes={r['crashes']}")
            continue
        t = r["time"]
        gold = round(t * 1.15, 1)
        silver = round(t * 1.45, 1)
        bronze = round(t * 1.85, 1)
        proposals[lid] = (gold, silver, bronze)
        print(f"{lid:12s} {l['biome']:8s} {t:7.2f} {r['crashes']:5d}  ({gold}/{silver}/{bronze})")
    print()
    print("Proposed MEDALS dict:")
    print("MEDALS = {")
    for lid, (g, s, b) in proposals.items():
        print(f'    "{lid}":   ({g}, {s}, {b}),')
    print("}")


if __name__ == "__main__":
    main()
