export class Player {
    constructor(playerId, carData, inputConfig) {
        this.playerId = playerId;
        this.carData = carData;
        this.inputConfig = inputConfig;
        this.car = null; // Will be created in race scene

        // Stats
        this.wins = 0;
        this.perfectShifts = 0;
        this.goodShifts = 0;
        this.badShifts = 0;
    }

    /**
     * Get player name
     */
    getName() {
        return `Joueur ${this.playerId + 1}`;
    }

    /**
     * Get display color for this player
     */
    getColor() {
        const colors = [
            '#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3',
            '#F38181', '#AA96DA', '#FCBAD3', '#A8D8EA'
        ];
        return colors[this.playerId % colors.length];
    }

    /**
     * Record a shift
     */
    recordShift(quality) {
        if (quality === 'PERFECT') this.perfectShifts++;
        else if (quality === 'GOOD') this.goodShifts++;
        else this.badShifts++;
    }
}
