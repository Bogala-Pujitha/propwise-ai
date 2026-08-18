(function () {
  "use strict";

  const COLORS = {
    Apartment: "#1E3A8A",
    House: "#475569",
    Villa: "#B85C38",
    Plot: "#B68B2E",
    Selected: "#0F172A"
  };

  window.PROPWISE_PROPERTY_COLORS = COLORS;
  window.propertyTypeColors = COLORS;

  function loadGoogleMaps() {
    if (window.google && window.google.maps) return Promise.resolve();
    if (window.__propwiseGoogleMapsPromise) return window.__propwiseGoogleMapsPromise;

    const key = window.PROPWISE_GOOGLE_MAPS_KEY || "";
    if (!key) return Promise.reject(new Error("GOOGLE_MAPS_API_KEY is not configured."));

    window.__propwiseGoogleMapsPromise = new Promise((resolve, reject) => {
      const callback = "__propwiseGoogleMapsReady";
      window[callback] = resolve;

      const script = document.createElement("script");
      script.async = true;
      script.defer = true;
      script.src =
        "https://maps.googleapis.com/maps/api/js?key=" +
        encodeURIComponent(key) +
        "&loading=async&callback=" + callback;
      script.onerror = () => reject(new Error("Google Maps failed to load."));
      document.head.appendChild(script);
    });

    return window.__propwiseGoogleMapsPromise;
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

  window.renderMap = async function (result, inputData) {
    const container = document.getElementById("map");
    if (!container) return;

    const lat = Number(result?.location_features?.latitude || 17.385);
    const lng = Number(result?.location_features?.longitude || 78.4867);

    try {
      await loadGoogleMaps();
    } catch (error) {
      container.innerHTML =
        '<div class="map-api-message"><strong>Google Maps setup required.</strong><br>' +
        'Set GOOGLE_MAPS_API_KEY in your .env file.</div>';
      return;
    }

    container.innerHTML = "";

    const map = new google.maps.Map(container, {
      center: { lat, lng },
      zoom: 13,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: true
    });

    const selected = new google.maps.Marker({
      map,
      position: { lat, lng },
      title: "Selected property",
      icon: markerIcon(COLORS.Selected, 10)
    });

    const selectedInfo = new google.maps.InfoWindow({
      content:
        "<strong>Selected Property</strong><br>" +
        (inputData?.property_type || "Property") +
        " · " +
        (inputData?.locality || inputData?.city || "") +
        "<br>INR " +
        Number(result?.predicted_price || 0).toLocaleString("en-IN")
    });

    selected.addListener("click", () => selectedInfo.open(map, selected));

    try {
      const query = new URLSearchParams({
        city: inputData?.city || "Hyderabad",
        locality: inputData?.locality || ""
      });

      const response = await fetch("/api/map/properties?" + query.toString());
      const data = await response.json();

      (data.properties || []).forEach((property) => {
        const pLat = Number(property.latitude);
        const pLng = Number(property.longitude);
        if (!Number.isFinite(pLat) || !Number.isFinite(pLng)) return;

        const type = property.property_type || "Apartment";

        const marker = new google.maps.Marker({
          map,
          position: { lat: pLat, lng: pLng },
          title: type,
          icon: markerIcon(COLORS[type] || "#6B747A", 7)
        });

        const info = new google.maps.InfoWindow({
          content:
            "<strong>" + type + "</strong><br>" +
            (property.locality || "") + "<br>" +
            (property.area_sqft
              ? Number(property.area_sqft).toLocaleString("en-IN") + " sqft<br>"
              : "") +
            (property.price
              ? "INR " + Number(property.price).toLocaleString("en-IN")
              : "")
        });

        marker.addListener("click", () => info.open(map, marker));
      });
    } catch (error) {
      console.warn("Property map layer unavailable:", error);
    }
  };

  document.addEventListener("DOMContentLoaded", function () {
    document.documentElement.style.scrollBehavior = "auto";
  });
})();
