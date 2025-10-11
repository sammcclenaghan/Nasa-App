import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
  static targets = ["map"];
  static values = {
    latitude: { type: Number, default: 40.7128 },
    longitude: { type: Number, default: -74.006 },
    zoom: { type: Number, default: 13 },
  };

  connect() {
    console.log("Map controller connected!");
    this.initializeMap();
  }

  disconnect() {
    if (this.map) {
      try {
        this.map.remove();
      } catch (e) {
        // ignore removal errors
      }
      this.map = null;
    }

    // Remove the resize listener we added during connect/initialize
    if (this._resizeHandler) {
      try {
        window.removeEventListener("resize", this._resizeHandler);
      } catch (e) {
        // ignore
      }
      this._resizeHandler = null;
    }
  }

  initializeMap() {
    try {
      console.log("Initializing map...");

      // Wait for Leaflet to be available
      if (typeof window.L === "undefined") {
        console.log("Leaflet not loaded yet, waiting...");
        setTimeout(() => this.initializeMap(), 100);
        return;
      }

      const L = window.L;
      console.log("L (Leaflet):", L);

      // Fix for default markers in Leaflet with Webpack/import maps
      delete L.Icon.Default.prototype._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl:
          "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
        iconUrl:
          "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
        shadowUrl:
          "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
      });

      // Initialize the map
      this.map = L.map(this.element, { doubleClickZoom: false }).setView(
        [this.latitudeValue, this.longitudeValue],
        this.zoomValue,
      );

      // Add Humanitarian OpenStreetMap tile layer
      L.tileLayer("https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png", {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles courtesy of <a href="https://hot.openstreetmap.org/" target="_blank">Humanitarian OpenStreetMap Team</a>',
        maxZoom: 19,
      }).addTo(this.map);

      // Expose the
      this.drawnItems = new L.FeatureGroup();
      this.map.addLayer(this.drawnItems);

      // Prepare rectangle drawing options (we won't show the side toolbar)
      const rectangleOptions = {
        shapeOptions: {
          color: "#ff7800",
          weight: 2,
          fillOpacity: 0.2,
        },
      };
      this.rectangleDrawerActive = false;

      // If there are already layers in the feature group (for example server-rendered),
      // attach the same click-to-delete handler so all rectangles behave consistently.
      if (this.drawnItems && typeof this.drawnItems.eachLayer === "function") {
        this.drawnItems.eachLayer((layer) => {
          this.attachDeleteHandler(layer);
        });
      }

      // Enable rectangle drawing via double-click (prevents the default double-click zoom)
      this.map.on("dblclick", (e) => {
        if (this.rectangleDrawerActive) return;
        this.rectangleDrawerActive = true;
        // Programmatically enable rectangle drawing
        this.rectangleDrawer = new L.Draw.Rectangle(this.map, rectangleOptions);
        this.rectangleDrawer.enable();
      });

      // Add event listeners for drawing
      this.map.on(L.Draw.Event.CREATED, (event) => {
        const layer = event.layer;

        // Ensure only one rectangle exists: remove any existing rectangles before adding the new one
        try {
          this.removeAllRectangles();
        } catch (e) {
          console.error(
            "Error clearing existing rectangles before adding new one:",
            e,
          );
        }

        this.drawnItems.addLayer(layer);
        this.updateFormFromRectangle(layer);

        // Attach a unified delete handler for this new layer (defined on the controller)
        this.attachDeleteHandler(layer);

        if (this.rectangleDrawer) {
          try {
            this.rectangleDrawer.disable();
          } catch (e) {}
          this.rectangleDrawer = null;
        }
        this.rectangleDrawerActive = false;
      });

      this.map.on(L.Draw.Event.EDITED, (event) => {
        const layers = event.layers;
        layers.eachLayer((layer) => {
          this.updateFormFromRectangle(layer);
        });
      });

      this.map.on(L.Draw.Event.DELETED, (event) => {
        this.clearFormFields();
        if (this.rectangleDrawer) {
          try {
            this.rectangleDrawer.disable();
          } catch (e) {}
          this.rectangleDrawer = null;
        }
        this.rectangleDrawerActive = false;
      });

      console.log("Map initialized successfully!");

      // Ensure Leaflet recalculates the map size after initialization. When the map
      // is initialized while its container is hidden or layout isn't settled
      // (common in containers with sidebars / flex layout in Docker/dev differences),
      // Leaflet can end up with a 0-sized map. Invalidate size after a short delay
      // and also on window resize.
      try {
        // Small timeout to allow the DOM/CSS to settle (helps with layout changes
        // introduced by Tailwind/containers/etc).
        setTimeout(() => {
          try {
            if (this.map && typeof this.map.invalidateSize === "function") {
              this.map.invalidateSize({ animate: false });
            }
          } catch (e) {
            // no-op
          }
        }, 200);
      } catch (e) {
        // no-op
      }

      // Store a named resize handler so we can remove it on disconnect()
      this._resizeHandler = () => {
        try {
          if (this.map && typeof this.map.invalidateSize === "function") {
            this.map.invalidateSize({ animate: false });
          }
        } catch (e) {
          // ignore
        }
      };
      window.addEventListener("resize", this._resizeHandler);
    } catch (error) {
      console.error("Error initializing map:", error);
    }
  }

  // Attach a click handler that asks the user to confirm deletion and removes the layer.
  // Kept as a separate method so it can be reused for newly created AND pre-existing layers.
  attachDeleteHandler(layer) {
    const controller = this;
    const L = window.L;
    layer.on("click", (clickEvent) => {
      // Try to stop propagation so the map doesn't handle the click (best-effort)
      try {
        if (L && L.DomEvent && clickEvent)
          L.DomEvent.stopPropagation(clickEvent);
      } catch (err) {
        // ignore if stopPropagation isn't available
      }

      const shouldDelete = window.confirm("Delete this rectangle?");
      if (shouldDelete) {
        // Prefer removing from the feature group if present
        try {
          if (controller.drawnItems && controller.drawnItems.hasLayer(layer)) {
            controller.drawnItems.removeLayer(layer);
          } else if (typeof layer.remove === "function") {
            layer.remove();
          }
        } catch (err) {
          // fallback: try calling remove on the layer
          try {
            layer.remove();
          } catch (e) {}
        }
        controller.clearFormFields();
      } else {
        // If the user doesn't delete, reopen the popup so info remains visible
        try {
          layer.openPopup();
        } catch (e) {}
      }
    });
  }

  // Remove all existing rectangles from the drawnItems feature group
  removeAllRectangles() {
    try {
      if (!this.drawnItems || typeof this.drawnItems.eachLayer !== "function")
        return;
      const layersToRemove = [];
      this.drawnItems.eachLayer((l) => {
        layersToRemove.push(l);
      });
      layersToRemove.forEach((l) => {
        try {
          if (this.drawnItems && this.drawnItems.hasLayer(l)) {
            this.drawnItems.removeLayer(l);
          } else if (typeof l.remove === "function") {
            l.remove();
          }
        } catch (err) {
          // ignore individual layer remove errors
        }
      });
    } catch (e) {
      console.error("Error removing existing rectangles:", e);
    }
  }

  addMarker(latlng) {
    const L = window.L;
    L.marker(latlng)
      .addTo(this.map)
      .bindPopup(`Lat: ${latlng.lat.toFixed(4)}, Lng: ${latlng.lng.toFixed(4)}`)
      .openPopup();
  }

  // Method to update map center
  setCenter(lat, lng) {
    if (this.map) {
      this.map.setView([lat, lng], this.zoomValue);
      this.marker.setLatLng([lat, lng]);
    }
  }

  // Method to add a marker at specific coordinates
  addMarkerAt(lat, lng, popupText = "") {
    if (this.map) {
      const L = window.L;
      L.marker([lat, lng])
        .addTo(this.map)
        .bindPopup(popupText || `Lat: ${lat}, Lng: ${lng}`);
    }
  }

  updateFormFromRectangle(rectangle) {
    try {
      const bounds = rectangle.getBounds();
      const southWest = bounds.getSouthWest();
      const northEast = bounds.getNorthEast();

      // Calculate center point
      const centerLat = (southWest.lat + northEast.lat) / 2;
      const centerLng = (southWest.lng + northEast.lng) / 2;

      // Update form fields
      const latField = document.querySelector(
        'input[name="weather_result[lat]"]',
      );
      const lngField = document.querySelector(
        'input[name="weather_result[lon]"]',
      );

      if (latField) latField.value = centerLat.toFixed(6);
      if (lngField) lngField.value = centerLng.toFixed(6);

      console.log("Form updated with rectangle bounds:", {
        center: { lat: centerLat, lng: centerLng },
        bounds: {
          southWest: { lat: southWest.lat, lng: southWest.lng },
          northEast: { lat: northEast.lat, lng: northEast.lng },
        },
      });

      // Show a popup with the bounds info
      const L = window.L;
      rectangle
        .bindPopup(
          `
        <strong>Rectangle Bounds:</strong><br>
        Center: ${centerLat.toFixed(6)}, ${centerLng.toFixed(6)}<br>
        SW: ${southWest.lat.toFixed(6)}, ${southWest.lng.toFixed(6)}<br>
        NE: ${northEast.lat.toFixed(6)}, ${northEast.lng.toFixed(6)}
      `,
        )
        .openPopup();
    } catch (error) {
      console.error("Error updating form from rectangle:", error);
    }
  }

  clearFormFields() {
    const latField = document.querySelector(
      'input[name="weather_result[lat]"]',
    );
    const lngField = document.querySelector(
      'input[name="weather_result[lon]"]',
    );

    if (latField) latField.value = "";
    if (lngField) lngField.value = "";

    console.log("Form fields cleared");
  }
}
