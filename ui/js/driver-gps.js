let driverGpsMap = null;
let driverGpsMarker = null;
let driverGpsInterval = null;
let driverGpsGeneration = 0;
let driverGpsBusy = false;
let driverGpsVehicle = null;
let driverGpsCentered = false;

function driverGpsVisible() {
  const section = document.getElementById("driverView");

  return currentUser?.role === "DRIVER" &&
    section &&
    !section.classList.contains("hide");
}

function driverGpsStop() {
  driverGpsGeneration++;

  if (driverGpsInterval !== null) {
    clearInterval(driverGpsInterval);
    driverGpsInterval = null;
  }
}

async function driverGpsStart() {
  driverGpsStop();

  if (!driverGpsVisible()) return;

  const generation = driverGpsGeneration;
  const status = document.getElementById("driverGpsStatus");
  const details = document.getElementById("driverGpsDetails");

  if (typeof L === "undefined") {
    status.textContent = "Bibliothèque Leaflet indisponible.";
    return;
  }

  status.textContent = "Recherche du véhicule affecté...";
  details.textContent = "";
  driverGpsVehicle = null;

  if (driverGpsMarker && driverGpsMap) {
    driverGpsMap.removeLayer(driverGpsMarker);
    driverGpsMarker = null;
  }

  driverGpsCentered = false;

  try {
    const vehicles = await api("/gps/v2/phone/vehicles");

    if (generation !== driverGpsGeneration || !driverGpsVisible()) {
      return;
    }

    if (!Array.isArray(vehicles) || vehicles.length === 0) {
      status.textContent = "Aucun véhicule actuellement affecté.";
      return;
    }

    if (vehicles.length !== 1) {
      status.textContent =
        "Plusieurs véhicules affectés. Contactez l'exploitation.";
      return;
    }

    driverGpsVehicle = vehicles[0];

    if (!driverGpsMap) {
      driverGpsMap = L.map("driverGpsMap").setView(
        [-4.2634, 15.2429],
        12
      );

      L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
          maxZoom: 19,
          attribution: "OpenStreetMap contributors"
        }
      ).addTo(driverGpsMap);
    }

    setTimeout(() => {
      if (driverGpsVisible() && driverGpsMap) {
        driverGpsMap.invalidateSize();
      }
    }, 100);

    await driverGpsRefresh();

    if (generation !== driverGpsGeneration || !driverGpsVisible()) {
      return;
    }

    driverGpsInterval = setInterval(driverGpsRefresh, 5000);

  } catch (error) {
    if (generation === driverGpsGeneration && driverGpsVisible()) {
      status.textContent = "Erreur GPS : " + error.message;
    }
  }
}

async function driverGpsRefresh() {
  if (!driverGpsVisible() || !driverGpsVehicle || driverGpsBusy) {
    return;
  }

  const generation = driverGpsGeneration;
  const vehicle = driverGpsVehicle;

  driverGpsBusy = true;

  try {
    const position = await api(
      "/gps/v2/live/" +
      encodeURIComponent(vehicle.id) +
      "?mode=AUTO"
    );

    if (
      generation !== driverGpsGeneration ||
      !driverGpsVisible() ||
      driverGpsVehicle?.id !== vehicle.id
    ) {
      return;
    }

    const status = document.getElementById("driverGpsStatus");
    const details = document.getElementById("driverGpsDetails");

    const name = vehicle.code || ("Bus " + vehicle.id);

    if (
      position.status !== "ONLINE" ||
      position.latitude == null ||
      position.longitude == null
    ) {
      status.textContent = name + " : GPS hors ligne";
      details.textContent = "Aucune position disponible.";

      if (driverGpsMarker) {
        driverGpsMap.removeLayer(driverGpsMarker);
        driverGpsMarker = null;
      }

      driverGpsCentered = false;
      return;
    }

    const lat = Number(position.latitude);
    const lng = Number(position.longitude);

    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
      status.textContent = "Coordonnées GPS invalides.";
      return;
    }

    const coordinates = [lat, lng];

    if (!driverGpsMarker) {
      driverGpsMarker = L.marker(coordinates).addTo(driverGpsMap);
    } else {
      driverGpsMarker.setLatLng(coordinates);
    }

    driverGpsMarker.bindPopup(name);

    status.textContent = name + " : GPS en ligne";

    details.textContent =
      "Source : " + (position.source || "-") +
      " | Vitesse : " + (position.speed ?? "-") + " km/h" +
      " | Dernière position : " +
      (position.recorded_at
        ? new Date(position.recorded_at).toLocaleString("fr-FR")
        : "-");

    if (!driverGpsCentered) {
      driverGpsMap.invalidateSize();
      driverGpsMap.setView(coordinates, 15, { animate: false });
      driverGpsCentered = true;
    }

  } catch (error) {
    if (generation === driverGpsGeneration && driverGpsVisible()) {
      document.getElementById("driverGpsStatus").textContent =
        "Erreur GPS : " + error.message;
    }
  } finally {
    driverGpsBusy = false;
  }
}