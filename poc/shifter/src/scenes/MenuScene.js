export class MenuScene extends Phaser.Scene {
    constructor() {
        super({ key: 'MenuScene' });
    }

    create() {
        const { width, height } = this.cameras.main;

        // Animated background
        this.createAnimatedBackground();

        // Title with glow effect
        const title = this.add.text(width / 2, height * 0.25, 'SHIFTER', {
            fontSize: '140px',
            fontFamily: 'Arial Black',
            color: '#FF6B6B',
            stroke: '#000000',
            strokeThickness: 10
        }).setOrigin(0.5);

        // Title glow
        const titleGlow = this.add.text(width / 2, height * 0.25, 'SHIFTER', {
            fontSize: '140px',
            fontFamily: 'Arial Black',
            color: '#FF6B6B',
            alpha: 0.3
        }).setOrigin(0.5).setScale(1.05);

        // Pulsing animation for title
        this.tweens.add({
            targets: [titleGlow],
            scale: { from: 1.05, to: 1.15 },
            alpha: { from: 0.3, to: 0.1 },
            duration: 1500,
            yoyo: true,
            repeat: -1,
            ease: 'Sine.easeInOut'
        });

        // Subtitle with style
        this.add.text(width / 2, height * 0.35, '⚡ DRAG RACING ⚡', {
            fontSize: '42px',
            fontFamily: 'Arial Black',
            color: '#FFE66D',
            stroke: '#000000',
            strokeThickness: 6
        }).setOrigin(0.5);

        this.add.text(width / 2, height * 0.40, 'Fast & Furious Style', {
            fontSize: '28px',
            fontFamily: 'Arial',
            color: '#4ECDC4',
            alpha: 0.9
        }).setOrigin(0.5);

        // Instructions with better styling
        this.add.text(width / 2, height * 0.52, 'SÉLECTIONNEZ LE NOMBRE DE JOUEURS', {
            fontSize: '28px',
            fontFamily: 'Arial Bold',
            color: '#FFFFFF',
            stroke: '#000000',
            strokeThickness: 4
        }).setOrigin(0.5);

        // Player count buttons with enhanced design
        const playerCounts = [2, 3, 4, 5, 6];
        const buttonY = height * 0.68;
        const buttonSpacing = 130;
        const startX = width / 2 - (playerCounts.length - 1) * buttonSpacing / 2;

        playerCounts.forEach((count, index) => {
            const x = startX + index * buttonSpacing;

            // Button shadow
            const shadow = this.add.rectangle(x + 3, buttonY + 3, 100, 100, 0x000000, 0.5);
            shadow.setStrokeStyle(0);

            // Main button
            const button = this.add.rectangle(x, buttonY, 100, 100, 0x4ECDC4);
            button.setStrokeStyle(4, 0x95E1D3);

            // Button glow
            const glow = this.add.rectangle(x, buttonY, 110, 110, 0x4ECDC4, 0);
            glow.setStrokeStyle(3, 0x4ECDC4, 0.5);

            // Number text
            const text = this.add.text(x, buttonY, count.toString(), {
                fontSize: '56px',
                fontFamily: 'Arial Black',
                color: '#FFFFFF',
                stroke: '#000000',
                strokeThickness: 5
            }).setOrigin(0.5);

            // Players label
            const label = this.add.text(x, buttonY + 60, 'JOUEURS', {
                fontSize: '14px',
                fontFamily: 'Arial Bold',
                color: '#FFFFFF',
                alpha: 0.8
            }).setOrigin(0.5);

            button.setInteractive({ useHandCursor: true });

            button.on('pointerover', () => {
                button.setFillStyle(0x95E1D3);
                this.tweens.add({
                    targets: [button, text, label],
                    scale: 1.15,
                    duration: 150,
                    ease: 'Back.easeOut'
                });
                this.tweens.add({
                    targets: glow,
                    alpha: 0.8,
                    scale: 1.2,
                    duration: 150
                });
            });

            button.on('pointerout', () => {
                button.setFillStyle(0x4ECDC4);
                this.tweens.add({
                    targets: [button, text, label],
                    scale: 1.0,
                    duration: 150,
                    ease: 'Back.easeIn'
                });
                this.tweens.add({
                    targets: glow,
                    alpha: 0,
                    scale: 1.1,
                    duration: 150
                });
            });

            button.on('pointerdown', () => {
                this.cameras.main.flash(300, 255, 107, 107);
                this.time.delayedCall(100, () => {
                    this.startGame(count);
                });
            });
        });

        // Footer with style
        this.add.text(width / 2, height * 0.92, '🏎️ Inspiré par NFS Underground & Fast and Furious 🏁', {
            fontSize: '22px',
            fontFamily: 'Arial',
            color: '#FFFFFF',
            alpha: 0.6
        }).setOrigin(0.5);

        // Controls hint
        this.add.text(width / 2, height * 0.97, 'Cliquez sur un nombre pour commencer !', {
            fontSize: '18px',
            fontFamily: 'Arial',
            color: '#4ECDC4',
            alpha: 0.7
        }).setOrigin(0.5);
    }

    createAnimatedBackground() {
        const { width, height } = this.cameras.main;

        // Dark gradient background
        const bg = this.add.graphics();
        bg.fillGradientStyle(0x0a0a14, 0x0a0a14, 0x1a1a2e, 0x1a1a2e, 1, 1, 1, 1);
        bg.fillRect(0, 0, width, height);

        // Animated racing lines
        for (let i = 0; i < 15; i++) {
            const line = this.add.rectangle(
                Phaser.Math.Between(-100, width + 100),
                Phaser.Math.Between(0, height),
                Phaser.Math.Between(100, 300),
                3,
                0xFFFFFF,
                0.1
            ).setAngle(Phaser.Math.Between(-5, 5));

            // Animate lines moving
            this.tweens.add({
                targets: line,
                x: width + 200,
                duration: Phaser.Math.Between(3000, 8000),
                repeat: -1,
                delay: Phaser.Math.Between(0, 3000)
            });
        }
    }

    startGame(playerCount) {
        this.scene.start('CarSelectScene', { playerCount });
    }
}
