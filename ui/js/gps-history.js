
"use strict";

// Historique GPS - Boukoulou Transport V5.9
// Carte independante du suivi GPS en temps reel.

let gpsHistoryMap = null;
let gpsHistoryLayer = null;
let gpsHistoryRequestId = 0;

function gpsHistoryStatus(message) {
  const element = document.getElementById("gpsHistoryStatus");
  if (element) element.textContent = message;
}

function gpsHistoryInit() {
  const container = document.getElementById("gpsHistoryMap");

  if (!container || typeof L === "undefined") {
    gpsHistoryStatus("Carte Leaflet indisponible.");
    return;
  }

  if (!gpsHistoryMap) {
    gpsHistoryMap = L.map(container).setView(
      [-4.2634, 15.2429],
      12
    );

    L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        maxZoom: 19,
        attribution: "OpenStreetMap contributors"
      }
    ).addTo(gpsHistoryMap);
  }

  setTimeout(() => {
    if (gpsHistoryMap) gpsHistoryMap.invalidateSize();
  }, 100);
}

function gpsHistoryClear() {
  gpsHistoryRequestId++;

  if (gpsHistoryMap && gpsHistoryLayer) {
    gpsHistoryMap.removeLayer(gpsHistoryLayer);
  }

  gpsHistoryLayer = null;

  const details = document.getElementById("gpsHistoryDetails");
  if (details) details.textContent = "";

  gpsHistoryStatus("Historique efface.");
}

function gpsHistoryDate(value) {
  if (!value) return "-";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? "-"
    : date.toLocaleString("fr-FR");
}

async function gpsHistoryLoadVehicles() {
  const select = document.getElementById("gpsHistoryVehicle");
  if (!select) return;

  try {
    const result = await api("/gps/v2/live/fleet?mode=AUTO");
    const vehicles = result.vehicles || [];
    const previous = select.value;

    select.replaceChildren();

    for (const vehicle of vehicles) {
      const option = document.createElement("option");
      option.value = String(vehicle.vehicle_id);
      option.textContent =
        vehicle.code || ("Bus " + vehicle.vehicle_id);

      select.appendChild(option);
    }

    if (vehicles.some(v => String(v.vehicle_id) === previous)) {
      select.value = previous;
    }

    if (!vehicles.length) {
      gpsHistoryStatus("Aucun vehicule disponible.");
    }
  } catch (error) {
    gpsHistoryStatus(
      "Erreur chargement vehicules : " + error.message
    );
  }
}

async function gpsHistoryShow() {
  const vehicle = document.getElementById("gpsHistoryVehicle");
  const source = document.getElementById("gpsHistorySource");
  const start = document.getElementById("gpsHistoryStart");
  const end = document.getElementById("gpsHistoryEnd");

  if (!vehicle || !source || !start || !end) return;

  if (!vehicle.value) {
    gpsHistoryStatus("Selectionne un vehicule.");
    return;
  }

  const requestId = ++gpsHistoryRequestId;

  gpsHistoryStatus("Chargement de l'historique...");

  try {
    const params = new URLSearchParams();
    params.set("limit", "2000");

    if (source.value !== "ALL") {
      params.set("source", source.value);
    }

    if (start.value) {
      params.set(
        "start",
        new Date(start.value).toISOString()
      );
    }

    if (end.value) {
      params.set(
        "end",
        new Date(end.value).toISOString()
      );
    }

    const result = await api(
      "/gps/v2/history/" +
      encodeURIComponent(vehicle.value) +
      "?" +
      params.toString()
    );

    if (requestId !== gpsHistoryRequestId) return;

    gpsHistoryInit();

    if (!gpsHistoryMap) return;

    if (gpsHistoryLayer) {
      gpsHistoryMap.removeLayer(gpsHistoryLayer);
      gpsHistoryLayer = null;
    }

    const positions = (result.positions || []).filter(p =>
      Number.isFinite(Number(p.latitude)) &&
      Number.isFinite(Number(p.longitude)) &&
      Number(p.latitude) >= -90 &&
      Number(p.latitude) <= 90 &&
      Number(p.longitude) >= -180 &&
      Number(p.longitude) <= 180
    );

    if (!positions.length) {
      gpsHistoryStatus("Aucune position sur cette periode.");
      return;
    }

    gpsHistoryLayer = L.layerGroup().addTo(gpsHistoryMap);

    const coordinates = positions.map(p => [
      Number(p.latitude),
      Number(p.longitude)
    ]);

    if (coordinates.length > 1) {
      L.polyline(coordinates, {
        color: "#2563eb",
        weight: 5,
        opacity: 0.85
      }).addTo(gpsHistoryLayer);
    }

    const first = positions[0];
    const last = positions[positions.length - 1];

    function addPoint(point, label, color) {
      const marker = L.circleMarker(
        [Number(point.latitude), Number(point.longitude)],
        {
          radius: 8,
          color: "#ffffff",
          weight: 2,
          fillColor: color,
          fillOpacity: 1
        }
      ).addTo(gpsHistoryLayer);

      const popup = document.createElement("div");
      const heading = document.createElement("strong");
      const info = document.createElement("p");

      heading.textContent = label;

      info.textContent =
        "Date : " + gpsHistoryDate(point.recorded_at) +
        " | Vitesse : " + point.speed + " km/h" +
        " | Source : " + point.source;

      popup.append(heading, info);
      marker.bindPopup(popup);
    }

    addPoint(first, "Depart", "#16a34a");

    if (positions.length > 1) {
      addPoint(last, "Arrivee", "#dc2626");
    }

    gpsHistoryMap.invalidateSize();

    if (coordinates.length === 1) {
      gpsHistoryMap.setView(coordinates[0], 16);
    } else {
      gpsHistoryMap.fitBounds(
        L.latLngBounds(coordinates).pad(0.15),
        { maxZoom: 16 }
      );
    }

    const details = document.getElementById("gpsHistoryDetails");

    if (details) {
      details.textContent =
        "Positions : " + result.returned +
        " / " + result.total +
        " | Debut : " + gpsHistoryDate(first.recorded_at) +
        " | Fin : " + gpsHistoryDate(last.recorded_at);
    }

    gpsHistoryStatus(
      result.truncated
        ? "Attention : trajet incomplet, limite de positions atteinte."
        : "Historique charge avec succes."
    );

  } catch (error) {
    if (requestId === gpsHistoryRequestId) {
      gpsHistoryStatus("Erreur historique : " + error.message);
    }
  }
}
