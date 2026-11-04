(() => {
  "use strict";

  let map = null;
  let markerLayer = null;
  let stopLayer = null;
  let stopPositions = [];
  let activeLineId = null;
  let hasFittedBounds = false;

  const markers = new Map();


  function getElements() {
    return {
      section: document.getElementById("gps-section"),
      container: document.getElementById("gps-map"),
      status: document.getElementById("gps-status"),
      lineName: document.getElementById("gps-line-name")
    };
  }

  function setStatus(message) {
    const { status } = getElements();

    if (status) {
      status.textContent = message;
    }
  }

  function ensureMap() {
    if (map) {
      return map;
    }

    if (!window.L) {
      throw new Error("Bibliotheque Leaflet indisponible.");
    }

    const { container } = getElements();

    if (!container) {
      throw new Error("Conteneur de carte GPS introuvable.");
    }

    map = window.L.map(container, {
      scrollWheelZoom: false
    });

    window.L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
      }
    ).addTo(map);

    markerLayer = window.L.layerGroup().addTo(map);
    stopLayer = window.L.layerGroup().addTo(map);

    map.setView([0, 15], 3);

    return map;
  }

  function validCoordinate(latitude, longitude) {
    return (
      Number.isFinite(latitude) &&
      Number.isFinite(longitude) &&
      latitude >= -90 &&
      latitude <= 90 &&
      longitude >= -180 &&
      longitude <= 180
    );
  }

  function clearMarkers() {
    if (markerLayer) {
      markerLayer.clearLayers();
    }

    markers.clear();
  }

  function clearStopMarkers() {
    stopPositions = [];

    if (stopLayer) {
      stopLayer.clearLayers();
    }
  }

  function createStopMarker(stop, label, color) {
    if (!stop ||
        stop.latitude == null ||
        stop.longitude == null) {
      return null;
    }

    const latitude = Number(stop.latitude);
    const longitude = Number(stop.longitude);

    if (!validCoordinate(latitude, longitude)) {
      return null;
    }

    const marker = window.L.circleMarker(
      [latitude, longitude],
      {
        radius: 9,
        color: "#ffffff",
        weight: 2,
        fillColor: color,
        fillOpacity: 1
      }
    );

    const popup = document.createElement("div");

    const title = document.createElement("strong");
    title.textContent = label;

    const name = document.createElement("div");
    name.textContent = String(stop.name || "Arret");

    popup.appendChild(title);
    popup.appendChild(name);

    marker.bindPopup(popup);
    marker.addTo(stopLayer);

    stopPositions.push([latitude, longitude]);

    return marker;
  }

  function setStops(departure, arrival) {
    ensureMap();
    clearStopMarkers();
    hasFittedBounds = false;

    createStopMarker(
      departure,
      "Depart",
      "#15803d"
    );

    createStopMarker(
      arrival,
      "Arrivee",
      "#dc2626"
    );

    if (stopPositions.length === 2) {
      map.fitBounds(stopPositions, {
        padding: [50, 50],
        maxZoom: 15
      });
      hasFittedBounds = true;
    } else if (stopPositions.length === 1) {
      map.setView(stopPositions[0], 14);
      hasFittedBounds = true;
    }
  }

  function stop() {
    activeLineId = null;
    hasFittedBounds = false;

    clearMarkers();
    clearStopMarkers();

    const { section, lineName } = getElements();

    if (section) {
      section.hidden = true;
    }

    if (lineName) {
      lineName.textContent = "";
    }

    setStatus("");
  }

  function start(lineId, lineName, cityId) {
    if (!Number.isSafeInteger(Number(lineId)) ||
        Number(lineId) <= 0) {
      throw new Error("Identifiant de ligne invalide.");
    }

    stop();

    activeLineId = Number(lineId);

    const elements = getElements();

    if (!elements.section) {
      throw new Error("Section GPS introuvable.");
    }

    elements.section.hidden = false;

    if (elements.lineName) {
      elements.lineName.textContent = String(lineName || "");
    }

    setStatus("Recherche des bus en circulation...");

    const currentMap = ensureMap();

    // Centrage independant des identifiants des villes.
    currentMap.setView([0, 15], 3);

    currentMap.invalidateSize();
  }

  function update(data) {
    if (!data || Number(data.line_id) !== activeLineId) {
      return;
    }

    if (!Array.isArray(data.vehicles)) {
      setStatus("Reponse GPS invalide.");
      clearMarkers();
      return;
    }

    ensureMap();

    const currentIds = new Set();
    const positions = [];

    for (const vehicle of data.vehicles) {
      const id = Number(vehicle.vehicle_id);
      const latitude = Number(vehicle.latitude);
      const longitude = Number(vehicle.longitude);

      if (!Number.isSafeInteger(id) || id <= 0 ||
          vehicle.latitude == null ||
          vehicle.longitude == null ||
          !validCoordinate(latitude, longitude)) {
        continue;
      }

      currentIds.add(id);
      positions.push([latitude, longitude]);

      const code = String(vehicle.code || `Bus ${id}`);

      let marker = markers.get(id);

      if (marker) {
        marker.setLatLng([latitude, longitude]);
      } else {
        marker = window.L.marker([latitude, longitude]);
        marker.addTo(markerLayer);
        markers.set(id, marker);
      }

      const popup = document.createElement("div");
      popup.className = "gps-bus-popup";

      const title = document.createElement("strong");
      title.textContent = code;

      const description = document.createElement("span");
      description.textContent = "Bus en circulation";

      popup.appendChild(title);
      popup.appendChild(description);

      marker.bindPopup(popup);
    }

    for (const [id, marker] of markers) {
      if (!currentIds.has(id)) {
        markerLayer.removeLayer(marker);
        markers.delete(id);
      }
    }

    if (positions.length === 0) {
      setStatus(
        "Aucun bus avec une position GPS recente sur cette ligne."
      );
      return;
    }

    setStatus(
      positions.length +
      " bus localise(s). Actualisation automatique."
    );

    if (!hasFittedBounds) {
      if (positions.length === 1) {
        map.setView(positions[0], 14);
      } else {
        map.fitBounds(positions, {
          padding: [40, 40],
          maxZoom: 15
        });
      }

      hasFittedBounds = true;
    }
  }

  function showError(message) {
    clearMarkers();

    setStatus(
      message || "Impossible de recuperer les positions GPS."
    );
  }

  window.BoukoulouMap = {
    start,
    update,
    stop,
    showError,
    setStops
  };
})();
