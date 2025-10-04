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

      // Add a marker at the center
      this.marker = L.marker([this.latitudeValue, this.longitudeValue]).addTo(this.map)
        .bindPopup('A pretty CSS3 popup.<br> Easily customizable.')
        .openPopup()

      // Add click event to add markers
      this.map.on('click', (e) => {
        this.addMarker(e.latlng)
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
}