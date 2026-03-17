import { INPUT_MAPPING } from '../config.js';

export class InputManager {
    constructor(scene) {
        this.scene = scene;
        this.keys = {};
        this.keyStates = {};  // Current frame key states
        this.lastFrameKeyStates = {};  // Previous frame key states (for copying)
        this.previousKeyStates = {};  // States used for JustDown detection
        this.gamepads = [];

        // Setup keyboard inputs for up to 6 players
        this.setupKeyboard();
    }

    setupKeyboard() {
        // Initialize key states for all players
        INPUT_MAPPING.keyboard.forEach((mapping, index) => {
            this.keyStates[`p${index}_up`] = false;
            this.keyStates[`p${index}_down`] = false;
            this.lastFrameKeyStates[`p${index}_up`] = false;
            this.lastFrameKeyStates[`p${index}_down`] = false;
            this.previousKeyStates[`p${index}_up`] = false;
            this.previousKeyStates[`p${index}_down`] = false;
        });

        // Listen to keyboard events for all keys (including special characters)
        this.scene.input.keyboard.on('keydown', (event) => {
            this.handleKeyEvent(event, true);
        });

        this.scene.input.keyboard.on('keyup', (event) => {
            this.handleKeyEvent(event, false);
        });
    }

    handleKeyEvent(event, isDown) {
        INPUT_MAPPING.keyboard.forEach((mapping, index) => {
            // Check if this key matches any player's controls
            if (event.key.toUpperCase() === mapping.up.toUpperCase() ||
                event.key === mapping.up) {
                this.keyStates[`p${index}_up`] = isDown;
            }
            if (event.key.toUpperCase() === mapping.down.toUpperCase() ||
                event.key === mapping.down) {
                this.keyStates[`p${index}_down`] = isDown;
            }
        });
    }

    /**
     * Check if shift up was just pressed for a player
     */
    isShiftUpJustPressed(playerIndex) {
        const key = `p${playerIndex}_up`;
        const justPressed = this.keyStates[key] && !this.previousKeyStates[key];
        return justPressed;
    }

    /**
     * Check if shift down was just pressed for a player
     */
    isShiftDownJustPressed(playerIndex) {
        const key = `p${playerIndex}_down`;
        const justPressed = this.keyStates[key] && !this.previousKeyStates[key];
        return justPressed;
    }

    /**
     * Update key states for JustDown detection
     * Must be called BEFORE checking JustPressed in the game loop
     */
    update() {
        // First, copy last frame's states to previous (for JustDown detection)
        INPUT_MAPPING.keyboard.forEach((mapping, index) => {
            this.previousKeyStates[`p${index}_up`] = this.lastFrameKeyStates[`p${index}_up`];
            this.previousKeyStates[`p${index}_down`] = this.lastFrameKeyStates[`p${index}_down`];
        });

        // Then, save current states for next frame
        INPUT_MAPPING.keyboard.forEach((mapping, index) => {
            this.lastFrameKeyStates[`p${index}_up`] = this.keyStates[`p${index}_up`];
            this.lastFrameKeyStates[`p${index}_down`] = this.keyStates[`p${index}_down`];
        });

        // Gamepad support can be added later
        this.gamepads = this.scene.input.gamepad.gamepads;
    }
}
