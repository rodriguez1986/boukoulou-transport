"use strict";

const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");

const source = fs.readFileSync(
  "/scripts/voyageurs-map.js",
  "utf8"
);

const elements = {};

function element(id) {
  if (!elements[id]) {
    elements[id] = {
      hidden: true,
      textContent: "",
      children: [],
      appendChild(child) {
        this.children.push(child);
      }
    };
  }

  return elements[id];
}

let leafletMap = null;

const leaflet = {
  map() {
    leafletMap = {
      center: null,
      zoom: null,
      setView(center, zoom) {
        this.center = Array.from(center);
        this.zoom = zoom;
        return this;
      },
      invalidateSize() {},
      fitBounds() {
        return this;
      }
    };

    return leafletMap;
  },

  tileLayer() {
    return {
      addTo() {
        return this;
      }
    };
  },

  layerGroup() {
    return {
      addTo() {
        return this;
      },
      clearLayers() {},
      removeLayer() {}
    };
  }
};

const context = {
  window: { L: leaflet },
  document: {
    getElementById: element,
    createElement() {
      return {
        textContent: "",
        children: [],
        appendChild(child) {
          this.children.push(child);
        }
      };
    }
  },
  Map,
  Set,
  console
};

vm.createContext(context);
vm.runInContext(source, context);

const gpsMap = context.window.BoukoulouMap;

assert.ok(gpsMap, "Module cartographique introuvable");

console.log("\n=== TEST 1 : CENTRAGE BRAZZAVILLE ===");

gpsMap.start(1, "Mairie de Mfilou - Marche Total", 1);

assert.deepEqual(
  leafletMap.center,
  [-4.2634, 15.2429]
);
assert.equal(leafletMap.zoom, 12);
assert.equal(element("gps-section").hidden, false);

console.log("OK : carte centree sur Brazzaville");

console.log("\n=== TEST 2 : CENTRAGE LIBREVILLE ===");

gpsMap.start(2, "IAI - Mont Bouet", 2);

assert.deepEqual(
  leafletMap.center,
  [0.3924, 9.4536]
);
assert.equal(leafletMap.zoom, 12);

console.log("OK : carte centree sur Libreville");

console.log("\n=== TEST 3 : RETOUR A BRAZZAVILLE ===");

gpsMap.start(1, "Mairie de Mfilou - Marche Total", 1);

assert.deepEqual(
  leafletMap.center,
  [-4.2634, 15.2429]
);
assert.equal(leafletMap.zoom, 12);

console.log("OK : changement de ville fonctionne");

console.log("\n=== TEST 4 : ABSENCE DE BUS GPS ===");

gpsMap.update({
  line_id: 1,
  vehicles: []
});

assert.deepEqual(
  leafletMap.center,
  [-4.2634, 15.2429]
);
assert.equal(leafletMap.zoom, 12);

console.log("OK : la carte reste sur Brazzaville");

console.log("\n=== TEST 5 : ARRET DU SUIVI ===");

gpsMap.stop();

assert.equal(element("gps-section").hidden, true);

console.log("OK : carte masquee");

console.log("\nTOUS LES TESTS DE CENTRAGE ONT REUSSI");
