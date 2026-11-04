"use strict";

(() => {
  const API = {
    cities: "/urban/public/cities",
    stops: "/urban/public/stops",
    routes: "/urban/public/routes/search"
  };

  const citySelect = document.getElementById("city-select");
  const departureSelect = document.getElementById("departure-select");
  const arrivalSelect = document.getElementById("arrival-select");
  const searchButton = document.getElementById("search-button");
  const form = document.getElementById("route-search-form");
  const message = document.getElementById("search-message");
  const resultsSection = document.getElementById("results-section");
  const resultsCount = document.getElementById("results-count");
  const routeResults = document.getElementById("route-results");

  if (
    !citySelect ||
    !departureSelect ||
    !arrivalSelect ||
    !searchButton ||
    !form ||
    !message ||
    !resultsSection ||
    !resultsCount ||
    !routeResults
  ) {
    console.error("Interface voyageurs incomplete.");
    return;
  }

  let cities = [];
  let stops = [];
  let cityRequestId = 0;
  let searchRequestId = 0;
  let loading = false;

  function setMessage(text, type = "") {
    message.textContent = text;
    message.className = type ? "message " + type : "message";
  }

  function clearResults() {
    if (window.BoukoulouGPS) {
      window.BoukoulouGPS.stop();
    }

    if (window.BoukoulouMap) {
      window.BoukoulouMap.stop();
    }

    document.querySelectorAll(".gps-follow-button").forEach(
      button => {
        button.disabled = false;
        button.textContent = "Suivre les bus";
      }
    );

    searchRequestId++;
    loading = false;
    resultsSection.hidden = true;
    resultsCount.textContent = "";
    routeResults.replaceChildren();
  }

  function makeOption(value, label) {
    const option = document.createElement("option");
    option.value = String(value);
    option.textContent = String(label);
    return option;
  }

  function resetSelect(select, placeholder) {
    select.replaceChildren(makeOption("", placeholder));
    select.value = "";
    select.disabled = true;
  }

  function updateButton() {
    const departure = departureSelect.value;
    const arrival = arrivalSelect.value;

    searchButton.disabled = (
      loading ||
      !citySelect.value ||
      !departure ||
      !arrival ||
      departure === arrival
    );
  }

  async function getJson(url) {
    const response = await fetch(url, {
      method: "GET",
      credentials: "omit",
      cache: "no-store",
      headers: {
        "Accept": "application/json"
      }
    });

    if (!response.ok) {
      let detail = "";

      try {
        const body = await response.json();

        if (typeof body.detail === "string") {
          detail = body.detail;
        }
      } catch (_) {
        // Conserver un message generique.
      }

      throw new Error(
        detail || "Erreur HTTP " + response.status
      );
    }

    return response.json();
  }

  function validId(value) {
    const number = Number(value);
    return Number.isSafeInteger(number) && number > 0;
  }

  async function loadCities() {
    citySelect.disabled = true;
    resetSelect(citySelect, "Chargement des villes...");
    resetSelect(departureSelect, "Choisissez une ville");
    resetSelect(arrivalSelect, "Choisissez une ville");

    clearResults();
    setMessage("Chargement des villes...");

    try {
      const data = await getJson(API.cities);

      if (!Array.isArray(data)) {
        throw new Error("Format des villes invalide.");
      }

      cities = data.filter(
        city => city && validId(city.id)
      );

      citySelect.replaceChildren(
        makeOption("", "Choisissez votre ville")
      );

      for (const city of cities) {
        citySelect.appendChild(
          makeOption(city.id, city.name || "Ville " + city.id)
        );
      }

      if (cities.length === 0) {
        citySelect.disabled = true;
        setMessage(
          "Aucune ville disponible pour le moment."
        );
        return;
      }

      citySelect.disabled = false;
      setMessage("Selectionnez une ville pour commencer.");

    } catch (error) {
      resetSelect(citySelect, "Villes indisponibles");
      setMessage(
        "Impossible de charger les villes : " + error.message,
        "error"
      );
    }
  }

  async function loadStops() {
    const requestId = ++cityRequestId;
    const cityId = citySelect.value;

    // Invalider immediatement toute ancienne recherche.
    clearResults();
    updateButton();

    stops = [];

    resetSelect(departureSelect, "Chargement des arrets...");
    resetSelect(arrivalSelect, "Chargement des arrets...");
    updateButton();

    if (!validId(cityId)) {
      resetSelect(departureSelect, "Choisissez une ville");
      resetSelect(arrivalSelect, "Choisissez une ville");
      setMessage("Selectionnez une ville.");
      return;
    }

    setMessage("Chargement des arrets...");

    try {
      const url = API.stops +
        "?city_id=" + encodeURIComponent(cityId);

      const data = await getJson(url);

      if (requestId !== cityRequestId) {
        return;
      }

      if (!Array.isArray(data)) {
        throw new Error("Format des arrets invalide.");
      }

      stops = data.filter(
        stop =>
          stop &&
          validId(stop.id) &&
          String(stop.city_id) === String(cityId)
      );

      const placeholder = makeOption(
        "",
        "Selectionnez un arret"
      );

      departureSelect.replaceChildren(
        placeholder.cloneNode(true)
      );

      arrivalSelect.replaceChildren(
        placeholder.cloneNode(true)
      );

      for (const stop of stops) {
        const label = stop.name || "Arret " + stop.id;

        departureSelect.appendChild(
          makeOption(stop.id, label)
        );

        arrivalSelect.appendChild(
          makeOption(stop.id, label)
        );
      }

      if (stops.length < 2) {
        resetSelect(
          departureSelect,
          "Arrets insuffisants"
        );
        resetSelect(
          arrivalSelect,
          "Arrets insuffisants"
        );

        setMessage(
          "Cette ville ne dispose pas encore de suffisamment d'arrets."
        );
        return;
      }

      departureSelect.disabled = false;
      arrivalSelect.disabled = false;

      setMessage(
        "Choisissez votre arret de depart et votre arret d'arrivee."
      );

    } catch (error) {
      if (requestId !== cityRequestId) {
        return;
      }

      resetSelect(departureSelect, "Arrets indisponibles");
      resetSelect(arrivalSelect, "Arrets indisponibles");

      setMessage(
        "Impossible de charger les arrets : " + error.message,
        "error"
      );

    } finally {
      if (requestId === cityRequestId) {
        updateButton();
      }
    }
  }

  function addTextElement(parent, tag, className, text) {
    const element = document.createElement(tag);

    if (className) {
      element.className = className;
    }

    element.textContent = String(text);
    parent.appendChild(element);

    return element;
  }

  function formatFare(fare) {
    if (fare === null || fare === undefined || fare === "") {
      return "Tarif non disponible";
    }

    const amount = Number(fare);

    if (!Number.isFinite(amount) || amount < 0) {
      return "Tarif non disponible";
    }

    const city = cities.find(
      item => String(item.id) === citySelect.value
    );

    // La devise sera confirmee par les donnees pays.
    // Ne pas attribuer arbitrairement une devise.
    const formatted = new Intl.NumberFormat("fr-FR", {
      maximumFractionDigits: 2
    }).format(amount);

    return formatted + " (devise a confirmer)";
  }

  function createStopBlock(label, name) {
    const block = document.createElement("div");

    addTextElement(block, "span", "stop-label", label);
    addTextElement(
      block,
      "div",
      "stop-name",
      name || "Arret inconnu"
    );

    return block;
  }

  function renderRoute(route) {
    const card = document.createElement("article");
    card.className = "route-card";

    const header = document.createElement("div");
    header.className = "route-header";

    const heading = document.createElement("div");

    addTextElement(
      heading,
      "span",
      "route-code",
      route.line_code || "Ligne " + route.line_id
    );

    addTextElement(
      heading,
      "h3",
      "route-name",
      route.line_name || "Ligne urbaine"
    );

    header.appendChild(heading);

    addTextElement(
      header,
      "div",
      "route-fare",
      formatFare(route.fare)
    );

    card.appendChild(header);

    const stopsContainer = document.createElement("div");
    stopsContainer.className = "route-stops";

    stopsContainer.appendChild(
      createStopBlock(
        "Depart",
        route.departure_stop?.name
      )
    );

    addTextElement(
      stopsContainer,
      "span",
      "route-arrow",
      "\u2192"
    );

    stopsContainer.appendChild(
      createStopBlock(
        "Arrivee",
        route.arrival_stop?.name
      )
    );

    card.appendChild(stopsContainer);

    const intermediate = Array.isArray(route.intermediate_stops)
      ? route.intermediate_stops
      : [];

    const intermediateBlock = document.createElement("div");
    intermediateBlock.className = "intermediate-stops";

    if (intermediate.length > 0) {
      addTextElement(
        intermediateBlock,
        "strong",
        "",
        "Arrets intermediaires : "
      );

      intermediateBlock.appendChild(
        document.createTextNode(
          intermediate.map(stop => stop.name).join(" - ")
        )
      );
    } else {
      intermediateBlock.textContent =
        "Trajet direct sans arret intermediaire.";
    }

    card.appendChild(intermediateBlock);

    const gpsButton = document.createElement("button");
    gpsButton.type = "button";
    gpsButton.className = "gps-follow-button";
    gpsButton.textContent = "Suivre les bus";

    gpsButton.addEventListener("click", () => {
      if (!validId(route.line_id)) {
        setMessage("Identifiant de ligne invalide.", "error");
        return;
      }

      if (!window.BoukoulouGPS) {
        setMessage("Module GPS indisponible.", "error");
        return;
      }

      window.BoukoulouGPS.stop();

      if (!window.BoukoulouMap) {
        setMessage("Module cartographique indisponible.", "error");
        return;
      }

      try {
        window.BoukoulouMap.start(
          route.line_id,
          route.line_name || route.code || "Ligne urbaine",
          citySelect.value
        );
      } catch (error) {
        setMessage(
          "Impossible d'ouvrir la carte : " + error.message,
          "error"
        );
        return;
      }

      document.querySelectorAll(".gps-follow-button").forEach(
        button => {
          button.disabled = false;
          button.textContent = "Suivre les bus";
        }
      );

      gpsButton.disabled = true;
      gpsButton.textContent = "Suivi GPS actif";

      setMessage("Recherche des bus en circulation...");

      window.BoukoulouGPS.start(
        route.line_id,

        data => {
          window.BoukoulouMap.update(data);

          const vehicles = data.vehicles;

          if (vehicles.length === 0) {
            setMessage(
              "Aucun bus en circulation avec une position GPS recente."
            );
            return;
          }

          const codes = vehicles.map(
            vehicle => vehicle.code || "Bus " + vehicle.vehicle_id
          );

          setMessage(
            vehicles.length +
            " bus en circulation : " +
            codes.join(", "),
            "success"
          );
        },

        error => {
          window.BoukoulouMap.showError(
            "Suivi GPS indisponible : " + error.message
          );

          setMessage(
            "Suivi GPS indisponible : " + error.message,
            "error"
          );
        }
      );
    });

    card.appendChild(gpsButton);

    return card;
  }

  async function searchRoutes(event) {
    event.preventDefault();

    const cityId = citySelect.value;
    const departureId = departureSelect.value;
    const arrivalId = arrivalSelect.value;

    clearResults();
    const requestId = searchRequestId;

    if (
      !validId(cityId) ||
      !validId(departureId) ||
      !validId(arrivalId)
    ) {
      setMessage("Selectionnez une ville et deux arrets.", "error");
      return;
    }

    if (departureId === arrivalId) {
      setMessage(
        "Le depart et l'arrivee doivent etre differents.",
        "error"
      );
      return;
    }

    const knownStops = stops.map(stop => String(stop.id));

    if (
      !knownStops.includes(departureId) ||
      !knownStops.includes(arrivalId)
    ) {
      setMessage("Arrets invalides pour cette ville.", "error");
      return;
    }

    loading = true;
    updateButton();
    setMessage("Recherche des itineraires...");

    try {
      const url = API.routes +
        "?departure_stop_id=" + encodeURIComponent(departureId) +
        "&arrival_stop_id=" + encodeURIComponent(arrivalId);

      const data = await getJson(url);

      if (requestId !== searchRequestId) {
        return;
      }

      if (!Array.isArray(data)) {
        throw new Error("Format des itineraires invalide.");
      }

      resultsSection.hidden = false;
      resultsCount.textContent =
        data.length + " ligne(s) trouvee(s)";

      if (data.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent =
          "Aucun trajet direct disponible pour ces arrets.";
        routeResults.appendChild(empty);
        setMessage("Aucun trajet direct trouve.");
        return;
      }

      for (const route of data) {
        routeResults.appendChild(renderRoute(route));
      }

      setMessage("Itineraires disponibles.", "success");

    } catch (error) {
      if (requestId !== searchRequestId) {
        return;
      }

      setMessage(
        "Recherche impossible : " + error.message,
        "error"
      );

    } finally {
      if (requestId === searchRequestId) {
        loading = false;
        updateButton();
      }
    }
  }

  citySelect.addEventListener("change", loadStops);

  departureSelect.addEventListener("change", () => {
    clearResults();
    updateButton();
  });

  arrivalSelect.addEventListener("change", () => {
    clearResults();
    updateButton();
  });

  form.addEventListener("submit", searchRoutes);

  loadCities();
})();