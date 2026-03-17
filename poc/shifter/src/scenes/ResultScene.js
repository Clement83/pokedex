export class ResultScene extends Phaser.Scene {
    constructor() {
        super({ key: 'ResultScene' });
    }

    init(data) {
        this.results = data.results;
    }

    create() {
        const { width, height } = this.cameras.main;

        // Background
        this.add.rectangle(0, 0, width, height, 0x1a1a2e).setOrigin(0);

        // Title
        this.add.text(width / 2, 80, 'RÉSULTATS DE LA COURSE', {
            fontSize: '56px',
            fontFamily: 'Arial Black',
            color: '#FFE66D'
        }).setOrigin(0.5);

        // Winner announcement
        const winner = this.results[0];
        this.add.text(width / 2, 160, `🏆 ${winner.player.getName()} GAGNE ! 🏆`, {
            fontSize: '42px',
            fontFamily: 'Arial Black',
            color: winner.player.getColor()
        }).setOrigin(0.5);

        // Results table
        const startY = 240;
        const rowHeight = 80;
        const tableWidth = 1400;
        const tableX = (width - tableWidth) / 2;

        // Headers
        const headerY = startY;
        this.add.text(tableX + 50, headerY, 'POS', {
            fontSize: '20px',
            fontFamily: 'Arial Bold',
            color: '#FFFFFF',
            alpha: 0.7
        });
        this.add.text(tableX + 150, headerY, 'JOUEUR', {
            fontSize: '20px',
            fontFamily: 'Arial Bold',
            color: '#FFFFFF',
            alpha: 0.7
        });
        this.add.text(tableX + 400, headerY, 'VOITURE', {
            fontSize: '20px',
            fontFamily: 'Arial Bold',
            color: '#FFFFFF',
            alpha: 0.7
        });
        this.add.text(tableX + 750, headerY, 'TEMPS', {
            fontSize: '20px',
            fontFamily: 'Arial Bold',
            color: '#FFFFFF',
            alpha: 0.7
        });
        this.add.text(tableX + 950, headerY, 'VITESSE MAX', {
            fontSize: '20px',
            fontFamily: 'Arial Bold',
            color: '#FFFFFF',
            alpha: 0.7
        });
        this.add.text(tableX + 1150, headerY, 'SHIFTS', {
            fontSize: '20px',
            fontFamily: 'Arial Bold',
            color: '#FFFFFF',
            alpha: 0.7
        });

        // Draw each result
        this.results.forEach((result, index) => {
            const y = startY + 40 + (index * rowHeight);
            const bgColor = index === 0 ? 0xFFD700 : (index === 1 ? 0xC0C0C0 : (index === 2 ? 0xCD7F32 : 0x2a2a2a));
            const bgAlpha = index < 3 ? 0.3 : 0.15;

            // Row background
            this.add.rectangle(tableX, y, tableWidth, rowHeight - 10, bgColor, bgAlpha).setOrigin(0);

            // Position
            const posText = index === 0 ? '🥇' : (index === 1 ? '🥈' : (index === 2 ? '🥉' : `${index + 1}`));
            this.add.text(tableX + 50, y + (rowHeight - 10) / 2, posText, {
                fontSize: '32px',
                fontFamily: 'Arial Black',
                color: '#FFFFFF'
            }).setOrigin(0, 0.5);

            // Player name
            this.add.text(tableX + 150, y + (rowHeight - 10) / 2, result.player.getName(), {
                fontSize: '28px',
                fontFamily: 'Arial Bold',
                color: result.player.getColor()
            }).setOrigin(0, 0.5);

            // Car name
            this.add.text(tableX + 400, y + (rowHeight - 10) / 2, result.car.name, {
                fontSize: '22px',
                fontFamily: 'Arial',
                color: '#FFFFFF'
            }).setOrigin(0, 0.5);

            // Time
            this.add.text(tableX + 750, y + (rowHeight - 10) / 2, `${result.time.toFixed(3)}s`, {
                fontSize: '28px',
                fontFamily: 'Arial Black',
                color: '#4ECDC4'
            }).setOrigin(0, 0.5);

            // Max speed
            this.add.text(tableX + 950, y + (rowHeight - 10) / 2, `${Math.round(result.car.speed)} km/h`, {
                fontSize: '24px',
                fontFamily: 'Arial',
                color: '#FFFFFF'
            }).setOrigin(0, 0.5);

            // Shifts
            const shiftsText = `✓${result.perfectShifts} ○${result.goodShifts} ✗${result.badShifts}`;
            this.add.text(tableX + 1150, y + (rowHeight - 10) / 2, shiftsText, {
                fontSize: '20px',
                fontFamily: 'Arial',
                color: '#FFFFFF'
            }).setOrigin(0, 0.5);
        });

        // Buttons
        const buttonY = height - 100;

        // Replay button
        const replayButton = this.add.rectangle(width / 2 - 200, buttonY, 300, 60, 0x4ECDC4);
        const replayText = this.add.text(width / 2 - 200, buttonY, 'REJOUER', {
            fontSize: '28px',
            fontFamily: 'Arial Black',
            color: '#FFFFFF'
        }).setOrigin(0.5);

        replayButton.setInteractive({ useHandCursor: true });
        replayButton.on('pointerover', () => {
            replayButton.setFillStyle(0x95E1D3);
            replayButton.setScale(1.05);
            replayText.setScale(1.05);
        });
        replayButton.on('pointerout', () => {
            replayButton.setFillStyle(0x4ECDC4);
            replayButton.setScale(1.0);
            replayText.setScale(1.0);
        });
        replayButton.on('pointerdown', () => {
            // Replay with same players
            this.scene.start('RaceScene', { players: this.results.map(r => r.player) });
        });

        // Menu button
        const menuButton = this.add.rectangle(width / 2 + 200, buttonY, 300, 60, 0xFF6B6B);
        const menuText = this.add.text(width / 2 + 200, buttonY, 'MENU', {
            fontSize: '28px',
            fontFamily: 'Arial Black',
            color: '#FFFFFF'
        }).setOrigin(0.5);

        menuButton.setInteractive({ useHandCursor: true });
        menuButton.on('pointerover', () => {
            menuButton.setFillStyle(0xFF9999);
            menuButton.setScale(1.05);
            menuText.setScale(1.05);
        });
        menuButton.on('pointerout', () => {
            menuButton.setFillStyle(0xFF6B6B);
            menuButton.setScale(1.0);
            menuText.setScale(1.0);
        });
        menuButton.on('pointerdown', () => {
            this.scene.start('MenuScene');
        });

        // Key instructions
        this.add.text(width / 2, height - 30, 'Cliquez sur un bouton ou appuyez sur ESPACE pour rejouer', {
            fontSize: '18px',
            fontFamily: 'Arial',
            color: '#FFFFFF',
            alpha: 0.6
        }).setOrigin(0.5);

        // Keyboard shortcut
        this.input.keyboard.once('keydown-SPACE', () => {
            this.scene.start('RaceScene', { players: this.results.map(r => r.player) });
        });
    }
}
