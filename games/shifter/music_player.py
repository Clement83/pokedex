"""
Pont vers le music_player centralisé (racine du projet).
=========================================================
En conditions normales, ce fichier n'est jamais importé : main.py insère
la racine du projet en tête de sys.path *avant* tout import, donc c'est
``/music_player.py`` qui est trouvé en premier par Python.

Ce fichier sert uniquement de fallback si le module est importé directement
sans passer par main.py (ex. tests isolés). Il se substitue lui-même dans
sys.modules par la version centralisée pour garantir un singleton partagé.
"""
from __future__ import annotations
import sys as _sys
import os as _os
import importlib.util as _ilu

_root_file = _os.path.normpath(
    _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'music_player.py')
)
_spec = _ilu.spec_from_file_location('music_player', _root_file)
_mod  = _ilu.module_from_spec(_spec)
# Enregistrer le module centralisé AVANT exec pour éviter toute récursion
_sys.modules['music_player'] = _mod
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]
