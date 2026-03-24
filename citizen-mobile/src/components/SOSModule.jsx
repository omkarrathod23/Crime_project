import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { ShieldAlert, X, MapPin, Radio, Wifi, Zap, Building2 } from 'lucide-react';
import { io } from 'socket.io-client';
import api, { API_BASE_URL } from '../services/api';
import { useAuth } from '../context/AuthContext';
import trackingService from '../services/TrackingService';

const SOSModule = ({ onClose }) => {
  const { user } = useAuth();
  const [status, setStatus] = useState('initializing'); // initializing, transmitting, active, error
  const [location, setLocation] = useState(null);
  const [timer, setTimer] = useState(0);
  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState('');
  const socketRef = useRef(null);
  const [sosId, setSosId] = useState(null);

  useEffect(() => {
    // 1. Fetch Stations
    const fetchStations = async () => {
      try {
        const response = await api.get('/api/police/stations');
        setStations(response.data);
      } catch (err) {
        console.error('Failed to fetch stations');
      }
    };
    fetchStations();

    // 2. Get Geolocation
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const loc = { lat: pos.coords.latitude, lon: pos.coords.longitude };
          setLocation(loc);
          setStatus('ready');
        },
        (err) => {
          console.error('Geo error:', err);
          setStatus('error');
        }
      );
    }

    // 3. Initialize Socket.IO
    socketRef.current = io(API_BASE_URL);
    
    return () => {
      if (socketRef.current) socketRef.current.disconnect();
      trackingService.stopTracking();
    };
  }, []);

  const triggerSOS = async () => {
    if (!location) return;
    try {
      setStatus('transmitting');
      const response = await api.post('/sos/trigger', {
        latitude: location.lat,
        longitude: location.lon,
        selected_station: selectedStation || undefined
      });
      setSosId(response.data.sos_id);
      setStatus('active');
      
      // Start Live Tracking
      trackingService.startLiveTracking(response.data.sos_id);
      
      // Join room for real-time updates if backend supports it
      if (socketRef.current) {
        socketRef.current.emit('join', { room: response.data.assigned_station });
      }
    } catch (err) {
      console.error('SOS Trigger failed:', err);
      setStatus('error');
    }
  };

  useEffect(() => {
    let interval;
    if (status === 'active') {
      interval = setInterval(() => setTimer(t => t + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [status]);

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center p-6"
    >
      <div className="absolute inset-0 bg-red-950/95 backdrop-blur-2xl"></div>
      
      <motion.div 
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        className="glass-card w-full max-w-sm pt-12 pb-8 px-8 relative z-10 border-red-500/50 shadow-[0_0_50px_rgba(220,38,38,0.3)]"
      >
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-white/30 hover:text-white transition-colors"
        >
          <X size={24} />
        </button>

        <div className="flex flex-col items-center">
          <div className="relative mb-8">
            <motion.div 
              animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0.2, 0.5] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="w-24 h-24 bg-red-600/30 rounded-full absolute -inset-0"
            ></motion.div>
            <div className={`w-24 h-24 rounded-full flex items-center justify-center relative z-10 shadow-[0_0_50px_rgba(220,38,38,0.5)] transition-colors duration-500 ${status === 'active' ? 'bg-red-600' : 'bg-slate-800 border border-white/10'}`}>
              <ShieldAlert size={48} className="text-white" />
            </div>
          </div>

          <h1 className="text-2xl font-black text-white text-center tracking-widest uppercase italic">Emergency SOS</h1>
          <p className="text-red-400 text-[10px] tracking-[5px] uppercase mt-2 font-bold">
            {status === 'active' ? 'Signal Transmitting' : 'Uplink Ready'}
          </p>

          <div className="w-full mt-10 space-y-3">
            {status === 'ready' && (
              <div className="relative">
                <Building2 size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                <select
                  className="input-cyber pl-12 py-3 appearance-none !bg-white/5 border-white/10 text-white"
                  value={selectedStation}
                  onChange={(e) => setSelectedStation(e.target.value)}
                >
                  <option value="">AUTO-ASSIGN STATION</option>
                  {stations.map(s => (
                    <option key={s.id} value={s.name} className="bg-slate-900">{s.name}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/5">
              <div className="flex items-center gap-3">
                <Wifi size={18} className="text-cyan-400" />
                <span className="text-[10px] font-black text-white uppercase tracking-widest">Link Status</span>
              </div>
              <span className={`text-[10px] font-bold uppercase tracking-widest ${status === 'active' ? 'text-green-500' : 'text-cyan-400'}`}>
                {status === 'active' ? 'Encrypted' : 'Standby'}
              </span>
            </div>

            <div className="flex items-center justify-between p-4 bg-white/5 rounded-2xl border border-white/5">
              <div className="flex items-center gap-3">
                <MapPin size={18} className="text-cyan-400" />
                <span className="text-[10px] font-black text-white uppercase tracking-widest">Coordinates</span>
              </div>
              <span className="text-[10px] text-slate-400 font-bold font-mono">
                {location ? `${location.lat.toFixed(4)}, ${location.lon.toFixed(4)}` : "LOCKING..."}
              </span>
            </div>

            {status === 'active' && (
              <div className="flex items-center justify-between p-4 bg-red-500/10 rounded-2xl border border-red-500/20 animate-pulse">
                <div className="flex items-center gap-3 text-red-500">
                  <Radio size={18} />
                  <span className="text-[10px] font-black uppercase tracking-widest">Active Ping</span>
                </div>
                <span className="text-sm font-black text-red-500">{Math.floor(timer/60)}:{(timer%60).toString().padStart(2, '0')}</span>
              </div>
            )}
          </div>

          {status === 'ready' ? (
            <button 
              onClick={triggerSOS}
              className="w-full py-5 bg-red-600 rounded-2xl text-xs font-black text-white tracking-[4px] uppercase mt-10 shadow-[0_0_30px_rgba(220,38,38,0.4)] active:scale-95 transition-all"
            >
              Confirm SOS Uplink
            </button>
          ) : status === 'active' ? (
            <button 
              onClick={onClose}
              className="w-full py-5 bg-white/5 rounded-2xl text-[10px] font-black text-white tracking-[4px] uppercase mt-10 border border-white/10 hover:bg-white/10 transition-all"
            >
              Abort Transmission
            </button>
          ) : status === 'transmitting' ? (
            <div className="w-full py-5 text-center text-[10px] font-black text-red-500 tracking-[4px] uppercase mt-10 animate-pulse">
              Negotiating Link...
            </div>
          ) : (
            <button 
              onClick={() => window.location.reload()}
              className="w-full py-5 bg-slate-800 rounded-2xl text-[10px] font-black text-white tracking-[4px] uppercase mt-10"
            >
              Re-initialize System
            </button>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default SOSModule;
