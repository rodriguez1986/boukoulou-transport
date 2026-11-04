"use strict";

window.BoukoulouGPS = (() => {
  const DEFAULT_REFRESH_MS = 5000;
  const MAX_REFRESH_MS = 60000;

  let timer = null;
  let controller = null;
  let activeLineId = null;
  let generation = 0;

  function validLineId(value) {
    const id = Number(value);
    return Number.isSafeInteger(id) && id > 0;
  }

  function stop() {
    generation += 1;
    activeLineId = null;

    if (timer !== null) {
      clearTimeout(timer);
      timer = null;
    }

    if (controller !== null) {
      controller.abort();
      controller = null;
    }
  }

  async function fetchVehicles(lineId, signal) {
    const url = "/urban/public/lines/" +
      encodeURIComponent(lineId) +
      "/vehicles";

    const response = await fetch(url, {
      method: "GET",
      credentials: "omit",
      cache: "no-store",
      headers: {
        "Accept": "application/json"
      },
      signal
    });

    if (!response.ok) {
      throw new Error("Erreur GPS HTTP " + response.status);
    }

    const data = await response.json();

    if (
      !data ||
      Number(data.line_id) !== Number(lineId) ||
      !Array.isArray(data.vehicles)
    ) {
      throw new Error("Reponse GPS invalide.");
    }

    return data;
  }

  function start(lineId, onUpdate, onError) {
    if (!validLineId(lineId)) {
      throw new Error("Identifiant de ligne invalide.");
    }

    if (typeof onUpdate !== "function") {
      throw new Error("Callback GPS manquant.");
    }

    stop();

    activeLineId = Number(lineId);
    const currentGeneration = generation;

    async function refresh() {
      if (currentGeneration !== generation) {
        return;
      }

      const requestController = new AbortController();
      controller = requestController;

      let delay = DEFAULT_REFRESH_MS;

      try {
        const data = await fetchVehicles(
          activeLineId,
          requestController.signal
        );

        if (currentGeneration !== generation) {
          return;
        }

        const seconds = Number(data.refresh_seconds);

        if (Number.isFinite(seconds) && seconds > 0) {
          delay = Math.min(
            MAX_REFRESH_MS,
            Math.max(1000, seconds * 1000)
          );
        }

        onUpdate(data);

      } catch (error) {
        if (
          currentGeneration !== generation ||
          requestController.signal.aborted
        ) {
          return;
        }

        if (typeof onError === "function") {
          onError(error);
        }

      } finally {
        if (controller === requestController) {
          controller = null;
        }

        if (currentGeneration === generation) {
          timer = setTimeout(refresh, delay);
        }
      }
    }

    refresh();
  }

  return Object.freeze({
    start,
    stop,
    getActiveLineId: () => activeLineId
  });
})();
