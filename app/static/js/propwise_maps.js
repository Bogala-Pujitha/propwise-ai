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

  function createLeafletIcon(color, isSelected) {
    const size = isSelected ? 18 : 12;
    const borderWidth = isSelected ? 3 : 2;
    const html = '<div style="' +
      'background:' + color + ';' +
      'width:' + size + 'px;' +
      'height:' + size + 'px;' +
      'border-radius:50%;' +
      'border:' + borderWidth + 'px solid #fff;' +
      'box-shadow:0 2px 8px rgba(0,0,0,0.35);' +
      '"></div>';

    return L.divIcon({
      className: 'pw-marker',
      html: html,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2]
    });
  }

  window.PW_createLeafletMap = function (containerId, center, zoom) {
    const element = document.getElementById(containerId);
    if (!element) return null;

    element.innerHTML = "";

    const map = L.map(containerId).setView([center.lat, center.lng], zoom || 13);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> contributors"
    }).addTo(map);

    return map;
  };

  window.PW_renderDashboardMap = async function (result, inputData) {
    const element = document.getElementById("map");

    if (!element) {
      return;
    }

    const locationFeatures =
      result && result.location_features
        ? result.location_features
        : {};

    const center = {
      lat: Number(locationFeatures.latitude || 17.385),
      lng: Number(locationFeatures.longitude || 78.4867)
    };

    const map = window.PW_createLeafletMap("map", center, 13);

    if (!map) {
      return;
    }

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

    let properties = [];

    try {
      const response = await fetch(
        "/api/map/properties?" + params.toString()
      );

      const data = await response.json();

      properties = data.properties || [];
    } catch (error) {
      console.warn(
        "Property map data unavailable:",
        error
      );
    }

    const selectedProperty = properties.find(function (p) {
      if (locality && p.locality === locality) return true;
      return p.city === city;
    }) || properties[0];

    if (selectedProperty && Number.isFinite(selectedProperty.latitude) && Number.isFinite(selectedProperty.longitude)) {
      const selectedMarker = L.marker(
        [selectedProperty.latitude, selectedProperty.longitude],
        { icon: createLeafletIcon(COLORS.Selected, true) }
      ).addTo(map);

      selectedMarker.bindPopup(
        "<strong>Your Property</strong><br>" +
        (selectedProperty.property_type || "") +
        "<br>" +
        (selectedProperty.locality || "") +
        "<br>" +
        (selectedProperty.area_sqft
          ? Number(selectedProperty.area_sqft).toLocaleString("en-IN") + " sqft<br>"
          : "") +
        (selectedProperty.price
          ? "INR " + Number(selectedProperty.price).toLocaleString("en-IN")
          : "")
      );
    }

    properties.forEach(function (property) {
      if (property === selectedProperty) {
        return;
      }

      const lat = Number(property.latitude);
      const lng = Number(property.longitude);

      if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
        return;
      }

      const type = property.property_type || "Apartment";

      const marker = L.marker(
        [lat, lng],
        { icon: createLeafletIcon(COLORS[type] || "#6B747A", false) }
      ).addTo(map);

      marker.bindPopup(
        "<strong>" + type + "</strong><br>" +
        (property.locality || "") + "<br>" +
        (property.area_sqft
          ? Number(property.area_sqft).toLocaleString("en-IN") + " sqft<br>"
          : "") +
        (property.price
          ? "INR " + Number(property.price).toLocaleString("en-IN")
          : "") +
        (property.approximate
          ? "<br><small>Area-level location</small>"
          : "")
      );
    });

    const validPoints = properties.filter(function (p) {
      return Number.isFinite(p.latitude) && Number.isFinite(p.longitude);
    });

    if (validPoints.length > 1) {
      const bounds = L.latLngBounds();
      validPoints.forEach(function (p) {
        bounds.extend([p.latitude, p.longitude]);
      });
      map.fitBounds(bounds.pad(0.2));
    }
  };

  window.PW_renderStandaloneMap = async function (
    containerId,
    properties
  ) {
    const element = document.getElementById(containerId);

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

    const center = {
      lat: Number(first.latitude),
      lng: Number(first.longitude)
    };

    const map = window.PW_createLeafletMap(containerId, center, 12);

    if (!map) {
      return;
    }

    properties.forEach(function (property) {
      const lat = Number(property.latitude);
      const lng = Number(property.longitude);

      if (
        !Number.isFinite(lat) ||
        !Number.isFinite(lng)
      ) {
        return;
      }

      const type = property.property_type || "Apartment";
      const isSelected = property.is_selected;

      const marker = L.marker(
        [lat, lng],
        {
          icon: createLeafletIcon(
            COLORS[type] || "#6B747A",
            isSelected
          )
        }
      ).addTo(map);

      marker.bindPopup(
        "<strong>" + type + "</strong><br>" +
        (property.locality || "") + "<br>" +
        (property.area_sqft
          ? Number(property.area_sqft).toLocaleString("en-IN") + " sqft<br>"
          : "") +
        (property.price
          ? "INR " + Number(property.price).toLocaleString("en-IN")
          : "")
      );
    });

    const validPoints = properties.filter(function (p) {
      return Number.isFinite(p.latitude) && Number.isFinite(p.longitude);
    });

    if (validPoints.length > 1) {
      const bounds = L.latLngBounds();
      validPoints.forEach(function (p) {
        bounds.extend([p.latitude, p.longitude]);
      });
      map.fitBounds(bounds.pad(0.2));
    }
  };
})();
