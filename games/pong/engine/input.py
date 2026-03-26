"""Gestion des entrees clavier / manette."""
from config import CTRL, AXIS_DEAD


def is_held(action, keys, joystick=None, btn_held=None):
    """True si l'action est active (touche ou bouton maintenu)."""
    spec = CTRL.get(action, {})

    for k in spec.get('keys', []):
        if keys[k]:
            return True

    if btn_held is not None:
        btn = spec.get('btn')
        if btn is not None and btn in btn_held:
            return True

    if joystick:
        hat_spec = spec.get('hat')
        if hat_spec:
            try:
                if joystick.get_hat(0) == hat_spec:
                    return True
            except Exception:
                pass
        ax_spec = spec.get('axis')
        if ax_spec:
            ax_id, direction = ax_spec
            try:
                v = joystick.get_axis(ax_id)
                if direction == -1 and v < -AXIS_DEAD:
                    return True
                if direction == 1 and v > AXIS_DEAD:
                    return True
            except Exception:
                pass

    return False
