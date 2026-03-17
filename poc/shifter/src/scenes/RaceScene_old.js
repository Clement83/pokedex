import { Car } from '../entities/Car.js';
import { InputManager } from '../systems/InputManager.js';
import { ParallaxBackground } from '../systems/ParallaxBackground.js';
import { GAME_CONFIG } from '../config.js';

export class RaceScene extends Phaser.Scene {
    constructor() {
        super({ key: 'RaceScene' });
    }

    preload() {
        // Précharger les sprite sheets si pas déjà fait
        if (!this.textures.exists('vehicle1_sheet')) {
            this.load.spritesheet('vehicle1_sheet', 'asset/sprite/vehicle1.png', {
                frameWidth: 128,
                frameHeight: 128
            });
        }

        if (!this.textures.exists('vehicle2_sheet')) {
            this.load.spritesheet('vehicle2_sheet', 'asset/sprite/vehicle2.png', {
                frameWidth: 128,
                frameHeight: 128
            });
        }
    }

    init(data) {
        this.players = data.players;
        this.playerCount = this.players.length;
        this.cars = [];
        this.raceStarted = false;
        this.raceFinished = false;
        this.startTimer = 0;
        this.startPhase = 'red'; // red, orange, green, racing

        // Configuration du monde de jeu
        this.worldWidth = 10000;  // Largeur du monde
        this.laneWidth = 200;     // Largeur d'une lane
        this.laneHeight = 300;    // Hauteur visible d'une lane
    }

    create() {
        const { width, height } = this.cameras.main;

        // Background général
        const bg = this.add.graphics();
        bg.fillGradientStyle(0x0a0a14, 0x0a0a14, 0x1a1a2e, 0x1a1a2e, 1, 1, 1, 1);
        bg.fillRect(0, 0, this.worldWidth, height);
        bg.setScrollFactor(0);

        // Create input manager
        this.inputManager = new InputManager(this);

        // Initialize cars
        this.initializeCars();

        // Create race world
        this.createRaceWorld();

        // Setup cameras (split-screen)
        this.setupCameras();

        // Start countdown
        this.startCountdown();
    }

    initializeCars() {
        this.players.forEach((player, index) => {
            const car = new Car(player.carData);
            this.cars.push(car);
            player.car = car;
            player.laneIndex = index;
        });
    }

    createRaceWorld() {
        // Créer le monde de course avec les lanes pour chaque joueur
        this.lanes = [];
        this.parallaxBackgrounds = [];
        this.carSprites = [];
        this.playerUIs = [];

        this.players.forEach((player, index) => {
            this.createPlayerLane(player, index);
        });
    }

    createPlayerLane(player, index) {
        const laneY = index * this.laneHeight;

        // Container pour cette lane
        const laneContainer = this.add.container(0, laneY);

        // Sol de la lane
        const ground = this.add.rectangle(
            0, this.laneHeight / 2,
            this.worldWidth, this.laneHeight,
            0x2c2c2c, 1
        ).setOrigin(0, 0.5);
        laneContainer.add(ground);

        // Lignes de séparation des lanes
        if (index > 0) {
            const separator = this.add.rectangle(
                0, 0,
                this.worldWidth, 3,
                0xFFE500, 0.8
            ).setOrigin(0, 0.5);
            laneContainer.add(separator);
        }

        // Ligne de départ
        const startLine = this.add.rectangle(
            50, this.laneHeight / 2,
            5, this.laneHeight * 0.6,
            0x00FF00, 1
        ).setOrigin(0, 0.5);
        laneContainer.add(startLine);

        // Ligne d'arrivée
        const finishLine = this.add.rectangle(
            GAME_CONFIG.raceDistance + 50, this.laneHeight / 2,
            5, this.laneHeight * 0.6,
            0xFF0000, 1
        ).setOrigin(0, 0.5);
        laneContainer.add(finishLine);

        // Créer les sprites de tous les joueurs pour cette lane
        const laneCarSprites = [];
        this.players.forEach((otherPlayer, otherIndex) => {
            const carY = laneY + this.laneHeight / 2;
            const carSprite = this.add.sprite(
                50, carY,
                otherPlayer.carData.sprite, otherPlayer.carData.spriteFrame
            ).setOrigin(0.5)
                .setAngle(90);

            // Le joueur principal est plus grand
            if (otherIndex === index) {
                carSprite.setScale(0.6);
                carSprite.setDepth(100);
            } else {
                carSprite.setScale(0.4);
                carSprite.setDepth(50);
                carSprite.setAlpha(0.7);
            }

            laneCarSprites.push({
                sprite: carSprite,
                playerIndex: otherIndex
            });

            if (otherIndex === index) {
                player.mainCarSprite = carSprite;
            }
        });

        this.carSprites.push(laneCarSprites);

        // Stocker les données de la lane
        this.lanes.push({
            container: laneContainer,
            laneY: laneY,
            playerIndex: index,
            ground: ground
        });

        player.laneData = {
            laneY: laneY,
            container: laneContainer
        };
    }

    setupCameras() {
        const { width, height } = this.cameras.main;

        // Détruire la caméra par défaut après avoir gardé ses dimensions
        this.cameras.main.setVisible(false);

        // Calculer le layout des caméras
        let cols, rows;
        if (this.playerCount === 1) {
            cols = 1; rows = 1;
        } else if (this.playerCount === 2) {
            cols = 1; rows = 2;
        } else if (this.playerCount <= 4) {
            cols = 2; rows = 2;
        } else if (this.playerCount <= 6) {
            cols = 3; rows = 2;
        } else {
            cols = 4; rows = 2;
        }

        const camWidth = width / cols;
        const camHeight = height / rows;

        this.players.forEach((player, index) => {
            const col = index % cols;
            const row = Math.floor(index / cols);

            // Créer une caméra pour ce joueur
            const camera = this.cameras.add(
                col * camWidth,
                row * camHeight,
                camWidth,
                camHeight
            );

            // Configurer la caméra pour suivre le joueur
            camera.setBounds(0, player.laneData.laneY - this.laneHeight / 2, this.worldWidth, this.laneHeight);
            camera.centerOn(400, player.laneData.laneY + this.laneHeight / 2);

            // Créer le système de parallax pour cette caméra
            const parallax = new ParallaxBackground(this, camera);
            parallax.setDepth(1);
            this.parallaxBackgrounds.push(parallax);

            // Créer l'UI pour ce joueur
            this.createPlayerUI(player, index, camera, col * camWidth, row * camHeight, camWidth, camHeight);

            player.camera = camera;
            player.parallax = parallax;
        });
    }

    createPlayerUI(player, index, camera, screenX, screenY, screenW, screenH) {
        // UI fixe qui ne scroll pas avec la caméra
        const ui = this.add.container(screenX, screenY);
        ui.setScrollFactor(0);
        ui.setDepth(1000);

        // Bordure de la zone du joueur
        const border = this.add.rectangle(2, 2, screenW - 4, screenH - 4, 0x000000, 0);
        border.setOrigin(0);
        border.setStrokeStyle(3, parseInt(player.getColor().replace('#', '0x')), 1);
        ui.add(border);

        // Nom du joueur
        const nameText = this.add.text(10, 10, player.getName(), {
            fontSize: '20px',
            fontFamily: 'Arial Black',
            color: player.getColor(),
            stroke: '#000000',
            strokeThickness: 4
        });
        ui.add(nameText);

        // Compte-tours circulaire
        const tachoX = screenW - 100;
        const tachoY = screenH - 100;
        const tachoRadius = 60;

        const tachoBg = this.add.circle(tachoX, tachoY, tachoRadius, 0x0a0a0a);
        const tachoOutline = this.add.circle(tachoX, tachoY, tachoRadius, 0x000000, 0)
            .setStrokeStyle(3, parseInt(player.getColor().replace('#', '0x')), 1);
        ui.add([tachoBg, tachoOutline]);

        player.tachoGraphics = this.add.graphics();
        ui.add(player.tachoGraphics);
        player.tachoData = { x: tachoX, y: tachoY, radius: tachoRadius };

        // RPM text
        player.rpmText = this.add.text(tachoX, tachoY - 10, '1000', {
            fontSize: '24px',
            fontFamily: 'Arial Black',
            color: '#FFFFFF',
            stroke: '#000000',
            strokeThickness: 3
        }).setOrigin(0.5);
        ui.add(player.rpmText);

        // Gear text
        player.gearText = this.add.text(tachoX, tachoY + 15, '1', {
            fontSize: '28px',
            fontFamily: 'Arial Black',
            color: '#FFE66D',
            stroke: '#000000',
            strokeThickness: 3
        }).setOrigin(0.5);
        ui.add(player.gearText);

        // Vitesse
        player.speedText = this.add.text(100, screenH - 60, '0', {
            fontSize: '48px',
            fontFamily: 'Arial Black',
            color: '#00FF88',
            stroke: '#000000',
            strokeThickness: 5
        }).setOrigin(0.5);
        ui.add(player.speedText);

        const speedLabel = this.add.text(100, screenH - 25, 'KM/H', {
            fontSize: '16px',
            fontFamily: 'Arial Bold',
            color: '#FFFFFF',
            alpha: 0.7
        }).setOrigin(0.5);
        ui.add(speedLabel);

        // Distance et position
        player.distanceText = this.add.text(10, 40, '0m / 400m', {
            fontSize: '16px',
            fontFamily: 'Arial Bold',
            color: '#FFFFFF'
        });
        ui.add(player.distanceText);

        player.positionText = this.add.text(10, 60, '', {
            fontSize: '20px',
            fontFamily: 'Arial Black',
            color: '#FFE66D'
        });
        ui.add(player.positionText);

        // Time
        player.timeText = this.add.text(screenW - 10, 40, '0.000s', {
            fontSize: '18px',
            fontFamily: 'Arial',
            color: '#FFFFFF'
        }).setOrigin(1, 0);
        ui.add(player.timeText);

        // Shift quality
        player.shiftQualityText = this.add.text(screenW / 2, 100, '', {
            fontSize: '32px',
            fontFamily: 'Arial Black',
            color: '#4ECDC4',
            stroke: '#000000',
            strokeThickness: 5
        }).setOrigin(0.5);
        ui.add(player.shiftQualityText);

        this.playerUIs.push(ui);
    }

    startCountdown() {
        const { width, height } = this.cameras.main;

        // Animated background with gradient
        const bg = this.add.graphics();
        bg.fillGradientStyle(0x0a0a14, 0x0a0a14, 0x1a1a2e, 0x1a1a2e, 1, 1, 1, 1);
        bg.fillRect(0, 0, width, height);

        // Create input manager
        this.inputManager = new InputManager(this);

        // Create player zones and initialize cars
        this.createRaceLayout();

        // Create track visuals
        this.createTrack();

        // Start countdown
        this.startCountdown();
    }

    createRaceLayout() {
        const { width, height } = this.cameras.main;

        // Calculate zone dimensions based on player count
        let zoneLayout = this.calculateZoneLayout();

        this.players.forEach((player, index) => {
            const zone = zoneLayout.zones[index];

            // Create car instance
            const car = new Car(player.carData);
            this.cars.push(car);
            player.car = car;

            // Create UI for this player
            this.createPlayerUI(player, index, zone);
        });
    }

    calculateZoneLayout() {
        const { width, height } = this.cameras.main;
        const zones = [];

        let cols, rows;
        if (this.playerCount === 2) {
            cols = 1; rows = 2;
        } else if (this.playerCount <= 4) {
            cols = 2; rows = 2;
        } else if (this.playerCount <= 6) {
            cols = 3; rows = 2;
        } else {
            cols = 4; rows = 2;
        }

        const zoneWidth = width / cols;
        const zoneHeight = height / rows;

        for (let i = 0; i < this.playerCount; i++) {
            const col = i % cols;
            const row = Math.floor(i / cols);

            zones.push({
                x: col * zoneWidth,
                y: row * zoneHeight,
                width: zoneWidth,
                height: zoneHeight
            });
        }

        return { cols, rows, zoneWidth, zoneHeight, zones };
    }

    createPlayerUI(player, index, zone) {
        const { x, y, width, height } = zone;

        // Border avec effet glow
        const border = this.add.rectangle(x, y, width, height, 0x0f3460, 0).setOrigin(0);
        border.setStrokeStyle(3, player.getColor().replace('#', '0x'), 0.8);

        // Background avec gradient
        const bg = this.add.rectangle(x + 2, y + 2, width - 4, height - 4, 0x0a1929, 0.4).setOrigin(0);

        // Player name
        this.add.text(x + 10, y + 10, player.getName(), {
            fontSize: '24px',
            fontFamily: 'Arial Black',
            color: player.getColor()
        });

        // Track visualization
        const trackY = y + height * 0.35;
        const trackWidth = width - 40;
        const trackHeight = 80;
        const trackX = x + 20;

        // Track background avec effet asphalte
        this.add.rectangle(trackX, trackY, trackWidth, trackHeight, 0x1a1a1a).setOrigin(0);
        this.add.rectangle(trackX, trackY + trackHeight / 2 - 2, trackWidth, 4, 0xFFE500, 0.6).setOrigin(0);

        // Start line (verte)
        this.add.rectangle(trackX, trackY, 5, trackHeight, 0x00FF00).setOrigin(0);
        this.add.text(trackX + 8, trackY + 5, 'START', {
            fontSize: '12px',
            fontFamily: 'Arial Bold',
            color: '#00FF00'
        });

        // Finish line (damier)
        const finishX = trackX + trackWidth - 5;
        this.add.rectangle(finishX, trackY, 5, trackHeight, 0xFF0000).setOrigin(0);
        this.add.text(finishX - 45, trackY + 5, 'FINISH', {
            fontSize: '12px',
            fontFamily: 'Arial Bold',
            color: '#FF0000'
        });

        // Car sprite on track - ROTATION 90° POUR POINTER VERS LA DROITE
        const carSprite = this.add.sprite(trackX, trackY + trackHeight / 2,
            player.carData.sprite, player.carData.spriteFrame)
            .setOrigin(0.5)
            .setAngle(90)  // ROTATION POUR ORIENTATION CORRECTE
            .setScale(0.18);
        player.carSprite = carSprite;
        player.trackData = { trackX, trackWidth, trackY, trackHeight };

        // Tachometer (simplified circular gauge)
        const tachoX = x + width * 0.25;
        const tachoY = y + height * 0.7;
        const tachoRadius = Math.min(width, height) * 0.12;

        // Tacho background avec effet néon
        const tachoBg = this.add.circle(tachoX, tachoY, tachoRadius, 0x0a0a0a);
        const tachoOutline = this.add.circle(tachoX, tachoY, tachoRadius, 0x000000, 0)
            .setStrokeStyle(4, parseInt(player.getColor().replace('#', '0x')), 1);

        // Glow effect
        const tachoGlow = this.add.circle(tachoX, tachoY, tachoRadius + 5, 0x000000, 0)
            .setStrokeStyle(8, parseInt(player.getColor().replace('#', '0x')), 0.3);

        // RPM zones (arcs) - will be drawn as colored segments
        const greenStart = -135;
        const yellowStart = -45;
        const redStart = 45;

        player.tachoGraphics = this.add.graphics();
        player.tachoData = { x: tachoX, y: tachoY, radius: tachoRadius };

        // RPM text avec ombre
        player.rpmText = this.add.text(tachoX, tachoY - 15, '1000', {
            fontSize: '32px',
            fontFamily: 'Arial Black',
            color: '#FFFFFF',
            stroke: '#000000',
            strokeThickness: 4
        }).setOrigin(0.5);

        // Gear text avec style
        player.gearText = this.add.text(tachoX, tachoY + 20, '1', {
            fontSize: '36px',
            fontFamily: 'Arial Black',
            color: '#FFE66D',
            stroke: '#000000',
            strokeThickness: 4
        }).setOrigin(0.5);

        // Label "GEAR"
        this.add.text(tachoX, tachoY + 40, 'GEAR', {
            fontSize: '14px',
            fontFamily: 'Arial',
            color: '#FFFFFF',
            alpha: 0.6
        }).setOrigin(0.5);

        // Speed avec style racing
        player.speedText = this.add.text(x + width * 0.75, y + height * 0.7 - 20, '0', {
            fontSize: '56px',
            fontFamily: 'Arial Black',
            color: '#00FF88',
            stroke: '#000000',
            strokeThickness: 6
        }).setOrigin(0.5);

        this.add.text(x + width * 0.75, y + height * 0.7 + 25, 'KM/H', {
            fontSize: '20px',
            fontFamily: 'Arial Bold',
            color: '#FFFFFF',
            alpha: 0.7
        }).setOrigin(0.5);

        // Distance avec barre de progression
        const progressBarWidth = width - 60;
        const progressBarX = x + 30;
        const progressBarY = y + height * 0.55;

        // Background de la barre
        this.add.rectangle(progressBarX, progressBarY, progressBarWidth, 8, 0x2a2a2a).setOrigin(0);

        // Barre de progression
        player.progressBar = this.add.rectangle(progressBarX, progressBarY, 0, 8,
            parseInt(player.getColor().replace('#', '0x'))).setOrigin(0);
        player.progressBarWidth = progressBarWidth;

        player.distanceText = this.add.text(x + width / 2, progressBarY + 20, '0m / 400m', {
            fontSize: '18px',
            fontFamily: 'Arial Bold',
            color: '#FFFFFF',
            alpha: 0.9
        }).setOrigin(0.5);

        // Time
        player.timeText = this.add.text(x + width - 10, y + 40, '0.000s', {
            fontSize: '20px',
            fontFamily: 'Arial',
            color: '#FFFFFF'
        }).setOrigin(1, 0);

        // Position
        player.positionText = this.add.text(x + width - 10, y + 70, '', {
            fontSize: '24px',
            fontFamily: 'Arial Black',
            color: '#FFE66D'
        }).setOrigin(1, 0);

        // Shift quality indicator avec effet
        player.shiftQualityText = this.add.text(x + width / 2, trackY - 50, '', {
            fontSize: '36px',
            fontFamily: 'Arial Black',
            color: '#4ECDC4',
            stroke: '#000000',
            strokeThickness: 6
        }).setOrigin(0.5);
    }

    createTrack() {
        // Track is visualized in each player's zone
        // No shared track needed
    }

    startCountdown() {
        const { width, height } = this.cameras.main;

        // Create lights display in center
        this.lightsContainer = this.add.container(width / 2, 60);

        const lightSpacing = 100;
        this.redLight = this.add.circle(-lightSpacing, 0, 30, 0x333333).setStrokeStyle(3, 0xFF0000);
        this.orangeLight = this.add.circle(0, 0, 30, 0x333333).setStrokeStyle(3, 0xFFA500);
        this.greenLight = this.add.circle(lightSpacing, 0, 30, 0x333333).setStrokeStyle(3, 0x00FF00);

        this.lightsContainer.add([this.redLight, this.orangeLight, this.greenLight]);

        // Start sequence
        this.time.delayedCall(100, () => {
            this.redLight.setFillStyle(0xFF0000);
            this.startPhase = 'red';
        });

        this.time.delayedCall(3100, () => {
            this.orangeLight.setFillStyle(0xFFA500);
            this.startPhase = 'orange';
        });

        this.time.delayedCall(4100, () => {
            this.greenLight.setFillStyle(0x00FF00);
            this.redLight.setFillStyle(0x333333);
            this.orangeLight.setFillStyle(0x333333);
            this.startPhase = 'green';
            this.startRace();
        });

        this.time.delayedCall(5600, () => {
            this.lightsContainer.destroy();
        });
    }

    startRace() {
        this.raceStarted = true;
        this.cars.forEach(car => car.start());
    }

    update(time, delta) {
        const deltaTime = delta / 1000; // Convert to seconds

        if (!this.raceStarted) {
            // Check for early starts
            this.checkEarlyStarts();
            return;
        }

        // Update input
        this.inputManager.update();

        // Handle player inputs
        this.players.forEach((player, index) => {
            const car = player.car;

            if (car.hasFinished) return;

            // Check for shift inputs
            if (this.inputManager.isShiftUpJustPressed(index)) {
                const oldQuality = car.shiftQuality;
                car.shiftUp();
                if (car.shiftQuality && car.shiftQuality !== oldQuality) {
                    player.recordShift(car.shiftQuality);
                }
            }

            if (this.inputManager.isShiftDownJustPressed(index)) {
                car.shiftDown();
            }
        });

        // Update all cars
        this.cars.forEach(car => car.update(deltaTime));

        // Update UI
        this.updateUI();

        // Check if race is finished
        if (!this.raceFinished && this.cars.every(car => car.hasFinished)) {
            this.raceFinished = true;
            this.time.delayedCall(2000, () => this.endRace());
        }
    }

    checkEarlyStarts() {
        this.players.forEach((player, index) => {
            if (this.inputManager.isShiftUpJustPressed(index) ||
                this.inputManager.isShiftDownJustPressed(index)) {
                player.car.penalizeEarlyStart();
            }
        });
    }

    updateUI() {
        // Calculate positions
        const sortedCars = [...this.cars]
            .map((car, idx) => ({ car, index: idx }))
            .sort((a, b) => b.car.position - a.car.position);

        this.players.forEach((player, index) => {
            const car = player.car;

            // Update car position on track
            const progress = Math.min(car.position / GAME_CONFIG.raceDistance, 1.0);
            const newX = player.trackData.trackX + progress * player.trackData.trackWidth;
            player.carSprite.x = newX;

            // Effet de vibration quand proche du limiteur
            if (car.rpm > car.maxRPM * 0.95) {
                player.carSprite.y = player.trackData.trackY + player.trackData.trackHeight / 2 +
                    Math.sin(Date.now() / 50) * 2;
            } else {
                player.carSprite.y = player.trackData.trackY + player.trackData.trackHeight / 2;
            }

            // Update progress bar
            player.progressBar.width = progress * player.progressBarWidth;

            // Update tachometer
            this.drawTachometer(player, car);

            // Update texts
            player.rpmText.setText(Math.round(car.rpm));
            player.gearText.setText(car.gear);
            player.speedText.setText(Math.round(car.speed));
            player.distanceText.setText(`${Math.round(car.position)}m / ${GAME_CONFIG.raceDistance}m`);
            player.timeText.setText(`${car.time.toFixed(3)}s`);

            // Change RPM color based on zone
            const rpmPercent = car.rpm / car.maxRPM;
            if (rpmPercent > 0.95) {
                player.rpmText.setColor('#FF0000'); // Rouge si proche limiteur
            } else if (Math.abs(car.rpm - car.optimalShiftRPM) < 300) {
                player.rpmText.setColor('#00FF00'); // Vert si zone optimale
            } else {
                player.rpmText.setColor('#FFFFFF'); // Blanc sinon
            }

            // Update position
            const position = sortedCars.findIndex(item => item.index === index) + 1;
            const suffix = ['er', 'e', 'e', 'e', 'e', 'e', 'e', 'e'][position - 1];
            player.positionText.setText(`${position}${suffix}`);

            // Update shift quality indicator avec animation
            if (car.shiftQuality && car.shiftBonusTimer > 0) {
                player.shiftQualityText.setText(car.shiftQuality);
                const colors = { 'PERFECT': '#00FF00', 'GOOD': '#FFE66D', 'BAD': '#FF6B6B' };
                player.shiftQualityText.setColor(colors[car.shiftQuality]);
                const alpha = car.shiftBonusTimer / GAME_CONFIG.shiftZones.duration;
                player.shiftQualityText.setAlpha(alpha);
                player.shiftQualityText.setScale(1 + (1 - alpha) * 0.3); // Effet de zoom out
            } else {
                player.shiftQualityText.setText('');
            }
        });
    }

    drawTachometer(player, car) {
        const { x, y, radius } = player.tachoData;
        const graphics = player.tachoGraphics;

        graphics.clear();

        // Calculate RPM percentage
        const rpmPercent = car.rpm / car.maxRPM;
        const angle = -135 + (rpmPercent * 270); // -135° to 135°

        // Draw RPM zones as background arcs
        // Green zone
        const optimalPercent = car.optimalShiftRPM / car.maxRPM;
        const greenZone = GAME_CONFIG.shiftZones.perfect / car.maxRPM;
        const yellowZone = GAME_CONFIG.shiftZones.good / car.maxRPM;

        const greenStart = -135 + ((optimalPercent - greenZone / 2) * 270);
        const greenEnd = -135 + ((optimalPercent + greenZone / 2) * 270);
        const yellowStart1 = -135 + ((optimalPercent - yellowZone / 2) * 270);
        const yellowEnd1 = greenStart;
        const yellowStart2 = greenEnd;
        const yellowEnd2 = -135 + ((optimalPercent + yellowZone / 2) * 270);

        // Draw zones
        graphics.lineStyle(8, 0xFF0000, 0.3);
        graphics.arc(x, y, radius - 10, Phaser.Math.DegToRad(-135), Phaser.Math.DegToRad(yellowStart1), false);

        graphics.lineStyle(8, 0xFFE66D, 0.3);
        graphics.arc(x, y, radius - 10, Phaser.Math.DegToRad(yellowStart1), Phaser.Math.DegToRad(yellowEnd1), false);

        graphics.lineStyle(8, 0x00FF00, 0.5);
        graphics.arc(x, y, radius - 10, Phaser.Math.DegToRad(greenStart), Phaser.Math.DegToRad(greenEnd), false);

        graphics.lineStyle(8, 0xFFE66D, 0.3);
        graphics.arc(x, y, radius - 10, Phaser.Math.DegToRad(yellowStart2), Phaser.Math.DegToRad(yellowEnd2), false);

        graphics.lineStyle(8, 0xFF0000, 0.3);
        graphics.arc(x, y, radius - 10, Phaser.Math.DegToRad(yellowEnd2), Phaser.Math.DegToRad(135), false);

        // Draw needle
        const needleLength = radius - 15;
        const needleX = x + Math.cos(Phaser.Math.DegToRad(angle)) * needleLength;
        const needleY = y + Math.sin(Phaser.Math.DegToRad(angle)) * needleLength;

        graphics.lineStyle(4, 0xFFFFFF, 1);
        graphics.beginPath();
        graphics.moveTo(x, y);
        graphics.lineTo(needleX, needleY);
        graphics.strokePath();

        // Center dot
        graphics.fillStyle(0xFFFFFF, 1);
        graphics.fillCircle(x, y, 5);
    }

    endRace() {
        // Calculate final standings
        const results = this.cars.map((car, index) => ({
            player: this.players[index],
            car: car,
            time: car.time,
            maxSpeed: Math.max(...this.cars.map(c => c.speed)),
            perfectShifts: this.players[index].perfectShifts,
            goodShifts: this.players[index].goodShifts,
            badShifts: this.players[index].badShifts
        })).sort((a, b) => a.time - b.time);

        this.scene.start('ResultScene', { results });
    }
}
