import { Player } from '../entities/Player.js';
import { INPUT_MAPPING } from '../config.js';

export class CarSelectScene extends Phaser.Scene {
    constructor() {
        super({ key: 'CarSelectScene' });
    }

    init(data) {
        this.playerCount = data.playerCount || 2;
        this.players = [];
        this.selectedCars = new Array(this.playerCount).fill(null);
        this.ready = new Array(this.playerCount).fill(false);
        this.carData = null;
    }

    preload() {
        // Load car data
        this.load.json('cars', 'asset/data/cars.json');

        // Load sprite sheets - chaque sheet contient 6 véhicules
        // Disposition: 2 colonnes x 3 lignes (1536x1024px total)
        this.load.spritesheet('vehicle1_sheet', 'asset/sprite/vehicle1.png', {
            frameWidth: 768,   // 1536 / 2 colonnes
            frameHeight: 341   // 1024 / 3 lignes
        });

        this.load.spritesheet('vehicle2_sheet', 'asset/sprite/vehicle2.png', {
            frameWidth: 768,
            frameHeight: 341
        });
    }

    create() {
        const { width, height } = this.cameras.main;
        this.carData = this.cache.json.get('cars').cars;

        // Créer les textures individuelles à partir des sprite sheets
        this.createVehicleTextures();

        // Background with gradient
        const bg = this.add.graphics();
        bg.fillGradientStyle(0x0a0a14, 0x0a0a14, 0x16213e, 0x16213e, 1, 1, 1, 1);
        bg.fillRect(0, 0, width, height);

        // Title with glow effect
        const title = this.add.text(width / 2, 60, '🏁 SÉLECTION DES VÉHICULES 🏁', {
            fontSize: '52px',
            fontFamily: 'Arial Black',
            color: '#FFE66D',
            stroke: '#000000',
            strokeThickness: 8
        }).setOrigin(0.5);

        // Title glow
        this.add.text(width / 2, 60, '🏁 SÉLECTION DES VÉHICULES 🏁', {
            fontSize: '52px',
            fontFamily: 'Arial Black',
            color: '#FFE66D',
            alpha: 0.3
        }).setOrigin(0.5).setScale(1.05);

        // Create zones for each player
        this.createPlayerZones();

        // Setup input
        this.setupInput();

        // Instructions
        this.updateInstructions();
    }

    createVehicleTextures() {
        // Créer des textures individuelles pour chaque véhicule des sprite sheets
        // vehicle1_sheet: frames 0-5 (6 véhicules)
        // vehicle2_sheet: frames 0-5 (6 véhicules)
        const vehicleMapping = [
            { sheet: 'vehicle1_sheet', frame: 0, name: 'vehicle1_0' },
            { sheet: 'vehicle1_sheet', frame: 1, name: 'vehicle1_1' },
            { sheet: 'vehicle1_sheet', frame: 2, name: 'vehicle1_2' },
            { sheet: 'vehicle1_sheet', frame: 3, name: 'vehicle1_3' },
            { sheet: 'vehicle1_sheet', frame: 4, name: 'vehicle1_4' },
            { sheet: 'vehicle1_sheet', frame: 5, name: 'vehicle1_5' },
            { sheet: 'vehicle2_sheet', frame: 0, name: 'vehicle2_0' },
            { sheet: 'vehicle2_sheet', frame: 1, name: 'vehicle2_1' },
            { sheet: 'vehicle2_sheet', frame: 2, name: 'vehicle2_2' },
            { sheet: 'vehicle2_sheet', frame: 3, name: 'vehicle2_3' },
            { sheet: 'vehicle2_sheet', frame: 4, name: 'vehicle2_4' },
            { sheet: 'vehicle2_sheet', frame: 5, name: 'vehicle2_5' }
        ];

        // Les textures sont déjà disponibles via le spritesheet,
        // on peut y accéder avec sheet:frame
    }

    createPlayerZones() {
        const { width, height } = this.cameras.main;
        const headerHeight = 100;
        const availableHeight = height - headerHeight - 100;
        const availableWidth = width - 40;

        // Calculate grid layout
        let cols, rows;
        if (this.playerCount <= 2) {
            cols = 2; rows = 1;
        } else if (this.playerCount <= 4) {
            cols = 2; rows = 2;
        } else if (this.playerCount <= 6) {
            cols = 3; rows = 2;
        } else {
            cols = 4; rows = 2;
        }

        const zoneWidth = availableWidth / cols;
        const zoneHeight = availableHeight / rows;

        for (let i = 0; i < this.playerCount; i++) {
            const col = i % cols;
            const row = Math.floor(i / cols);
            const x = 20 + col * zoneWidth;
            const y = headerHeight + row * zoneHeight;

            this.createPlayerZone(i, x, y, zoneWidth, zoneHeight);
        }
    }

    createPlayerZone(playerIndex, x, y, w, h) {
        const player = new Player(playerIndex, null, INPUT_MAPPING.keyboard[playerIndex]);
        this.players.push(player);

        // Zone background with gradient and border
        const zoneBg = this.add.graphics();
        zoneBg.fillStyle(0x0a1929, 0.7);
        zoneBg.fillRoundedRect(x, y, w - 20, h - 20, 12);
        zoneBg.lineStyle(3, parseInt(player.getColor().replace('#', '0x')), 0.8);
        zoneBg.strokeRoundedRect(x, y, w - 20, h - 20, 12);

        // Player name with glow
        this.add.text(x + w / 2, y + 25, player.getName(), {
            fontSize: '32px',
            fontFamily: 'Arial Black',
            color: player.getColor(),
            stroke: '#000000',
            strokeThickness: 6
        }).setOrigin(0.5);

        // Controls legend - Clean and professional
        const controls = INPUT_MAPPING.keyboard[playerIndex];
        this.createControlsLegend(x + w / 2, y + 85, controls, player.getColor());

        // Car preview (will be updated) - pointing right
        const carSprite = this.add.sprite(x + w / 2, y + h / 2 + 30, 'vehicle1_sheet', 0)
            .setScale(0.25)  // Agrandi pour meilleure visibilité
            .setAngle(0)  // Pas de rotation, orientation naturelle
            .setAlpha(0.7);
        carSprite.setData('playerIndex', playerIndex);

        // Car name with better style
        const carName = this.add.text(x + w / 2, y + h - 90, '', {
            fontSize: '26px',
            fontFamily: 'Arial Black',
            color: '#FFFFFF',
            stroke: '#000000',
            strokeThickness: 5
        }).setOrigin(0.5);

        // Car stats with icons
        const carStats = this.add.text(x + w / 2, y + h - 55, '', {
            fontSize: '18px',
            fontFamily: 'Arial Bold',
            color: '#4ECDC4',
            alpha: 0.9
        }).setOrigin(0.5);

        // Ready indicator with animation
        const readyIndicator = this.add.text(x + w / 2, y + h - 20, '', {
            fontSize: '24px',
            fontFamily: 'Arial Black',
            color: '#00FF00',
            stroke: '#000000',
            strokeThickness: 4
        }).setOrigin(0.5);

        // Store references
        player.carSprite = carSprite;
        player.carName = carName;
        player.carStats = carStats;
        player.readyIndicator = readyIndicator;
        player.currentCarIndex = 0;
        player.zoneBg = zoneBg;

        this.updatePlayerCar(playerIndex, 0);
    }

    createControlsLegend(centerX, centerY, controls, playerColor) {
        // Background panel - more compact
        const panel = this.add.graphics();
        panel.fillStyle(0x000000, 0.75);
        panel.fillRoundedRect(centerX - 140, centerY - 50, 280, 100, 8);
        panel.lineStyle(2, parseInt(playerColor.replace('#', '0x')), 0.7);
        panel.strokeRoundedRect(centerX - 140, centerY - 50, 280, 100, 8);

        // Title
        this.add.text(centerX, centerY - 30, 'VOS TOUCHES', {
            fontSize: '13px',
            fontFamily: 'Arial Black',
            color: '#FFD700',
            stroke: '#000000',
            strokeThickness: 2
        }).setOrigin(0.5);

        // Layout: 2 columns, 2 rows
        const col1X = centerX - 60;
        const col2X = centerX + 60;
        const row1Y = centerY + 5;
        const row2Y = centerY + 35;

        // Row 1: Navigation (selection menu)
        this.createCompactKeyBadge(col1X, row1Y, controls.up, '⬆ Choix', playerColor);
        this.createCompactKeyBadge(col2X, row1Y, controls.down, '⬇ Choix', playerColor);

        // Row 2: Action + Shift (race)
        this.createCompactKeyBadge(col1X, row2Y, 'SPC', '✓ Prêt', '#00FF00');
        const shiftKeys = `${controls.up}/${controls.down}`;
        this.createCompactKeyBadge(col2X, row2Y, shiftKeys, '⚡ Shift', '#FF6B35');
    }

    createCompactKeyBadge(x, y, key, label, accentColor) {
        // Key button background
        const keyBg = this.add.graphics();
        keyBg.fillStyle(0x1a1a1a, 0.95);
        keyBg.fillRoundedRect(x - 30, y - 22, 60, 22, 4);
        keyBg.lineStyle(2, parseInt(accentColor.replace('#', '0x')), 0.9);
        keyBg.strokeRoundedRect(x - 30, y - 22, 60, 22, 4);

        // Key text
        this.add.text(x, y - 11, key.toUpperCase(), {
            fontSize: '14px',
            fontFamily: 'Arial Black',
            color: accentColor,
            stroke: '#000000',
            strokeThickness: 3
        }).setOrigin(0.5);

        // Label text below
        this.add.text(x, y + 8, label, {
            fontSize: '11px',
            fontFamily: 'Arial',
            color: '#FFFFFF',
            alpha: 0.85
        }).setOrigin(0.5);
    }

    setupInput() {
        this.input.keyboard.on('keydown', (event) => {
            for (let i = 0; i < this.playerCount; i++) {
                const controls = INPUT_MAPPING.keyboard[i];

                if (event.key.toUpperCase() === controls.up) {
                    if (!this.ready[i]) {
                        // Next car
                        const nextIndex = (this.players[i].currentCarIndex + 1) % this.carData.length;
                        this.updatePlayerCar(i, nextIndex);
                    }
                } else if (event.key.toUpperCase() === controls.down) {
                    if (!this.ready[i]) {
                        // Previous car
                        const prevIndex = (this.players[i].currentCarIndex - 1 + this.carData.length) % this.carData.length;
                        this.updatePlayerCar(i, prevIndex);
                    } else {
                        // Unready
                        this.ready[i] = false;
                        this.updateReadyStatus(i);
                    }
                } else if (event.key === 'Enter' || event.key === ' ') {
                    // Toggle ready for current player (simple approach: space for all)
                    if (!this.ready[i]) {
                        this.ready[i] = true;
                        this.updateReadyStatus(i);
                    }
                }
            }

            // Check if all players are ready
            if (this.ready.every(r => r)) {
                this.startRace();
            }
        });
    }

    updatePlayerCar(playerIndex, carIndex) {
        const player = this.players[playerIndex];
        const car = this.carData[carIndex];

        player.currentCarIndex = carIndex;
        player.carData = car;

        // Fade out animation
        this.tweens.add({
            targets: player.carSprite,
            alpha: 0,
            duration: 100,
            onComplete: () => {
                // Update sprite - utiliser le spritesheet et la frame
                player.carSprite.setTexture(car.sprite, car.spriteFrame);

                // Fade in animation
                this.tweens.add({
                    targets: player.carSprite,
                    alpha: this.ready[playerIndex] ? 1.0 : 0.8,
                    duration: 100
                });
            }
        });

        // Update text
        player.carName.setText(car.name);
        player.carStats.setText(`⚡ ${car.stats.power}hp • ⚖ ${car.stats.weight}kg • ⚙ ${car.stats.gears} vitesses`);
    }

    updateReadyStatus(playerIndex) {
        const player = this.players[playerIndex];

        if (this.ready[playerIndex]) {
            player.readyIndicator.setText('✓ PRÊT');
            player.carSprite.setAlpha(1.0);

            // Pulse animation when ready
            this.tweens.add({
                targets: player.readyIndicator,
                scale: { from: 1.0, to: 1.2 },
                duration: 500,
                yoyo: true,
                repeat: -1
            });
        } else {
            player.readyIndicator.setText('');
            player.carSprite.setAlpha(0.8);
            this.tweens.killTweensOf(player.readyIndicator);
            player.readyIndicator.setScale(1.0);
        }

        this.updateInstructions();
    }

    updateInstructions() {
        const { width, height } = this.cameras.main;
        const readyCount = this.ready.filter(r => r).length;

        if (this.instructionText) {
            this.instructionText.destroy();
        }

        this.instructionText = this.add.text(
            width / 2,
            height - 40,
            `Utilisez vos touches ↑↓ pour choisir • ESPACE pour valider • ${readyCount}/${this.playerCount} prêts`,
            {
                fontSize: '20px',
                fontFamily: 'Arial',
                color: '#FFFFFF',
                stroke: '#000000',
                strokeThickness: 3,
                alpha: 0.9
            }
        ).setOrigin(0.5);
    }

    startRace() {
        this.scene.start('RaceScene', {
            players: this.players
        });
    }
}
