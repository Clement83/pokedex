import pygame
from config import KEY_MAPPINGS, JOYSTICK_MAPPINGS

# --- State for axes and hats ---
# To keep track of the last state and generate press/release events
_axis_states = {}
_hat_states = {}

# --- Mapping from action string to a keyboard key ---
# Used to create fake keyboard events from joystick input. We take the first key mapped to the action.
ACTION_TO_KEY = {action: keys[0] for action, keys in KEY_MAPPINGS.items() if keys}

def _post_key_event(action, event_type):
    """Creates and posts a fake keyboard event."""
    if action in ACTION_TO_KEY:
        key = ACTION_TO_KEY[action]
        # Use a dictionary for keyword arguments for clarity and compatibility
        event_dict = {
            "key": key,
            "mod": pygame.KMOD_NONE,
            "unicode": "",
            "scancode": 0 # scancode is not essential for this logic
        }
        event = pygame.event.Event(event_type, event_dict)
        pygame.event.post(event)

def process_joystick_input(game_state, event):
    """
    Processes a single joystick event, handles volume changes directly,
    and posts keyboard-like events for other actions.
    """
    global _axis_states, _hat_states

    if event.type == pygame.JOYBUTTONDOWN:
        action = JOYSTICK_MAPPINGS["BUTTONS"].get(event.button)
        if action == "VOLUME_UP":
            game_state.music_volume = min(1.0, game_state.music_volume + 0.1)
            pygame.mixer.music.set_volume(game_state.music_volume)
        elif action == "VOLUME_DOWN":
            game_state.music_volume = max(0.0, game_state.music_volume - 0.1)
            pygame.mixer.music.set_volume(game_state.music_volume)
        elif action:
            _post_key_event(action, pygame.KEYDOWN)
    
    elif event.type == pygame.JOYBUTTONUP:
        action = JOYSTICK_MAPPINGS["BUTTONS"].get(event.button)
        if action:
            _post_key_event(action, pygame.KEYUP)

    elif event.type == pygame.JOYAXISMOTION:
        deadzone = JOYSTICK_MAPPINGS["AXIS_DEADZONE"]
        axis_idx = event.axis
        curr_val = event.value
        prev_val = _axis_states.get(axis_idx, 0.0)

        # Find all actions associated with this axis
        for (ax_idx, direction), action in JOYSTICK_MAPPINGS["AXES"].items():
            if ax_idx == axis_idx:
                # Check for press
                if direction == -1 and curr_val < -deadzone and prev_val >= -deadzone:
                    _post_key_event(action, pygame.KEYDOWN)
                elif direction == 1 and curr_val > deadzone and prev_val <= deadzone:
                    _post_key_event(action, pygame.KEYDOWN)
                
                # Check for release
                if direction == -1 and curr_val >= -deadzone and prev_val < -deadzone:
                    _post_key_event(action, pygame.KEYUP)
                elif direction == 1 and curr_val <= deadzone and prev_val > deadzone:
                    _post_key_event(action, pygame.KEYUP)
        
        _axis_states[axis_idx] = curr_val

    elif event.type == pygame.JOYHATMOTION:
        prev_x, prev_y = _hat_states.get(event.hat, (0, 0))
        curr_x, curr_y = event.value

        # Y-axis (Up/Down)
        if curr_y == 1 and prev_y != 1: _post_key_event("UP", pygame.KEYDOWN)
        if curr_y != 1 and prev_y == 1: _post_key_event("UP", pygame.KEYUP)
        if curr_y == -1 and prev_y != -1: _post_key_event("DOWN", pygame.KEYDOWN)
        if curr_y != -1 and prev_y == -1: _post_key_event("DOWN", pygame.KEYUP)

        # X-axis (Left/Right)
        if curr_x == 1 and prev_x != 1: _post_key_event("RIGHT", pygame.KEYDOWN)
        if curr_x != 1 and prev_x == 1: _post_key_event("RIGHT", pygame.KEYUP)
        if curr_x == -1 and prev_x != -1: _post_key_event("LEFT", pygame.KEYDOWN)
        if curr_x != -1 and prev_x == -1: _post_key_event("LEFT", pygame.KEYUP)

        _hat_states[event.hat] = event.value