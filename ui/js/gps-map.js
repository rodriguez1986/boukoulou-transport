let gpsMap = null;
let gpsMarkers = new Map();
let gpsInterval = null;
let gpsRequestActive = false;
let gpsGeneration = 0;
let gpsMapCentered = false;

let gpsLastCountry = null;
let gpsLastMode = null;
let gpsLastVisibleIds = "";

function gpsStop() {
  gpsGeneration++;

  if (gpsInterval !== null) {
    clearInterval(gpsInterval);
    gpsInterval = null;
  }
}

function gpsVisible() {
  const section = document.getElementById("gpsMap");

  return !!section &&
    !section.classList.contains("hide") &&
    currentUser?.role === "ADMIN";
}

function gpsStart() {
  gpsStop();

  if (!gpsVisible()) return;

  if (typeof L === "undefined") {
    document.getElementById("gpsStatus").textContent =
      "Bibliotheque Leaflet indisponible.";
    return;
  }

  if (!gpsMap) {
    gpsMap = L.map("gpsLeafletMap").setView(
      [-4.2634, 15.2429],
      12
    );

    L.tileLayer(
      "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
      {
        maxZoom: 19,
        attribution: "OpenStreetMap contributors"
      }
    ).addTo(gpsMap);
  }

  setTimeout(() => {
    if (gpsVisible() && gpsMap) {
      gpsMap.invalidateSize();
    }
  }, 100);

  gpsRefresh();
  if (typeof gpsHistoryInit === "function") {
  gpsHistoryInit();
}

if (typeof gpsHistoryLoadVehicles === "function") {
  gpsHistoryLoadVehicles();
}



  gpsInterval = setInterval(gpsRefresh, 5000);
}

function gpsClearMarkers() {
  for (const marker of gpsMarkers.values()) {
    if (gpsMap) {
      gpsMap.removeLayer(marker);
    }
  }

  gpsMarkers.clear();
  gpsMapCentered = false;
  gpsLastVisibleIds = "";
  gpsLastCountry = null;
  gpsLastMode = null;
}

function gpsFormatDate(value) {
  if (!value) return "-";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? "-"
    : date.toLocaleString("fr-FR");
}

function gpsDisplayVehicles(vehicles) {
  const container = document.getElementById("gpsVehicles");

  if (!container) return;

  container.replaceChildren();

  for (const vehicle of vehicles) {
    const item = document.createElement("div");
    item.className = "gps-vehicle-item";

    const title = document.createElement("strong");
    title.textContent =
      vehicle.code || ("Bus " + vehicle.vehicle_id);

    const details = document.createElement("div");

    details.textContent =
      "Pays : " + vehicle.country_id +
      " | Statut : " + vehicle.status +
      " | Source : " + (vehicle.source || "-") +
      " | Vitesse : " + (vehicle.speed ?? "-") + " km/h" +
      " | Derniere position : " +
      gpsFormatDate(vehicle.recorded_at);

    item.append(title, details);
    container.appendChild(item);
  }
}

function gpsFitVehicles(vehicles) {
  if (!gpsMap || !vehicles.length) return;

  const positions = vehicles.map(vehicle => [
    Number(vehicle.latitude),
    Number(vehicle.longitude)
  ]);

  gpsMap.invalidateSize();

  if (positions.length === 1) {
    gpsMap.setView(positions[0], 15, {
      animate: false
    });
  } else {
    const bounds = L.latLngBounds(positions);

    gpsMap.fitBounds(bounds.pad(0.25), {
      maxZoom: 15,
      padding: [35, 35],
      animate: false
    });
  }

  gpsMapCentered = true;
}

async function gpsRefresh() {
  if (!gpsVisible() || gpsRequestActive) return;

  const generation = gpsGeneration;
  gpsRequestActive = true;

  try {
    const modeElement = document.getElementById("gpsMode");
    const countryElement = document.getElementById("gpsCountry");

    if (!modeElement || !countryElement) return;

    const mode = modeElement.value;
    const country = countryElement.value;

    const result = await api(
      "/gps/v2/live/fleet?mode=" +
      encodeURIComponent(mode)
    );

    if (generation !== gpsGeneration || !gpsVisible()) {
      return;
    }

    // Ignorer une reponse si les filtres ont change
    // pendant la requete.
    if (
      modeElement.value !== mode ||
      countryElement.value !== country
    ) {
      return;
    }

    const vehicles = (result.vehicles || []).filter(vehicle =>
      country === "ALL" ||
      String(vehicle.country_id) === country
    );

    const online = vehicles.filter(vehicle =>
      vehicle.status === "ONLINE" &&
      vehicle.latitude != null &&
      vehicle.longitude != null &&
      Number.isFinite(Number(vehicle.latitude)) &&
      Number.isFinite(Number(vehicle.longitude))
    );

    document.getElementById("gpsTotal").textContent =
      String(vehicles.length);

    document.getElementById("gpsOnline").textContent =
      String(online.length);

    document.getElementById("gpsOffline").textContent =
      String(vehicles.length - online.length);

    document.getElementById("gpsStatus").textContent =
      "Supervision GPS active | Mode : " + mode;

    document.getElementById("gpsDetails").textContent =
      "Derniere actualisation : " +
      new Date().toLocaleTimeString("fr-FR");

    gpsDisplayVehicles(vehicles);

    const visibleIds = new Set();

    for (const vehicle of online) {
      const id = String(vehicle.vehicle_id);

      visibleIds.add(id);

      const position = [
        Number(vehicle.latitude),
        Number(vehicle.longitude)
      ];

      let marker = gpsMarkers.get(id);

      if (!marker) {
        marker = L.marker(position).addTo(gpsMap);
        gpsMarkers.set(id, marker);
      } else {
        marker.setLatLng(position);
      }

      const popup = document.createElement("div");

      const name = document.createElement("strong");
      name.textContent = vehicle.code || id;

      const info = document.createElement("p");

      info.textContent =
        "Source : " + (vehicle.source || "-") +
        " | Vitesse : " + (vehicle.speed ?? "-") +
        " km/h" +
        " | Position : " +
        gpsFormatDate(vehicle.recorded_at);

      popup.append(name, info);
      marker.bindPopup(popup);
    }

    for (const [id, marker] of gpsMarkers) {
      if (!visibleIds.has(id)) {
        gpsMap.removeLayer(marker);
        gpsMarkers.delete(id);
      }
    }

    const visibleIdsKey = [...visibleIds]
      .sort()
      .join(",");

    const filtersChanged =
      gpsLastCountry !== country ||
      gpsLastMode !== mode;

    const fleetChanged =
      gpsLastVisibleIds !== visibleIdsKey;

    // Recadrage uniquement :
    // - au premier chargement ;
    // - lors d'un changement de filtre ;
    // - lorsque la liste des bus ONLINE change.
    //
    // Un simple rafraichissement GPS ne modifie
    // donc pas le zoom choisi manuellement.
    const shouldFit =
      !gpsMapCentered ||
      filtersChanged ||
      fleetChanged;

    if (online.length && shouldFit) {
      gpsFitVehicles(online);
    }

    if (!online.length) {
      gpsMapCentered = false;
    }

    gpsLastCountry = country;
    gpsLastMode = mode;
    gpsLastVisibleIds = visibleIdsKey;

  } catch (error) {
    if (
      generation !== gpsGeneration ||
      !gpsVisible()
    ) {
      return;
    }

    document.getElementById("gpsStatus").textContent =
      "Erreur GPS : " + error.message;

    document.getElementById("gpsDetails").textContent = "";

  } finally {
    gpsRequestActive = false;
  }
}
