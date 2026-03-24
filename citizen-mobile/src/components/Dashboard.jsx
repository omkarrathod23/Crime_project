import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, LogOut, MapPin, Navigation, Shield, CheckCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [step, setStep] = useState('standby'); // standby, locating, selecting, sending, active
  const [location, setLocation] = useState(null);
  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);
  const [sosId, setSosId] = useState(null);
  const [error, setError] = useState(null);
  
  const trackingInterval = useRef(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (trackingInterval.current) clearInterval(trackingInterval.current);
    };
  }, []);

  const startSOSFlow = () => {
    setStep('locating');
    setError(null);
    
    if (!navigator.geolocation) {
      setError('Geolocation not supported');
      setStep('standby');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const coords = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        setLocation(coords);
        fetchNearestStations(coords);
      },
      (err) => {
        console.error('Geo error:', err);
        setError('Could not lock location');
        setStep('standby');
      },
      { enableHighAccuracy: true, timeout: 5000 }
    );
  };

  const fetchNearestStations = async (coords) => {
    try {
      const response = await api.get(`/sos/nearest-stations?lat=${coords.lat}&lon=${coords.lon}`);
      setStations(response.data);
      setStep('selecting');
    } catch (err) {
      console.error('Failed to fetch stations:', err);
      if (err.response && err.response.status === 401) {
        setError('Session Stale. Please Logout and Login again.');
      } else {
        setError('Failed to reach command center');
      }
      setStep('standby');
    }
  };

  const sendSOS = async (stationName) => {
    setSelectedStation(stationName);
    setStep('sending');
    try {
      const response = await api.post('/sos/trigger', {
        lat: location.lat,
        lon: location.lon,
        selected_station: stationName
      });
      setSosId(response.data.sos_id);
      setStep('active');
      startLiveTracking(response.data.sos_id);
    } catch (err) {
      console.error('SOS failed:', err);
      if (err.response && err.response.status === 401) {
        setError('Session Stale. Please Re-login.');
      } else {
        setError('Transmission Failed');
      }
      setStep('standby');
    }
  };

  const startLiveTracking = (id) => {
    if (trackingInterval.current) {
        if (typeof trackingInterval.current === 'number') {
            navigator.geolocation.clearWatch(trackingInterval.current);
        } else {
            clearInterval(trackingInterval.current);
        }
    }
    
    trackingInterval.current = navigator.geolocation.watchPosition(
      (pos) => {
        api.post('/sos/update-location', {
          sos_id: id,
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude
        }).catch(err => console.error('Tracking update failed', err));
      },
      (err) => console.error('Watch error:', err),
      { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
    );
  };

  const abortSOS = () => {
    if (trackingInterval.current) {
        if (typeof trackingInterval.current === 'number') {
            navigator.geolocation.clearWatch(trackingInterval.current);
        } else {
            clearInterval(trackingInterval.current);
        }
    }
    setStep('standby');
    setSosId(null);
    setSelectedStation(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-white relative overflow-hidden">
      {/* Background Dynamics */}
      <div className={`absolute inset-0 transition-colors duration-1000 ${
        step === 'active' ? 'bg-red-950/40' : 'bg-transparent'
      }`}></div>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,#ef444415,transparent_70%)]"></div>

      {/* Header HUD */}
      <div className="absolute top-0 left-0 right-0 p-6 flex justify-between items-center z-20">
        <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center border transition-all ${
                step === 'active' ? 'bg-red-500/20 border-red-500' : 'bg-slate-900 border-white/10'
            }`}>
                <ShieldAlert className={step === 'active' ? 'text-red-500' : 'text-slate-400'} size={18} />
            </div>
            <div>
                <h1 className="text-sm font-black tracking-[3px] uppercase italic text-white leading-none">Sentinel:Mobile</h1>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mt-1">Uplink: {step === 'active' ? 'ACTIVE' : 'READY'}</p>
            </div>
        </div>
        <button onClick={logout} className="p-2.5 bg-white/5 rounded-xl border border-white/10 hover:bg-white/10 transition-all">
          <LogOut size={18} className="text-slate-400" />
        </button>
      </div>

      <AnimatePresence mode="wait">
        {step === 'standby' && (
          <motion.div 
            key="standby"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.1 }}
            className="flex flex-col items-center gap-12 relative z-10 w-full max-w-xs"
          >
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={startSOSFlow}
              className="w-64 h-64 rounded-full bg-red-600 shadow-[0_0_80px_rgba(220,38,38,0.4)] flex items-center justify-center relative group"
            >
              <div className="absolute inset-0 rounded-full bg-white/5 animate-pulse"></div>
              <div className="flex flex-col items-center gap-2">
                <ShieldAlert size={80} className="text-white drop-shadow-2xl" />
                <span className="font-black text-3xl tracking-tighter uppercase italic">SOS</span>
              </div>
            </motion.button>

            <div className="text-center">
              <h2 className="text-slate-400 text-[10px] font-black tracking-[5px] uppercase mb-4">Tactical Emergency Trigger</h2>
              {error && <p className="text-red-500 text-xs font-bold uppercase animate-bounce">{error}</p>}
            </div>
          </motion.div>
        )}

        {step === 'locating' && (
          <motion.div 
            key="locating"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center gap-8 z-10"
          >
            <div className="w-20 h-20 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center relative">
                <Navigation size={32} className="text-cyan-400 animate-pulse" />
                <motion.div 
                    animate={{ rotate: 360 }}
                    transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                    className="absolute inset-0 border-2 border-transparent border-t-cyan-500 rounded-2xl"
                />
            </div>
            <p className="text-sm font-black tracking-[4px] uppercase text-cyan-400">Locking Coordinates...</p>
          </motion.div>
        )}

        {step === 'selecting' && (
          <motion.div 
            key="selecting"
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="w-full max-w-sm z-10 space-y-6"
          >
            <div className="text-center space-y-2 mb-8">
                <h3 className="text-xl font-black italic uppercase">Select Response Unit</h3>
                <p className="text-slate-500 text-[10px] tracking-widest font-bold uppercase">Nearest units detected via Haversine scan</p>
            </div>

            <div className="space-y-4">
                {stations.map((s, idx) => (
                    <motion.button
                        initial={{ x: -20, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: idx * 0.1 }}
                        key={s.name}
                        onClick={() => sendSOS(s.name)}
                        className="w-full p-5 glass-card bg-white/5 border-white/5 flex items-center justify-between group hover:bg-white/10 hover:border-cyan-500/30 transition-all"
                    >
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-xl bg-slate-900 border border-white/10 flex items-center justify-center text-slate-500 group-hover:text-cyan-400">
                                <Shield size={20} />
                            </div>
                            <div className="text-left">
                                <h4 className="text-sm font-black uppercase text-white tracking-widest leading-none">{s.name}</h4>
                                <p className="text-[10px] text-slate-500 font-bold uppercase mt-1">{s.city}</p>
                            </div>
                        </div>
                        <div className="text-right">
                            <span className="text-xs font-black text-cyan-400">{s.distance} KM</span>
                        </div>
                    </motion.button>
                ))}
            </div>

            <button 
                onClick={() => setStep('standby')}
                className="w-full py-4 text-[10px] font-black text-slate-500 hover:text-white tracking-[4px] uppercase transition-colors"
             >
                Cancel Transmission
            </button>
          </motion.div>
        )}

        {(step === 'sending' || step === 'active') && (
            <motion.div 
                key="active"
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="flex flex-col items-center gap-10 z-10 w-full max-w-xs"
            >
                <div className="relative">
                    <motion.div 
                        animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
                        transition={{ repeat: Infinity, duration: 1.5 }}
                        className="absolute inset-0 rounded-full border-4 border-red-500"
                    />
                    <div className="w-48 h-48 rounded-full bg-red-600 flex items-center justify-center shadow-[0_0_60px_rgba(220,38,38,0.5)]">
                        <ShieldAlert size={64} className="text-white animate-pulse" />
                    </div>
                </div>

                <div className="text-center space-y-4">
                    <h3 className="text-2xl font-black italic uppercase text-white">
                        {step === 'sending' ? 'Transmitting...' : 'Alert Active'}
                    </h3>
                    <div className="px-4 py-2 bg-red-500/10 rounded-full border border-red-500/20 inline-block">
                        <span className="text-[10px] font-black text-red-500 uppercase tracking-[2px]">
                            {selectedStation} Responsive
                        </span>
                    </div>
                    <div className="flex items-center justify-center gap-4 mt-6">
                        <div className="flex flex-col items-center">
                            <span className="text-[8px] text-slate-500 uppercase font-bold tracking-widest">Signal</span>
                            <span className="text-xs font-black text-green-500">ENCRYPTED</span>
                        </div>
                        <div className="w-px h-8 bg-white/10" />
                        <div className="flex flex-col items-center">
                            <span className="text-[8px] text-slate-500 uppercase font-bold tracking-widest">Protocol</span>
                            <span className="text-xs font-black text-white">X-STREAM</span>
                        </div>
                    </div>
                </div>

                <button 
                    onClick={abortSOS}
                    className="mt-6 px-10 py-4 bg-white/5 rounded-2xl border border-white/10 text-[10px] font-black text-slate-400 tracking-[5px] uppercase hover:bg-white/10 hover:text-white transition-all"
                >
                    Terminate SOS
                </button>
            </motion.div>
        )}
      </AnimatePresence>

      {/* Identity Banner */}
      {step === 'standby' && (
        <div className="absolute bottom-12 px-8 py-3 bg-white/5 rounded-2xl border border-white/5 backdrop-blur-xl">
            <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.5)]"></div>
                <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Node: {user?.name || 'Authorized Citizen'}</span>
            </div>
        </div>
      )}

      {/* Footer Meta */}
      <div className="absolute bottom-6 text-[8px] text-slate-700 font-bold uppercase tracking-[6px] opacity-40">
        Emergency Uplink Protocol v2.5.0
      </div>
    </div>
  );
};

export default Dashboard;
