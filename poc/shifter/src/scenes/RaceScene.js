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
                frameWidth: 768,   // 1536 / 2 colonnes
                frameHeight: 341   // 1024 / 3 lignes
            });
        }

        if (!this.textures.exists('vehicle2_sheet')) {
            this.load.spritesheet('vehicle2_sheet', 'asset/sprite/vehicle2.png', {
                frameWidth: 768,
                frameHeight: 341
            });
        }
    }

    init(data) {
        this.players = data.players;
        this.playerCount = this.players.length;
        this.cars = [];
        this.raceStarted = false;
        this.raceFinished = false;
        this.startPhase = 'red';

        // Vue de côté : caméra fixe, voitures fixes, décor qui défile
        this.carFixedX = 150; // Position X fixe des voitures à l'écran
        this.laneHeight = 80; // Hauteur de chaque "lane" pour séparer les voitures
    }

    create() {
        const { width, height } = this.cameras.main;

        // Fond du ciel fixe
        const bg = this.add.graphics();
        bg.fillGradientStyle(0x87CEEB, 0x87CEEB, 0xe0f6ff, 0xe0f6ff, 1, 1, 1, 1);
        bg.fillRect(0, 0, width, height);
        bg.setScrollFactor(0);
        bg.setDepth(-1000);

        // Create input manager
        this.inputManager = new InputManager(this);

        // Initialize cars
        this.initializeCars();

        // Create parallax background
        this.parallaxBg = new ParallaxBackground(this, width, height);

        // Create race world (voitures)
        this.createRaceWorld();

        // Create finish line indicator
        this.createFinishLine();

        // Setup UI
        this.setupUI();

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
        // === VOITURES CÔTE À CÔTE (VUE DE PROFIL) ===
        this.createAllCars();
    }

    createAllCars() {
        this.carSprites = [];
        const { height } = this.cameras.main;

        // Calculer l'espacement vertical entre les voitures (positionnées plus bas)
        const startY = height * 0.65 - (this.playerCount - 1) * this.laneHeight / 2;

        this.players.forEach((player, index) => {
            // Position Y pour chaque voiture (côte à côte horizontalement)
            const carY = startY + index * this.laneHeight;

            const carSprite = this.add.sprite(
                this.carFixedX, carY,
                player.carData.sprite, player.carData.spriteFrame
            ).setOrigin(0.5, 0.5)
                .setAngle(0)
                .setScale(0.28)
                .setDepth(100 + index);

            this.carSprites.push({
                sprite: carSprite,
                playerIndex: index,
                baseY: carY,
                laneY: carY
            });

            player.mainCarSprite = carSprite;
            player.carY = carY;
        });
    }

    createFinishLine() {
        const { width, height } = this.cameras.main;

        // Container pour la ligne d'arrivée (damier noir et blanc)
        this.finishLineContainer = this.add.container(width + 200, 0);
        this.finishLineContainer.setDepth(50);

        const roadY = height * 0.35;
        const roadHeight = height * 0.65;
        const numSquares = 20;
        const squareHeight = roadHeight / numSquares;

        for (let i = 0; i < numSquares; i++) {
            const color = i % 2 === 0 ? 0x000000 : 0xFFFFFF;
            const square = this.add.rectangle(
                0, roadY + i * squareHeight,
                15, squareHeight,
                color, 1
            ).setOrigin(0, 0);

            this.finishLineContainer.add(square);
        }

        // Texte "ARRIVÉE"
        const finishText = this.add.text(20, height / 2, 'ARRIVÉE', {
            fontSize: '48px',
            fontFamily: 'Arial Black',
            color: '#FFD700',
            stroke: '#000000',
            strokeThickness: 6
        }).setOrigin(0, 0.5).setAngle(-90);

        this.finishLineContainer.add(finishText);
    }

    setupUI() {
        const { width, height } = this.cameras.main;

        this.playerUIs = [];

        // Créer l'UI pour chaque joueur (en haut de l'écran)
        this.players.forEach((player, index) => {
            this.createPlayerUI(player, index, width, height);
        });
    }

    createPlayerUI(player, index, screenW, screenH) {
        const ui = this.add.container(0, 0);
        ui.setScrollFactor(0);
        ui.setDepth(1000);

        // Position de l'UI selon le joueur
        const uiY = index * 80 + 10;
        const color = parseInt(player.getColor().replace('#', '0x'));

        // Nom du joueur avec bordure colorée
        const nameBg = this.add.rectangle(10, uiY, 150, 30, 0x000000, 0.7);
        nameBg.setOrigin(0, 0);
        nameBg.setStrokeStyle(2, color, 1);
        ui.add(nameBg);

        const nameText = this.add.text(15, uiY + 5, player.getName(), {
            fontSize: '18px',
            fontFamily: 'Arial Black',
            color: player.getColor(),
        });
        ui.add(nameText);

        // Compte-tours (compact, à droite)
        const tachoX = screenW - 80;
        const tachoY = uiY + 40;
        const tachoRadius = 30;

        const tachoBg = this.add.circle(tachoX, tachoY, tachoRadius, 0x0a0a0a);
        const tachoOutline = this.add.circle(tachoX, tachoY, tachoRadius, 0x000000, 0)
            .setStrokeStyle(2, color, 1);
        ui.add([tachoBg, tachoOutline]);

        player.tachoGraphics = this.add.graphics();
        ui.add(player.tachoGraphics);
        player.tachoData = { x: tachoX, y: tachoY, radius: tachoRadius };

        player.rpmText = this.add.text(tachoX, tachoY - 5, '1000', {
            fontSize: '14px',
            fontFamily: 'Arial Black',
            color: '#FFFFFF',
        }).setOrigin(0.5);
        ui.add(player.rpmText);

        player.gearText = this.add.text(tachoX, tachoY + 8, '1', {
            fontSize: '18px',
            fontFamily: 'Arial Black',
            color: '#FFE66D',
        }).setOrigin(0.5);
        ui.add(player.gearText);

        // Vitesse (à côté du nom)
        player.speedText = this.add.text(170, uiY + 5, '0', {
            fontSize: '24px',
            fontFamily: 'Arial Black',
            color: '#00FF88',
            stroke: '#000000',
            strokeThickness: 3
        });
        ui.add(player.speedText);

        const speedLabel = this.add.text(220, uiY + 8, 'KM/H', {
            fontSize: '12px',
            fontFamily: 'Arial Bold',
            color: '#FFFFFF',
            alpha: 0.7
        });
        ui.add(speedLabel);

        // Distance et position
        player.distanceText = this.add.text(300, uiY + 8, '0m / 400m', {
            fontSize: '14px',
            fontFamily: 'Arial Bold',
            color: '#FFFFFF'
        });
        ui.add(player.distanceText);

        player.positionText = this.add.text(450, uiY + 5, '', {
            fontSize: '20px',
            fontFamily: 'Arial Black',
            color: '#FFE66D'
        });
        ui.add(player.positionText);

        player.timeText = this.add.text(screenW - 150, uiY + 8, '0.000s', {
            fontSize: '16px',
            fontFamily: 'Arial',
            color: '#FFFFFF'
        });
        ui.add(player.timeText);

        // Texte de qualité de shift (au centre, au-dessus de la voiture)
        player.shiftQualityText = this.add.text(this.carFixedX + 100, player.carY - 50, '', {
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

        // Créer les feux au centre de l'écran
        const lightsContainer = this.add.container(width / 2, 100);
        lightsContainer.setScrollFactor(0);
        lightsContainer.setDepth(2000);

        const spacing = 50;
        const redLight = this.add.circle(-spacing, 0, 25, 0x333333).setStrokeStyle(3, 0xFF0000);
        const orangeLight = this.add.circle(0, 0, 25, 0x333333).setStrokeStyle(3, 0xFFA500);
        const greenLight = this.add.circle(spacing, 0, 25, 0x333333).setStrokeStyle(3, 0x00FF00);

        lightsContainer.add([redLight, orangeLight, greenLight]);

        // Séquence de démarrage
        this.time.delayedCall(100, () => {
            redLight.setFillStyle(0xFF0000);
        });

        this.time.delayedCall(3100, () => {
            orangeLight.setFillStyle(0xFFA500);
        });

        this.time.delayedCall(4100, () => {
            greenLight.setFillStyle(0x00FF00);
            redLight.setFillStyle(0x333333);
            orangeLight.setFillStyle(0x333333);
            this.startRace();
        });

        this.time.delayedCall(5600, () => {
            lightsContainer.destroy();
        });
    }

    startRace() {
        this.raceStarted = true;
        this.cars.forEach(car => car.start());
    }

    update(time, delta) {
        const deltaTime = delta / 1000;

        if (!this.raceStarted) {
            this.checkEarlyStarts();
            return;
        }

        this.inputManager.update();

        // Handle player inputs
        this.players.forEach((player, index) => {
            const car = player.car;

            if (car.hasFinished) return;

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

        // Update positions and cameras
        this.updatePositions();

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

    updatePositions() {
        const { width } = this.cameras.main;
        const leadPosition = Math.max(...this.cars.map(car => car.position));
        const minPosition = Math.min(...this.cars.map(car => car.position));
        const minSpeed = Math.min(...this.cars.map(car => car.speed));
        const distanceToFinish = GAME_CONFIG.raceDistance - leadPosition;

        // La voiture la plus lente reste fixe à gauche (carFixedX)
        // Les autres avancent proportionnellement à leur écart de position
        this.carSprites.forEach(carSpriteData => {
            const player = this.players[carSpriteData.playerIndex];
            const car = player.car;

            // Différence de position par rapport au plus lent (en mètres)
            // Le plus lent est à 0, les autres sont devant
            const positionDiff = car.position - minPosition;

            // Convertir en pixels (1 mètre = 2 pixels d'écart visuel)
            const xOffset = positionDiff * 2;

            // Position X : le plus lent est à carFixedX, les autres sont devant
            carSpriteData.sprite.x = this.carFixedX + xOffset;
            carSpriteData.sprite.y = carSpriteData.baseY;
        });

        // Mettre à jour le parallax (décor qui défile à la vitesse du plus lent)
        this.parallaxBg.update(minSpeed);

        // Afficher la ligne d'arrivée dans les derniers 100m
        if (distanceToFinish <= 100) {
            // Calculer la position à l'écran de la voiture en tête
            const leadCarPositionDiff = leadPosition - minPosition;
            const leadCarScreenX = this.carFixedX + (leadCarPositionDiff * 2);

            // La ligne d'arrivée vient vers la position du leader à l'écran
            // À 100m : width + 200 (hors écran à droite)
            // À 0m : position exacte du leader
            const finishLineX = (width + 200) - ((100 - distanceToFinish) / 100) * ((width + 200) - leadCarScreenX);
            this.finishLineContainer.x = finishLineX;
            this.finishLineContainer.setVisible(true);
        } else {
            this.finishLineContainer.setVisible(false);
        }
    }

    updateUI() {
        const sortedCars = [...this.cars]
            .map((car, idx) => ({ car, index: idx }))
            .sort((a, b) => b.car.position - a.car.position);

        this.players.forEach((player, index) => {
            const car = player.car;

            // Update tachometer
            this.drawTachometer(player, car);

            // Update texts
            player.rpmText.setText(Math.round(car.rpm));
            player.gearText.setText(car.gear);
            player.speedText.setText(Math.round(car.speed));
            player.distanceText.setText(`${Math.round(car.position)}m / ${GAME_CONFIG.raceDistance}m`);
            player.timeText.setText(`${car.time.toFixed(3)}s`);

            // Change RPM color
            const rpmPercent = car.rpm / car.maxRPM;
            if (rpmPercent > 0.95) {
                player.rpmText.setColor('#FF0000');
            } else if (Math.abs(car.rpm - car.optimalShiftRPM) < 300) {
                player.rpmText.setColor('#00FF00');
            } else {
                player.rpmText.setColor('#FFFFFF');
            }

            // Update position
            const position = sortedCars.findIndex(item => item.index === index) + 1;
            const suffix = ['er', 'e', 'e', 'e', 'e', 'e', 'e', 'e'][position - 1];
            player.positionText.setText(`${position}${suffix}`);

            // Update shift quality
            if (car.shiftQuality && car.shiftBonusTimer > 0) {
                player.shiftQualityText.setText(car.shiftQuality);
                const colors = { 'PERFECT': '#00FF00', 'GOOD': '#FFE66D', 'BAD': '#FF6B6B' };
                player.shiftQualityText.setColor(colors[car.shiftQuality]);
                const alpha = car.shiftBonusTimer / GAME_CONFIG.shiftZones.duration;
                player.shiftQualityText.setAlpha(alpha);
                player.shiftQualityText.setScale(1 + (1 - alpha) * 0.3);
            } else {
                player.shiftQualityText.setText('');
            }
        });
    }

    drawTachometer(player, car) {
        const { x, y, radius } = player.tachoData;
        const graphics = player.tachoGraphics;

        graphics.clear();

        const rpmPercent = car.rpm / car.maxRPM;
        const angle = -135 + (rpmPercent * 270);

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
        graphics.lineStyle(6, 0xFF0000, 0.3);
        graphics.arc(x, y, radius - 10, Phaser.Math.DegToRad(-135), Phaser.Math.DegToRad(yellowStart1), false);

        graphics.lineStyle(6, 0xFFE66D, 0.3);
        graphics.arc(x, y, radius - 10, Phaser.Math.DegToRad(yellowStart1), Phaser.Math.DegToRad(yellowEnd1), false);

        graphics.lineStyle(6, 0x00FF00, 0.5);
        graphics.arc(x, y, radius - 10, Phaser.Math.DegToRad(greenStart), Phaser.Math.DegToRad(greenEnd), false);

        graphics.lineStyle(6, 0xFFE66D, 0.3);
        graphics.arc(x, y, radius - 10, Phaser.Math.DegToRad(yellowStart2), Phaser.Math.DegToRad(yellowEnd2), false);

        graphics.lineStyle(6, 0xFF0000, 0.3);
        graphics.arc(x, y, radius - 10, Phaser.Math.DegToRad(yellowEnd2), Phaser.Math.DegToRad(135), false);

        // Draw needle
        const needleLength = radius - 15;
        const needleX = x + Math.cos(Phaser.Math.DegToRad(angle)) * needleLength;
        const needleY = y + Math.sin(Phaser.Math.DegToRad(angle)) * needleLength;

        graphics.lineStyle(3, 0xFFFFFF, 1);
        graphics.beginPath();
        graphics.moveTo(x, y);
        graphics.lineTo(needleX, needleY);
        graphics.strokePath();

        graphics.fillStyle(0xFFFFFF, 1);
        graphics.fillCircle(x, y, 4);
    }

    endRace() {
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
