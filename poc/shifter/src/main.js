import { MenuScene } from './scenes/MenuScene.js';
import { CarSelectScene } from './scenes/CarSelectScene.js';
import { RaceScene } from './scenes/RaceScene.js';
import { ResultScene } from './scenes/ResultScene.js';

// Phaser game configuration
const config = {
    type: Phaser.AUTO,
    width: 1920,
    height: 1080,
    parent: 'game-container',
    backgroundColor: '#1a1a2e',
    scale: {
        mode: Phaser.Scale.FIT,
        autoCenter: Phaser.Scale.CENTER_BOTH
    },
    physics: {
        default: 'arcade',
        arcade: {
            gravity: { y: 0 },
            debug: false
        }
    },
    input: {
        gamepad: true
    },
    scene: [MenuScene, CarSelectScene, RaceScene, ResultScene]
};

// Create the game instance
const game = new Phaser.Game(config);

// Export for global access if needed
window.game = game;
