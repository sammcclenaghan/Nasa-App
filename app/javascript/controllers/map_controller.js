import { Controller } from "@hotwired/stimulus"

export default class extends Controller {
  static targets = ["map"]
  static values = { 
    latitude: { type: Number, default: 40.7128 },
    longitude: { type: Number, default: -74.0060 },
    zoom: { type: Number, default: 13 }
  }

  connect() {
    console.log('Map controller connected!')
    this.initializeMap()
  }

  disconnect() {
    if (this.map) {
      this.map.remove()
    }
  }

  initializeMap() {
    try {
      console.log('Initializing map...')
      
      // Wait for Leaflet to be available
      if (typeof window.L === 'undefined') {
        console.log('Leaflet not loaded yet, waiting...')
        setTimeout(() => this.initializeMap(), 100)
        return
      }
      
      const L = window.L
      console.log('L (Leaflet):', L)
      
      // Fix for default markers in Leaflet with Webpack/import maps
      delete L.Icon.Default.prototype._getIconUrl
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
        iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
      })

      // Initialize the map
      this.map = L.map(this.element).setView([this.latitudeValue, this.longitudeValue], this.zoomValue)

      // Add Humanitarian OpenStreetMap tile layer
      L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles courtesy of <a href="https://hot.openstreetmap.org/" target="_blank">Humanitarian OpenStreetMap Team</a>',
        maxZoom: 19
      }).addTo(this.map)

      // Initialize the feature group to store editable layers
      this.drawnItems = new L.FeatureGroup()
      this.map.addLayer(this.drawnItems)

      // Initialize the draw control and pass it the FeatureGroup of editable layers
      this.drawControl = new L.Control.Draw({
        edit: {
          featureGroup: this.drawnItems
        },
        draw: {
          // Disable all drawing tools except rectangle
          polygon: false,
          polyline: false,
          circle: false,
          marker: false,
          circlemarker: false,
          rectangle: {
            shapeOptions: {
              color: '#ff7800',
              weight: 2,
              fillOpacity: 0.2
            }
          }
        }
      })
      this.map.addControl(this.drawControl)

      // Add event listeners for drawing
      this.map.on(L.Draw.Event.CREATED, (event) => {
        const layer = event.layer
        this.drawnItems.addLayer(layer)
        this.updateFormFromRectangle(layer)
      })

      this.map.on(L.Draw.Event.EDITED, (event) => {
        const layers = event.layers
        layers.eachLayer((layer) => {
          this.updateFormFromRectangle(layer)
        })
      })

      this.map.on(L.Draw.Event.DELETED, (event) => {
        this.clearFormFields()
      })
      
      console.log('Map initialized successfully!')
    } catch (error) {
      console.error('Error initializing map:', error)
    }
  }

  addMarker(latlng) {
    const L = window.L
    L.marker(latlng).addTo(this.map)
      .bindPopup(`Lat: ${latlng.lat.toFixed(4)}, Lng: ${latlng.lng.toFixed(4)}`)
      .openPopup()
  }

  // Method to update map center
  setCenter(lat, lng) {
    if (this.map) {
      this.map.setView([lat, lng], this.zoomValue)
      this.marker.setLatLng([lat, lng])
    }
  }

  // Method to add a marker at specific coordinates
  addMarkerAt(lat, lng, popupText = '') {
    if (this.map) {
      const L = window.L
      L.marker([lat, lng]).addTo(this.map)
        .bindPopup(popupText || `Lat: ${lat}, Lng: ${lng}`)
    }
  }

  updateFormFromRectangle(rectangle) {
    try {
      const bounds = rectangle.getBounds()
      const southWest = bounds.getSouthWest()
      const northEast = bounds.getNorthEast()
      
      // Calculate center point
      const centerLat = (southWest.lat + northEast.lat) / 2
      const centerLng = (southWest.lng + northEast.lng) / 2
      
      // Update form fields
      const latField = document.querySelector('input[name="weather_result[lat]"]')
      const lngField = document.querySelector('input[name="weather_result[lon]"]')
      
      if (latField) latField.value = centerLat.toFixed(6)
      if (lngField) lngField.value = centerLng.toFixed(6)
      
      console.log('Form updated with rectangle bounds:', {
        center: { lat: centerLat, lng: centerLng },
        bounds: {
          southWest: { lat: southWest.lat, lng: southWest.lng },
          northEast: { lat: northEast.lat, lng: northEast.lng }
        }
      })
      
      // Show a popup with the bounds info
      const L = window.L
      rectangle.bindPopup(`
        <strong>Rectangle Bounds:</strong><br>
        Center: ${centerLat.toFixed(6)}, ${centerLng.toFixed(6)}<br>
        SW: ${southWest.lat.toFixed(6)}, ${southWest.lng.toFixed(6)}<br>
        NE: ${northEast.lat.toFixed(6)}, ${northEast.lng.toFixed(6)}
      `).openPopup()
      
    } catch (error) {
      console.error('Error updating form from rectangle:', error)
    }
  }

  clearFormFields() {
    const latField = document.querySelector('input[name="weather_result[lat]"]')
    const lngField = document.querySelector('input[name="weather_result[lon]"]')
    
    if (latField) latField.value = ''
    if (lngField) lngField.value = ''
    
    console.log('Form fields cleared')
  }
}