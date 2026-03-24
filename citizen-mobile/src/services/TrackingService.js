import api from './api';

class TrackingService {
  constructor() {
    this.watchId = null;
    this.sosId = null;
    this.interval = null;
  }

  startLiveTracking(sosId) {
    this.sosId = sosId;
    if (this.watchId) return;

    if (navigator.geolocation) {
      this.watchId = navigator.geolocation.watchPosition(
        (pos) => {
          this.updateBackend(pos.coords.latitude, pos.coords.longitude);
        },
        (err) => console.error('Tracking Error:', err),
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
      );
    }
  }

  async updateBackend(lat, lon) {
    if (!this.sosId) return;
    try {
      await api.post('/sos/update-location', {
        sos_id: this.sosId,
        latitude: lat,
        longitude: lon
      });
      console.log('Location updated:', lat, lon);
    } catch (err) {
      console.error('Failed to update tracking backend:', err);
    }
  }

  stopTracking() {
    if (this.watchId) {
      navigator.geolocation.clearWatch(this.watchId);
      this.watchId = null;
    }
    this.sosId = null;
  }
}

export default new TrackingService();
