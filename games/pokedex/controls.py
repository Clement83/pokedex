import pygame
from config import KEY_MAPPINGS, JOYSTICK_MAPPINGS
import debug_actions
import sys, os as _os
_root = _os.path.abspath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..'))
if _root not in sys.path:
    sys.path.insert(0, _root)
import music_player

# --- State for axes and hats ---
_axis_states = {}
_hat_states = {}

# --- Debug combination state ---
_debug_combo_start_time = {}
_debug_combo_active = {}
DEBUG_HOLD_DURATION = 5000  # 5 seconds in milliseconds

ACTION_TO_KEY = {action: keys[0] for action, keys in KEY_MAPPINGS.items() if keys}

def _post_key_event(action, event_type):
    """Creates and posts a fake keyboard event."""
    if action in ACTION_TO_KEY:
        key = ACTION_TO_KEY[action]
        event_dict = {"key": key, "mod": pygame.KMOD_NONE, "unicode": "", "scancode": 0}
        event = pygame.event.Event(event_type, event_dict)
        pygame.event.post(event)

def process_joystick_input(game_state, event):
    """
    Processes joystick events, handles debug combinations, volume changes,
    and posts keyboard-like events for other actions.
    """
    global _axis_states, _hat_states, _debug_combo_start_time, _debug_combo_active

    if event.type == pygame.JOYBUTTONDOWN:
        game_state.pressed_buttons.add(event.button)

        # --- Debug Actions Check (require holding for 5 seconds) ---
        # Check for combinations with button 12 (Select button on Odroid)
        if 12 in game_state.pressed_buttons:
            now = pygame.time.get_ticks()

            if 14 in game_state.pressed_buttons: # Select + PageDown (reset game)
                combo_key = "reset_game"
                if combo_key not in _debug_combo_start_time:
                    _debug_combo_start_time[combo_key] = now
                    _debug_combo_active[combo_key] = False
                return

            if 15 in game_state.pressed_buttons: # Select + PageUp (next milestone)
                combo_key = "next_milestone"
                if combo_key not in _debug_combo_start_time:
                    _debug_combo_start_time[combo_key] = now
                    _debug_combo_active[combo_key] = False
                return

        action = JOYSTICK_MAPPINGS["BUTTONS"].get(event.button)
        if action in ("VOLUME_UP", "VOLUME_DOWN"):
            pass  # géré par music_player.tick() dans la boucle principale
        elif action:
            _post_key_event(action, pygame.KEYDOWN)

    elif event.type == pygame.JOYBUTTONUP:
        if event.button in game_state.pressed_buttons:
            game_state.pressed_buttons.remove(event.button)

        # Reset debug combo timers when buttons are released
        if event.button == 12 or event.button == 13 or event.button == 14 or event.button == 15:
            _debug_combo_start_time.clear()
            _debug_combo_active.clear()

        action = JOYSTICK_MAPPINGS["BUTTONS"].get(event.button)
        if action:
            _post_key_event(action, pygame.KEYUP)

    elif event.type == pygame.JOYAXISMOTION:
        deadzone = JOYSTICK_MAPPINGS["AXIS_DEADZONE"]
        axis_idx = event.axis
        curr_val = event.value
        prev_val = _axis_states.get(axis_idx, 0.0)

        for (ax_idx, direction), action in JOYSTICK_MAPPINGS["AXES"].items():
            if ax_idx == axis_idx:
                if direction == -1 and curr_val < -deadzone and prev_val >= -deadzone:
                    _post_key_event(action, pygame.KEYDOWN)
                elif direction == 1 and curr_val > deadzone and prev_val <= deadzone:
                    _post_key_event(action, pygame.KEYDOWN)

                if direction == -1 and curr_val >= -deadzone and prev_val < -deadzone:
                    _post_key_event(action, pygame.KEYUP)
                elif direction == 1 and curr_val <= deadzone and prev_val > deadzone:
                    _post_key_event(action, pygame.KEYUP)

        _axis_states[axis_idx] = curr_val

    elif event.type == pygame.JOYHATMOTION:
        prev_x, prev_y = _hat_states.get(event.hat, (0, 0))
        curr_x, curr_y = event.value

        if curr_y == 1 and prev_y != 1: _post_key_event("UP", pygame.KEYDOWN)
        if curr_y != 1 and prev_y == 1: _post_key_event("UP", pygame.KEYUP)
        if curr_y == -1 and prev_y != -1: _post_key_event("DOWN", pygame.KEYDOWN)
        if curr_y != -1 and prev_y == -1: _post_key_event("DOWN", pygame.KEYUP)

        if curr_x == 1 and prev_x != 1: _post_key_event("RIGHT", pygame.KEYDOWN)
        if curr_x != 1 and prev_x == 1: _post_key_event("RIGHT", pygame.KEYUP)
        if curr_x == -1 and prev_x != -1: _post_key_event("LEFT", pygame.KEYDOWN)
        if curr_x != -1 and prev_x == -1: _post_key_event("LEFT", pygame.KEYUP)

        _hat_states[event.hat] = event.value

def check_debug_combos(game_state):
    """
    Checks if debug combinations have been held long enough and triggers actions.
    Should be called in the main game loop.
    """
    global _debug_combo_start_time, _debug_combo_active

    if not _debug_combo_start_time:
        return

    now = pygame.time.get_ticks()
    screen = game_state.screen
    font = game_state.font

    for combo_key, start_time in list(_debug_combo_start_time.items()):
        elapsed = now - start_time

        # Draw progress bar
        if elapsed < DEBUG_HOLD_DURATION:
            progress = elapsed / DEBUG_HOLD_DURATION
            bar_width = 200
            bar_height = 20
            bar_x = (screen.get_width() - bar_width) // 2
            bar_y = screen.get_height() - 40

            # Draw background
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            # Draw progress
            pygame.draw.rect(screen, (255, 200, 0), (bar_x, bar_y, int(bar_width * progress), bar_height))
            # Draw border
            pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)

            # Draw text
            combo_names = {
                "reset_game": "Reset Game",
                "next_milestone": "Next Milestone"
            }
            text = font.render(f"Hold for: {combo_names.get(combo_key, 'Debug Action')}", True, (255, 255, 255))
            text_rect = text.get_rect(center=(screen.get_width() // 2, bar_y - 15))
            screen.blit(text, text_rect)

        # Execute action if held long enough
        elif not _debug_combo_active.get(combo_key, False):
            _debug_combo_active[combo_key] = True

            if combo_key == "reset_game":
                debug_actions.reset_game_state(game_state)
            elif combo_key == "next_milestone":
                debug_actions.go_to_next_milestone(game_state)

            # Clear the combo after execution
            _debug_combo_start_time.clear()
            _debug_combo_active.clear()
            break
