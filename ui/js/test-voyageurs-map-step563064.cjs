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
      className: "",
      children: [],
      appendChild(child) {
        this.children.push(child);
      }
    };
  }
  return elements[id];
}

const layers = new Set();
const markers = [];

const leaflet = {
  map() {
    return {
      setView(position, zoom) {
        this.center = position;
        this.zoom = zoom;
        return this;
      },
      fitBounds(bounds) {
        this.bounds = bounds;
        return this;
      },
      invalidateSize() {}
    };
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
      clearLayers() {
        layers.clear();
      },
      removeLayer(marker) {
        layers.delete(marker);
      }
    };
  },

  marker(position) {
    const marker = {
      position,
      setLatLng(next) {
        this.position = next;
      },
      addTo() {
        layers.add(this);
        return this;
      },
      bindPopup(popup) {
        this.popup = popup;
      }
    };

    markers.push(marker);
    return marker;
  }
};

const context = {
  window: { L: leaflet },
  document: {
    getElementById: element,
    createElement() {
      return {
        textContent: "",
        className: "",
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

const map = context.window.BoukoulouMap;

assert.ok(map, "Module cartographique introuvable");

console.log("\n=== TEST 1 : OUVERTURE DE LA CARTE ===");

map.start(1, "Mairie de Mfilou - Marche Total");

assert.equal(element("gps-section").hidden, false);

console.log("OK : carte ouverte");

console.log("\n=== TEST 2 : AFFICHAGE DE DEUX BUS ===");

map.update({
  line_id: 1,
  vehicles: [
    {
      vehicle_id: 1,
      code: "BUS-TEST-001",
      latitude: -4.30,
      longitude: 15.25
    },
    {
      vehicle_id: 2,
      code: "BUS-TEST-002",
      latitude: -4.31,
      longitude: 15.26
    }
  ]
});

assert.equal(layers.size, 2);

console.log("OK : deux marqueurs affiches");

console.log("\n=== TEST 3 : DEPLACEMENT D'UN BUS ===");

const firstMarker = markers[0];

map.update({
  line_id: 1,
  vehicles: [
    {
      vehicle_id: 1,
      code: "BUS-TEST-001",
      latitude: -4.32,
      longitude: 15.27
    }
  ]
});

assert.equal(layers.size, 1);
assert.equal(markers[0], firstMarker);
assert.equal(firstMarker.position[0], -4.32);
assert.equal(firstMarker.position[1], 15.27);

console.log("OK : position actualisee sans recreer le marqueur");

console.log("\n=== TEST 4 : SUPPRESSION DES BUS ABSENTS ===");

map.update({
  line_id: 1,
  vehicles: []
});

assert.equal(layers.size, 0);

console.log("OK : marqueurs obsoletes supprimes");

console.log("\n=== TEST 5 : ARRET DU SUIVI ===");

map.stop();

assert.equal(element("gps-section").hidden, true);
assert.equal(layers.size, 0);

console.log("OK : carte masquee et marqueurs nettoyes");

console.log("\nTOUS LES TESTS DE LA CARTE GPS ONT REUSSI");
