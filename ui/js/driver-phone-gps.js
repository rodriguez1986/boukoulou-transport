"use strict";

let driverPhoneGpsWatchId = null;
let driverPhoneGpsActive = false;
let driverPhoneGpsSending = false;
let driverPhoneGpsAbortController = null;
let driverPhoneGpsLastAttempt = 0;
let driverPhoneGpsSession = 0;
let driverPhoneGpsVehicleId = null;

function driverPhoneGpsSetStatus(message) {
  const element = document.getElementById("driverPhoneGpsStatus");
  if (element) element.textContent = message;
}

function driverPhoneGpsUpdateButtons() {
  const start = document.getElementById("driverPhoneGpsStartBtn");
  const stop = document.getElementById("driverPhoneGpsStopBtn");

  if (start) {
    start.disabled = driverPhoneGpsActive ||
      !driverPhoneGpsVehicleId ||
      currentUser?.role !== "DRIVER";
  }

  if (stop) {
    stop.disabled = !driverPhoneGpsActive;
  }
}

function driverPhoneGpsReady(vehicle) {
  driverPhoneGpsVehicleId = vehicle?.id ?? null;
  driverPhoneGpsUpdateButtons();
}

function driverPhoneGpsStop() {
  driverPhoneGpsSession++;
  driverPhoneGpsActive = false;

  if (driverPhoneGpsAbortController) {
    driverPhoneGpsAbortController.abort();
    driverPhoneGpsAbortController = null;
  }

  driverPhoneGpsSending = false;

  if (driverPhoneGpsWatchId !== null &&
      navigator.geolocation) {
    navigator.geolocation.clearWatch(driverPhoneGpsWatchId);
  }

  driverPhoneGpsWatchId = null;
  driverPhoneGpsVehicleId = null;
  driverPhoneGpsLastAttempt = 0;

  driverPhoneGpsSetStatus("Partage GPS arrêté.");
  driverPhoneGpsUpdateButtons();
}

function driverPhoneGpsStart() {
  if (driverPhoneGpsActive) return;

  if (
    currentUser?.role !== "DRIVER" ||
    !driverGpsVisible() ||
    !driverPhoneGpsVehicleId
  ) {
    driverPhoneGpsSetStatus(
      "Aucun véhicule autorisé pour le partage GPS."
    );
    return;
  }

  if (!window.isSecureContext) {
    driverPhoneGpsSetStatus(
      "Connexion HTTPS nécessaire pour utiliser le GPS."
    );
    return;
  }

  if (!navigator.geolocation) {
    driverPhoneGpsSetStatus(
      "Géolocalisation indisponible sur cet appareil."
    );
    return;
  }

  const vehicleId = driverPhoneGpsVehicleId;
  const session = ++driverPhoneGpsSession;

  driverPhoneGpsActive = true;
  driverPhoneGpsLastAttempt = 0;
  driverPhoneGpsUpdateButtons();

  driverPhoneGpsSetStatus(
    "Demande d'autorisation GPS en cours..."
  );

  try {
    driverPhoneGpsWatchId = navigator.geolocation.watchPosition(
      async (position) => {
        if (
          !driverPhoneGpsActive ||
          session !== driverPhoneGpsSession ||
          !driverGpsVisible() ||
          driverPhoneGpsVehicleId !== vehicleId
        ) {
          return;
        }

        const now = Date.now();

        if (
          driverPhoneGpsSending ||
          now - driverPhoneGpsLastAttempt < 5000
        ) {
          return;
        }

        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        if (
          !Number.isFinite(latitude) ||
          !Number.isFinite(longitude)
        ) {
          driverPhoneGpsSetStatus(
            "Coordonnées GPS invalides."
          );
          return;
        }

        driverPhoneGpsLastAttempt = now;
        driverPhoneGpsSending = true;
        const controller = new AbortController();
        driverPhoneGpsAbortController = controller;

        const speedMs = position.coords.speed;
        const speedKmh =
          Number.isFinite(speedMs) && speedMs >= 0
            ? speedMs * 3.6
            : 0;

        const payload = {
          latitude: latitude,
          longitude: longitude,
          speed: Math.round(speedKmh * 10) / 10,
          recorded_at: new Date(position.timestamp).toISOString()
        };

        try {
          await api(
            "/gps/v2/phone/" +
              encodeURIComponent(vehicleId) +
              "/positions",
            {
              method: "POST",
              body: JSON.stringify(payload),
              signal: controller.signal
            }
          );

          if (
            session !== driverPhoneGpsSession ||
            !driverPhoneGpsActive
          ) {
            return;
          }

          driverPhoneGpsSetStatus(
            "GPS actif : position transmise au serveur."
          );

          const last = document.getElementById(
            "driverPhoneGpsLastSent"
          );

          if (last) {
            last.textContent =
              "Dernière position envoyée : " +
              new Date().toLocaleString("fr-FR") +
              " | Latitude : " + latitude.toFixed(6) +
              " | Longitude : " + longitude.toFixed(6);
          }

        } catch (error) {
          if (session !== driverPhoneGpsSession) return;

          driverPhoneGpsSetStatus(
            "Échec de transmission GPS : " + error.message
          );

          if (
            /non affecté|non autorisé|forbidden|unauthorized/i
              .test(error.message)
          ) {
            driverPhoneGpsStop();
          }

        } finally {
          if (driverPhoneGpsAbortController === controller) {
            driverPhoneGpsAbortController = null;
            driverPhoneGpsSending = false;
          }
        }
      },

      (error) => {
        if (session !== driverPhoneGpsSession) return;

        const messages = {
          1: "Autorisation GPS refusée.",
          2: "Position GPS indisponible.",
          3: "Délai de localisation dépassé."
        };

        driverPhoneGpsSetStatus(
          messages[error.code] || "Erreur de géolocalisation."
        );

        if (error.code === 1) {
          driverPhoneGpsStop();
          driverPhoneGpsSetStatus(
            "Autorisation GPS refusée. Partage arrêté."
          );
        }
      },

      {
        enableHighAccuracy: true,
        maximumAge: 0,
        timeout: 15000
      }
    );

  } catch (error) {
    driverPhoneGpsStop();
    driverPhoneGpsSetStatus(
      "Impossible de démarrer le GPS : " + error.message
    );
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const start = document.getElementById(
    "driverPhoneGpsStartBtn"
  );

  const stop = document.getElementById(
    "driverPhoneGpsStopBtn"
  );

  if (start) {
    start.addEventListener("click", driverPhoneGpsStart);
  }

  if (stop) {
    stop.addEventListener("click", driverPhoneGpsStop);
  }

  driverPhoneGpsUpdateButtons();
});

window.addEventListener("pagehide", driverPhoneGpsStop);