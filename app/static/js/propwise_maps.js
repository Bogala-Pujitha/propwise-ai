(function () {
  "use strict";

  const COLORS = {
    Apartment: "#1E3A8A",
    House: "#475569",
    Villa: "#B85C38",
    Plot: "#B68B2E",
    Selected: "#0F172A"
  };

  window.PW_COLORS = COLORS;

  function loadGoogleMaps() {
    if (window.google && window.google.maps) {
      return Promise.resolve();
    }

    if (window.__pwMapsPromise) {
      return window.__pwMapsPromise;
    }

    const key = window.PROPWISE_GOOGLE_MAPS_KEY || "";

    if (!key) {
      return Promise.reject(
        new Error("GOOGLE_MAPS_API_KEY is missing")
      );
    }

    window.__pwMapsPromise = new Promise(function (resolve, reject) {
      const callback = "__propwiseMapsReady";
      window[callback] = resolve;

      const script = document.createElement("script");
      script.async = true;
      script.defer = true;
      script.src =
        "https://maps.googleapis.com/maps/api/js?key=" +
        encodeURIComponent(key) +
        "&loading=async&callback=" +
        callback;

      script.onerror = function () {
        reject(new Error("Google Maps could not be loaded."));
      };

      document.head.appendChild(script);
    });

    return window.__pwMapsPromise;
  }

  function markerIcon(color, scale) {
    return {
      path: google.maps.SymbolPath.CIRCLE,
      fillColor: color,
      fillOpacity: 1,
      strokeColor: "#FFFFFF",
      strokeWeight: 2,
      scale: scale || 7
    };
  }

  window.PW_renderDashboardMap = async function (result, inputData) {
    const element = document.getElementById("map");

    if (!element) {
      return;
    }

    try {
      await loadGoogleMaps();
    } catch (error) {
      element.innerHTML =
        '<div class="map-api-message">' +
        "<strong>Google Maps setup required.</strong><br>" +
        "Add GOOGLE_MAPS_API_KEY to your .env file." +
        "</div>";
      return;
    }

    element.innerHTML = "";

    const locationFeatures =
      result && result.location_features
        ? result.location_features
        : {};

    const center = {
      lat: Number(locationFeatures.latitude || 17.385),
      lng: Number(locationFeatures.longitude || 78.4867)
    };

    const map = new google.maps.Map(element, {
      center: center,
      zoom: 13,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: true
    });

    const city =
      inputData && inputData.city
        ? inputData.city
        : "Hyderabad";

    const locality =
      inputData && inputData.locality
        ? inputData.locality
        : "";

    const params = new URLSearchParams({
      city: city,
      locality: locality
    });

    try {
      const response = await fetch(
        "/api/map/properties?" + params.toString()
      );

      const data = await response.json();

      (data.properties || []).forEach(function (property) {
        const lat = Number(property.latitude);
        const lng = Number(property.longitude);

        if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
          return;
        }

        const type = property.property_type || "Apartment";

        const marker = new google.maps.Marker({
          map: map,
          position: {
            lat: lat,
            lng: lng
          },
          title: type,
          icon: markerIcon(
            COLORS[type] || "#6B747A"
          )
        });

        const info = new google.maps.InfoWindow({
          content:
            "<strong>" +
            type +
            "</strong><br>" +
            (property.locality || "") +
            "<br>" +
            (
              property.area_sqft
                ? Number(property.area_sqft)
                    .toLocaleString("en-IN") +
                  " sqft<br>"
                : ""
            ) +
            (
              property.price
                ? "INR " +
                  Number(property.price)
                    .toLocaleString("en-IN")
                : ""
            ) +
            (
              property.approximate
                ? "<br><small>Area-level location</small>"
                : ""
            )
        });

        marker.addListener(
          "click",
          function () {
            info.open(map, marker);
          }
        );
      });
    } catch (error) {
      console.warn(
        "Property map data unavailable:",
        error
      );
    }
  };

  window.PW_renderStandaloneMap =
    async function (
      containerId,
      properties
    ) {
      await loadGoogleMaps();

      const element =
        document.getElementById(containerId);

      if (!element) {
        return;
      }

      const first =
        properties && properties.length
          ? properties[0]
          : {
              latitude: 17.385,
              longitude: 78.4867
            };

      const map = new google.maps.Map(
        element,
        {
          center: {
            lat: Number(first.latitude),
            lng: Number(first.longitude)
          },
          zoom: 12,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: true
        }
      );

      (properties || []).forEach(
        function (property) {
          const lat = Number(property.latitude);
          const lng = Number(property.longitude);

          if (
            !Number.isFinite(lat) ||
            !Number.isFinite(lng)
          ) {
            return;
          }

          const type =
            property.property_type ||
            "Apartment";

          const marker =
            new google.maps.Marker({
              map: map,
              position: {
                lat: lat,
                lng: lng
              },
              title: type,
              icon: markerIcon(
                COLORS[type] || "#6B747A"
              )
            });

          const info =
            new google.maps.InfoWindow({
              content:
                "<strong>" +
                type +
                "</strong><br>" +
                (property.locality || "") +
                "<br>" +
                (
                  property.area_sqft
                    ? Number(
                        property.area_sqft
                      ).toLocaleString(
                        "en-IN"
                      ) + " sqft<br>"
                    : ""
                ) +
                (
                  property.price
                    ? "INR " +
                      Number(
                        property.price
                      ).toLocaleString(
                        "en-IN"
                      )
                    : ""
                )
            });

          marker.addListener(
            "click",
            function () {
              info.open(map, marker);
            }
          );
        }
      );
    };
})();
