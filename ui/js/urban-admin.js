"use strict";

/*
 * Boukoulou Transport V5.9
 * Administration dynamique des villes et des arrêts.
 * Réservé aux administrateurs.
 */

function urbanSelectOptions(selectId, rows, placeholder) {
  const element = document.getElementById(selectId);
  if (!element) return;

  const previous = element.value;

  element.innerHTML =
    `<option value="">${esc(placeholder)}</option>` +
    rows.map(item =>
      `<option value="${Number(item.id)}">${esc(item.name)}</option>`
    ).join("");

  if (rows.some(item => String(item.id) === previous)) {
    element.value = previous;
  }
}

function updateUrbanStopCities() {
  const countryId = Number($("#urbanStopCountry").value);

  const cities = (cache.cities || []).filter(
    city => Number(city.country_id) === countryId
  );

  urbanSelectOptions(
    "urbanStopCity",
    cities,
    "Sélectionner une ville"
  );
}

function updateUrbanStopsCities() {
  const countryId = Number($("#urbanStopsCountry").value);

  const cities = (cache.cities || []).filter(
    city => Number(city.country_id) === countryId
  );

  urbanSelectOptions(
    "urbanStopsCity",
    cities,
    "Sélectionner une ville"
  );

  loadUrbanStops();
}

function refreshUrbanAdmin() {
  if (currentUser?.role !== "ADMIN") return;

  const countries = cache.countries || [];

  urbanSelectOptions(
    "urbanCityCountry",
    countries,
    "Sélectionner un pays"
  );

  urbanSelectOptions(
    "urbanStopCountry",
    countries,
    "Sélectionner un pays"
  );

  urbanSelectOptions(
    "urbanStopsCountry",
    countries,
    "Sélectionner un pays"
  );

  updateUrbanStopCities();
  updateUrbanStopsCities();
}

async function addUrbanCity() {
  if (currentUser?.role !== "ADMIN") return;

  const countryId = Number($("#urbanCityCountry").value);
  const name = $("#urbanCityName").value.trim();

  if (!countryId || !name) {
    alert("Sélectionnez un pays et indiquez le nom de la ville.");
    return;
  }

  try {
    await api("/cities", {
      method: "POST",
      body: JSON.stringify({
        country_id: countryId,
        name: name
      })
    });

    $("#urbanCityName").value = "";

    await load();

    refreshUrbanAdmin();

    alert("Ville enregistrée avec succès.");
  } catch (error) {
    alert("Impossible d'enregistrer la ville : " + error.message);
  }
}

async function addUrbanStop() {
  if (currentUser?.role !== "ADMIN") return;

  const cityId = Number($("#urbanStopCity").value);
  const name = $("#urbanStopName").value.trim();

  const latText = $("#urbanStopLatitude").value.trim();
  const lonText = $("#urbanStopLongitude").value.trim();

  if (!cityId || !name) {
    alert("Sélectionnez une ville et indiquez le nom de l'arrêt.");
    return;
  }

  if ((latText === "") !== (lonText === "")) {
    alert("Renseignez les deux coordonnées GPS ou laissez les deux vides.");
    return;
  }

  const latitude = latText === "" ? null : Number(latText);
  const longitude = lonText === "" ? null : Number(lonText);

  if (
    (latitude !== null &&
      (!Number.isFinite(latitude) || latitude < -90 || latitude > 90)) ||
    (longitude !== null &&
      (!Number.isFinite(longitude) || longitude < -180 || longitude > 180))
  ) {
    alert("Les coordonnées GPS sont invalides.");
    return;
  }

  try {
    await api("/stops", {
      method: "POST",
      body: JSON.stringify({
        city_id: cityId,
        name: name,
        latitude: latitude,
        longitude: longitude
      })
    });

    $("#urbanStopName").value = "";
    $("#urbanStopLatitude").value = "";
    $("#urbanStopLongitude").value = "";

    if ($("#urbanStopsCity").value === String(cityId)) {
      await loadUrbanStops();
    }

    alert("Arrêt enregistré avec succès.");
  } catch (error) {
    alert("Impossible d'enregistrer l'arrêt : " + error.message);
  }
}

async function loadUrbanStops() {
  const container = $("#urbanStopsList");

  if (!container || currentUser?.role !== "ADMIN") return;

  const cityId = Number($("#urbanStopsCity").value);

  if (!cityId) {
    container.textContent = "Sélectionnez une ville.";
    return;
  }

  container.textContent = "Chargement des arrêts...";

  try {
    const stops = await api(
      `/stops?city_id=${encodeURIComponent(cityId)}`
    );

    if (!Array.isArray(stops)) {
      throw new Error("Réponse API inattendue.");
    }

    if (Number($("#urbanStopsCity").value) !== cityId) return;

    if (stops.length === 0) {
      container.textContent = "Aucun arrêt enregistré pour cette ville.";
      return;
    }

    const ordered = [...stops].sort(
      (a, b) => String(a.name).localeCompare(
        String(b.name),
        "fr"
      )
    );

    container.innerHTML = table(
      ["ID", "Arrêt", "Latitude", "Longitude"],
      ordered.map(stop => `
        <tr>
          <td>${Number(stop.id)}</td>
          <td>${esc(stop.name)}</td>
          <td>${stop.latitude == null ? "—" : Number(stop.latitude)}</td>
          <td>${stop.longitude == null ? "—" : Number(stop.longitude)}</td>
        </tr>
      `)
    );
  } catch (error) {
    if (Number($("#urbanStopsCity").value) !== cityId) return;
    container.textContent = "Erreur : " + error.message;
  }
}

/*
 * Intégration sans modification de app.js.
 * Le chargement initial de l'administrateur est déjà assuré
 * par show() puis load().
 */
const originalUrbanLoad = load;

load = async function (...args) {
  const result = await originalUrbanLoad(...args);

  if (currentUser?.role === "ADMIN") {
    refreshUrbanAdmin();
  }

  return result;
};


// ============================================================
// 56.30.74.13 - Gestion des itineraires urbains
// ============================================================

let urbanRouteStopsCache = [];
let urbanRouteLoading = false;
let urbanRouteSaving = false;
let urbanRouteRequestId = 0;

function refreshUrbanRouteLines() {
    if (currentUser?.role !== "ADMIN") return;

    const select = document.getElementById("urbanRouteLine");
    if (!select) return;

    const previous = select.value;

    const lines = (cache.lines || [])
        .filter(line => Number(line.city_id) > 0)
        .sort((a, b) =>
            String(a.name).localeCompare(String(b.name), "fr")
        );

    select.innerHTML =
        '<option value="">Sélectionner une ligne</option>' +
        lines.map(line => {
            const city = (cache.cities || []).find(
                item => Number(item.id) === Number(line.city_id)
            );

            const label =
                `${line.code} - ${line.name}` +
                ` (${city?.name || "Ville inconnue"})`;

            return `<option value="${Number(line.id)}">` +
                `${esc(label)}</option>`;
        }).join("");

    if (lines.some(line => String(line.id) === previous)) {
        select.value = previous;
    }

    loadUrbanLineStops();
}

async function loadUrbanLineStops() {
    if (currentUser?.role !== "ADMIN") return;

    const select = document.getElementById("urbanRouteLine");
    const info = document.getElementById("urbanRouteInfo");
    const container = document.getElementById("urbanRouteStops");
    const available = document.getElementById(
        "urbanRouteAvailableStop"
    );
    const message = document.getElementById("urbanRouteMessage");

    if (!select || !info || !container || !available) return;

    const requestId = ++urbanRouteRequestId;
    const lineId = Number(select.value);

    urbanRouteStopsCache = [];
    available.innerHTML =
        '<option value="">Sélectionner un arrêt</option>';

    if (!lineId) {
        info.textContent =
            "Sélectionnez une ligne pour afficher son itinéraire.";
        container.textContent = "";
        if (message) message.textContent = "";
        return;
    }

    const line = (cache.lines || []).find(
        item => Number(item.id) === lineId
    );

    if (!line || !Number(line.city_id)) {
        info.textContent = "Ligne urbaine introuvable.";
        container.textContent = "";
        return;
    }

    const city = (cache.cities || []).find(
        item => Number(item.id) === Number(line.city_id)
    );

    info.textContent =
        `Ligne : ${line.code} — ${line.name} | ` +
        `Ville : ${city?.name || "Inconnue"}`;

    container.textContent = "Chargement de l'itinéraire...";

    try {
        const [associations, cityStops] = await Promise.all([
            api(`/lines/${lineId}/stops`),
            api(`/stops?city_id=${encodeURIComponent(line.city_id)}`)
        ]);

        if (
            requestId !== urbanRouteRequestId ||
            Number(select.value) !== lineId
        ) return;

        if (
            !Array.isArray(associations) ||
            !Array.isArray(cityStops)
        ) {
            throw new Error("Réponse API inattendue.");
        }

        const ordered = [...associations].sort(
            (a, b) =>
                Number(a.stop_order) - Number(b.stop_order)
        );

        urbanRouteStopsCache = ordered;

        if (ordered.length === 0) {
            container.textContent =
                "Aucun arrêt associé à cette ligne.";
        } else {
            container.innerHTML = table(
                ["Ordre", "Arrêt", "Latitude", "Longitude"],
                ordered.map(stop => `
                    <tr>
                        <td>${Number(stop.stop_order)}</td>
                        <td>${esc(stop.name)}</td>
                        <td>${stop.latitude == null
                            ? "—"
                            : Number(stop.latitude)}</td>
                        <td>${stop.longitude == null
                            ? "—"
                            : Number(stop.longitude)}</td>
                    </tr>
                `)
            );
        }

        const usedIds = new Set(
            ordered.map(stop => Number(stop.stop_id))
        );

        const remaining = cityStops
            .filter(stop =>
                Number(stop.city_id) === Number(line.city_id) &&
                !usedIds.has(Number(stop.id))
            )
            .sort((a, b) =>
                String(a.name).localeCompare(String(b.name), "fr")
            );

        available.innerHTML =
            '<option value="">Sélectionner un arrêt</option>' +
            remaining.map(stop =>
                `<option value="${Number(stop.id)}">` +
                `${esc(stop.name)}</option>`
            ).join("");

        if (message) {
            message.textContent = remaining.length
                ? `${remaining.length} arrêt(s) disponible(s).`
                : "Tous les arrêts de cette ville sont déjà associés.";
        }

    } catch (error) {
        if (
            requestId !== urbanRouteRequestId ||
            Number(select.value) !== lineId
        ) return;

        container.textContent =
            "Erreur de chargement : " + error.message;
        if (message) message.textContent = "";
    }
}

async function addUrbanLineStop() {
    if (currentUser?.role !== "ADMIN") return;
    if (urbanRouteSaving) return;

    const lineSelect = document.getElementById("urbanRouteLine");
    const stopSelect = document.getElementById(
        "urbanRouteAvailableStop"
    );
    const message = document.getElementById("urbanRouteMessage");

    if (!lineSelect || !stopSelect) return;

    const lineId = Number(lineSelect.value);
    const stopId = Number(stopSelect.value);

    if (!lineId || !stopId) {
        alert("Sélectionnez une ligne et un arrêt disponible.");
        return;
    }

    const line = (cache.lines || []).find(
        item => Number(item.id) === lineId
    );

    if (!line || !Number(line.city_id)) {
        alert("Cette ligne n'est pas associée à une ville.");
        return;
    }

    urbanRouteSaving = true;

    try {
        // Relire les donnees pour eviter un ordre obsolete.
        const [associations, cityStops] = await Promise.all([
            api(`/lines/${lineId}/stops`),
            api(`/stops?city_id=${encodeURIComponent(line.city_id)}`)
        ]);

        if (
            !Array.isArray(associations) ||
            !Array.isArray(cityStops)
        ) {
            throw new Error("Réponse API inattendue.");
        }

        if (Number(lineSelect.value) !== lineId) {
            throw new Error("La ligne sélectionnée a changé.");
        }

        const selectedStop = cityStops.find(
            stop => Number(stop.id) === stopId
        );

        if (
            !selectedStop ||
            Number(selectedStop.city_id) !== Number(line.city_id)
        ) {
            throw new Error(
                "L'arrêt n'appartient pas à la ville de la ligne."
            );
        }

        if (associations.some(
            item => Number(item.stop_id) === stopId
        )) {
            throw new Error(
                "Cet arrêt est déjà associé à cette ligne."
            );
        }

        const nextOrder = associations.reduce(
            (max, item) =>
                Math.max(max, Number(item.stop_order) || 0),
            0
        ) + 1;

        await api(`/lines/${lineId}/stops`, {
            method: "POST",
            body: JSON.stringify({
                stop_id: stopId,
                stop_order: nextOrder
            })
        });

        if (message) {
            message.textContent =
                `Arrêt ajouté à l'ordre ${nextOrder}.`;
        }

        await loadUrbanLineStops();

        alert("Arrêt ajouté à l'itinéraire avec succès.");

    } catch (error) {
        alert("Impossible d'ajouter l'arrêt : " + error.message);

    } finally {
        urbanRouteSaving = false;
    }
}

// Integrer les lignes au chargement administrateur.
const previousUrbanRefreshAdmin = refreshUrbanAdmin;

refreshUrbanAdmin = function(...args) {
    const result = previousUrbanRefreshAdmin(...args);
    refreshUrbanRouteLines();
    return result;
};