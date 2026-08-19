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

  function createLeafletIcon(color, isSelected) {
    const size = isSelected ? 16 : 10;
    const borderWidth = isSelected ? 3 : 2;
    const html = '<div style="' +
      'background:' + color + ';' +
      'width:' + size + 'px;' +
      'height:' + size + 'px;' +
      'border-radius:50%;' +
      'border:' + borderWidth + 'px solid #fff;' +
      'box-shadow:0 2px 6px rgba(0,0,0,0.3);' +
      '"></div>';

    return L.divIcon({
      className: 'pw-marker',
      html: html,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2]
    });
  }

  window.renderMap = async function (result, inputData) {
    const container = document.getElementById("map");
    if (!container) return;

    const lat = Number(result?.location_features?.latitude || 17.385);
    const lng = Number(result?.location_features?.longitude || 78.4867);

    container.innerHTML = "";

    const map = L.map("map").setView([lat, lng], 13);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: "&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a> contributors"
    }).addTo(map);

    const selected = L.marker([lat, lng], {
      icon: createLeafletIcon(COLORS.Selected, true)
    }).addTo(map);

    selected.bindPopup(
      "<strong>Selected Property</strong><br>" +
      (inputData?.property_type || "Property") +
      " · " +
      (inputData?.locality || inputData?.city || "") +
      "<br>INR " +
      Number(result?.predicted_price || 0).toLocaleString("en-IN")
    );

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

        const marker = L.marker([pLat, pLng], {
          icon: createLeafletIcon(COLORS[type] || "#6B747A", false)
        }).addTo(map);

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
    } catch (error) {
      console.warn("Property map layer unavailable:", error);
    }
  };

  document.addEventListener("DOMContentLoaded", function () {
    document.documentElement.style.scrollBehavior = "auto";
  });
})();
