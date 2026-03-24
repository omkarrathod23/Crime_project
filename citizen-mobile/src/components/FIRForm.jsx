import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  FileText, 
  MapPin, 
  ChevronLeft, 
  AlertTriangle, 
  Send,
  Camera,
  Layers,
  ShieldAlert,
  Wifi,
  UploadCloud
} from 'lucide-react';
import { motion } from 'framer-motion';
import api from '../services/api';
import { useNavigate } from 'react-router-dom';

const FIRForm = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [stations, setStations] = useState([]);
  const [locationStatus, setLocationStatus] = useState('detecting');
  const [formData, setFormData] = useState({
    crime_type: '',
    description: '',
    latitude: '',
    longitude: '',
    location_name: '',
    selected_station: '',
    priority: 'Medium'
  });

  useEffect(() => {
    const fetchStations = async () => {
      try {
        const response = await api.get('/api/police/stations');
        setStations(response.data);
      } catch (err) {
        console.error('Failed to fetch stations:', err);
      }
    };
    fetchStations();

    // Get current location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setFormData(prev => ({
            ...prev,
            latitude: pos.coords.latitude.toFixed(6),
            longitude: pos.coords.longitude.toFixed(6)
          }));
          setLocationStatus('locked');
        },
        () => setLocationStatus('failed')
      );
    }
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    // Converting to Form Data for backend compatibility
    const data = new FormData();
    Object.keys(formData).forEach(key => data.append(key, formData[key]));
    
    try {
      await api.post('/fir/add/api', data, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      navigate('/');
    } catch (err) {
      console.error('FIR Submission Error:', err);
      alert('Failed to submit report. Please check connection.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 pb-12">
      <header className="p-6 flex items-center gap-4 border-b border-white/5 bg-slate-950/80 sticky top-0 z-30 backdrop-blur-xl">
        <button onClick={() => navigate('/')} className="p-2.5 bg-white/5 rounded-xl text-slate-400 active:bg-cyan-500 active:text-white transition-all">
          <ChevronLeft size={20} />
        </button>
        <div>
          <h2 className="text-xs font-black text-white tracking-[3px] uppercase italic">Field Incident</h2>
          <p className="text-[9px] text-cyan-500 font-bold uppercase tracking-widest mt-0.5">Transmission Unit: Delta-4</p>
        </div>
      </header>

      <motion.form 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleSubmit} 
        className="p-6 space-y-8"
      >
        {/* Core Intel Section */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-1.5 h-4 bg-cyan-500 rounded-full"></div>
            <label className="text-[10px] text-slate-400 font-black tracking-[4px] uppercase">Incident Parameters</label>
          </div>
          
          <div className="relative">
            <Layers size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-cyan-500/50" />
            <select
              className="input-cyber pl-12 py-4 appearance-none"
              value={formData.crime_type}
              onChange={(e) => setFormData({...formData, crime_type: e.target.value})}
              required
            >
              <option value="">CRIME CATEGORY</option>
              <option value="Theft">THEFT / ROBBERY</option>
              <option value="Assault">PHYSICAL ASSAULT</option>
              <option value="Cybercrime">CYBERCRIME</option>
              <option value="Missing Person">MISSING PERSON</option>
              <option value="Harassment">HARASSMENT</option>
              <option value="Other">OTHER INCIDENT</option>
            </select>
          </div>

          <div className="relative">
            <textarea
              placeholder="DETAILED DESCRIPTION OF INTEL..."
              className="input-cyber min-h-[140px] resize-none pt-4"
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              required
            ></textarea>
            <div className="absolute bottom-4 right-4 text-[9px] text-slate-600 font-black uppercase tracking-widest">Text Link Active</div>
          </div>
        </section>

        {/* Routing & Geo Section */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-1.5 h-4 bg-cyan-500 rounded-full"></div>
            <label className="text-[10px] text-slate-400 font-black tracking-[4px] uppercase">Routing & Geo-Lock</label>
          </div>
          
          <div className="relative">
            <MapPin size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-cyan-500/50" />
            <input
              type="text"
              placeholder="INCIDENT LOCALITY (AUTO-DETECTED)"
              className="input-cyber pl-12"
              value={formData.location_name}
              onChange={(e) => setFormData({...formData, location_name: e.target.value})}
            />
            <div className="absolute right-4 top-1/2 -translate-y-1/2 flex items-center gap-2">
               <span className={`text-[8px] font-black uppercase ${locationStatus === 'locked' ? 'text-green-500' : 'text-yellow-500'}`}>
                 {locationStatus}
               </span>
               <Wifi size={12} className={locationStatus === 'locked' ? 'text-green-500' : 'text-yellow-500 animate-pulse'} />
            </div>
          </div>

          <div className="relative">
            <ShieldAlert size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-cyan-500/50" />
            <select
              className="input-cyber pl-12 py-4 appearance-none"
              value={formData.selected_station}
              onChange={(e) => setFormData({...formData, selected_station: e.target.value})}
              required
            >
              <option value="">TARGET JURISDICTION</option>
              <option value="AUTO" className="text-cyan-400 font-bold italic">-- AUTO-ASSIGN NEAREST STATION --</option>
              {stations.map(s => (
                <option key={s.id} value={s.name} className="bg-slate-900">{s.name}</option>
              ))}
            </select>
          </div>
        </section>

        {/* Visual Evidence Area */}
        <section className="space-y-4">
           <div className="flex items-center gap-2 mb-2">
            <div className="w-1.5 h-4 bg-cyan-500 rounded-full"></div>
            <label className="text-[10px] text-slate-400 font-black tracking-[4px] uppercase">Visual Artifacts</label>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-28 glass-card border-dashed border-white/10 flex flex-col items-center justify-center gap-2 text-slate-500 hover:border-cyan-500/50 hover:text-cyan-400 transition-all cursor-pointer group">
              <Camera size={24} className="group-hover:scale-110 transition-transform" />
              <span className="text-[9px] uppercase font-black tracking-[2px]">Capture Frame</span>
            </div>
            <div className="h-28 glass-card border-dashed border-white/10 flex flex-col items-center justify-center gap-2 text-slate-500 hover:border-cyan-500/50 hover:text-cyan-400 transition-all cursor-pointer group">
              <UploadCloud size={24} className="group-hover:scale-110 transition-transform" />
              <span className="text-[9px] uppercase font-black tracking-[2px]">Attach Node</span>
            </div>
          </div>
        </section>

        <div className="p-4 bg-cyan-500/5 border border-cyan-500/10 rounded-2xl flex gap-4">
          <AlertTriangle size={20} className="text-cyan-500 shrink-0" />
          <p className="text-[10px] text-slate-500 uppercase leading-loose tracking-widest italic">
            I VERIFY THAT THE ABOVE INTEL IS ACCURATE. FALSE REPORTING WILL TRIGGER <span className="text-cyan-400 font-bold underline">COUNTER-PROTOCOL 8</span>.
          </p>
        </div>

        <button 
          type="submit" 
          disabled={loading}
          className="btn-cyber w-full py-5 !bg-cyan-600 hover:!bg-cyan-500 shadow-[0_10px_30px_rgba(8,145,178,0.3)]"
        >
          {loading ? "MODULATING SIGNAL..." : (
            <>
              TRANSMIT INCIDENT INTEL <Send size={20} className="ml-2" />
            </>
          )}
        </button>
      </motion.form>
    </div>
  );
};

export default FIRForm;
