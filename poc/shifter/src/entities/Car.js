import { GAME_CONFIG } from '../config.js';

export class Car {
    constructor(carData) {
        this.id = carData.id;
        this.name = carData.name;
        this.category = carData.category;
        this.description = carData.description;
        this.sprite = carData.sprite;

        // Stats
        this.maxPower = carData.stats.power;
        this.weight = carData.stats.weight;
        this.maxGears = carData.stats.gears;
        this.maxRPM = carData.stats.maxRPM;
        this.optimalShiftRPM = carData.stats.optimalShiftRPM;
        this.shiftTime = carData.stats.shiftTime;

        // Power curve (array of [rpm, power] points)
        this.powerCurve = carData.powerCurve;
        this.gearRatios = carData.gearRatios;

        // Dynamic state
        this.rpm = 1000;
        this.speed = 0;           // km/h
        this.gear = 1;
        this.position = 0;        // meters
        this.time = 0;            // seconds
        this.isShifting = false;
        this.shiftBonus = 1.0;
        this.shiftBonusTimer = 0;
        this.hasStarted = false;
        this.hasFinished = false;
        this.earlyStartPenalty = false;
    }

    /**
     * Get power at specific RPM using linear interpolation
     */
    getPowerAtRPM(rpm) {
        // Clamp RPM
        rpm = Math.max(1000, Math.min(this.maxRPM, rpm));

        // Find the two points to interpolate between
        for (let i = 0; i < this.powerCurve.length - 1; i++) {
            const [rpm1, power1] = this.powerCurve[i];
            const [rpm2, power2] = this.powerCurve[i + 1];

            if (rpm >= rpm1 && rpm <= rpm2) {
                // Linear interpolation
                const t = (rpm - rpm1) / (rpm2 - rpm1);
                return power1 + (power2 - power1) * t;
            }
        }

        // If beyond last point, return last power value
        return this.powerCurve[this.powerCurve.length - 1][1];
    }

    /**
     * Calculate RPM based on speed and current gear
     */
    calculateRPM(speed, gear) {
        // Formule réaliste: RPM = (vitesse_m/s * ratio * finalDrive * 60) / (2 * pi * wheelRadius)
        // Simplifié: RPM = speed_kmh * gearRatio * constant
        if (speed < 1) return 1000; // Idle RPM

        const constant = 40; // Constante de tuning calibrée
        const rpm = speed * this.gearRatios[gear - 1] * constant;
        return Math.max(1000, Math.min(rpm, this.maxRPM + 500));
    }

    /**
     * Shift up one gear
     */
    shiftUp() {
        if (this.gear < this.maxGears && !this.isShifting) {
            this.isShifting = true;
            const oldGear = this.gear;
            this.gear++;

            // RPM drop when shifting up
            this.rpm = this.rpm * 0.7;

            // Calculate shift quality
            this.evaluateShift(oldGear);

            // Shift takes time
            setTimeout(() => {
                this.isShifting = false;
            }, this.shiftTime * 1000);
        }
    }

    /**
     * Shift down one gear
     */
    shiftDown() {
        if (this.gear > 1 && !this.isShifting) {
            this.isShifting = true;
            this.gear--;

            // RPM increase when shifting down (but capped at maxRPM)
            this.rpm = Math.min(this.rpm * 1.4, this.maxRPM);

            setTimeout(() => {
                this.isShifting = false;
            }, this.shiftTime * 1000);
        }
    }

    /**
     * Evaluate shift quality and apply bonuses/penalties
     */
    evaluateShift(gearBeforeShift) {
        const rpmDiff = Math.abs(this.rpm / 0.7 - this.optimalShiftRPM); // Reverse the drop
        const { perfect, good } = GAME_CONFIG.shiftZones;
        const { bonuses, duration } = GAME_CONFIG.shiftZones;

        if (rpmDiff <= perfect) {
            // Perfect shift!
            this.shiftBonus = bonuses.perfect;
            this.shiftQuality = 'PERFECT';
        } else if (rpmDiff <= good) {
            // Good shift
            this.shiftBonus = bonuses.good;
            this.shiftQuality = 'GOOD';
        } else {
            // Bad shift
            this.shiftBonus = bonuses.bad;
            this.shiftQuality = 'BAD';
        }

        // Reset bonus after duration
        this.shiftBonusTimer = duration;
    }

    /**
     * Update car physics
     */
    update(deltaTime) {
        if (!this.hasStarted || this.hasFinished) return;

        // Update shift bonus timer
        if (this.shiftBonusTimer > 0) {
            this.shiftBonusTimer -= deltaTime * 1000;
            if (this.shiftBonusTimer <= 0) {
                this.shiftBonus = 1.0;
                this.shiftQuality = null;
            }
        }

        // Get current power from curve (en chevaux)
        let powerHP = this.getPowerAtRPM(this.rpm) * this.shiftBonus;

        // Conversion power to force: Power(HP) -> Power(Watts) -> Force(N)
        // 1 HP = 745.7 Watts
        // Power(W) = Force(N) * Velocity(m/s)
        // Force = Power / Velocity
        const powerWatts = powerHP * 745.7;
        const velocityMS = this.speed / 3.6; // km/h to m/s

        // Force disponible (éviter division par zéro)
        const wheelForce = velocityMS > 0.1 ? powerWatts / velocityMS : powerWatts * 10;

        // Accélération: F = m * a => a = F / m
        let acceleration = wheelForce / this.weight;

        // Résistances (air + friction)
        const airDrag = GAME_CONFIG.airResistance * this.speed * this.speed;
        const rollingDrag = GAME_CONFIG.rollingResistance * this.weight * 9.81;
        const totalDrag = airDrag + rollingDrag;

        // Accélération nette
        let netAcceleration = acceleration - totalDrag / this.weight;

        // Pénalité pendant le changement de vitesse
        if (this.isShifting) {
            netAcceleration *= 0.3;
        }

        // Rev limiter (coupe puissance si on tape le limiteur)
        if (this.rpm >= this.maxRPM) {
            netAcceleration *= 0.2;
        }

        // Update speed (m/s²)
        this.speed += netAcceleration * deltaTime * 3.6; // Convert acceleration to km/h
        this.speed = Math.max(0, this.speed);

        // Update RPM based on speed and gear
        this.rpm = this.calculateRPM(this.speed, this.gear);

        // Update position
        this.position += (this.speed / 3.6) * deltaTime; // Convert km/h to m/s

        // Update time
        this.time += deltaTime;

        // Check if finished
        if (this.position >= GAME_CONFIG.raceDistance) {
            this.hasFinished = true;
            this.position = GAME_CONFIG.raceDistance;
        }
    }

    /**
     * Start the race
     */
    start() {
        this.hasStarted = true;
    }

    /**
     * Penalize for early start
     */
    penalizeEarlyStart() {
        this.earlyStartPenalty = true;
        this.time += GAME_CONFIG.startSequence.earlyPenalty / 1000;
    }

    /**
     * Reset car to initial state
     */
    reset() {
        this.rpm = 1000;
        this.speed = 0;
        this.gear = 1;
        this.position = 0;
        this.time = 0;
        this.isShifting = false;
        this.shiftBonus = 1.0;
        this.shiftBonusTimer = 0;
        this.hasStarted = false;
        this.hasFinished = false;
        this.earlyStartPenalty = false;
        this.shiftQuality = null;
    }
}
