// Game configuration
export const GAME_CONFIG = {
    width: 1920,
    height: 1080,
    targetFPS: 60,
    raceDistance: 400, // meters (1/4 mile)

    // Physics constants
    gravity: 9.81,
    airResistance: 0.0008,      // Réduit pour plus d'accélération
    rollingResistance: 0.003,   // Réduit pour plus d'accélération
    wheelRadius: 0.33,          // Rayon de roue en mètres
    finalDrive: 3.5,            // Ratio de différentiel

    // Shift zones (RPM offset from optimal)
    shiftZones: {
        perfect: 200,   // ±200 RPM = green zone
        good: 500,      // ±500 RPM = yellow zone
        // anything else = red zone

        bonuses: {
            perfect: 1.05,  // 5% power bonus
            good: 1.0,      // no bonus
            bad: 0.9        // 10% penalty
        },

        duration: 500   // bonus/penalty duration in ms
    },

    // Start sequence timing
    startSequence: {
        red: 3000,
        orange: 1000,
        green: 0,
        earlyPenalty: 1000  // 1 second penalty for early start
    }
};

// Input mapping for up to 6 players (AZERTY - espacées au maximum)
export const INPUT_MAPPING = {
    keyboard: [
        { up: 'A', down: 'Q' },           // Player 1 (extrême gauche)
        { up: 'P', down: 'M' },           // Player 2 (extrême droite)
        { up: 'E', down: 'D' },           // Player 3 (milieu-gauche)
        { up: 'U', down: 'J' },           // Player 4 (milieu-droite)
        { up: 'O', down: 'L' },           // Player 5 (droite)
        { up: 'T', down: 'G' }            // Player 6 (centre)
    ]
};
