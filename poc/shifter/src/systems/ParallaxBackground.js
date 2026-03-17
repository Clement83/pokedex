/**
 * Système de parallax pour créer l'illusion de vitesse
 * Vue de côté : route qui défile de droite à gauche
 */
export class ParallaxBackground {
    constructor(scene, width, height) {
        this.scene = scene;
        this.width = width;
        this.height = height;
        this.layers = [];
        this.scrollSpeed = 0;
        this.frozen = false; // Pour figer le parallax

        this.createLayers();
    }

    createLayers() {
        // Montennes/horizon (très loin)
        this.createMountainLayer();

        // Arbres lointains
        this.createTreesLayer();

        // Route au sol
        this.createRoadLayer();

        // Lignes de route (proches)
        this.createRoadLinesLayer();
    }

    createMountainLayer() {
        const layer = {
            name: 'mountains',
            speed: 0.05,
            objects: [],
            container: this.scene.add.container(0, 0).setDepth(-100)
        };

        // Silhouettes de montagnes stylisées
        for (let i = 0; i < 10; i++) {
            const x = i * 300;
            const y = this.height * 0.3;
            const width = 200 + Math.random() * 100;
            const height = 60 + Math.random() * 40;

            const mountain = this.scene.add.triangle(
                x, y,
                0, height,
                width / 2, 0,
                width, height,
                0x4a5568,
                0.4
            ).setOrigin(0, 0);

            layer.objects.push(mountain);
            layer.container.add(mountain);
        }

        this.layers.push(layer);
    }

    createTreesLayer() {
        const layer = {
            name: 'trees',
            speed: 0.2,
            objects: [],
            container: this.scene.add.container(0, 0).setDepth(-50)
        };

        // Arbres simples (triangle + rectangle)
        for (let i = 0; i < 30; i++) {
            const x = i * 100 + Math.random() * 50;
            const y = this.height * 0.25;

            // Tronc
            const trunk = this.scene.add.rectangle(
                x, y,
                10, 40,
                0x8B4513,
                0.6
            ).setOrigin(0.5, 0);

            // Feuillage
            const foliage = this.scene.add.circle(
                x, y - 10,
                25,
                0x228B22,
                0.6
            );

            layer.objects.push(trunk, foliage);
            layer.container.add([trunk, foliage]);
        }

        this.layers.push(layer);
    }

    createRoadLayer() {
        const layer = {
            name: 'road',
            speed: 1.0,
            objects: [],
            container: this.scene.add.container(0, 0).setDepth(-20)
        };

        // Asphalte gris
        const roadHeight = this.height * 0.65;
        const roadY = this.height * 0.35;

        for (let i = 0; i < 50; i++) {
            const x = i * 200;

            const road = this.scene.add.rectangle(
                x, roadY,
                200, roadHeight,
                0x404040,
                1
            ).setOrigin(0, 0);

            layer.objects.push(road);
            layer.container.add(road);
        }

        // Bordures de route (bandes blanches en haut et bas)
        for (let i = 0; i < 50; i++) {
            const x = i * 200;

            const topBorder = this.scene.add.rectangle(
                x, roadY,
                200, 8,
                0xFFFFFF,
                0.8
            ).setOrigin(0, 0);

            const bottomBorder = this.scene.add.rectangle(
                x, roadY + roadHeight - 8,
                200, 8,
                0xFFFFFF,
                0.8
            ).setOrigin(0, 0);

            layer.objects.push(topBorder, bottomBorder);
            layer.container.add([topBorder, bottomBorder]);
        }

        this.layers.push(layer);
    }

    createRoadLinesLayer() {
        const layer = {
            name: 'roadLines',
            speed: 2.0,
            objects: [],
            container: this.scene.add.container(0, 0).setDepth(-10)
        };

        // Lignes blanches pointillées au centre de la route
        const lineY = this.height * 0.67;

        for (let i = 0; i < 100; i++) {
            const x = i * 80;

            const line = this.scene.add.rectangle(
                x, lineY,
                40, 4,
                0xFFFFFF,
                0.9
            ).setOrigin(0, 0.5);

            layer.objects.push(line);
            layer.container.add(line);
        }

        this.layers.push(layer);
    }

    update(speed) {
        // Si le parallax est figé, ne rien faire
        if (this.frozen) {
            return;
        }

        // speed est en km/h, on la convertit en pixels par frame
        const pixelSpeed = speed / 5;

        this.layers.forEach(layer => {
            const layerSpeed = pixelSpeed * layer.speed;

            // Déplacer tous les objets de cette couche vers la gauche
            layer.objects.forEach(obj => {
                obj.x -= layerSpeed;

                // Réinitialiser la position si l'objet est sorti de l'écran
                if (obj.x < -200) {
                    // Trouver l'objet le plus à droite de cette couche
                    const maxX = Math.max(...layer.objects.map(o => o.x));
                    obj.x = maxX + 200;
                }
            });
        });
    }

    freeze() {
        // Fige complètement le parallax
        this.frozen = true;
    }

    unfreeze() {
        // Relance le parallax
        this.frozen = false;
    }

    destroy() {
        this.layers.forEach(layer => {
            layer.container.destroy();
        });
        this.layers = [];
    }
}
