
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
  gpsPlaybackReset();

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
  gpsPlaybackReset();

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
    gpsPlaybackLoad(positions);

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

/* ==========================================
   LECTURE ANIMEE DES TRAJETS GPS
   Boukoulou Transport V5.9
   ========================================== */

let gpsPlaybackPositions = [];
let gpsPlaybackIndex = 0;
let gpsPlaybackTimer = null;
let gpsPlaybackMarker = null;
let gpsPlaybackRunning = false;

function gpsPlaybackStop() {
  if (gpsPlaybackTimer !== null) {
    clearInterval(gpsPlaybackTimer);
    gpsPlaybackTimer = null;
  }

  gpsPlaybackRunning = false;

  const button = document.getElementById("gpsPlaybackPlay");

  if (button) {
    button.textContent = "▶ Lecture";
  }
}

function gpsPlaybackReset() {
  gpsPlaybackStop();

  gpsPlaybackPositions = [];
  gpsPlaybackIndex = 0;

  if (gpsHistoryMap && gpsPlaybackMarker) {
    gpsHistoryMap.removeLayer(gpsPlaybackMarker);
  }

  gpsPlaybackMarker = null;

  const slider = document.getElementById("gpsPlaybackSlider");
  const play = document.getElementById("gpsPlaybackPlay");
  const restart = document.getElementById("gpsPlaybackRestart");
  const info = document.getElementById("gpsPlaybackInfo");

  if (slider) {
    slider.min = "0";
    slider.max = "0";
    slider.value = "0";
    slider.disabled = true;
  }

  if (play) play.disabled = true;
  if (restart) restart.disabled = true;

  if (info) {
    info.textContent = "Chargez un trajet pour activer la lecture.";
  }
}

function gpsPlaybackLoad(positions) {
  gpsPlaybackReset();

  if (!Array.isArray(positions) || positions.length === 0) {
    return;
  }

  gpsPlaybackPositions = positions;
  gpsPlaybackIndex = 0;

  const slider = document.getElementById("gpsPlaybackSlider");
  const play = document.getElementById("gpsPlaybackPlay");
  const restart = document.getElementById("gpsPlaybackRestart");

  if (slider) {
    slider.min = "0";
    slider.max = String(positions.length - 1);
    slider.value = "0";
    slider.disabled = positions.length < 2;
  }

  if (play) play.disabled = positions.length < 2;
  if (restart) restart.disabled = false;

  gpsPlaybackRender(0);
}

function gpsPlaybackRender(index) {
  if (!gpsHistoryMap || !gpsPlaybackPositions.length) return;

  const safeIndex = Math.max(
    0,
    Math.min(
      Number(index) || 0,
      gpsPlaybackPositions.length - 1
    )
  );

  gpsPlaybackIndex = safeIndex;

  const point = gpsPlaybackPositions[safeIndex];

  const position = [
    Number(point.latitude),
    Number(point.longitude)
  ];

  if (!gpsPlaybackMarker) {
    gpsPlaybackMarker = L.circleMarker(position, {
      radius: 10,
      color: "#ffffff",
      weight: 3,
      fillColor: "#f59e0b",
      fillOpacity: 1
    }).addTo(gpsHistoryMap);
  } else {
    gpsPlaybackMarker.setLatLng(position);
  }

  const slider = document.getElementById("gpsPlaybackSlider");

  if (slider) {
    slider.value = String(safeIndex);
  }

  const info = document.getElementById("gpsPlaybackInfo");

  if (info) {
    info.textContent =
      "Position " + (safeIndex + 1) +
      " / " + gpsPlaybackPositions.length +
      " | Heure : " + gpsHistoryDate(point.recorded_at) +
      " | Vitesse : " + (point.speed ?? "-") + " km/h" +
      " | Source : " + (point.source || "-");
  }
}

function gpsPlaybackSeek(value) {
  gpsPlaybackStop();
  gpsPlaybackRender(value);
}

function gpsPlaybackRestart() {
  gpsPlaybackStop();
  gpsPlaybackRender(0);
}

function gpsPlaybackToggle() {
  if (gpsPlaybackRunning) {
    gpsPlaybackStop();
    return;
  }

  if (gpsPlaybackPositions.length < 2) return;

  if (gpsPlaybackIndex >= gpsPlaybackPositions.length - 1) {
    gpsPlaybackRender(0);
  }

  const speedElement = document.getElementById("gpsPlaybackSpeed");

  const speed = Number(speedElement?.value || 1);

  const delay = Math.max(
    50,
    Math.round(1000 / (Number.isFinite(speed) && speed > 0 ? speed : 1))
  );

  gpsPlaybackRunning = true;

  const button = document.getElementById("gpsPlaybackPlay");

  if (button) {
    button.textContent = "⏸ Pause";
  }

  gpsPlaybackTimer = setInterval(() => {
    if (gpsPlaybackIndex >= gpsPlaybackPositions.length - 1) {
      gpsPlaybackStop();
      return;
    }

    gpsPlaybackRender(gpsPlaybackIndex + 1);

    if (gpsPlaybackIndex >= gpsPlaybackPositions.length - 1) {
      gpsPlaybackStop();
    }
  }, delay);
}
