(function () {

  "use strict";


  /* =========================================================
     PROPERTY TYPE COLORS
  ========================================================== */

  const COLORS = {

      Apartment: "#1E3A8A",

      House: "#475569",

      Villa: "#B85C38",

      Plot: "#B68B2E",

      Selected: "#0F172A"
  };


  window.PW_COLORS = COLORS;


  /* =========================================================
     MAP INSTANCES
  ========================================================== */

  let selectedLocationMap = null;

  let propertyComparablesMap = null;

  let propertyTypesMap = null;


  /* =========================================================
     MARKERS
  ========================================================== */

  let propertyTypeMarkers = [];

  let comparableMarkers = [];


  /* =========================================================
     LEAFLET ICON
  ========================================================== */

  function createLeafletIcon(
      color,
      selected
  ) {

      const size = selected
          ? 18
          : 12;

      const borderWidth = selected
          ? 3
          : 2;


      return L.divIcon({

          className:
              "pw-three-map-marker",

          html:
              '<div style="' +

              "background:" +
              color +
              ";" +

              "width:" +
              size +
              "px;" +

              "height:" +
              size +
              "px;" +

              "border-radius:50%;" +

              "border:" +
              borderWidth +
              "px solid #fff;" +

              "box-shadow:0 2px 8px rgba(0,0,0,.35);" +

              '"></div>',

          iconSize: [
              size,
              size
          ],

          iconAnchor: [
              size / 2,
              size / 2
          ]
      });

  }


  /* =========================================================
     CREATE OPENSTREETMAP + LEAFLET MAP
  ========================================================== */

  function createMap(
      containerId,
      center,
      zoom
  ) {

      const element =
          document.getElementById(
              containerId
          );


      if (!element) {
          return null;
      }


      if (element._leaflet_id) {

          element._leaflet_id =
              undefined;

          element.innerHTML = "";

      }


      const map =
          L.map(
              containerId,
              {
                  scrollWheelZoom: true,
                  zoomControl: true
              }
          )
          .setView(
              [
                  center.lat,
                  center.lng
              ],
              zoom || 13
          );


      L.tileLayer(
          "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
          {
              maxZoom: 19,

              attribution:
                  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          }
      ).addTo(map);


      return map;
  }


  /* =========================================================
     MAP 1
     SELECTED LOCATION
  ========================================================== */

  async function renderSelectedLocationMap(
      predictionData
  ) {

      const element =
          document.getElementById(
              "selectedLocationMap"
          );


      if (!element) {
          return;
      }


      if (selectedLocationMap) {

          selectedLocationMap.remove();

          selectedLocationMap =
              null;
      }


      const location =
          predictionData &&
          predictionData.location_features
              ? predictionData.location_features
              : {};


      const lat =
          Number(
              location.latitude
          );

      const lng =
          Number(
              location.longitude
          );


      if (
          !Number.isFinite(lat)
          ||
          !Number.isFinite(lng)
      ) {

          element.innerHTML =
              '<div style="padding:20px;text-align:center;color:#64748b;">' +
              "Location coordinates unavailable" +
              "</div>";

          return;
      }


      selectedLocationMap =
          createMap(
              "selectedLocationMap",
              {
                  lat: lat,
                  lng: lng
              },
              14
          );


      if (!selectedLocationMap) {
          return;
      }


      const marker =
          L.marker(
              [lat, lng],
              {
                  icon:
                      createLeafletIcon(
                          COLORS.Selected,
                          true
                      )
              }
          )
          .addTo(
              selectedLocationMap
          );


      const city =
          predictionData.city
          || "Selected City";

      const locality =
          predictionData.locality
          || "Selected Locality";


      marker.bindPopup(
          "<strong>Selected Location</strong><br>" +
          city +
          "<br>" +
          locality +
          "<br>" +
          "Latitude: " +
          lat.toFixed(6) +
          "<br>" +
          "Longitude: " +
          lng.toFixed(6)
      );


      const info =
          document.getElementById(
              "selectedLocationInfo"
          );


      if (info) {

          info.innerHTML =
              "<strong>" +
              city +
              "</strong> · " +
              locality +
              "<br>" +
              "Coordinates: " +
              lat.toFixed(6) +
              ", " +
              lng.toFixed(6);
      }


      setTimeout(
          function () {

              selectedLocationMap
                  .invalidateSize();

          },
          100
      );

  }


  /* =========================================================
     MAP 2
     SELECTED PROPERTY + COMPARABLES
  ========================================================== */

  async function renderPropertyComparablesMap(
      predictionData
  ) {

      const element =
          document.getElementById(
              "propertyComparablesMap"
          );


      if (!element) {
          return;
      }


      if (propertyComparablesMap) {

          propertyComparablesMap.remove();

          propertyComparablesMap =
              null;
      }


      comparableMarkers = [];


      const city =
          predictionData.city
          || "Hyderabad";

      const locality =
          predictionData.locality
          || "";


      const area =
          Number(
              predictionData.area_sqft
              || 0
          );

      const bhk =
          Number(
              predictionData.bhk
              || 0
          );


      const propertyType =
          predictionData.property_type
          || "Apartment";


      let selectedProperty =
          null;


      /* =====================================================
         GET EXACT DATASET PROPERTY
      ====================================================== */

      try {

          const response =
              await fetch(
                  "/api/map/selected-property",
                  {
                      method: "POST",

                      headers: {
                          "Content-Type":
                              "application/json"
                      },

                      body: JSON.stringify({

                          city: city,

                          locality:
                              locality,

                          property_type:
                              propertyType,

                          area_sqft:
                              area,

                          bhk:
                              bhk
                      })
                  }
              );


          const data =
              await response.json();


          selectedProperty =
              data.property || null;


      } catch (error) {

          console.warn(
              "Selected property map data unavailable:",
              error
          );

      }


      /* =====================================================
         FALLBACK TO LOCATION FEATURES
      ====================================================== */

      if (!selectedProperty) {

          const lf =
              predictionData
                  .location_features
              || {};


          const lat =
              Number(
                  lf.latitude
              );

          const lng =
              Number(
                  lf.longitude
              );


          if (
              Number.isFinite(lat)
              &&
              Number.isFinite(lng)
          ) {

              selectedProperty = {

                  latitude: lat,

                  longitude: lng,

                  city: city,

                  locality: locality,

                  property_type:
                      propertyType,

                  area_sqft:
                      area,

                  bhk: bhk,

                  price:
                      predictionData
                          .predicted_price

              };

          }
      }


      /* =====================================================
         GET COMPARABLES
      ====================================================== */

      let comparables = [];


      try {

          const response =
              await fetch(
                  "/api/map/comparables",
                  {
                      method: "POST",

                      headers: {
                          "Content-Type":
                              "application/json"
                      },

                      body: JSON.stringify({

                          property_type:
                              propertyType,

                          city:
                              city,

                          locality:
                              locality,

                          area_sqft:
                              area,

                          bhk:
                              bhk,

                          bathrooms:
                              Number(
                                  predictionData
                                      .bathrooms
                                  || 2
                              ),

                          property_age:
                              Number(
                                  predictionData
                                      .property_age
                                  || 5
                              )

                      })
                  }
              );


          if (response.ok) {

              const data =
                  await response.json();


              comparables =
                  Array.isArray(
                      data.properties
                  )
                      ? data.properties
                      : [];

          }


      } catch (error) {

          console.warn(
              "Comparable map data unavailable:",
              error
          );

      }


      /* =====================================================
         DATASET FALLBACK FOR MAP 2
         If the comparable engine returns no rows,
         use actual dataset properties from the same
         city/locality/property type.
      ====================================================== */

      if (
          comparables.length === 0
          &&
          city
      ) {

          try {

              const fallbackParams =
                  new URLSearchParams({

                      city:
                          city,

                      locality:
                          locality,

                      property_type:
                          propertyType

                  });


              const fallbackResponse =
                  await fetch(
                      "/api/map/properties?" +
                      fallbackParams.toString()
                  );


              if (fallbackResponse.ok) {

                  const fallbackData =
                      await fallbackResponse.json();


                  comparables =
                      Array.isArray(
                          fallbackData.properties
                      )
                          ? fallbackData.properties
                          : [];

              }


          } catch (error) {

              console.warn(
                  "Dataset comparable fallback unavailable:",
                  error
              );

          }

      }


      /*
       * Keep only real latitude/longitude records.
       * The dataset itself is NOT changed.
       * The 15-marker limit only prevents Map 2 from becoming
       * visually overloaded.
       */

      comparables =
          comparables
              .filter(
                  function (property) {

                      return (
                          Number.isFinite(
                              Number(
                                  property.latitude
                              )
                          )
                          &&
                          Number.isFinite(
                              Number(
                                  property.longitude
                              )
                          )
                      );

                  }
              )
              .slice(0, 15);


      /* =====================================================
         DETERMINE MAP CENTER
      ====================================================== */

      let center = {

          lat: 17.385,

          lng: 78.4867

      };


      if (selectedProperty) {

          const lat =
              Number(
                  selectedProperty
                      .latitude
              );

          const lng =
              Number(
                  selectedProperty
                      .longitude
              );


          if (
              Number.isFinite(lat)
              &&
              Number.isFinite(lng)
          ) {

              center = {

                  lat: lat,

                  lng: lng

              };

          }
      }


      propertyComparablesMap =
          createMap(
              "propertyComparablesMap",
              center,
              14
          );


      if (!propertyComparablesMap) {
          return;
      }


      const bounds =
          L.latLngBounds();


      /* =====================================================
         SELECTED PROPERTY MARKER
      ====================================================== */

      if (selectedProperty) {

          const lat =
              Number(
                  selectedProperty.latitude
              );

          const lng =
              Number(
                  selectedProperty.longitude
              );


          if (
              Number.isFinite(lat)
              &&
              Number.isFinite(lng)
          ) {

              const marker =
                  L.marker(
                      [lat, lng],
                      {
                          icon:
                              createLeafletIcon(
                                  COLORS.Selected,
                                  true
                              )
                      }
                  )
                  .addTo(
                      propertyComparablesMap
                  );


              marker.bindPopup(

                  "<strong>Selected Property</strong><br>" +

                  (
                      selectedProperty
                          .property_type
                      || propertyType
                  ) +

                  "<br>" +

                  (
                      selectedProperty
                          .locality
                      || locality
                  ) +

                  "<br>" +

                  (
                      selectedProperty.area_sqft
                          ? Number(
                              selectedProperty
                                  .area_sqft
                            ).toLocaleString(
                                "en-IN"
                            ) +
                            " sqft<br>"
                          : ""
                  ) +

                  (
                      selectedProperty.price
                          ? "INR " +
                            Number(
                              selectedProperty.price
                            ).toLocaleString(
                                "en-IN"
                            )
                          : ""
                  )

              );


              bounds.extend(
                  [lat, lng]
              );

          }
      }


      /* =====================================================
         COMPARABLE PROPERTY MARKERS
      ====================================================== */

      comparables.forEach(
          function (property) {

              const lat =
                  Number(
                      property.latitude
                  );

              const lng =
                  Number(
                      property.longitude
                  );


              if (
                  !Number.isFinite(lat)
                  ||
                  !Number.isFinite(lng)
              ) {
                  return;
              }


              const type =
                  property.property_type
                  || "Apartment";


              const color =
                  COLORS[type]
                  || COLORS.Apartment;


              const marker =
                  L.marker(
                      [lat, lng],
                      {
                          icon:
                              createLeafletIcon(
                                  color,
                                  false
                              )
                      }
                  )
                  .addTo(
                      propertyComparablesMap
                  );


              marker.bindPopup(

                  "<strong>" +
                  type +
                  "</strong><br>" +

                  (
                      property.locality
                      || ""
                  ) +

                  "<br>" +

                  (
                      property.area_sqft
                          ? Number(
                              property.area_sqft
                            ).toLocaleString(
                                "en-IN"
                            ) +
                            " sqft<br>"
                          : ""
                  ) +

                  (
                      property.bhk
                          ? property.bhk +
                            " BHK<br>"
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

              );


              comparableMarkers.push(
                  marker
              );


              bounds.extend(
                  [lat, lng]
              );

          }
      );


      if (!bounds.isEmpty()) {

          propertyComparablesMap
              .fitBounds(
                  bounds.pad(0.2)
              );

      }


      setTimeout(
          function () {

              propertyComparablesMap
                  .invalidateSize();

          },
          100
      );

  }


  /* =========================================================
     MAP 3
     PROPERTY TYPES IN SELECTED AREA
  ========================================================== */

  async function loadPropertyTypesMap(
      city,
      locality
  ) {

      if (!city || !locality) {
          return;
      }


      const element =
          document.getElementById(
              "propertyTypesMap"
          );


      if (!element) {
          return;
      }


      if (propertyTypesMap) {

          propertyTypesMap.remove();

          propertyTypesMap =
              null;
      }


      propertyTypeMarkers = [];


      let properties = [];


      try {

          const url =
              "/api/map/properties?" +
              new URLSearchParams({

                  city: city,

                  locality: locality

              }).toString();


          const response =
              await fetch(url);


          const data =
              await response.json();


          properties =
              data.properties || [];


      } catch (error) {

          console.warn(
              "Area property map unavailable:",
              error
          );

          return;
      }


      const validProperties =
          properties.filter(
              function (property) {

                  return Number.isFinite(
                      Number(
                          property.latitude
                      )
                  )
                  &&
                  Number.isFinite(
                      Number(
                          property.longitude
                      )
                  );

              }
          );


      if (
          validProperties.length === 0
      ) {

          element.innerHTML =
              '<div style="padding:20px;text-align:center;color:#64748b;">' +
              "No property coordinates available for this locality." +
              "</div>";

          return;
      }


      const first =
          validProperties[0];


      propertyTypesMap =
          createMap(
              "propertyTypesMap",
              {
                  lat:
                      Number(
                          first.latitude
                      ),

                  lng:
                      Number(
                          first.longitude
                      )
              },
              13
          );


      if (!propertyTypesMap) {
          return;
      }


      const bounds =
          L.latLngBounds();


      validProperties.forEach(
          function (property) {

              const lat =
                  Number(
                      property.latitude
                  );

              const lng =
                  Number(
                      property.longitude
                  );


              const type =
                  property.property_type
                  || "Apartment";


              const color =
                  COLORS[type]
                  || COLORS.Apartment;


              const marker =
                  L.marker(
                      [lat, lng],
                      {
                          icon:
                              createLeafletIcon(
                                  color,
                                  false
                              )
                      }
                  )
                  .addTo(
                      propertyTypesMap
                  );


              marker.bindPopup(

                  "<strong>" +
                  type +
                  "</strong><br>" +

                  (
                      property.locality
                      || locality
                  ) +

                  "<br>" +

                  (
                      property.area_sqft
                          ? Number(
                              property.area_sqft
                            ).toLocaleString(
                                "en-IN"
                            ) +
                            " sqft<br>"
                          : ""
                  ) +

                  (
                      property.bhk
                          ? property.bhk +
                            " BHK<br>"
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
                  ) +

                  (
                      property.approximate
                          ? "<br><small>Area-level location</small>"
                          : ""
                  )

              );


              propertyTypeMarkers.push(
                  marker
              );


              bounds.extend(
                  [lat, lng]
              );

          }
      );


      if (!bounds.isEmpty()) {

          propertyTypesMap
              .fitBounds(
                  bounds.pad(0.15)
              );

      }


      setTimeout(
          function () {

              propertyTypesMap
                  .invalidateSize();

          },
          100
      );

  }


  /* =========================================================
     THIRD MAP DROPDOWNS
  ========================================================== */

  function setupAreaSelectors(
      dropdownData
  ) {

      const citySelect =
          document.getElementById(
              "threeMapCity"
          );

      const localitySelect =
          document.getElementById(
              "threeMapLocality"
          );


      if (
          !citySelect
          ||
          !localitySelect
      ) {
          return;
      }


      citySelect.addEventListener(
          "change",
          function () {

              const city =
                  String(
                      this.value || ""
                  ).trim();


              localitySelect.innerHTML =
                  '<option value="">Select Locality</option>';


              localitySelect.disabled =
                  !city;


              if (!city) {

                  if (
                      propertyTypesMap
                  ) {

                      propertyTypesMap.remove();

                      propertyTypesMap =
                          null;

                  }

                  return;
              }


              const localities =
                  (
                      dropdownData
                      &&
                      dropdownData.localities
                      &&
                      dropdownData.localities[city]
                  )
                  ||
                  [];


              localities.forEach(
                  function (locality) {

                      const option =
                          document.createElement(
                              "option"
                          );


                      option.value =
                          locality;

                      option.textContent =
                          locality;


                      localitySelect
                          .appendChild(
                              option
                          );

                  }
              );


              /* Enable locality only when this city has actual localities. */
              localitySelect.disabled =
                  localities.length === 0;

          }
      );


      localitySelect.addEventListener(
          "change",
          function () {

              const selectedCity =
                  String(
                      citySelect.value || ""
                  ).trim();


              const selectedLocality =
                  String(
                      this.value || ""
                  ).trim();


              if (
                  !selectedCity
                  ||
                  !selectedLocality
              ) {
                  return;
              }


              loadPropertyTypesMap(
                  selectedCity,
                  selectedLocality
              );

          }
      );


      /*
       * The existing HTML can have the locality select disabled on load.
       * Trigger the city handler once so a pre-selected city populates
       * and enables the locality dropdown immediately.
       */

      if (citySelect.value) {

          citySelect.dispatchEvent(
              new Event("change")
          );

      }

  }


  /* =========================================================
     MAIN FUNCTION
  ========================================================== */

  window.PW_renderThreeMaps =
      async function (
          predictionData,
          inputData
      ) {

          predictionData =
              predictionData
              || {};

          inputData =
              inputData
              || {};


          const merged =
              Object.assign(
                  {},
                  predictionData,
                  inputData
              );


          await Promise.all([

              renderSelectedLocationMap(
                  merged
              ),

              renderPropertyComparablesMap(
                  merged
              )

          ]);

      };


  /* =========================================================
     INITIALIZE THIRD MAP
  ========================================================== */

  window.PW_initThreeMapControls =
      function (
          dropdownData
      ) {

          setupAreaSelectors(
              dropdownData
              || {}
          );

      };

})(); (function () {

    "use strict";
  
  
    /* =========================================================
       PROPERTY TYPE COLORS
    ========================================================== */
  
    const COLORS = {
  
        Apartment: "#1E3A8A",
  
        House: "#475569",
  
        Villa: "#B85C38",
  
        Plot: "#B68B2E",
  
        Selected: "#0F172A"
    };
  
  
    window.PW_COLORS = COLORS;
  
  
    /* =========================================================
       MAP INSTANCES
    ========================================================== */
  
    let selectedLocationMap = null;
  
    let propertyComparablesMap = null;
  
    let propertyTypesMap = null;
  
  
    /* =========================================================
       MARKERS
    ========================================================== */
  
    let propertyTypeMarkers = [];
  
    let comparableMarkers = [];
  
  
    /* =========================================================
       LEAFLET ICON
    ========================================================== */
  
    function createLeafletIcon(
        color,
        selected
    ) {
  
        const size = selected
            ? 18
            : 12;
  
        const borderWidth = selected
            ? 3
            : 2;
  
  
        return L.divIcon({
  
            className:
                "pw-three-map-marker",
  
            html:
                '<div style="' +
  
                "background:" +
                color +
                ";" +
  
                "width:" +
                size +
                "px;" +
  
                "height:" +
                size +
                "px;" +
  
                "border-radius:50%;" +
  
                "border:" +
                borderWidth +
                "px solid #fff;" +
  
                "box-shadow:0 2px 8px rgba(0,0,0,.35);" +
  
                '"></div>',
  
            iconSize: [
                size,
                size
            ],
  
            iconAnchor: [
                size / 2,
                size / 2
            ]
        });
  
    }
  
  
    /* =========================================================
       CREATE OPENSTREETMAP + LEAFLET MAP
    ========================================================== */
  
    function createMap(
        containerId,
        center,
        zoom
    ) {
  
        const element =
            document.getElementById(
                containerId
            );
  
  
        if (!element) {
            return null;
        }
  
  
        if (element._leaflet_id) {
  
            element._leaflet_id =
                undefined;
  
            element.innerHTML = "";
  
        }
  
  
        const map =
            L.map(
                containerId,
                {
                    scrollWheelZoom: true,
                    zoomControl: true
                }
            )
            .setView(
                [
                    center.lat,
                    center.lng
                ],
                zoom || 13
            );
  
  
        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                maxZoom: 19,
  
                attribution:
                    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }
        ).addTo(map);
  
  
        return map;
    }
  
  
    /* =========================================================
       MAP 1
       SELECTED LOCATION
    ========================================================== */
  
    async function renderSelectedLocationMap(
        predictionData
    ) {
  
        const element =
            document.getElementById(
                "selectedLocationMap"
            );
  
  
        if (!element) {
            return;
        }
  
  
        if (selectedLocationMap) {
  
            selectedLocationMap.remove();
  
            selectedLocationMap =
                null;
        }
  
  
        const location =
            predictionData &&
            predictionData.location_features
                ? predictionData.location_features
                : {};
  
  
        const lat =
            Number(
                location.latitude
            );
  
        const lng =
            Number(
                location.longitude
            );
  
  
        if (
            !Number.isFinite(lat)
            ||
            !Number.isFinite(lng)
        ) {
  
            element.innerHTML =
                '<div style="padding:20px;text-align:center;color:#64748b;">' +
                "Location coordinates unavailable" +
                "</div>";
  
            return;
        }
  
  
        selectedLocationMap =
            createMap(
                "selectedLocationMap",
                {
                    lat: lat,
                    lng: lng
                },
                14
            );
  
  
        if (!selectedLocationMap) {
            return;
        }
  
  
        const marker =
            L.marker(
                [lat, lng],
                {
                    icon:
                        createLeafletIcon(
                            COLORS.Selected,
                            true
                        )
                }
            )
            .addTo(
                selectedLocationMap
            );
  
  
        const city =
            predictionData.city
            || "Selected City";
  
        const locality =
            predictionData.locality
            || "Selected Locality";
  
  
        marker.bindPopup(
            "<strong>Selected Location</strong><br>" +
            city +
            "<br>" +
            locality +
            "<br>" +
            "Latitude: " +
            lat.toFixed(6) +
            "<br>" +
            "Longitude: " +
            lng.toFixed(6)
        );
  
  
        const info =
            document.getElementById(
                "selectedLocationInfo"
            );
  
  
        if (info) {
  
            info.innerHTML =
                "<strong>" +
                city +
                "</strong> · " +
                locality +
                "<br>" +
                "Coordinates: " +
                lat.toFixed(6) +
                ", " +
                lng.toFixed(6);
        }
  
  
        setTimeout(
            function () {
  
                selectedLocationMap
                    .invalidateSize();
  
            },
            100
        );
  
    }
  
  
    /* =========================================================
       MAP 2
       SELECTED PROPERTY + COMPARABLES
    ========================================================== */
  
    async function renderPropertyComparablesMap(
        predictionData
    ) {
  
        const element =
            document.getElementById(
                "propertyComparablesMap"
            );
  
  
        if (!element) {
            return;
        }
  
  
        if (propertyComparablesMap) {
  
            propertyComparablesMap.remove();
  
            propertyComparablesMap =
                null;
        }
  
  
        comparableMarkers = [];
  
  
        const city =
            predictionData.city
            || "Hyderabad";
  
        const locality =
            predictionData.locality
            || "";
  
  
        const area =
            Number(
                predictionData.area_sqft
                || 0
            );
  
        const bhk =
            Number(
                predictionData.bhk
                || 0
            );
  
  
        const propertyType =
            predictionData.property_type
            || "Apartment";
  
  
        let selectedProperty =
            null;
  
  
        /* =====================================================
           GET EXACT DATASET PROPERTY
        ====================================================== */
  
        try {
  
            const response =
                await fetch(
                    "/api/map/selected-property",
                    {
                        method: "POST",
  
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
  
                        body: JSON.stringify({
  
                            city: city,
  
                            locality:
                                locality,
  
                            property_type:
                                propertyType,
  
                            area_sqft:
                                area,
  
                            bhk:
                                bhk
                        })
                    }
                );
  
  
            const data =
                await response.json();
  
  
            selectedProperty =
                data.property || null;
  
  
        } catch (error) {
  
            console.warn(
                "Selected property map data unavailable:",
                error
            );
  
        }
  
  
        /* =====================================================
           FALLBACK TO LOCATION FEATURES
        ====================================================== */
  
        if (!selectedProperty) {
  
            const lf =
                predictionData
                    .location_features
                || {};
  
  
            const lat =
                Number(
                    lf.latitude
                );
  
            const lng =
                Number(
                    lf.longitude
                );
  
  
            if (
                Number.isFinite(lat)
                &&
                Number.isFinite(lng)
            ) {
  
                selectedProperty = {
  
                    latitude: lat,
  
                    longitude: lng,
  
                    city: city,
  
                    locality: locality,
  
                    property_type:
                        propertyType,
  
                    area_sqft:
                        area,
  
                    bhk: bhk,
  
                    price:
                        predictionData
                            .predicted_price
  
                };
  
            }
        }
  
  
        /* =====================================================
           GET COMPARABLES
        ====================================================== */
  
        let comparables = [];
  
  
        try {
  
            const response =
                await fetch(
                    "/api/map/comparables",
                    {
                        method: "POST",
  
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
  
                        body: JSON.stringify({
  
                            property_type:
                                propertyType,
  
                            city:
                                city,
  
                            locality:
                                locality,
  
                            area_sqft:
                                area,
  
                            bhk:
                                bhk,
  
                            bathrooms:
                                Number(
                                    predictionData
                                        .bathrooms
                                    || 2
                                ),
  
                            property_age:
                                Number(
                                    predictionData
                                        .property_age
                                    || 5
                                )
  
                        })
                    }
                );
  
  
            if (response.ok) {
  
                const data =
                    await response.json();
  
  
                comparables =
                    Array.isArray(
                        data.properties
                    )
                        ? data.properties
                        : [];
  
            }
  
  
        } catch (error) {
  
            console.warn(
                "Comparable map data unavailable:",
                error
            );
  
        }
  
  
        /* =====================================================
           DATASET FALLBACK FOR MAP 2
           If the comparable engine returns no rows,
           use actual dataset properties from the same
           city/locality/property type.
        ====================================================== */
  
        if (
            comparables.length === 0
            &&
            city
        ) {
  
            try {
  
                const fallbackParams =
                    new URLSearchParams({
  
                        city:
                            city,
  
                        locality:
                            locality,
  
                        property_type:
                            propertyType
  
                    });
  
  
                const fallbackResponse =
                    await fetch(
                        "/api/map/properties?" +
                        fallbackParams.toString()
                    );
  
  
                if (fallbackResponse.ok) {
  
                    const fallbackData =
                        await fallbackResponse.json();
  
  
                    comparables =
                        Array.isArray(
                            fallbackData.properties
                        )
                            ? fallbackData.properties
                            : [];
  
                }
  
  
            } catch (error) {
  
                console.warn(
                    "Dataset comparable fallback unavailable:",
                    error
                );
  
            }
  
        }
  
  
        /*
         * Keep only real latitude/longitude records.
         * The dataset itself is NOT changed.
         * The 15-marker limit only prevents Map 2 from becoming
         * visually overloaded.
         */
  
        comparables =
            comparables
                .filter(
                    function (property) {
  
                        return (
                            Number.isFinite(
                                Number(
                                    property.latitude
                                )
                            )
                            &&
                            Number.isFinite(
                                Number(
                                    property.longitude
                                )
                            )
                        );
  
                    }
                )
                .slice(0, 15);
  
  
        /* =====================================================
           DETERMINE MAP CENTER
        ====================================================== */
  
        let center = {
  
            lat: 17.385,
  
            lng: 78.4867
  
        };
  
  
        if (selectedProperty) {
  
            const lat =
                Number(
                    selectedProperty
                        .latitude
                );
  
            const lng =
                Number(
                    selectedProperty
                        .longitude
                );
  
  
            if (
                Number.isFinite(lat)
                &&
                Number.isFinite(lng)
            ) {
  
                center = {
  
                    lat: lat,
  
                    lng: lng
  
                };
  
            }
        }
  
  
        propertyComparablesMap =
            createMap(
                "propertyComparablesMap",
                center,
                14
            );
  
  
        if (!propertyComparablesMap) {
            return;
        }
  
  
        const bounds =
            L.latLngBounds();
  
  
        /* =====================================================
           SELECTED PROPERTY MARKER
        ====================================================== */
  
        if (selectedProperty) {
  
            const lat =
                Number(
                    selectedProperty.latitude
                );
  
            const lng =
                Number(
                    selectedProperty.longitude
                );
  
  
            if (
                Number.isFinite(lat)
                &&
                Number.isFinite(lng)
            ) {
  
                const marker =
                    L.marker(
                        [lat, lng],
                        {
                            icon:
                                createLeafletIcon(
                                    COLORS.Selected,
                                    true
                                )
                        }
                    )
                    .addTo(
                        propertyComparablesMap
                    );
  
  
                marker.bindPopup(
  
                    "<strong>Selected Property</strong><br>" +
  
                    (
                        selectedProperty
                            .property_type
                        || propertyType
                    ) +
  
                    "<br>" +
  
                    (
                        selectedProperty
                            .locality
                        || locality
                    ) +
  
                    "<br>" +
  
                    (
                        selectedProperty.area_sqft
                            ? Number(
                                selectedProperty
                                    .area_sqft
                              ).toLocaleString(
                                  "en-IN"
                              ) +
                              " sqft<br>"
                            : ""
                    ) +
  
                    (
                        selectedProperty.price
                            ? "INR " +
                              Number(
                                selectedProperty.price
                              ).toLocaleString(
                                  "en-IN"
                              )
                            : ""
                    )
  
                );
  
  
                bounds.extend(
                    [lat, lng]
                );
  
            }
        }
  
  
        /* =====================================================
           COMPARABLE PROPERTY MARKERS
        ====================================================== */
  
        comparables.forEach(
            function (property) {
  
                const lat =
                    Number(
                        property.latitude
                    );
  
                const lng =
                    Number(
                        property.longitude
                    );
  
  
                if (
                    !Number.isFinite(lat)
                    ||
                    !Number.isFinite(lng)
                ) {
                    return;
                }
  
  
                const type =
                    property.property_type
                    || "Apartment";
  
  
                const color =
                    COLORS[type]
                    || COLORS.Apartment;
  
  
                const marker =
                    L.marker(
                        [lat, lng],
                        {
                            icon:
                                createLeafletIcon(
                                    color,
                                    false
                                )
                        }
                    )
                    .addTo(
                        propertyComparablesMap
                    );
  
  
                marker.bindPopup(
  
                    "<strong>" +
                    type +
                    "</strong><br>" +
  
                    (
                        property.locality
                        || ""
                    ) +
  
                    "<br>" +
  
                    (
                        property.area_sqft
                            ? Number(
                                property.area_sqft
                              ).toLocaleString(
                                  "en-IN"
                              ) +
                              " sqft<br>"
                            : ""
                    ) +
  
                    (
                        property.bhk
                            ? property.bhk +
                              " BHK<br>"
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
  
                );
  
  
                comparableMarkers.push(
                    marker
                );
  
  
                bounds.extend(
                    [lat, lng]
                );
  
            }
        );
  
  
        if (!bounds.isEmpty()) {
  
            propertyComparablesMap
                .fitBounds(
                    bounds.pad(0.2)
                );
  
        }
  
  
        setTimeout(
            function () {
  
                propertyComparablesMap
                    .invalidateSize();
  
            },
            100
        );
  
    }
  
  
    /* =========================================================
       MAP 3
       PROPERTY TYPES IN SELECTED AREA
    ========================================================== */
  
    async function loadPropertyTypesMap(
        city,
        locality
    ) {
  
        if (!city || !locality) {
            return;
        }
  
  
        const element =
            document.getElementById(
                "propertyTypesMap"
            );
  
  
        if (!element) {
            return;
        }
  
  
        if (propertyTypesMap) {
  
            propertyTypesMap.remove();
  
            propertyTypesMap =
                null;
        }
  
  
        propertyTypeMarkers = [];
  
  
        let properties = [];
  
  
        try {
  
            const url =
                "/api/map/properties?" +
                new URLSearchParams({
  
                    city: city,
  
                    locality: locality
  
                }).toString();
  
  
            const response =
                await fetch(url);
  
  
            const data =
                await response.json();
  
  
            properties =
                data.properties || [];
  
  
        } catch (error) {
  
            console.warn(
                "Area property map unavailable:",
                error
            );
  
            return;
        }
  
  
        const validProperties =
            properties.filter(
                function (property) {
  
                    return Number.isFinite(
                        Number(
                            property.latitude
                        )
                    )
                    &&
                    Number.isFinite(
                        Number(
                            property.longitude
                        )
                    );
  
                }
            );
  
  
        if (
            validProperties.length === 0
        ) {
  
            element.innerHTML =
                '<div style="padding:20px;text-align:center;color:#64748b;">' +
                "No property coordinates available for this locality." +
                "</div>";
  
            return;
        }
  
  
        const first =
            validProperties[0];
  
  
        propertyTypesMap =
            createMap(
                "propertyTypesMap",
                {
                    lat:
                        Number(
                            first.latitude
                        ),
  
                    lng:
                        Number(
                            first.longitude
                        )
                },
                13
            );
  
  
        if (!propertyTypesMap) {
            return;
        }
  
  
        const bounds =
            L.latLngBounds();
  
  
        validProperties.forEach(
            function (property) {
  
                const lat =
                    Number(
                        property.latitude
                    );
  
                const lng =
                    Number(
                        property.longitude
                    );
  
  
                const type =
                    property.property_type
                    || "Apartment";
  
  
                const color =
                    COLORS[type]
                    || COLORS.Apartment;
  
  
                const marker =
                    L.marker(
                        [lat, lng],
                        {
                            icon:
                                createLeafletIcon(
                                    color,
                                    false
                                )
                        }
                    )
                    .addTo(
                        propertyTypesMap
                    );
  
  
                marker.bindPopup(
  
                    "<strong>" +
                    type +
                    "</strong><br>" +
  
                    (
                        property.locality
                        || locality
                    ) +
  
                    "<br>" +
  
                    (
                        property.area_sqft
                            ? Number(
                                property.area_sqft
                              ).toLocaleString(
                                  "en-IN"
                              ) +
                              " sqft<br>"
                            : ""
                    ) +
  
                    (
                        property.bhk
                            ? property.bhk +
                              " BHK<br>"
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
                    ) +
  
                    (
                        property.approximate
                            ? "<br><small>Area-level location</small>"
                            : ""
                    )
  
                );
  
  
                propertyTypeMarkers.push(
                    marker
                );
  
  
                bounds.extend(
                    [lat, lng]
                );
  
            }
        );
  
  
        if (!bounds.isEmpty()) {
  
            propertyTypesMap
                .fitBounds(
                    bounds.pad(0.15)
                );
  
        }
  
  
        setTimeout(
            function () {
  
                propertyTypesMap
                    .invalidateSize();
  
            },
            100
        );
  
    }
  
    /* =========================================================
    THIRD MAP DROPDOWNS
    Uses the project's existing /api/map/options endpoint.
    This does NOT modify Map 1, Map 2, or any other dashboard
    output.
 ========================================================== */
 
 async function setupAreaSelectors() {
 
     const citySelect =
         document.getElementById(
             "threeMapCity"
         );
 
     const localitySelect =
         document.getElementById(
             "threeMapLocality"
         );
 
 
     if (
         !citySelect ||
         !localitySelect
     ) {
         console.warn(
             "Map 3 dropdown elements were not found."
         );
 
         return;
     }
 
 
     /* =====================================================
        LOAD REAL CITY/LOCALITY DATA FROM FLASK
     ====================================================== */
 
     let mapOptions = null;
 
 
     try {
 
         const response =
             await fetch(
                 "/api/map/options",
                 {
                     method: "GET",
                     headers: {
                         "Accept":
                             "application/json"
                     },
                     cache: "no-store"
                 }
             );
 
 
         if (!response.ok) {
 
             throw new Error(
                 "Map options request failed: " +
                 response.status
             );
 
         }
 
 
         mapOptions =
             await response.json();
 
 
     } catch (error) {
 
         console.error(
             "Unable to load Map 3 city/locality options:",
             error
         );
 
         localitySelect.innerHTML =
             '<option value="">Unable to load localities</option>';
 
         localitySelect.disabled =
             true;
 
         return;
     }
 
 
     /* =====================================================
        LOCALITIES DATA
     ====================================================== */
 
     const localitiesData =
         mapOptions &&
         mapOptions.localities
             ? mapOptions.localities
             : {};
 
 
     /*
      * Normalize locality lookup so:
      *
      * Hyderabad
      * hyderabad
      * HYDERABAD
      *
      * are treated as the same city.
      */
 
     function getLocalitiesForCity(
         selectedCity
     ) {
 
         const city =
             String(
                 selectedCity || ""
             ).trim();
 
 
         if (!city) {
             return [];
         }
 
 
         /* -------------------------------------------------
            Normal object structure:
            {
                Hyderabad: [...]
            }
         -------------------------------------------------- */
 
         if (
             localitiesData &&
             typeof localitiesData === "object" &&
             !Array.isArray(localitiesData)
         ) {
 
             if (
                 Array.isArray(
                     localitiesData[city]
                 )
             ) {
 
                 return localitiesData[city];
 
             }
 
 
             const matchingKey =
                 Object.keys(
                     localitiesData
                 ).find(
                     function (key) {
 
                         return (
                             String(key)
                                 .trim()
                                 .toLowerCase()
                             ===
                             city.toLowerCase()
                         );
 
                     }
                 );
 
 
             if (
                 matchingKey &&
                 Array.isArray(
                     localitiesData[
                         matchingKey
                     ]
                 )
             ) {
 
                 return localitiesData[
                     matchingKey
                 ];
 
             }
 
         }
 
 
         return [];
     }
 
 
     /* =====================================================
        POPULATE LOCALITY DROPDOWN
     ====================================================== */
 
     function populateLocalities(
         selectedCity
     ) {
 
         const city =
             String(
                 selectedCity || ""
             ).trim();
 
 
         localitySelect.innerHTML =
             '<option value="">Select Locality</option>';
 
 
         localitySelect.disabled =
             true;
 
 
         if (!city) {
             return;
         }
 
 
         const localities =
             getLocalitiesForCity(
                 city
             );
 
 
         if (
             !Array.isArray(
                 localities
             ) ||
             localities.length === 0
         ) {
 
             localitySelect.innerHTML =
                 '<option value="">No localities available</option>';
 
             localitySelect.disabled =
                 true;
 
             return;
         }
 
 
         /*
          * Remove duplicates while preserving
          * the dataset/API ordering.
          */
 
         const uniqueLocalities =
             Array.from(
                 new Set(
                     localities
                         .map(
                             function (locality) {
 
                                 return String(
                                     locality || ""
                                 ).trim();
 
                             }
                         )
                         .filter(
                             function (locality) {
 
                                 return locality.length > 0;
 
                             }
                         )
                 )
             );
 
 
         uniqueLocalities.forEach(
             function (locality) {
 
                 const option =
                     document.createElement(
                         "option"
                     );
 
 
                 option.value =
                     locality;
 
                 option.textContent =
                     locality;
 
 
                 localitySelect
                     .appendChild(
                         option
                     );
 
             }
         );
 
 
         localitySelect.disabled =
             uniqueLocalities.length === 0;
 
     }
 
 
     /* =====================================================
        CITY CHANGE
     ====================================================== */
 
     citySelect.addEventListener(
         "change",
         function () {
 
             /*
              * Changing the city must only update
              * Map 3's locality selector.
              *
              * It must NOT affect Map 1 or Map 2.
              */
 
             populateLocalities(
                 this.value
             );
 
 
             /*
              * Remove the old Map 3 only.
              */
 
             if (
                 propertyTypesMap
             ) {
 
                 propertyTypesMap.remove();
 
                 propertyTypesMap =
                     null;
 
             }
 
 
             const mapContainer =
                 document.getElementById(
                     "propertyTypesMap"
                 );
 
 
             if (
                 mapContainer
             ) {
 
                 mapContainer.innerHTML =
                     "";
 
             }
 
         }
     );
 
 
     /* =====================================================
        LOCALITY CHANGE
     ====================================================== */
 
     localitySelect.addEventListener(
         "change",
         async function () {
 
             const city =
                 String(
                     citySelect.value || ""
                 ).trim();
 
 
             const locality =
                 String(
                     this.value || ""
                 ).trim();
 
 
             if (
                 !city ||
                 !locality
             ) {
 
                 return;
 
             }
 
 
             /*
              * IMPORTANT:
              * Only Map 3 is updated here.
              */
 
             await loadPropertyTypesMap(
                 city,
                 locality
             );
 
         }
     );
 
 
     /* =====================================================
        INITIALIZE CURRENT CITY
     ====================================================== */
 
     const initialCity =
         String(
             citySelect.value || ""
         ).trim();
 
 
     if (initialCity) {
 
         populateLocalities(
             initialCity
         );
 
     }
 
 }
 
 
 /* =========================================================
    MAIN FUNCTION
    Map 1 + Map 2 only.
    Map 3 remains controlled by its own dropdowns.
 ========================================================== */
 
 window.PW_renderThreeMaps =
     async function (
         predictionData,
         inputData
     ) {
 
         predictionData =
             predictionData
             || {};
 
 
         inputData =
             inputData
             || {};
 
 
         const merged =
             Object.assign(
                 {},
                 predictionData,
                 inputData
             );
 
 
         /*
          * Do NOT render Map 3 automatically
          * after prediction.
          *
          * Map 3 is controlled independently by:
          *
          * City → Locality → Map
          */
 
         await Promise.all([
 
             renderSelectedLocationMap(
                 merged
             ),
 
             renderPropertyComparablesMap(
                 merged
             )
 
         ]);
 
     };
 
 
 /* =========================================================
    INITIALIZE MAP 3
 
    Since propwise_maps.js is loaded at the bottom of
    admin_dashboard.html, the DOM elements already exist.
    We can initialize immediately, but the readyState check
    makes it safe in both cases.
 ========================================================== */
 
 function initializeMap3() {
 
     setupAreaSelectors()
         .catch(
             function (error) {
 
                 console.error(
                     "Map 3 initialization failed:",
                     error
                 );
 
             }
         );
 
 }
 
 
 if (
     document.readyState ===
     "loading"
 ) {
 
     document.addEventListener(
         "DOMContentLoaded",
         initializeMap3
     );
 
 } else {
 
     initializeMap3();
 
 }
 
 
 /* =========================================================
    KEEP THIS GLOBAL FUNCTION FOR COMPATIBILITY
 
    Existing dashboard code can still call this safely.
 ========================================================== */
 
 window.PW_initThreeMapControls =
     function () {
 
         initializeMap3();
 
     };
 
 
 })();