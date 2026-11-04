"use strict";

const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");

const source = fs.readFileSync(
  "/scripts/voyageurs-gps.js",
  "utf8"
);

const requests = [];
const timers = new Map();
const updates = [];
const errors = [];

let nextTimerId = 1;

const context = {
  window: {},
  AbortController,
  console,

  setTimeout(callback, delay) {
    const id = nextTimerId++;
    timers.set(id, { callback, delay });
    return id;
  },

  clearTimeout(id) {
    timers.delete(id);
  },

  async fetch(url, options) {
    requests.push({ url, options });

    return {
      ok: true,
      async json() {
        return {
          line_id: 1,
          line_code: "TEST-BZV-PNR",
          line_name: "Mairie de Mfilou-Marche Total",
          refresh_seconds: 5,
          vehicles: [
            {
              vehicle_id: 1,
              code: "BUS-TEST-001",
              latitude: -4.3,
              longitude: 15.25,
              recorded_at: new Date().toISOString()
            }
          ]
        };
      }
    };
  }
};

vm.createContext(context);
vm.runInContext(source, context);

const gps = context.window.BoukoulouGPS;

assert.ok(gps, "Module GPS introuvable");

async function main() {
  console.log("\n=== TEST 1 : DEMARRAGE GPS ===");

  gps.start(
    1,
    data => updates.push(data),
    error => errors.push(error)
  );

  await new Promise(resolve => setImmediate(resolve));

  assert.equal(gps.getActiveLineId(), 1);
  assert.equal(requests.length, 1);

  assert.equal(
    requests[0].url,
    "/urban/public/lines/1/vehicles"
  );

  assert.equal(requests[0].options.credentials, "omit");
  assert.equal(requests[0].options.cache, "no-store");

  console.log("OK : endpoint GPS public utilise");

  console.log("\n=== TEST 2 : RECEPTION DES VEHICULES ===");

  assert.equal(updates.length, 1);
  assert.equal(updates[0].vehicles.length, 1);
  assert.equal(
    updates[0].vehicles[0].code,
    "BUS-TEST-001"
  );

  console.log("OK : bus recu depuis l'API simulee");

  console.log("\n=== TEST 3 : ACTUALISATION AUTOMATIQUE ===");

  assert.equal(timers.size, 1);

  const timer = [...timers.values()][0];

  assert.equal(timer.delay, 5000);

  console.log("OK : actualisation programmee a 5000 ms");

  console.log("\n=== TEST 4 : ARRET GPS ===");

  gps.stop();

  assert.equal(gps.getActiveLineId(), null);
  assert.equal(timers.size, 0);
  assert.equal(errors.length, 0);

  console.log("OK : suivi GPS arrete");

  console.log("\nTOUS LES TESTS GPS FRONTEND ONT REUSSI");
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
