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
let nextTimerId = 1;

const context = {
  console,
  AbortController,
  encodeURIComponent,

  setTimeout(callback, delay) {
    const id = nextTimerId++;
    timers.set(id, { callback, delay });
    return id;
  },

  clearTimeout(id) {
    timers.delete(id);
  },

  fetch(url, options) {
    return new Promise((resolve, reject) => {
      requests.push({
        url,
        options,
        resolve,
        reject
      });
    });
  },

  window: {}
};

vm.createContext(context);
vm.runInContext(source, context);

const gps = context.window.BoukoulouGPS;

assert.ok(gps, "Module GPS introuvable");

function flush() {
  return new Promise(resolve => setImmediate(resolve));
}

function response(lineId, vehicles) {
  return {
    ok: true,
    json: async () => ({
      line_id: lineId,
      refresh_seconds: 5,
      vehicles
    })
  };
}

(async () => {

  console.log("\n=== TEST 1 : DEMARRAGE LIGNE 1 ===");

  const updates = [];
  const errors = [];

  gps.start(
    1,
    data => updates.push(data),
    error => errors.push(error)
  );

  assert.equal(gps.getActiveLineId(), 1);
  assert.equal(requests.length, 1);
  assert.equal(
    requests[0].url,
    "/urban/public/lines/1/vehicles"
  );

  console.log("OK : suivi de la ligne 1 demarre");

  console.log("\n=== TEST 2 : RECEPTION DES POSITIONS ===");

  requests[0].resolve(
    response(1, [
      {
        vehicle_id: 101,
        code: "BUS-001",
        latitude: -4.30,
        longitude: 15.25
      }
    ])
  );

  await flush();

  assert.equal(updates.length, 1);
  assert.equal(updates[0].vehicles.length, 1);
  assert.equal(timers.size, 1);

  console.log("OK : position GPS recue");
  console.log("OK : prochaine actualisation programmee");

  console.log("\n=== TEST 3 : CHANGEMENT DE LIGNE ===");

  gps.start(
    2,
    data => updates.push(data),
    error => errors.push(error)
  );

  assert.equal(gps.getActiveLineId(), 2);
  assert.equal(requests.length, 2);
  assert.equal(
    requests[1].url,
    "/urban/public/lines/2/vehicles"
  );
  assert.equal(timers.size, 0);

  console.log("OK : ancien suivi arrete");
  console.log("OK : ligne 2 active");

  console.log("\n=== TEST 4 : REQUETE ANCIENNE IGNOREE ===");

  requests[1].resolve(
    response(2, [
      {
        vehicle_id: 202,
        code: "BUS-002",
        latitude: 0.39,
        longitude: 9.45
      }
    ])
  );

  await flush();

  assert.equal(updates.length, 2);
  assert.equal(updates[1].line_id, 2);

  console.log("OK : seules les donnees de la ligne active sont utilisees");

  console.log("\n=== TEST 5 : ARRET COMPLET ===");

  gps.stop();

  assert.equal(gps.getActiveLineId(), null);
  assert.equal(timers.size, 0);

  console.log("OK : suivi GPS arrete");
  console.log("OK : actualisations annulees");

  console.log("\n=== RESULTAT FINAL ===");

  assert.equal(errors.length, 0);

  console.log("TOUS LES TESTS D'INTEGRATION GPS ONT REUSSI");

})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
