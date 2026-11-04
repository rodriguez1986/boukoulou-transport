(() => {
  "use strict";

  let map = null;
  let markerLayer = null;
  let activeLineId = null;
  let hasFittedBounds = false;

  const markers = new Map();

  const CITY_CENTERS = Object.freeze({
    1: { center: [-4.2634, 15.2429], zoom: 12 },
    2: { center: [0.3924, 9.4536], zoom: 12 }
  });

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

  function stop() {
    activeLineId = null;
    hasFittedBounds = false;

    clearMarkers();

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

    const city = CITY_CENTERS[Number(cityId)];

    if (city) {
      currentMap.setView(city.center, city.zoom);
    }

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
    showError
  };
})();
